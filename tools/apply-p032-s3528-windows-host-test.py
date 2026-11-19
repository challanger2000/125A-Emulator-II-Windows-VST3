#!/usr/bin/env python3
"""P032: strengthen the real Windows P029 VST3 factory/IBStream checks:
EII Model 2 AND the original S3528 reconstruction stage default ON.
Older/explicit user projects must retain S3528 OFF without global leakage.
"""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"upstream/eii-emu/tools/vst3_host_test.cpp"

def one(source,old,new,name):
    n=source.count(old)
    if n!=1:raise RuntimeError(f"P032 {name}: {n} anchors, wanted 1")
    return source.replace(old,new,1)

def patch(s):
    if "P029 ACTUAL WINDOWS VST3 DEFAULT" not in s:
        raise RuntimeError("P032 requires the real P029 Windows VST3 host test")
    if "P032 S3528 REAL WINDOWS DEFAULT" in s:
        raise RuntimeError("P032 real Windows host test already installed")
    s=one(s,'            fresh=in.getState();\n',
        '            fresh=in.getState();\n'
        '            check(fresh.find("\\ns3528=1\\n")!=std::string::npos,\n'
        '                  "P032 S3528 REAL WINDOWS DEFAULT ON with original EII model 2");\n',
        "first new instance S3528 default")
    s=one(s,'            const auto oldProject=replaceKey(fresh,"model","4");',
        '            const auto oldProject=replaceKey(replaceKey(fresh,"model","4"),"s3528","0");',
        "old CEM project reconstruction off fixture")
    s=one(s,'''            check(in.getState().find("\\nmodel=4\\n")!=std::string::npos,
                  "P029 saved project retains EIII-CEM3387 after host setState");''',
        '''            check(in.getState().find("\\nmodel=4\\n")!=std::string::npos,
                  "P029 saved project retains EIII-CEM3387 after host setState");
            check(in.getState().find("\\ns3528=0\\n")!=std::string::npos,
                  "P032 old saved CEM project retains S3528 bypass OFF");''',
        "legacy project remains off")
    s=one(s,'''            check(in.getState().find("\\nmodel=5\\n")!=std::string::npos,
                  "P029 second fresh instance remains EII after CEM project termination");''',
        '''            check(in.getState().find("\\nmodel=5\\n")!=std::string::npos,
                  "P029 second fresh instance remains EII after CEM project termination");
            check(in.getState().find("\\ns3528=1\\n")!=std::string::npos,
                  "P032 new original EII still has reconstruction ON after old project close");''',
        "new model defaults after old song")
    s=one(s,'        const auto intentionalCem=replaceKey(fresh,"model","4");',
        '        const auto intentionalCem=replaceKey(replaceKey(fresh,"model","4"),"s3528","0");',
        "explicit user persisted off fixture")
    s=one(s,'''            check(in.getState().find("\\nmodel=4\\n")!=std::string::npos,
                  "P029 explicitly stored CEM user default is honored for fresh VST3");''',
        '''            check(in.getState().find("\\nmodel=4\\n")!=std::string::npos,
                  "P029 explicitly stored CEM user default is honored for fresh VST3");
            check(in.getState().find("\\ns3528=0\\n")!=std::string::npos,
                  "P032 explicit user preference S3528 bypass OFF remains honored");''',
        "explicit user-off preference")
    s=one(s,'''            check(in.getState().find("\\nmodel=5\\n")!=std::string::npos,
                  "P029 removing explicit override restores original EII built-in fallback");''',
        '''            check(in.getState().find("\\nmodel=5\\n")!=std::string::npos,
                  "P029 removing explicit override restores original EII built-in fallback");
            check(in.getState().find("\\ns3528=1\\n")!=std::string::npos,
                  "P032 removing user override restores EII original S3528 ON");''',
        "fresh fallback after explicit default removed")
    return s

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--verify",action="store_true")
    args=parser.parse_args()
    old=TARGET.read_text(encoding="utf-8")
    updated=patch(old)
    if args.verify:
        print("P032 actual Windows COM factory/default S3528 probe anchors PASS")
    else:
        TARGET.write_text(updated,encoding="utf-8",newline="\n")
        print("P032 actual Windows VST3 old-project/new-default reconstruction regression installed")
if __name__=="__main__":main()
