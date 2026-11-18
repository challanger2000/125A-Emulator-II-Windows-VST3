#!/usr/bin/env python3
"""P018 real Windows VST3 COM IBStream C3 per-song setting tests."""
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"upstream/eii-emu/tools/vst3_host_test.cpp"
def patch(s):
    a='''        check(first.setState(full),"P017 legacy bank song loads after HDD song");
        check(first.getState()==full,"P017 previous HDD is cleared on legacy song");
        first.shutdown();module.reset();'''
    b='''        check(first.setState(full),"P017 legacy bank song loads after HDD song");
        check(first.getState()==full,"P017 previous HDD is cleared on legacy song");

        // P018 real Windows IComponent + IBStream project save and reload.
        // The root-note mapping is a per-song host MIDI setting, not a
        // rewrite of the original ROM, DRAM or performance bank.
        const auto c3Settings=replaceKey(setting,"wavmidic3","1");
        const auto c3Song=encodeProject(c3Settings,disk,rawHdd);
        check(first.setState(c3Song),"P018 VST3 accepts MIDI C3 song with HDD");
        check(first.getState()==c3Song,
              "P018 VST3 persists exact C3 MIDI option with user bank + HDD");
        check(first.setState(setting),"P018 older legacy project loads original MIDI");
        check(first.getState()==setting,
              "P018 older song opens without forcing C3 transpose");
        const auto brokenC3=replaceKey(setting,"wavmidic3","9");
        check(!first.setState(encodeProject(brokenC3,{},rawHdd)),
              "P018 malformed keyboard note map rejected");
        check(first.getState()==setting,
              "P018 rejected root key cannot erase previous song state");
        first.shutdown();module.reset();'''
    if s.count(a)!=1:raise RuntimeError(f"P018 host test expected one P017 anchor, found {s.count(a)}")
    return s.replace(a,b,1)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    args=ap.parse_args()
    current=PATH.read_text(encoding="utf-8")
    result=patch(current)
    if args.verify:
        print("P018 Windows COM VST3 root-note song-state test anchors PASS")
        return
    PATH.write_text(result,encoding="utf-8",newline="\n")
    print("P018 real VST3 MIDI C3 + HDD + bank host state tests installed")
if __name__=="__main__":main()
