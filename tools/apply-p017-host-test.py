#!/usr/bin/env python3
"""P017: real Windows VST3 IComponent project-state roundtrip with synthetic HDD."""
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"upstream/eii-emu/tools/vst3_host_test.cpp"
def patch(s):
    include='#include "125a_portable_state.h"'
    if s.count(include)!=1:raise RuntimeError("P017 host codec include anchor missing")
    s=s.replace(include,include+'\n#include "125a_portable_hdd.h"',1)
    a='''        check(first.setState(full),"P014 real VST3 accepts later committed bank");
        check(first.getState()==full,"P014 committed bank clears pending warning");
        first.shutdown();module.reset();'''
    b='''        check(first.setState(full),"P014 real VST3 accepts later committed bank");
        check(first.getState()==full,"P014 committed bank clears pending warning");
        // P017 exercises real Windows COM IComponent+IBStream, not a codec
        // mock. This is an anonymous synthetic 20-MB original HDD image.
        std::vector<std::uint8_t> rawHdd(22597632,0x6c);
        for(unsigned k=0;k<17;++k)
            for(unsigned i=0;i<8192;++i)
                rawHdd[unsigned(k)*400000u+i+127u]=
                    std::uint8_t((i*11u+k*19u+(i>>4))&255u);
        const auto hddProject=encodeProject(setting,disk,rawHdd);
        check(hddProject.size()>full.size()&&hddProject.size()<maxProjectStateBytes,
              "P017 synthetic HDD stored with correct bounded VST3 state length");
        check(first.setState(hddProject),"P017 real VST3 accepts full original HDD song state");
        check(first.getState()==hddProject,
              "P017 real VST3 re-saves exact original HDD and last bank");
        check(second.create(factory,cid,host),"P017 independent second VST3 instance created");
        if(second.component){
            check(second.setState(hddProject),"P017 second VST3 loads HDD state");
            check(second.getState()==hddProject,
                  "P017 second VST3 independently re-saves HDD state");
            check(first.getState()==hddProject,"P017 original instance still owns its HDD");
            second.shutdown();
        }
        const auto badHdd=replaceKey(setting,"hddpending","invalid");
        check(!first.setState(encodeProject(badHdd,{},rawHdd)),
              "P017 invalid persistent HDD warning cannot replace song");
        check(first.getState()==hddProject,
              "P017 failed HDD state parse leaves valid first song intact");
        check(first.setState(full),"P017 legacy bank song loads after HDD song");
        check(first.getState()==full,"P017 previous HDD is cleared on legacy song");
        first.shutdown();module.reset();'''
    n=s.count(a)
    if n!=1:raise RuntimeError(f"P017 host probe anchor count {n}, expected 1")
    return s.replace(a,b,1)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    a=ap.parse_args()
    s=SRC.read_text(encoding="utf-8")
    new=patch(s)
    if a.verify:print("P017 Windows COM host HDD project-state test source PASS");return
    SRC.write_text(new,encoding="utf-8",newline="\n")
    print("P017 Windows COM VST3 HDD + bank / multiple-instance project test installed")
if __name__=="__main__":main()
