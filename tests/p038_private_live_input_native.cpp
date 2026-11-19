// SPDX-License-Identifier: GPL-3.0-only
// Owner-private genuine OS3.1 host-audio-input -> original Z80/SAR -> DISK7.
// This uses production PluginEngine::pushInput, NOT a WAV Source or DRAM injection.
#include "vst3/plugin_engine.h"
#include "125a_firmware_capture.h"
#include <array>
#include <cmath>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <string>
#include <algorithm>
using Clock=std::chrono::steady_clock;
using namespace std::chrono_literals;
static constexpr double pi=3.14159265358979323846264;
static void need(bool x,const std::string& s){if(!x)throw std::runtime_error(s);}
static bool has(const std::string& s,const char* x){return s.find(x)!=std::string::npos;}
int main(int argc,char**argv)try {
 need(argc==4,"usage: p038_private_live_input ROM_DIR OS31_FLOPPY CHOIR_FLOPPY");
 eii::vst::PluginEngine e;e.setupProcessing(48000,512);e.activate();
 eii::vst::PluginSettings settings;
 settings.romFolder=argv[1];settings.osImage=argv[2];settings.floppy=argv[3];
 settings.audioMode=eii::analog::RuntimeAudioMode::BasicVoice;
 settings.directImageWrites=false;settings.memory1mb=false;
 e.boot(settings,true);
 auto t0=Clock::now();eii::vst::EngineStatus s;
 while(Clock::now()-t0<240s){
  std::this_thread::sleep_for(75ms);s=e.status();
  if(s.boot.complete&&s.boot.stage==eii::portable::BootStage::Ready&&!s.autonomousBoot)break;
  if(s.halted)break;
 }
 need(s.boot.complete&&!s.autonomousBoot&&!s.halted,"original E-mu ROM boot failed");
 std::cerr<<"BOOT LCD="<<s.panel.lcd[0]<<" ticks="<<s.panel.ticks<<"\n";
 eii::wav::FirmwareCapture controller;
 auto first=controller.begin(s.panel.ticks,4000000);
 need(first.action==eii::wav::CaptureAction::SampleDown,"controller must press SAMPLE");
 e.button(eii::ScannerButton::Sample,true);
 std::array<float,512> input{},left{},right{};
 std::uint64_t frame=0,firstReadTick=0,startReads=s.sampleReads,priorReport=s.wavReport;
 bool complete=false;
 for(int b=0;b<36000;++b) {
  for(int i=0;i<512;++i)input[i]=float(.25*std::sin(2*pi*440.0*double(frame++)/48000.0));
  e.pushInput(input.data(),nullptr,512,false,false,true);
  e.render(left.data(),right.data(),512,true);
  if(b%4)continue;
  s=e.status();
  if(controller.phase()==eii::wav::CapturePhase::AwaitFirstRead &&
     s.sampleReads>startReads&&!firstReadTick)firstReadTick=s.panel.ticks;
  const bool sampleLcd=has(s.panel.lcd[0],"Sample")||
        has(s.panel.lcd[0],"VOICE")||has(s.panel.lcd[1],"VOICE");
  const auto step=controller.advance(s.panel.ticks,s.panel.lcd[0],s.panel.lcd[1],
      s.sampleReads,firstReadTick>0,firstReadTick,sampleLcd);
  using eii::wav::CaptureAction;
  switch(step.action) {
   case CaptureAction::SampleDown:e.button(eii::ScannerButton::Sample,true);break;
   case CaptureAction::SampleUp:e.button(eii::ScannerButton::Sample,false);break;
   case CaptureAction::ArmForceDown:e.button(eii::ScannerButton::Digit9,true);break;
   case CaptureAction::ForceUp:e.button(eii::ScannerButton::Digit9,false);break;
   case CaptureAction::StopDown:e.button(eii::ScannerButton::Digit0,true);break;
   case CaptureAction::StopUp:e.button(eii::ScannerButton::Digit0,false);break;
   default:break;
  }
  if(step.completed){
   need(step.success,std::string("real firmware SAMPLE failed: ")+
       (step.error?step.error:"unknown"));
   complete=true;break;
  }
  if(s.halted)break;
 }
 need(complete,"original SAMPLE/FORCE/STOP timed out");
 need(s.sampleReads>=startReads+27000,"insufficient actual original Z80 SAR bytes");
 need(s.sampleUnknownReads==0,"unknown original SAR bytes");
 need(s.inputDrops==0&&s.inputMissing==0,"real host input lost samples");
 std::cerr<<"SAMPLE DONE SAR reads="<<s.sampleReads
   <<" input frames="<<s.inputFrames<<" drops="<<s.inputDrops
   <<" missing="<<s.inputMissing<<"\n";
 e.saveCurrentBankInProject();
 bool saved=false;
 for(int b=0;b<35000;++b){
  input.fill(0);e.pushInput(input.data(),nullptr,512,false,true,true);
  e.render(left.data(),right.data(),512,true);
  if(b%16)continue;
  s=e.status();
  if(s.wavReport>=priorReport+2&&s.wavSuccess){saved=true;break;}
  need(s.panel.error.empty(),"original DISK7 failed: "+s.panel.error);
 }
 need(saved,"original DISK7 bank save did not commit");
 std::cerr<<"DISK7 "<<s.wavStatus<<"\n";
 const std::array<std::uint8_t,3> on{0x90,60,100},off{0x80,60,0};
 e.queueMidi(0,on.data(),3);
 std::uint64_t active=0;double peak=0,energy=0;
 for(int b=0;b<330;++b){
  if(b==200)e.queueMidi(0,off.data(),3);
  input.fill(0);e.pushInput(input.data(),nullptr,512,false,true,true);
  e.render(left.data(),right.data(),512,true);
  for(int i=0;i<512;++i){
   const auto a=std::max(std::abs(left[i]),std::abs(right[i]));
   need(std::isfinite(a),"nonfinite recorded audio");
   peak=std::max(peak,double(a));active+=a>1e-8;
   energy+=left[i]*left[i]+right[i]*right[i];
  }
 }
 need(active>2000&&peak>0.001,"recorded voice did not audibly play");
 std::cout<<"P038 NATIVE REAL ORIGINAL-ROM HOST-INPUT->SAR->DISK7->PCM PASS"
          <<" host_frames="<<frame<<" sar_reads="<<s.sampleReads
          <<" nonzero_pcm="<<active<<" peak="<<peak<<" energy="<<energy<<"\n";
 return 0;
}catch(const std::exception&e) {
 std::cerr<<"P038 OWNER-PRIVATE FAIL "<<e.what()<<"\n";return 1;
}
