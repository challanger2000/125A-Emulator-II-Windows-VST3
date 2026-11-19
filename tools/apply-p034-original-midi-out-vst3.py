#!/usr/bin/env python3
"""P034: original SCN2651 completed bytes -> sample-timed VST3 MIDI OUT bus.
Never echo host incoming notes or create firmware shortcuts.
The VST3 output cannot represent arbitrary MIDI 1.0 byte streams: only
channel voice messages are deliberately exposed as Steinberg output events.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"
ENGINE=UP/"src/vst3/plugin_engine.h"
PRODUCT=UP/"src/vst3/eii_vst3.cpp"
HEADER=UP/"src/125a_original_midi_out.h"

def one(src,old,new,label):
    n=src.count(old)
    if n!=1:raise RuntimeError(f"P034 {label}: {n} source anchors, expected 1")
    return src.replace(old,new,1)

def patch_engine(s):
    for required in ("bootGate_","autonomousBoot_","anchorHostPosLocal_","streamGeneration_",
                     "midiSerial.txBusy()"):
        if required not in s and required!="midiSerial.txBusy()":
            raise RuntimeError("P034 needs original P021 autonomously anchored host engine: "+required)
    s=one(s,
        '#include "vst3/rt_primitives.h"',
        '#include "vst3/rt_primitives.h"\n#include "125a_original_midi_out.h"',
        "pure original MIDI parser include")
    s=one(s,
        "    SpscQueue<HostEvent,8192> events_;",
        """    SpscQueue<HostEvent,8192> events_;
    // One producer: actual EII machine/Z80 owner. One consumer: host audio
    // callback. Output is independent of MIDI IN; never echo incoming notes.
    SpscQueue<midiout::Byte,8192> originalMidiOut_;
    std::atomic<std::uint64_t> originalMidiOutDrops_{0};
    std::atomic<std::uint64_t> originalMidiOutPreboot_{0};""",
        "owner->audio original MIDI output SPSC ring")
    s=one(s,
        "    std::uint64_t hostPos_=0,consumerEpoch_=0,nextPull_=0,consumerGeneration_=~std::uint64_t(0);float gainNow_=1;",
        """    std::uint64_t hostPos_=0,consumerEpoch_=0,nextPull_=0,consumerGeneration_=~std::uint64_t(0);float gainNow_=1;
    midiout::Assembler originalMidiParser_;
    std::uint64_t originalMidiConsumerEpoch_=0,originalMidiConsumerGeneration_=0;""",
        "audio-only output MIDI message state")
    s=one(s,
        "    std::int64_t minLead()const noexcept{return minLead_.load(std::memory_order_relaxed);}",
        """    std::uint64_t hostSamplePosition()const noexcept{return hostPos_;} // audio thread only
    template<class Sink>
    void drainOriginalMidiOut(std::uint64_t blockStart,int blockLength,Sink&& sink)noexcept{
        const auto epoch=epoch_.load(std::memory_order_acquire);
        const auto generation=streamGeneration_.load(std::memory_order_acquire);
        if(epoch!=originalMidiConsumerEpoch_||generation!=originalMidiConsumerGeneration_){
            originalMidiConsumerEpoch_=epoch;originalMidiConsumerGeneration_=generation;
            originalMidiParser_.reset();
        }
        if(blockLength<=0)return;
        const auto end=blockStart+std::uint64_t(blockLength);
        for(;;){
            const auto* next=originalMidiOut_.front();
            if(!next)break;
            const auto b=*next;
            if(b.epoch!=epoch||b.generation!=generation){originalMidiOut_.pop();continue;}
            if(b.frame>=end)break; // next future host block owns this byte
            originalMidiOut_.pop();
            midiout::Message msg{};
            if(originalMidiParser_.feed(b.value,msg)){
                const auto relative=b.frame>blockStart?b.frame-blockStart:0;
                sink(msg,int(std::min<std::uint64_t>(relative,std::uint64_t(blockLength-1))));
            }
        }
    }
    std::uint64_t originalMidiOutDrops()const noexcept{
        return originalMidiOutDrops_.load(std::memory_order_relaxed);
    }
    std::uint64_t originalMidiOutPreboot()const noexcept{
        return originalMidiOutPreboot_.load(std::memory_order_relaxed);
    }
    std::int64_t minLead()const noexcept{return minLead_.load(std::memory_order_relaxed);}""",
        "bounded MIDI OUT read with original output timing")
    s=one(s,
        '                machine_->run(n);',
        '''                machine_->run(n);
                // Drain *only completed* original SCN2651 transmitter bytes;
                // no direct host-note echo, no fake MIDI from voice allocation.
                MidiSerial2651::TxFrame completed{};
                while(machine_->midiSerial.popTx(completed)){
                    const auto epoch=epoch_.load(std::memory_order_acquire);
                    const auto tick=gOffset_+completed.tick;
                    if(autonomousBoot_.active()||
                       !bootGate_.load(std::memory_order_acquire)||
                       localAnchorEpoch_!=epoch||tick<anchorTickLocal_){
                        originalMidiOutPreboot_.fetch_add(1,std::memory_order_relaxed);
                        continue;
                    }
                    const auto rate=rate_.load(std::memory_order_relaxed);
                    const auto hostSample=anchorHostPosLocal_+
                        (tick-anchorTickLocal_)*std::uint64_t(rate)/cpuRate+
                        latency_.load(std::memory_order_relaxed);
                    const midiout::Byte packet{completed.byte,epoch,
                        streamGeneration_.load(std::memory_order_acquire),hostSample};
                    if(!originalMidiOut_.push(packet))
                        originalMidiOutDrops_.fetch_add(1,std::memory_order_relaxed);
                }''',
        "real Z80 owner TX output capture after original CPU machine run")
    return s

def patch_product(s):
    s=one(s,
        'if(type==kAudio&&dir==kOutput)return 1+auxOutputs;if(type==kAudio&&dir==kInput)return 1;if(type==kEvent&&dir==kInput)return 1;return 0;',
        'if(type==kAudio&&dir==kOutput)return 1+auxOutputs;if(type==kAudio&&dir==kInput)return 1;if(type==kEvent&&(dir==kInput||dir==kOutput))return 1;return 0;',
        "VST3 output event bus count")
    s=one(s,
        'else{bus.channelCount=16;copyAscii(bus.name,"MIDI In");}',
        'else{bus.channelCount=16;copyAscii(bus.name,dir==kOutput?"Original MIDI Out":"MIDI In");}',
        "original MIDI output bus identification")
    s=one(s,
        '    engine_->render(l,r,n,data.processMode==kOffline,anyJack?jacks.data():nullptr);',
        '''    const auto midiBlockStart=engine_->hostSamplePosition();
    engine_->render(l,r,n,data.processMode==kOffline,anyJack?jacks.data():nullptr);
    // Process output bytes *after* offline render: the emulation owner may
    // finish them while this same callback blocks on original PCM generation.
    // A failed/missing host outputEventList still drains the bounded stream.
    engine_->drainOriginalMidiOut(midiBlockStart,n,[&](const eii::vst::midiout::Message& msg,int offset){
        if(!data.outputEvents)return;
        Event e{};e.busIndex=0;e.sampleOffset=offset;
        const auto type=msg.status&0xf0;
        const auto ch=Steinberg::int16(msg.status&15);
        switch(type){
        case 0x80:case 0x90:{
            const bool on=type==0x90&&msg.data2!=0;
            e.type=on?Event::kNoteOnEvent:Event::kNoteOffEvent;
            if(on){e.noteOn.channel=ch;e.noteOn.pitch=msg.data1;
                e.noteOn.velocity=float(msg.data2)/127.f;e.noteOn.noteId=-1;}
            else{e.noteOff.channel=ch;e.noteOff.pitch=msg.data1;
                e.noteOff.velocity=float(msg.data2)/127.f;e.noteOff.noteId=-1;}
            break;
        }
        case 0xa0:
            e.type=Event::kPolyPressureEvent;e.polyPressure.channel=ch;
            e.polyPressure.pitch=msg.data1;e.polyPressure.pressure=float(msg.data2)/127.f;
            break;
        default:{
            e.type=Event::kLegacyMIDICCOutEvent;e.midiCCOut.channel=Steinberg::int8(ch);
            e.midiCCOut.value=Steinberg::int8(msg.data1);e.midiCCOut.value2=Steinberg::int8(msg.data2);
            e.midiCCOut.controlNumber=type==0xb0?msg.data1:
                type==0xc0?kCtrlProgramChange:type==0xd0?kAfterTouch:kPitchBend;
            if(type==0xb0)e.midiCCOut.value=Steinberg::int8(msg.data2);
            else if(type==0xc0||type==0xd0)e.midiCCOut.value2=0;
            break;
        }
        }
        // Host owns IEventList. addEvent may reject a full queue: fail
        // without blocking or allocating in the audio callback.
        (void)data.outputEvents->addEvent(e);
    });''',
        "VST3 original UART sample-aligned channel voice output")
    s=one(s,
        '"\\nmidiread="<<s.panel.midiRead',
        '"\\nmidiread="<<s.panel.midiRead<<"\\nmidioutdrops="<<engine_->originalMidiOutDrops()<<"\\nmidioutpreboot="<<engine_->originalMidiOutPreboot()',
        "real diagnostics expose original MIDI OUT counters")
    return s

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    a=ap.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError(f"P034 pinned original Emulator-II commit mismatch {sha}")
    oldEng=ENGINE.read_text(encoding="utf-8")
    oldVst=PRODUCT.read_text(encoding="utf-8")
    if "txCharacterTicks=1280" not in (UP/"src/midi_serial.h").read_text(encoding="utf-8"):
        raise RuntimeError("P034 requires P033 original SCN2651 transmitter hardware")
    if "originalMidiOut_" in oldEng:raise RuntimeError("P034 already applied")
    newEng=patch_engine(oldEng)
    newVst=patch_product(oldVst)
    if a.verify:
        print("P034 original MIDI TX -> VST3 outgoing event bus source-pinned preflight PASS")
    else:
        shutil.copyfile(ROOT/"src/125a_original_midi_out.h",HEADER)
        ENGINE.write_text(newEng,encoding="utf-8",newline="\n")
        PRODUCT.write_text(newVst,encoding="utf-8",newline="\n")
        print("P034 original UART MIDI OUT VST3 output bus/RT SPSC and channel voice conversion integrated")
if __name__=="__main__": main()
