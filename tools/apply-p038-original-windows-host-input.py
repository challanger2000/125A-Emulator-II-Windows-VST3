#!/usr/bin/env python3
"""P038: Windows VST3 COM genuine original firmware host-input acceptance.
Test-only private diagnostics can actuate the SAME public original scanner
contacts as the editor; no fake firmware, RAM injection, or bundled media.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"
IDS=UP/"src/vst3/eii_vst3_ids.h"
PLUGIN=UP/"src/vst3/eii_vst3.cpp"
HOST=UP/"tools/vst3_host_test.cpp"
HELPER=UP/"tools/p038_windows_original_host_capture.h"

def change_once(s, old, new, name):
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f"P038 {name}: expected exactly one source anchor, found {n}")
    return s.replace(old,new,1)

def prepare():
    pin=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if pin!=PIN:raise RuntimeError(f"P038 unexpected original core SHA: {pin}")
    ids=IDS.read_text(encoding="utf-8")
    plug=PLUGIN.read_text(encoding="utf-8")
    host=HOST.read_text(encoding="utf-8")
    if "qaScannerButton" in ids or "p038WindowsOriginalRecording" in host:
        raise RuntimeError("P038 already patched / source drift")
    ids=change_once(ids,
        "    virtual Steinberg::int32 PLUGIN_API statusText(char* buffer,Steinberg::int32 size)=0;",
        """    virtual Steinberg::int32 PLUGIN_API statusText(char* buffer,Steinberg::int32 size)=0;
    // Private owner QA; button numbers exactly match ScannerButton enum.
    // Both commands post to the original hardware owner, NOT the audio thread.
    virtual Steinberg::int32 PLUGIN_API qaScannerButton(Steinberg::int32 button,
                                                       Steinberg::int32 pressed)=0;
    virtual Steinberg::int32 PLUGIN_API qaSaveCurrentBank()=0;""",
        "private VST3 factory diagnostic protocol")
    plug=change_once(plug,
        "    int32 PLUGIN_API statusText(char* buffer,int32 size)override{",
        """    int32 PLUGIN_API qaScannerButton(int32 button,int32 pressed)override{
        if(!engine_ || button<0 || button>=30 || (pressed!=0 && pressed!=1))return -1;
        engine_->button(eii::ScannerButton(unsigned(button)),pressed!=0);
        return 0;
    }
    int32 PLUGIN_API qaSaveCurrentBank()override{
        if(!engine_)return -1;
        engine_->saveCurrentBankInProject();
        return 0;
    }
    int32 PLUGIN_API statusText(char* buffer,int32 size)override{""",
        "physical scanner contacts through test-only COM")
    plug=change_once(plug,
        '<<"\\ninputframes="<<s.inputFrames',
        '<<"\\nsamplereads="<<s.sampleReads<<"\\nsampleunknown="<<s.sampleUnknownReads'
        '<<"\\nwavreport="<<s.wavReport<<"\\nwavsuccess="<<s.wavSuccess'
        '<<"\\nwavactive="<<s.wavActive<<"\\nwavstatus="<<s.wavStatus'
        '<<"\\ninputframes="<<s.inputFrames',
        "observable original host/SAR state")
    host=change_once(host,
        "int main(int argc,char** argv)try{",
        '#include "p038_windows_original_host_capture.h"\n\nint main(int argc,char** argv)try{',
        "private VST3 capture harness included without link changes")
    host=change_once(host,
        "    auto host=owned(new HostApplication());",
        """    auto host=owned(new HostApplication());
    if(argc>5&&std::string(argv[5])=="original-windows-sar-qa-negative"){
        const auto result=p038WindowsQaNegative(factory,cid,host);
        module.reset();return result;
    }
    if(argc>5&&std::string(argv[5])=="original-windows-live-record"){
        // Windows x64 private local only. Real VST3 ProcessData, original
        // legally held ROM/OS image supplied in argv2/3; NEVER in public CI.
        const auto result=p038WindowsOriginalRecording(factory,cid,host,rom,floppy);
        module.reset();return result;
    }""",
        "owner-local Windows real original firmware acceptance entrypoint")
    return ids,plug,host

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    args=ap.parse_args()
    ids,plug,host=prepare()
    p=ROOT/"tests/p038_windows_original_host_capture.h"
    if not p.is_file():raise RuntimeError("P038 Windows host harness missing")
    if args.verify:
        print("P038 original OS3.1 Windows COM host production input patch: anchors PASS")
        return
    IDS.write_text(ids,encoding="utf-8",newline="\n")
    PLUGIN.write_text(plug,encoding="utf-8",newline="\n")
    HOST.write_text(host,encoding="utf-8",newline="\n")
    shutil.copyfile(p,HELPER)
    print("P038 Windows VST3 COM host real original firmware test installed; no media")

if __name__=="__main__":
    main()
