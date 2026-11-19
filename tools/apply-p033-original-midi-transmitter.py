#!/usr/bin/env python3
"""P033: bounded, clocked original SCN2651 MIDI TX holding/shift registers.

P033 is the genuine firmware-to-UART *hardware* leg, not a VST3 output bus
or a virtual MIDI cable. The underlying original Z80 and ROM are unmodified.
"""
import argparse
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"
UART=UP/"src/midi_serial.h"
MACHINE=UP/"src/machine.cpp"

def one(source,a,b,label):
    matches=source.count(a)
    if matches!=1:raise RuntimeError(f"P033 {label}: expected 1 source anchor, got {matches}")
    return source.replace(a,b,1)

def patch_uart(s):
    s=one(s,
        "// framing/parity, synchronous modes and host MIDI OUT remain outside this path.",
        "// framing/parity, synchronous modes and VST3 host MIDI OUT stay separate.\n"
        "// P033 adds original firmware-controlled TX holding/shift timing.",
        "scope comment")
    s=one(s,
        "    std::uint64_t received=0,reads=0,overruns=0,rejected=0;",
        """    std::uint64_t received=0,reads=0,overruns=0,rejected=0;
    // SCN2651 THR + shift register, with the EII 500 kHz / 16 external TX
    // clock and 8N1 frame (31250 baud, 1280 cycles at 4MHz). No bit-edge
    // waveform is synthesized: only the exact completed character boundary.
    struct TxFrame {std::uint8_t byte=0;std::uint64_t tick=0;};
    static constexpr std::uint64_t txCharacterTicks=1280;
    static constexpr unsigned txCapacity=512;
    std::uint64_t txCompleted=0,txRejected=0,txDropped=0;
    bool txEnabled() const noexcept{return midiMode()&&(command&1)!=0;}
    bool txReady() const noexcept{return txEnabled()&&!txHolding_;}
    bool txEmpty() const noexcept{return !txShifting_&&!txHolding_;}
    bool txBusy() const noexcept{return txShifting_||txHolding_;}
    bool writeTxData(std::uint8_t byte,std::uint64_t now) noexcept {
        if(!txEnabled()){++txRejected;return false;}
        if(!txShifting_ && !(command&8)) {
            txShifting_=true;txShift_=byte;txEnd_=now+txCharacterTicks;
            return true;
        }
        if(txHolding_){++txRejected;return false;}
        txHolding_=true;txHold_=byte;return true;
    }
    void advanceTx(std::uint64_t now) noexcept {
        if(txShifting_&&now>=txEnd_) {
            const TxFrame frame{txShift_,txEnd_};
            if(txCount_==txCapacity){++txDropped;txHead_=(txHead_+1)%txCapacity;--txCount_;}
            txFrames_[(txHead_+txCount_)%txCapacity]=frame;++txCount_;
            ++txCompleted;
            txShifting_=false;
            // A completed shift frees the second holding register. New TX
            // does not start if firmware disabled TxEN or requested BREAK.
            if(txHolding_&&txEnabled()&&!(command&8)){
                txShift_=txHold_;txHolding_=false;txShifting_=true;
                txEnd_=frame.tick+txCharacterTicks;
            }
        }
        if(!txShifting_&&txHolding_&&txEnabled()&&!(command&8)){
            txShift_=txHold_;txHolding_=false;txShifting_=true;
            txEnd_=now+txCharacterTicks;
        }
    }
    bool popTx(TxFrame& out) noexcept {
        if(!txCount_)return false;
        out=txFrames_[txHead_];txHead_=(txHead_+1)%txCapacity;--txCount_;
        return true;
    }
    unsigned txPending() const noexcept{return txCount_;}
""",
        "UART transmitter model")
    s=one(s,
        "        // DCD/DSR tied low on EII; TX holding-register timing is not modeled.\n"
        "        return std::uint8_t(0xc0|((command&1)?1:0)|(ready?2:0)|error_);",
        "        // DCD/DSR tied low on the EII. SR0=THR free; SR2=shift empty.\n"
        "        return std::uint8_t(0xc0|(txReady()?1:0)|(ready?2:0)|(txEmpty()?4:0)|error_);",
        "UART TXRDY/TXEMT status")
    s=one(s,
        "    std::uint8_t value_=0,error_=0;",
        """    std::uint8_t value_=0,error_=0;
    std::uint8_t txShift_=0,txHold_=0;
    bool txShifting_=false,txHolding_=false;
    std::uint64_t txEnd_=0;
    std::array<TxFrame,txCapacity> txFrames_{};
    unsigned txHead_=0,txCount_=0;""",
        "bounded transmitter state")
    return s

def patch_machine(s):
    s=one(s,
        '        if(p>=4&&p<=7) {if(p==4 && serialTx.size()<65536) serialTx+=char(v);return;}',
        '''        if(p>=4&&p<=7) {
            if(p==4){
                // Original Z80 OUT4 writes the SCN2651 TX holding register.
                // Diagnostic/legacy serial capture is retained unchanged.
                midiSerial.writeTxData(v,ticks);
                if(serialTx.size()<65536)serialTx+=char(v);
            }
            return;
        }''',"actual original CPU OUT4 -> UART THR")
    s=one(s,
        '        midiWire.advance(ticks,midiSerial);',
        '        midiWire.advance(ticks,midiSerial);\n'
        '        if(midiSerial.txBusy())midiSerial.advanceTx(ticks);',
        "4MHz serial transmitter clock")
    s=one(s,
        '    o<<"PIO transfers main->scanner="<<mainToScanTransfers<<" scanner->main="<<scanToMainTransfers<<"\\n";',
        '''    o<<"PIO transfers main->scanner="<<mainToScanTransfers<<" scanner->main="<<scanToMainTransfers<<"\\n";
    o<<"SCN2651 original MIDI TX complete="<<midiSerial.txCompleted
     <<" buffered="<<midiSerial.txPending()<<" rejected="<<midiSerial.txRejected
     <<" capture drops="<<midiSerial.txDropped
     <<" busy="<<midiSerial.txBusy()<<" (host MIDI OUT routing not yet implemented)\\n";''',
        "diagnostic original TX visibility")
    return s

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    args=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError(f"P033 upstream mismatch: {sha}")
    oldUART=UART.read_text(encoding="utf-8")
    oldMachine=MACHINE.read_text(encoding="utf-8")
    newUART=patch_uart(oldUART)
    newMachine=patch_machine(oldMachine)
    if args.verify:
        print("P033 source pinned SCN2651 UART TX original Z80 IO/clock/status anchors PASS")
    else:
        UART.write_text(newUART,encoding="utf-8",newline="\n")
        MACHINE.write_text(newMachine,encoding="utf-8",newline="\n")
        print("P033 original SCN2651 timed TX shift/THR + bounded completed bytes installed")
if __name__=="__main__": main()
