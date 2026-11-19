// SPDX-License-Identifier: GPL-3.0-only
// P040: owner-only real Windows x64 VST3 COM, *original E-mu OS3.1* firmware.
// This file is included after p038_windows_original_host_capture.h.
// NEVER use a fake ROM, direct sample RAM injection, or report an unexecuted
// private Windows positive as a CI PASS.
#include <cstdint>
#include <algorithm>
#include <cmath>
#include <chrono>
#include <string>
#include <vector>
#include <array>
#include <optional>
#include <iomanip>
#include <iostream>
#include <utility>
#include <filesystem>

struct P040Case {
    const char* name;
    int rate=48000;
    int inputHz=1000; // 0 = connected digital silence
    bool disconnected=false;
};
struct P040Metrics {
    double amp1000=0,amp500=0,peak=0,rms=0;
    std::uint64_t sarReads=0,hostFrames=0,inputDrops=0,inputMissing=0;
    bool storedInProject=false;
};
static double p040Tone(const std::vector<float>& pcm,int rate,double frequency) {
    const std::size_t first=std::size_t(rate*0.15),last=std::min(pcm.size(),std::size_t(rate*0.90));
    p038Need(last>first+std::size_t(rate/2),"P040 audition shorter than 0.5 seconds");
    const auto angle=2.0*3.14159265358979323846*frequency/double(rate);
    const double c=std::cos(angle),s=std::sin(angle);
    // Avoid trigonometric recurrence drift over long windows with a direct
    // phase calculation; 2/N normalized magnitude at the exact target tone.
    double sumC=0,sumS=0;
    for(std::size_t k=first;k<last;++k){
        const double phi=angle*double(k-first);
        sumC+=double(pcm[k])*std::cos(phi);
        sumS+=double(pcm[k])*std::sin(phi);
    }
    return 2.0*std::hypot(sumC,sumS)/double(last-first);
}
static P040Metrics p040OwnerCase(const VST3::Hosting::PluginFactory& factory,
      const VST3::UID& cid,FUnknown* host,const std::string& rom,
      const std::string& os31,const std::string& choir,const P040Case& tc) {
    using namespace eii::wav;
    using Clock=std::chrono::steady_clock;
    constexpr int block=512;
    constexpr double pi=3.14159265358979323846;
    auto req=[&](bool ok,const std::string& why){p038Need(ok,std::string(tc.name)+": "+why);};
    Instance in;
    req(in.create(factory,cid,host),"cannot create actual Windows VST3 COM component");
    const auto initial=eii::portable::decodeProject(in.getState());
    auto state=replaceKey(initial.settings,"rom",rom);
    state=replaceKey(state,"floppy",choir);
    state=replaceKey(state,"osimage",os31);
    state=replaceKey(state,"memory1mb","0");
    state=replaceKey(state,"autoboot","1");
    state=replaceKey(state,"wavmidic3","1"); // host C3/60 -> original firmware MIDI48
    state=replaceKey(state,"model","5");
    state=replaceKey(state,"native","0");
    state=replaceKey(state,"s3528","1");
    req(in.setState(eii::portable::encodeProject(state,initial.bank,initial.hdd)),
        "invalid original ROM/OS/Choir host project state");
    req(in.start(double(tc.rate),kOffline,block),"cannot activate original Windows VST3");
    auto begun=Clock::now();bool ready=false;
    while(Clock::now()-begun<std::chrono::seconds(240)){
        const auto error=in.status("error");
        req(error.empty(),"original-ROM boot exception: "+error);
        if(in.ready()&&in.status("loaded")=="1"){ready=true;break;}
        Sleep(75);
    }
    req(ready,"original firmware did not boot to Pxx");
    req(in.status("wavactive")=="0","unexpected WAV importer is active");
    const std::uint64_t startReads=p038Count(in,"samplereads");
    const std::uint64_t startReport=p038Count(in,"wavreport");
    FirmwareCapture capture;
    auto first=capture.begin(p038Count(in,"ticks"),4000000);
    req(first.action==CaptureAction::SampleDown,"SAMPLE entry did not arm");
    auto button=[&](eii::ScannerButton b,bool pressed) {
        req(in.diag->qaScannerButton(int(b),pressed?1:0)==0,
            "test-only original physical scanner control refused");
    };
    button(eii::ScannerButton::Sample,true);
    if(tc.disconnected)in.data.numInputs=0; // genuine disconnected VST3 input bus
    std::uint64_t hostFrames=0,firstReadTick=0;
    bool finished=false;
    std::string lastStage;
    for(int b=0;b<36000;++b){
        // A fresh sample each DAW frame, via IAudioProcessor::process.
        // Supplying silence is *not* the same as removing the input bus.
        for(int n=0;n<block;++n) {
            const float v=tc.inputHz==0||tc.disconnected?0.f:
                float(0.25*std::sin(2*pi*double(tc.inputHz)*
                                    double(hostFrames+n)/double(tc.rate)));
            in.inputLeft[n]=v;in.inputRight[n]=v;
        }
        hostFrames+=block;
        in.data.inputs[0].silenceFlags=0;
        req(in.process(),"VST3 host audio input callback failed");
        if(b%4)continue;
        const auto now=p038Count(in,"ticks"),reads=p038Count(in,"samplereads");
        if(capture.phase()==CapturePhase::AwaitFirstRead &&
           reads>startReads && firstReadTick==0) firstReadTick=now;
        const auto lcd0=in.status("lcd0"),lcd1=in.status("lcd1");
        const bool sampleMode=p038Contains(lcd0,"VOICE")||
                p038Contains(lcd0,"Sample")||p038Contains(lcd1,"VOICE");
        const auto step=capture.advance(now,lcd0,lcd1,reads,
                                        firstReadTick!=0,firstReadTick,sampleMode);
        switch(step.action){
            case CaptureAction::SampleDown:button(eii::ScannerButton::Sample,true);break;
            case CaptureAction::SampleUp:button(eii::ScannerButton::Sample,false);break;
            case CaptureAction::ArmForceDown:button(eii::ScannerButton::Digit9,true);break;
            case CaptureAction::ForceUp:button(eii::ScannerButton::Digit9,false);break;
            case CaptureAction::StopDown:button(eii::ScannerButton::Digit0,true);break;
            case CaptureAction::StopUp:button(eii::ScannerButton::Digit0,false);break;
            default:break;
        }
        const std::string stage=capture.stageName();
        if(stage!=lastStage){
            lastStage=stage;
            std::cout<<"P040 "<<tc.name<<" stage="<<stage
                     <<" lcd="<<lcd0<<" sar="<<reads
                     <<" host_frames="<<p038Count(in,"inputframes")
                     <<"\n"<<std::flush;
        }
        if(step.completed){
            req(step.success,std::string("original firmware capture rejected: ")+
                (step.error?step.error:"unspecified"));
            finished=true;break;
        }
        req(in.status("error").empty(),"original firmware errored: "+in.status("error"));
    }
    req(finished,"original OS SAMPLE/FORCE/STOP did not complete");
    P040Metrics out;
    out.sarReads=p038Count(in,"samplereads")-startReads;
    out.hostFrames=p038Count(in,"inputframes");
    out.inputDrops=p038Count(in,"inputdrops");
    out.inputMissing=p038Count(in,"inputmissing");
    req(out.sarReads>=27000,"original guest SAR did not record 1 second");
    req(p038Count(in,"sampleunknown")==0,"original guest SAR has unknown bytes");
    req(out.inputDrops==0,"actual VST3 audio input frames dropped");
    if(tc.disconnected) {
        // Production HostSampleInput intentionally publishes timestamped *zero*
        // frames on a disconnected bus, avoiding noncausal stalls. Thus a
        // nonzero frame count here is expected and is NOT evidence of audio input.
        req(in.data.numInputs==0,"negative control failed to disconnect VST3 bus");
    }else{
        req(out.hostFrames>=std::uint64_t(tc.rate)*2,
            "actual VST3 input buffers did not reach the guest");
        req(out.inputMissing==0,"connected host input samples were missed");
    }
    req(in.diag->qaSaveCurrentBank()==0,"original firmware DISK7 SAVE command refused");
    bool saved=false;
    for(int b=0;b<40000;++b){
        std::fill(in.inputLeft.begin(),in.inputLeft.end(),0.f);
        std::fill(in.inputRight.begin(),in.inputRight.end(),0.f);
        in.data.inputs[0].silenceFlags=3;
        req(in.process(),"host failed while original firmware wrote DISK7");
        if(b%16)continue;
        if(p038Count(in,"wavreport")>=startReport+2 &&
           in.status("wavsuccess")=="1"){saved=true;break;}
        req(in.status("error").empty(),"firmware bank save failed: "+in.status("error"));
    }
    req(saved,"original DISK7 bank was not committed");
    const auto project=in.getState();
    req(!project.empty(),"Windows VST3 IBStream state not saved");
    out.storedInProject=eii::portable::decodeProject(project).hasBank();
    req(out.storedInProject,"DISK7 completed but VST3 project bank snapshot absent");
    // Original recorded note from the production VST3 MIDI in, rather than
    // reading DRAM or calling the EII machine MIDI input directly.
    EventList noteOn,noteOff;
    auto startNote=note(true,60,0),endNote=note(false,60,0);
    noteOn.addEvent(startNote);noteOff.addEvent(endNote);
    std::vector<float> pcm;
    pcm.reserve(330*block);
    double sum=0;
    for(int b=0;b<330;++b){
        std::fill(in.inputLeft.begin(),in.inputLeft.end(),0.f);
        std::fill(in.inputRight.begin(),in.inputRight.end(),0.f);
        in.data.inputs[0].silenceFlags=3;
        req(in.process(b==0?&noteOn:b==200?&noteOff:nullptr),
            "original recorded voice playback COM callback failed");
        for(float v:in.left){
            req(std::isfinite(v),"nonfinite guest recorded PCM");
            out.peak=std::max(out.peak,double(std::abs(v)));
            sum+=double(v)*double(v);pcm.push_back(v);
        }
    }
    out.rms=std::sqrt(sum/double(pcm.size()));
    out.amp500=p040Tone(pcm,tc.rate,500.0);
    out.amp1000=p040Tone(pcm,tc.rate,1000.0);
    std::cout<<"P040 "<<tc.name<<" METRICS rate="<<tc.rate
             <<" input="<<(tc.disconnected?"DISCONNECTED":std::to_string(tc.inputHz))
             <<" sar="<<out.sarReads<<" host_frames="<<out.hostFrames
             <<" input_drops="<<out.inputDrops<<" missing="<<out.inputMissing
             <<" amp500="<<std::setprecision(9)<<out.amp500
             <<" amp1000="<<out.amp1000<<" peak="<<out.peak
             <<" rms="<<out.rms<<" bank_snapshot="<<out.storedInProject
             <<"\n"<<std::flush;
    in.shutdown();
    req(eiiThreads()==0,"Windows original firmware worker thread leak");
    return out;
}
static int p040WindowsOriginalAdversarial(
    const VST3::Hosting::PluginFactory& factory,const VST3::UID& cid,FUnknown* host,
    const std::string& rom,const std::string& os31,const std::string& choir){
    // A no-media public CI invocation must not boot, create a fake PCM
    // "positive" or wait for a 240-second original ROM deadline.
    namespace fs=std::filesystem;
    const fs::path dir(rom);
    for(const auto name:{"main.bin","scanner.bin","ic135.bin","ic137.bin"}){
        if(!fs::is_regular_file(dir/name)){
            std::cout<<"P040 PRIVATE ORIGINAL MEDIA ABSENT/BLOCKED (expected in public CI)\n";
            return 3;
        }
    }
    if(!fs::is_regular_file(os31)||!fs::is_regular_file(choir)||
       fs::file_size(os31)!=573440||fs::file_size(choir)!=573440){
        std::cout<<"P040 ORIGINAL OS/CHOIR MEDIA MISSING OR BAD SIZE: BLOCKED\n";
        return 3;
    }
    std::optional<P040Metrics> tone48,tone44,half48,silence48,noBus;
    int failed=0;
    auto run=[&](const P040Case& tc)->std::optional<P040Metrics>{
        try {
            const auto result=p040OwnerCase(factory,cid,host,rom,os31,choir,tc);
            std::cout<<"P040 CASE "<<tc.name<<" ORIGINAL_FIRMWARE_EXECUTED\n"<<std::flush;
            return result;
        }catch(const std::exception& e){
            ++failed;
            std::cout<<"P040 CASE "<<tc.name<<" FAIL: "<<e.what()<<"\n"<<std::flush;
            return std::nullopt;
        }
    };
    // First: two independently booted fresh VST3s with 1kHz original firmware
    // at 44.1k and 48k. Then 500Hz frequency change, silence, and no input bus.
    tone44=run({"POSITIVE_44100_1000HZ",44100,1000,false});
    tone48=run({"POSITIVE_48000_1000HZ",48000,1000,false});
    half48=run({"NEGATIVE_CHANGED_48000_500HZ",48000,500,false});
    silence48=run({"NEGATIVE_SILENCE_48000",48000,0,false});
    noBus=run({"NEGATIVE_DISCONNECTED_INPUT",48000,0,true});
    auto proof=[&](bool valid,const char* label){
        std::cout<<"P040 CHECK "<<label<<" "<<(valid?"PASS":"FAIL")<<"\n"<<std::flush;
        if(!valid)++failed;
    };
    if(tone44)proof(tone44->amp1000>0.003,"POSITIVE_44100_HAS_1KHZ");
    else proof(false,"POSITIVE_44100_HAS_1KHZ");
    if(tone48)proof(tone48->amp1000>0.003,"POSITIVE_48000_HAS_1KHZ");
    else proof(false,"POSITIVE_48000_HAS_1KHZ");
    if(half48)proof(half48->amp500>0.003,"CHANGED_INPUT_HAS_500HZ");
    else proof(false,"CHANGED_INPUT_HAS_500HZ");
    if(tone48&&silence48) {
        proof(silence48->amp1000 < tone48->amp1000*0.12,
              "MUTED_GUEST_HAS_NO_STALE_1000HZ");
    }else proof(false,"MUTED_GUEST_HAS_NO_STALE_1000HZ");
    if(half48&&silence48) {
        proof(silence48->amp500 < half48->amp500*0.12,
              "MUTED_GUEST_HAS_NO_STALE_500HZ");
    }else proof(false,"MUTED_GUEST_HAS_NO_STALE_500HZ");
    if(tone48&&noBus){
        proof(noBus->amp1000 < tone48->amp1000*0.12,
              "DISCONNECTED_GUEST_HAS_NO_STALE_1000HZ");
    }else proof(false,"DISCONNECTED_GUEST_HAS_NO_STALE_1000HZ");
    std::cout<<"P040 ORIGINAL WINDOWS VST3 OWNER-PRIVATE MULTIRATE + "
                "SILENCE + FREQUENCY CHANGE + NO-INPUT "<<
             (failed==0?"PASS":"FAIL")<<" failed_gates="<<failed<<"\n"<<std::flush;
    return failed==0?0:1;
}
