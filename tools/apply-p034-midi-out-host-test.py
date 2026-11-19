#!/usr/bin/env python3
"""P034: real Windows VST3 COM output event-bus + fail-closed MIDI OUT test.

No original private firmware/assets. The synthetic test MUST NOT emit MIDI
from incoming host notes without actual firmware TX writes.
"""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOST=ROOT/"upstream/eii-emu/tools/vst3_host_test.cpp"

def patch(s):
    if "P034 REAL WINDOWS ORIGINAL MIDI OUT BUS" in s:
        raise RuntimeError("P034 real Windows MIDI output test already applied")
    if "P029 ACTUAL WINDOWS VST3 DEFAULT" not in s or "P032 S3528 REAL WINDOWS DEFAULT" not in s:
        raise RuntimeError("P034 requires P029/P032 real Windows host regression overlays")
    marker="    auto host=owned(new HostApplication());"
    if s.count(marker)!=1:
        raise RuntimeError(f"P034 host main anchor count {s.count(marker)}")
    block=r'''
    if(argc>5&&std::string(argv[5])=="original-midi-out-bus"){
        // Instantiate the actual packaged VST3. This intentionally has NO
        // real original firmware. Existence of an event bus cannot fabricate
        // output MIDI unless original SCN2651 TX completed a character.
        Instance in;
        check(in.create(factory,cid,host),
              "P034 real Windows factory creates original MIDI OUT VST3");
        if(!in.component)throw std::runtime_error("P034 Windows COM component unavailable");
        check(in.component->getBusCount(kEvent,kInput)==1,
              "P034 VST3 existing incoming MIDI event bus preserved");
        check(in.component->getBusCount(kEvent,kOutput)==1,
              "P034 real Windows VST3 exposes exactly one MIDI event output bus");
        BusInfo info{};
        check(in.component->getBusInfo(kEvent,kOutput,0,info)==kResultOk&&
              info.channelCount==16&&info.busType==kMain,
              "P034 actual original MIDI output bus 16 channels/main");
        check(in.component->activateBus(kEvent,kOutput,0,true)==kResultTrue,
              "P034 real VST3 MIDI event output bus can activate");
        auto noBoot=replaceKey(in.getState(),"autoboot","0");
        noBoot=replaceKey(noBoot,"rom","");
        check(in.setState(noBoot),"P034 real VST3 disabled original boot accepted");
        check(in.start(48000,kOffline,512),"P034 actual Windows VST3 offline processor");
        EventList outgoing;
        in.data.outputEvents=&outgoing;
        for(int i=0;i<5;++i){
            EventList input;
            if(i==0){Event e=note(true,60,30);input.addEvent(e);}
            if(i==1){Event e=note(false,60,230);input.addEvent(e);}
            check(in.process(&input),
                  "P034 real Windows VST3 consumes host MIDI without fake output");
        }
        in.data.outputEvents=nullptr;
        check(outgoing.getEventCount()==0,
              "P034 host incoming notes never generate fake original TX events");
        check(in.status("midioutdrops")=="0"&&in.status("midioutpreboot")=="0",
              "P034 actual VST3 original MIDI output diagnostics remain clean");
        in.shutdown();
        module.reset();
        std::cout<<(failures?"P034 REAL WINDOWS ORIGINAL MIDI OUT BUS FAIL ":
                             "P034 REAL WINDOWS ORIGINAL MIDI OUT BUS PASS ")
                 <<failures<<" failure(s)\n";
        return failures?1:0;
    }
'''
    return s.replace(marker,marker+"\n"+block,1)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--verify",action="store_true")
    a=parser.parse_args()
    old=HOST.read_text(encoding="utf-8")
    edited=patch(old)
    if a.verify:
        print("P034 real Windows original MIDI out COM host insertion preflight PASS")
    else:
        HOST.write_text(edited,encoding="utf-8",newline="\n")
        print("P034 real Windows output bus / no-fake-TX COM acceptance integrated")
if __name__=="__main__":main()
