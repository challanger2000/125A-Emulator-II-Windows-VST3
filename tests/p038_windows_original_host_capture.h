// SPDX-License-Identifier: GPL-3.0-only
// P038 owner-local Windows x64 VST3 COM ProcessData real original OS3.1
// SAMPLE -> real host input -> SAR/DRAM -> DISK7 -> PCM -> IBStream fresh instance.
// No proprietary files can be compiled in or uploaded to GitHub Actions.
#include "125a_firmware_capture.h"
#include <array>
#include <cmath>
#include <sstream>
#include <stdexcept>
#include <vector>

static void p038Need(bool b,const std::string& what) {
    if(!b)throw std::runtime_error("P038 "+what);
}
static std::uint64_t p038Count(Instance& i,const char* key) {
    const auto value=i.status(key);
    p038Need(!value.empty(),std::string("missing VST3 diagnostic ")+key);
    return std::stoull(value);
}
static bool p038Contains(const std::string& s,const char* target) {
    return s.find(target)!=std::string::npos;
}
static double p038Freq(const std::vector<float>& pcm) {
    // Frequency proof for an audible, newly recorded 440Hz signal, not a stale
    // Choir voice. Inspect 0.15-0.90s at 48kHz and measure 400..480Hz.
    const std::size_t first=7200,last=std::min<std::size_t>(43200,pcm.size());
    p038Need(last-first>=24000,"PCM insufficient for independent frequency test");
    double maxEnergy=0,best=0;
    for(int f=400;f<=480;++f) {
        const double theta=2*3.14159265358979323846*f/48000.0;
        const double c=2*std::cos(theta);
        double u=0,v=0;
        for(std::size_t k=first;k<last;++k){const double w=pcm[k]+c*u-v;v=u;u=w;}
        const double energy=u*u+v*v-c*u*v;
        if(energy>maxEnergy){maxEnergy=energy;best=double(f);}
    }
    p038Need(maxEnergy>0,"frequency analyzer received digital silence");
    return best;
}
static int p038WindowsOriginalRecording(const VST3::Hosting::PluginFactory& factory,
    const VST3::UID& cid,FUnknown* host,const std::string& rom,
    const std::string& os31) {
    using namespace eii::wav;
    using Clock=std::chrono::steady_clock;
    constexpr int block=512;
    constexpr double pi=3.14159265358979323846;
    Instance in;
    p038Need(in.create(factory,cid,host),"cannot create real Windows VST3 COM instance");
    auto state=eii::portable::decodeProject(in.getState());
    auto settings=replaceKey(state.settings,"rom",rom);
    settings=replaceKey(settings,"floppy",os31);
    settings=replaceKey(settings,"osimage",os31);
    settings=replaceKey(settings,"memory1mb","0");
    settings=replaceKey(settings,"autoboot","1");
    settings=replaceKey(settings,"model","5");
    settings=replaceKey(settings,"native","0");
    settings=replaceKey(settings,"s3528","1");
    p038Need(in.setState(eii::portable::encodeProject(settings,state.bank,state.hdd)),
             "cannot configure original ROM+OS3.1 VST3 state");
    p038Need(in.start(48000,kOffline,block),"Windows VST3 host ProcessData startup failed");
    bool ready=false;
    const auto start=Clock::now();
    while(Clock::now()-start<std::chrono::seconds(240)) {
        const auto error=in.status("error");
        p038Need(error.empty(),"genuine original ROM boot halted: "+error);
        if(in.ready()&&in.status("loaded")=="1"){ready=true;break;}
        Sleep(75);
    }
    p038Need(ready,"genuine original OS3.1 firmware never reached Pxx");
    p038Need(p038Count(in,"callbacks")==0,"host callbacks occurred during autonomous ROM boot");

    auto send=[&](eii::ScannerButton b,bool pressed) {
        p038Need(in.diag->qaScannerButton(int(b),pressed?1:0)==0,
                 "private VST3 QA contact request failed");
    };
    // Real original firmware scanner contacts; no synthetic Z80 program,
    // injection into RAM, fake LCD, direct emulated ADC or preloaded waveform.
    FirmwareCapture capture;
    const auto sarStart=p038Count(in,"samplereads");
    const auto reportStart=p038Count(in,"wavreport");
    auto initial=capture.begin(p038Count(in,"ticks"),4000000);
    p038Need(initial.action==CaptureAction::SampleDown,"capture controller never pressed SAMPLE");
    send(eii::ScannerButton::Sample,true);

    std::uint64_t firstReadTick=0,hostFrames=0;
    bool completed=false;
    std::string lastStage;
    for(int b=0;b<34000;++b) {
        // The *actual IAudioProcessor::process* input bus, not a WAV importer.
        for(int n=0;n<block;++n) {
            const auto signal=float(.25*std::sin(2*pi*440.0*
                                       double(hostFrames++)/48000.0));
            in.inputLeft[n]=signal;in.inputRight[n]=signal;
        }
        in.data.inputs[0].silenceFlags=0;
        p038Need(in.process(),"original Windows ProcessData rejected audio input");
        if(b%4)continue;
        const auto now=p038Count(in,"ticks");
        const auto reads=p038Count(in,"samplereads");
        if(capture.phase()==CapturePhase::AwaitFirstRead &&
           reads>sarStart && !firstReadTick)firstReadTick=now;
        const auto lcd0=in.status("lcd0"),lcd1=in.status("lcd1");
        const bool mode=p038Contains(lcd0,"VOICE")||p038Contains(lcd0,"Sample")||
                        p038Contains(lcd1,"VOICE");
        auto step=capture.advance(now,lcd0,lcd1,reads,firstReadTick!=0,firstReadTick,mode);
        switch(step.action) {
        case CaptureAction::SampleDown:send(eii::ScannerButton::Sample,true);break;
        case CaptureAction::SampleUp:send(eii::ScannerButton::Sample,false);break;
        case CaptureAction::ArmForceDown:send(eii::ScannerButton::Digit9,true);break;
        case CaptureAction::ForceUp:send(eii::ScannerButton::Digit9,false);break;
        case CaptureAction::StopDown:send(eii::ScannerButton::Digit0,true);break;
        case CaptureAction::StopUp:send(eii::ScannerButton::Digit0,false);break;
        default:break;
        }
        if(lastStage!=capture.stageName()) {
            lastStage=capture.stageName();
            std::cout<<"P038 original_fw_stage="<<lastStage
                     <<" guest_lcd="<<lcd0<<" sar_reads="<<reads
                     <<" host_frames="<<p038Count(in,"inputframes")<<"\n";
        }
        if(step.completed){
            p038Need(step.success,std::string("firmware SAMPLE failed: ")+
                         (step.error?step.error:"unknown"));
            completed=true;break;
        }
        p038Need(in.status("error").empty(),"real guest error while sampling: "+in.status("error"));
    }
    p038Need(completed,"original OS3.1 SAMPLE/FORCE/STOP did not finish");
    p038Need(p038Count(in,"samplereads")>=sarStart+27000,
             "original SAR failed to capture one second of host input");
    p038Need(p038Count(in,"sampleunknown")==0,"original SAR contained unknown bytes");
    p038Need(p038Count(in,"inputdrops")==0,"VST3 host input queue dropped frames");
    p038Need(p038Count(in,"inputmissing")==0,"VST3 host input queue missed causal samples");

    // Real firmware DISK7 SAVE BANK; only published after original disk writer
    // finishes its physical emulated track writes and returns to Pxx.
    p038Need(in.diag->qaSaveCurrentBank()==0,"cannot request original DISK7 from COM");
    bool bankSaved=false;
    for(int b=0;b<36000;++b){
        std::fill(in.inputLeft.begin(),in.inputLeft.end(),0.f);
        std::fill(in.inputRight.begin(),in.inputRight.end(),0.f);
        in.data.inputs[0].silenceFlags=3;
        p038Need(in.process(),"real VST3 host rejected original bank save processing");
        if(b%16)continue;
        if(p038Count(in,"wavreport")>=reportStart+2 && in.status("wavsuccess")=="1") {
            bankSaved=true;break;
        }
        p038Need(in.status("error").empty(),"original firmware DISK7 error: "+in.status("error"));
    }
    p038Need(bankSaved,"original DISK7 bank save did not commit");
    const auto stored=in.getState();
    const auto decoded=eii::portable::decodeProject(stored);
    p038Need(decoded.hasBank(),"real VST3 IBStream lacks original DISK7 bank");

    auto play=[&](Instance& i)->std::pair<double,std::vector<float>> {
        EventList on,off;
        on.addEvent(note(true,60,0));off.addEvent(note(false,60,0));
        std::vector<float> pcm;pcm.reserve(330*block);
        double peak=0;
        for(int b=0;b<330;++b){
            i.inputLeft.assign(block,0.f);
            i.inputRight.assign(block,0.f);
            i.data.inputs[0].silenceFlags=3;
            p038Need(i.process(b==0?&on:b==200?&off:nullptr),
                     "Windows VST3 recorded voice playback callback rejected");
            for(int k=0;k<block;++k) {
                const float x=i.left[k];
                p038Need(std::isfinite(x),"NaN/Inf in guest recorded PCM");
                peak=std::max(peak,double(std::abs(x)));pcm.push_back(x);
            }
        }
        p038Need(peak>0.001,"newly recorded voice produced silent Windows PCM");
        const double f=p038Freq(pcm);
        p038Need(std::abs(f-440.0)<=5.0,"recorded output is not 440Hz input");
        return {f,std::move(pcm)};
    };
    const auto first=play(in);
    in.shutdown();
    p038Need(eiiThreads()==0,"first Windows original hardware instance leaked threads");

    Instance reopened;
    p038Need(reopened.create(factory,cid,host),"cannot create fresh Windows VST3");
    p038Need(reopened.setState(stored),"fresh IComponent rejected checksum-safe project");
    p038Need(reopened.start(48000,kOffline,512),"fresh original Windows VST3 setup failed");
    ready=false;
    const auto freshStart=Clock::now();
    while(Clock::now()-freshStart<std::chrono::seconds(240)) {
        p038Need(reopened.status("error").empty(),
                 "reopened original firmware halted: "+reopened.status("error"));
        if(reopened.ready()&&reopened.status("loaded")=="1"){ready=true;break;}
        Sleep(75);
    }
    p038Need(ready,"fresh original OS could not restore recorded project bank");
    const auto second=play(reopened);
    reopened.shutdown();
    p038Need(eiiThreads()==0,"reopened original Windows VST3 leaked threads");
    std::cout<<"P038 WINDOWS VST3 COM ORIGINAL OS31 HOST INPUT -> SAR -> "
                "DISK7 -> PROJECT IBStream -> FRESH PCM PASS "
             <<"original_hz="<<first.first<<" reopened_hz="<<second.first
             <<" host_frames="<<hostFrames<<"\n";
    return 0;
}
