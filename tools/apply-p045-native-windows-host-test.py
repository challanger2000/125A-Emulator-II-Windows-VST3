#!/usr/bin/env python3
"""P045: add strict real-Windows VST3 factory/IBStream persisted-native tests.

Installed only AFTER the P029/P032 real factory tests. P044 was independently
passed with actual original ROM/media on the owner's Windows machine.
"""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOST=ROOT/"upstream/eii-emu/tools/vst3_host_test.cpp"

def one(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"P045 {label} anchor count {n}, wanted 1")
    return s.replace(old,new,1)

def patch(s):
    if "P045 ACTUAL WINDOWS VST3 NATIVE DAC DEFAULT" in s:
        raise RuntimeError("P045 test already installed")
    if "P032 S3528 REAL WINDOWS DEFAULT" not in s:
        raise RuntimeError("P045 requires existing P032 Windows factory tests")
    s=one(s,
        '                  "P032 S3528 REAL WINDOWS DEFAULT ON with original EII model 2");',
        '                  "P032 S3528 REAL WINDOWS DEFAULT ON with original EII model 2");\n'
        '            check(fresh.find("\\nnative=1\\n")!=std::string::npos,\n'
        '                  "P045 ACTUAL WINDOWS VST3 NATIVE DAC DEFAULT ON with original EII model 2 and S3528");',
        "new instance default ON")
    s=one(s,
        'const auto oldProject=replaceKey(replaceKey(fresh,"model","4"),"s3528","0");',
        'const auto oldProject=replaceKey(replaceKey(replaceKey(fresh,"model","4"),"s3528","0"),"native","0");',
        "historical project native=OFF fixture")
    s=one(s,
        '                  "P032 old saved CEM project retains S3528 bypass OFF");',
        '                  "P032 old saved CEM project retains S3528 bypass OFF");\n'
        '            check(in.getState().find("\\nnative=0\\n")!=std::string::npos,\n'
        '                  "P045 old saved project retains explicit native DAC bypass OFF");',
        "historical project must remain OFF")
    s=one(s,
        '                  "P032 new original EII still has reconstruction ON after old project close");',
        '                  "P032 new original EII still has reconstruction ON after old project close");\n'
        '            check(in.getState().find("\\nnative=1\\n")!=std::string::npos,\n'
        '                  "P045 new EII still has native DAC ON after closing historical native=OFF project");',
        "new instance stays ON after old song")
    s=one(s,
        'const auto intentionalCem=replaceKey(replaceKey(fresh,"model","4"),"s3528","0");',
        'const auto intentionalCem=replaceKey(replaceKey(replaceKey(fresh,"model","4"),"s3528","0"),"native","0");',
        "explicit saved user default fixture native OFF")
    s=one(s,
        '                  "P032 explicit user preference S3528 bypass OFF remains honored");',
        '                  "P032 explicit user preference S3528 bypass OFF remains honored");\n'
        '            check(in.getState().find("\\nnative=0\\n")!=std::string::npos,\n'
        '                  "P045 explicit saved user preference native OFF remains honored");',
        "explicit saved user preference native OFF")
    s=one(s,
        '                  "P032 removing user override restores EII original S3528 ON");',
        '                  "P032 removing user override restores EII original S3528 ON");\n'
        '            check(in.getState().find("\\nnative=1\\n")!=std::string::npos,\n'
        '                  "P045 removing explicit saved native=0 preference restores EII native=1");',
        "restoring first-run native ON")
    return s

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    args=p.parse_args()
    s=HOST.read_text(encoding="utf-8")
    updated=patch(s)
    if args.verify:
        print("P045 actual Windows VST3 native factory/project/global preferences: TEST PATCH PREFLIGHT PASS")
    else:
        HOST.write_text(updated,encoding="utf-8",newline="\n")
        print("P045 real Windows COM factory and project/user-default native=ON/OFF acceptance installed")
if __name__=="__main__":
    main()
