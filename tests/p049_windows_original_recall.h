// SPDX-License-Identifier: GPL-3.0-only
// P049: owner-only authentic Windows VST3 with original OS 3.1 and bank recall.
// Requires a disposable SAMPLE-DISK COPY; never removes the user original.
#pragma once
#include <filesystem>
#include <chrono>
#include <thread>
#include <stdexcept>
#include <iostream>
#include <string>
#include <cmath>
#include <algorithm>
#include <tuple>
#include <array>


// The original OS boots on its independent emulation-owner thread. VST3
// process() callbacks do NOT advance that worker by a whole guest clock step.
// Wait for actual original LCD preset Pxx and verified loaded bank, exactly as
// the previously passing original-ROM Windows P044 host acceptance does.
// In particular, never mistake fast offline block submission for guest boot.
static void p049AwaitOriginalBoot(Instance& in,const char* phase) {
    using Clock=std::chrono::steady_clock;
    const auto started=Clock::now();
    auto nextNotice=started+std::chrono::seconds(10);
    std::cout<<"P049 "<<phase<<" original_firmware_boot=START\\n"<<std::flush;
    while(Clock::now()-started<std::chrono::seconds(240)) {
        const auto error=in.status("error");
        if(!error.empty())
            throw std::runtime_error(std::string("P049 ")+phase+
                " original firmware boot error: "+error);
        if(in.ready() && in.status("loaded")=="1") {
            std::cout<<"P049 "<<phase<<" original_firmware_boot=READY"
                <<" lcd0="<<in.status("lcd0")
                <<" loaded="<<in.status("loaded")
                <<" ticks="<<in.status("ticks")<<"\\n"<<std::flush;
            return;
        }
        if(Clock::now()>=nextNotice) {
            const auto seconds=std::chrono::duration_cast<std::chrono::seconds>(
                Clock::now()-started).count();
            std::cout<<"P049 "<<phase<<" original_firmware_boot=RUNNING"
                <<" seconds="<<seconds
                <<" lcd0="<<in.status("lcd0")
                <<" lcd1="<<in.status("lcd1")
                <<" loaded="<<in.status("loaded")
                <<" ticks="<<in.status("ticks")<<"\\n"<<std::flush;
            nextNotice=Clock::now()+std::chrono::seconds(10);
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(75));
    }
    throw std::runtime_error(std::string("P049 ")+phase+
        " original firmware did not reach a loaded Pxx preset display; lcd0="+
        in.status("lcd0")+" lcd1="+in.status("lcd1")+
        " loaded="+in.status("loaded")+" ticks="+in.status("ticks"));
}

static int p049OriginalChoirRecall(const VST3::Hosting::PluginFactory& factory,
      const VST3::UID& cid,FUnknown* host,const std::string& rom,
      const std::string& os31,const std::string& testDisk,
      const std::string& outDir){
 namespace fs=std::filesystem;
 const auto require=[](bool ok,const std::string& msg){
     if(!ok)throw std::runtime_error("P049: "+msg);
 };
 const fs::path romdir(rom),ospath(os31),diskpath(testDisk),outpath(outDir);
 for(const char* name:{"main.bin","scanner.bin","ic135.bin","ic137.bin"})
     if(!fs::is_regular_file(romdir/name)){
         std::cout<<"P049 BLOCKED: original ROM missing (no synthetic PASS)\n";
         return 3;
     }
 if(!fs::is_regular_file(ospath)||!fs::is_regular_file(diskpath)||
    fs::file_size(ospath)!=573440||fs::file_size(diskpath)!=573440){
     std::cout<<"P049 BLOCKED: original OS or sample floppy missing/invalid\n";
     return 3;
 }
 try{
     fs::create_directories(outpath);
     std::string project;
     PlayResult before,after;
     const auto w1=(outpath/"P049-VORHER.wav").string();
     const auto w2=(outpath/"P049-NACHHER.wav").string();
     std::cout<<"P049 START original OS3.1, actual EII sample bank, native DAC/SSM2045\n"<<std::flush;
     {
         Instance first;
         require(first.create(factory,cid,host),"first VST3 COM instance creation failed");
         const auto initial=eii::portable::decodeProject(first.getState());
         auto settings=replaceKey(initial.settings,"rom",rom);
         settings=replaceKey(settings,"osimage",os31);
         settings=replaceKey(settings,"floppy",testDisk);
         settings=replaceKey(settings,"autoboot","1");
         settings=replaceKey(settings,"memory1mb","0");
         settings=replaceKey(settings,"native","1");
         settings=replaceKey(settings,"s3528","1");
         settings=replaceKey(settings,"model","5");
         settings=replaceKey(settings,"wavmidic3","1");
         require(first.setState(eii::portable::encodeProject(settings,initial.bank,initial.hdd)),
                 "setState rejected actual sample disk");
         require(first.start(48000,kOffline,512),"first VST3 processor setup failed");
         p049AwaitOriginalBoot(first,"BEFORE");
         before=bootAndPlay(first,w1);
         require(before.booted,"original firmware did not reach preset display");
         require(before.level>0.0002,"sample bank produced no usable MIDI audio");
         require(first.status("loaded")=="1","original firmware did not confirm loaded bank");
         std::cout<<"P049 BEFORE AUDIO PASS level="<<before.level
                  <<" MIDI57="<<before.a3<<" MIDI60="<<before.c4
                  <<" MIDI69="<<before.a4<<"\n"<<std::flush;
         const auto reportStart=p038Count(first,"wavreport");
         require(first.diag->qaSaveCurrentBank()==0,"original DISK7 save command rejected");
         bool saved=false;
         for(int i=0;i<40000;++i){
             std::fill(first.inputLeft.begin(),first.inputLeft.end(),0.f);
             std::fill(first.inputRight.begin(),first.inputRight.end(),0.f);
             first.data.inputs[0].silenceFlags=3;
             require(first.process(),"process failed during original DISK7 commit");
             if(i%2000==0)std::cout<<"P049 original DISK7 block="<<i
               <<" stage="<<first.status("wavstatus")<<"\n"<<std::flush;
             if(i%8==0&&p038Count(first,"wavreport")>=reportStart+2&&
                 first.status("wavsuccess")=="1"){saved=true;break;}
             if(i%64==0)require(first.status("error").empty(),
                        "original DISK7 failed: "+first.status("error"));
         }
         require(saved,"original DISK7 did not commit project bank");
         project=first.getState();
         require(!project.empty(),"getState failed after original firmware commit");
         require(eii::portable::decodeProject(project).hasBank(),
                 "song state lacks original embedded sample bank");
         std::cout<<"P049 STATE CAPTURED bytes="<<project.size()
                  <<" embedded_bank=1\n"<<std::flush;
         first.shutdown();
     }
     require(eiiThreads()==0,"source VST3 guest threads survived shutdown");
     require(fs::remove(diskpath),"could not hide disposable test sample disk");
     require(!fs::exists(diskpath),"test sample disk still reachable");
     std::cout<<"P049 PORTABLE RECALL: sample disk physically unavailable\n"<<std::flush;
     {
         Instance second;
         require(second.create(factory,cid,host),"fresh VST3 instance creation failed");
         require(second.setState(project),"fresh VST3 rejected persisted DAW state");
         require(second.start(48000,kOffline,512),"restored VST3 processor setup failed");
         p049AwaitOriginalBoot(second,"AFTER");
         after=bootAndPlay(second,w2);
         require(after.booted,"fresh VST3 failed to boot without external sample floppy");
         require(after.level>0.0002,"restored sample bank silent");
         require(second.status("loaded")=="1","restored firmware did not confirm bank load");
         require(eii::portable::decodeProject(second.getState()).hasBank(),
                 "fresh project lost embedded EII bank on re-save");
         std::cout<<"P049 AFTER AUDIO level="<<after.level
                  <<" MIDI57="<<after.a3<<" MIDI60="<<after.c4
                  <<" MIDI69="<<after.a4<<"\n"<<std::flush;
         second.shutdown();
     }
     require(eiiThreads()==0,"restored VST3 left guest threads running");
     const auto levelRatio=after.level/before.level;
     require(levelRatio>0.65&&levelRatio<1.5,
             "before/after overall RMS level ratio outside 0.65..1.5");
     const std::array<std::tuple<const char*,double,double>,3> notes{{
         {"MIDI57",before.a3,after.a3},
         {"MIDI60",before.c4,after.c4},
         {"MIDI69",before.a4,after.a4}
     }};
     for(const auto& [name,a,b]:notes){
         require(a>20&&b>20,std::string(name)+" pitch check unavailable");
         require(std::abs(1200.*std::log2(b/a))<80,
                 std::string(name)+" changed pitch by >=80 cents");
     }
     std::cout<<"P049 ORIGINAL-FIRMWARE VST3 SAMPLE AUDIO RECALL PASS"
              <<" real_disk_absent=1 embedded_bank=1 level_ratio="<<levelRatio
              <<" audio_before_after=1 fresh_instance=1"
              <<" (not bit-identical audio or hardware accuracy proof)\n"<<std::flush;
     return 0;
 }catch(const std::exception& e){
     std::cerr<<"P049 ORIGINAL-FIRMWARE VST3 SAMPLE AUDIO RECALL FAIL: "
              <<e.what()<<"\n"<<std::flush;
     return 1;
 }
}
