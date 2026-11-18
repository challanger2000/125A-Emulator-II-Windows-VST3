#!/usr/bin/env python3
"""Augment the P004 real COM/IBStream host test with P014 pending transactions."""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"upstream/eii-emu/tools/vst3_host_test.cpp"
def patch(s):
    a='''        check(first.setState(setting),"P004 legacy VST3 project state remains loadable");
        check(first.getState()==setting,"P004 legacy project clears embedded sample bank");
        first.shutdown();module.reset();'''
    b='''        check(first.setState(setting),"P004 legacy VST3 project state remains loadable");
        check(first.getState()==setting,"P004 legacy project clears embedded sample bank");

        // P014: no private EII ROM is needed to validate the REAL VST3 COM
        // host state transaction: a pending WAV/firmware bank capture must
        // preserve last committed bank and the explicit pending marker.
        const auto pending=replaceKey(setting,"bankpending","1");
        const auto pendingWithBank=encode(pending,disk);
        check(first.setState(pendingWithBank),"P014 real VST3 accepts pending song state");
        check(first.getState()==pendingWithBank,
              "P014 real VST3 preserves last committed bank AND pending marker");
        auto badPending=replaceKey(setting,"bankpending","invalid");
        const auto corruptPending=encode(badPending,disk);
        check(!first.setState(corruptPending),"P014 rejects corrupt pending marker");
        check(first.getState()==pendingWithBank,
              "P014 failed state load cannot erase preceding pending song");
        check(first.setState(pending),"P014 real VST3 accepts pending-without-bank state");
        check(first.getState()==pending,
              "P014 real VST3 saves pending warning even when no bank is committed");
        check(first.setState(full),"P014 real VST3 accepts later committed bank");
        check(first.getState()==full,"P014 committed bank clears pending warning");
        first.shutdown();module.reset();'''
    n=s.count(a)
    if n!=1:raise RuntimeError(f"P014 host test expected one P004 anchor, found {n}")
    return s.replace(a,b,1)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    s=SRC.read_text(encoding="utf-8")
    if a.verify:patch(s);print("P014 real COM host-state pending test anchors PASS");return
    SRC.write_text(patch(s),encoding="utf-8",newline="\n")
    print("P014 pending-bank actual VST3 COM/IBStream host tests installed")
if __name__=="__main__":main()
