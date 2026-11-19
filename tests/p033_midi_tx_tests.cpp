#include "midi_serial.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>

static void require(bool good,const char* msg){if(!good)throw std::runtime_error(msg);}
int main()try{
    using U=eii::MidiSerial2651;
    U tx;
    U::TxFrame frame{};
    // Factory power-on does not enable fake MIDI data.
    require(!tx.writeTxData(0x90,17)&&tx.txRejected==1,"TX before original firmware TxEN MUST fail closed");
    tx.writeMode(0x4e);tx.writeMode(0);tx.writeCommand(0x27); // EII firmware: 8N1, 500k/16, Tx/Rx
    require(tx.midiMode()&&tx.txEnabled()&&tx.txReady()&&tx.txEmpty(),"original EII initial TxRDY/TxEMT");
    require((tx.status()&7)==5,"SCN2651 SR0 TXRDY and SR2 TXEMT when idle");
    require(tx.writeTxData(0x90,17),"original CPU first OUT4 starts shift");
    require(tx.txReady()&&!tx.txEmpty()&&((tx.status()&5)==1),"THR frees immediately after transferring into shift");
    require(tx.writeTxData(60,18),"second OUT4 queues THR while shift runs");
    require(!tx.txReady()&&!tx.txEmpty()&&!(tx.status()&1),"THR full -> SR0 busy");
    require(!tx.writeTxData(127,19)&&tx.txRejected==2,"full second register rejects third byte, no fabricated FIFO");
    tx.advanceTx(1296);require(!tx.popTx(frame),"no premature TX before 1280 original cycles");
    tx.advanceTx(1297);
    require(tx.popTx(frame)&&frame.byte==0x90&&frame.tick==1297,"first transmitted MIDI byte has precise 320us completion");
    require(tx.txReady()&&!tx.txEmpty(),"queued second byte immediately moves from THR to shift");
    tx.advanceTx(2576);require(!tx.popTx(frame),"no early second MIDI byte");
    tx.advanceTx(2577);
    require(tx.popTx(frame)&&frame.byte==60&&frame.tick==2577&&tx.txEmpty(),"second MIDI byte shift completion 1280 ticks later");
    require((tx.status()&5)==5&&tx.txCompleted==2,"TXRDY and TXEMT return only when both registers empty");
    require(!tx.popTx(frame),"TX completion ring drains once only");

    // Finish the already active shift on TxEN disable (documented SCN2651).
    require(tx.writeTxData(0xF8,3000),"realtime MIDI start");
    tx.writeCommand(0x26);
    require(!tx.txEnabled()&&!tx.txReady(),"disabled TX deasserts ready");
    tx.advanceTx(4279);require(!tx.popTx(frame),"disabled TX active shift not prematurely terminated");
    tx.advanceTx(4280);
    require(tx.popTx(frame)&&frame.byte==0xF8&&frame.tick==4280&&tx.txEmpty(),
            "TxEN disable completes already shifting character");

    // BREAK requests hold TxD spacing only AFTER current character; a
    // queued holding byte cannot escape until command clears BREAK.
    tx.writeCommand(0x27);tx.writeTxData(0x91,5000);tx.writeTxData(65,5001);
    tx.writeCommand(0x2f); // CR3 force BREAK after current shift
    tx.advanceTx(6280);
    require(tx.popTx(frame)&&frame.byte==0x91&&frame.tick==6280,"BREAK does not truncate current shift");
    require(!tx.txEmpty()&&!tx.txReady()&&!tx.popTx(frame),"BREAK holds queued byte");
    tx.writeCommand(0x27);tx.advanceTx(6281);tx.advanceTx(7561);
    require(tx.popTx(frame)&&frame.byte==65&&frame.tick==7561&&tx.txEmpty(),
            "clearing BREAK resumes buffered TX without duplicated bytes");

    // Switching mode to unsupported diagnostic format cannot invent MIDI bytes.
    tx.readCommand();tx.writeMode(0xca);tx.writeMode(0x3e);
    require(!tx.txEnabled()&&!tx.writeTxData(0x90,8000),"non-EII serial mode not silently emitted as MIDI");

    U flood;
    flood.writeMode(0x4e);flood.writeMode(0);flood.writeCommand(0x27);
    for(unsigned i=0;i<U::txCapacity+7;++i){
        auto now=10000+std::uint64_t(i)*U::txCharacterTicks;
        require(flood.writeTxData(std::uint8_t(i&127),now),"sequential unpaced TX retained");
        flood.advanceTx(now+U::txCharacterTicks);
    }
    require(flood.txCompleted==U::txCapacity+7&&flood.txDropped==7&&
            flood.txPending()==U::txCapacity,"bounded TX observation ring never grows");
    for(unsigned i=0;i<U::txCapacity;++i){
        require(flood.popTx(frame),"all retained TX frames recoverable");
        require(frame.byte==std::uint8_t((i+7)&127),"overflow drops OLDEST completed bytes only");
        require(frame.tick==10000+(std::uint64_t(i+8)*U::txCharacterTicks),
                "bounded capture preserves original completion timestamps");
    }
    require(!flood.popTx(frame)&&flood.txPending()==0,"bounded TX drain finishes");

    // Old firmware RX path must stay independent of TX.
    tx.readCommand();tx.writeMode(0x4e);tx.writeMode(0);tx.writeCommand(0x27);
    const std::array<std::uint8_t,3> note{0x90,48,100};
    eii::MidiWire wire;
    require(wire.enqueue(note,6000),"prior original host MIDI receive queue intact");
    wire.advance(7280,tx);
    require(tx.ready&&tx.readData()==0x90,"RX data unchanged with TX extension");

    std::cout<<"P033 SCN2651 timed original MIDI TX THR/shift/SR0/SR2/BREAK,"
                " 8N1-320us/overflow/disabled/RX isolation PASS\n";
}catch(const std::exception& e){std::cerr<<"P033 FAIL: "<<e.what()<<"\n";return 1;}
