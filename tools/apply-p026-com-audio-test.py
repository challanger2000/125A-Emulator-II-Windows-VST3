#!/usr/bin/env python3
"""P026: run REAL Windows VST3 COM processor with bad-ROM fail closed,
48/44.1k audio callbacks, two isolated instances and clean teardown.
No licensed ROM/audio required or included.
"""
from pathlib import Path
import argparse

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"upstream/eii-emu/tools/vst3_host_test.cpp"

def one(s,a,b,label):
    n=s.count(a)
    if n!=1:raise RuntimeError(f"P026 Windows host {label}: {n} anchors, expected exactly one")
    return s.replace(a,b,1)

def patch(s):
    if "P026 WINDOWS REAL VST3 COM" in s:raise RuntimeError("P026 already patched")
    if "P018 VST3 accepts MIDI C3 song with HDD" not in s:
        raise RuntimeError("P026 requires full P018 host-state acceptance")
    s=one(s,'#include <random>','#include <random>\n#include <filesystem>\n#include <array>',"C++ ROM-negative fixture headers")
    marker='    auto host=owned(new HostApplication());'
    block=r'''
    if(argc>5&&std::string(argv[5])=="windows-audio-safety"){
        // Actual Windows VST3 COM/IAudioProcessor, no original licensed ROM
        // or DAW install. The deliberately invalid all-NOP ROM triggers
        // original controller RFD bus conflict on virtual hardware tick 1.
        // It MUST NOT crash, report fake Pxx, emit audio or leak resources.
        namespace fs=std::filesystem;
        const auto fixture=fs::temp_directory_path()/
            ("eii_p026_badrom_"+std::to_string(GetCurrentProcessId()));
        fs::create_directories(fixture);
        auto writeZeros=[&](const char* name,std::size_t n){
            std::ofstream out(fixture/name,std::ios::binary);
            if(!out)throw std::runtime_error("P026 cannot write isolated synthetic ROM");
            const std::vector<char> bytes(n,0);
            out.write(bytes.data(),std::streamsize(bytes.size()));
            if(!out)throw std::runtime_error("P026 failed synthetic ROM write");
        };
        writeZeros("main.bin",8192);
        writeZeros("scanner.bin",8192);
        writeZeros("ic135.bin",512);
        writeZeros("ic137.bin",512);
        {
            Instance broken,clean;
            check(broken.create(factory,cid,host),
                  "P026 create actual Windows VST3 COM instance for invalid ROM");
            check(clean.create(factory,cid,host),
                  "P026 independent second actual Windows VST3 COM instance");
            if(!broken.component||!clean.component)throw std::runtime_error("P026 COM creation failed");
            const auto empty=broken.getState();
            const auto badRom=replaceKey(replaceKey(replaceKey(empty,"rom",fixture.string()),
                                                     "floppy",""),"autoboot","1");
            const auto noBoot=replaceKey(replaceKey(empty,"rom",""),"autoboot","0");
            check(broken.setState(badRom),
                  "P026 original invalid ROM project state accepted for boot");
            check(clean.setState(noBoot),
                  "P026 separate clean instance keeps autoboot disabled");
            check(broken.start(48000,kRealtime,512),
                  "P026 actual COM 48k realtime processor initialised");
            check(clean.start(44100,kRealtime,256),
                  "P026 concurrent COM 44.1k processor initialised");
            std::string error;
            for(unsigned wait=0;wait<180;++wait){
                error=broken.status("error");
                if(error.find("conflicting RFD bus drivers")!=std::string::npos)break;
                Sleep(25);
            }
            std::cout<<"P026 original invalid ROM fault: "<<error<<"\n";
            check(error.find("conflicting RFD bus drivers")!=std::string::npos,
                  "P026 genuine original production controller RFD hardware failure retained");
            check(broken.status("lcd0").rfind("P01",0)!=0,
                  "P026 invalid ROM cannot report firmware playable Pxx");
            check(clean.status("loaded")=="0",
                  "P026 second instance did not inherit first one's corrupt ROM boot");
            std::uint64_t zerosBroken=0,zerosClean=0,blocks=0;
            for(int i=0;i<160;++i){
                EventList midi;
                if(i%13==0){auto ev=note(true,60,i%256);midi.addEvent(ev);}
                if(i%13==8){auto ev=note(false,60,i%256);midi.addEvent(ev);}
                const bool okA=broken.process(i%13==0?&midi:nullptr);
                const bool okB=clean.process();
                check(okA&&okB,"P026 concurrent actual COM VST3 realtime callbacks accepted");
                for(const auto v:broken.left){
                    if(v==0.f)++zerosBroken;
                    check(std::isfinite(v),"P026 broken original hardware output is finite");
                }
                for(const auto v:broken.right)
                    check(v==0.f,"P026 invalid original ROM must not produce right-channel audio");
                for(const auto v:clean.left){
                    if(v==0.f)++zerosClean;
                    check(std::isfinite(v),"P026 second clean instance output is finite");
                }
                for(const auto v:clean.right)
                    check(v==0.f,"P026 unbooted clean instance stays silent on right");
                ++blocks;
            }
            check(zerosBroken==160ull*512&&zerosClean==160ull*256,
                  "P026 every sample of both independent Windows VST3 instances silent");
            check(broken.getState().find("autoboot=1")!=std::string::npos,
                  "P026 original corrupted ROM host state remains inspectable");
            check(clean.getState().find("autoboot=0")!=std::string::npos,
                  "P026 no-boot second song remains independent");
            check(clean.status("error").empty(),
                  "P026 original hardware fault does not cross into second instance");
            broken.shutdown();
            clean.shutdown();
            std::cout<<"P026 COM audio callbacks="<<blocks
                     <<" broken_48k_silent="<<zerosBroken
                     <<" clean_44k1_silent="<<zerosClean
                     <<" before final thread check="<<eiiThreads()<<"\n";
        }
        for(int i=0;i<60&&eiiThreads()>0;++i)Sleep(25);
        check(eiiThreads()==0,
              "P026 both actual Windows VST3 owners and workers release after COM teardown");
        std::error_code ec;fs::remove_all(fixture,ec);
        module.reset();
        std::cout<<(failures?"P026 WINDOWS REAL VST3 COM AUDIO/LIFECYCLE FAIL ":
                             "P026 WINDOWS REAL VST3 COM AUDIO/LIFECYCLE PASS ")
                 <<failures<<" failure(s)\n";
        return failures?1:0;
    }
'''
    return one(s,marker,marker+'\n'+block,"Windows COM host audio-mode insertion")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    a=ap.parse_args()
    old=P.read_text(encoding="utf-8")
    new=patch(old)
    if a.verify:
        print("P026 Windows real VST3 COM/audio safety test anchors PASS")
        return
    P.write_text(new,encoding="utf-8",newline="\n")
    print("P026 real Windows VST3 host audio fault/isolation/lifecycle test installed")
if __name__=="__main__":main()
