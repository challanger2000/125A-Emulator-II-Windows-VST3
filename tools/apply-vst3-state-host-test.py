#!/usr/bin/env python3
"""P004 Windows executable host-state validation, source-pinned and non-product."""
import argparse
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
P=UP/"tools/vst3_host_test.cpp"
SHA="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,a,b,what):
    n=s.count(a)
    if n!=1:raise RuntimeError(f"Host probe patch {what}: {n} anchor matches")
    return s.replace(a,b,1)

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--verify",action="store_true")
    a=arg.parse_args()
    if subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()!=SHA:
        raise RuntimeError("Host probe upstream SHA mismatch")
    s=P.read_text(encoding="utf-8")
    if "project-state" in s:raise RuntimeError("Duplicate host project-state probe")
    s=one(s,'#include "vst3/eii_vst3_ids.h"',
          '#include "vst3/eii_vst3_ids.h"\n#include "125a_portable_state.h"',
          "test codec include")
    mark='    auto host=owned(new HostApplication());'
    add=r'''
    if(argc>5&&std::string(argv[5])=="project-state"){
        using namespace eii::portable;
        Instance first,second;
        check(first.create(factory,cid,host),"P004 host created first real COM component");
        if(!first.component){module.reset();return 1;}
        const auto initial=first.getState();
        const auto setting=replaceKey(initial,"autoboot","0");
        std::vector<std::uint8_t> disk(bankBytes);
        for(std::size_t i=0;i<disk.size();++i)
            disk[i]=std::uint8_t((i*31+(i>>8)+7)&255u);
        const auto full=encode(setting,disk);
        check(full.size()>bankBytes&&full.size()<(1<<20),
              "P004 complete original bank fits within VST3 state bound");
        check(first.setState(full),"P004 real VST3 IComponent::setState accepts complete embedded bank");
        check(first.getState()==full,"P004 real VST3 getState identical binary bank + original settings");
        auto corrupt=full;corrupt[corrupt.size()-51]^=0x40;
        check(!first.setState(corrupt),"P004 real VST3 rejects corrupt bank before state replacement");
        check(first.getState()==full,"P004 failed setState preserves committed bank");
        check(second.create(factory,cid,host),"P004 independent second VST3 COM component");
        if(second.component){
            check(second.setState(full),"P004 second VST3 instance restores same bank");
            check(second.getState()==full,"P004 second instance re-saves identical portable bank");
            check(first.getState()==full,"P004 multiple instances remain isolated");
            auto otherDisk=disk;otherDisk[bankDataOffset+32244]^=0x41;
            const auto distinct=encode(setting,otherDisk);
            check(second.setState(distinct),"P004 second VST3 instance accepts distinct sample bank");
            check(second.getState()==distinct&&first.getState()==full,
                  "P004 separate instances retain separate original banks");
            second.shutdown();
        }
        check(first.setState(setting),"P004 legacy VST3 project state remains loadable");
        check(first.getState()==setting,"P004 legacy project clears embedded sample bank");
        first.shutdown();module.reset();
        std::cout<<(failures?"P004 REAL VST3 STATE HOST FAIL ":"P004 REAL VST3 STATE HOST PASS ")
                 <<failures<<" failure(s)\n";
        return failures?1:0;
    }
'''
    s=one(s,mark,mark+'\n'+add,"state host execution")
    if a.verify:
        print("P004 Windows host IBStream state-test anchors PASS")
        return
    P.write_text(s,encoding="utf-8",newline="\n")
    print("P004 native real VST3 host test applied locally")
if __name__=="__main__":
    main()
