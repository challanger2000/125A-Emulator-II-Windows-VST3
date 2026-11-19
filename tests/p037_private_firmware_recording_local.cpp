// Owner-local P037 genuine original E-mu OS 3.1 recording + playback probe.
// Uses private ROM and OS through arguments. Never commit private media.
#include "vst3/plugin_engine.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
using Clock=std::chrono::steady_clock;
using namespace std::chrono_literals;
constexpr double pi=3.1415926535897932384626433832795;
static void require(bool b,const std::string& m){if(!b)throw std::runtime_error(m);}
static void report(const eii::vst::EngineStatus& s,const char* stage){
 std::cerr<<stage<<" boot="<<eii::portable::bootStageName(s.boot.stage)
          <<" ticks="<<s.panel.ticks<<" romReady="<<s.boot.complete
          <<" lcd='"<<s.panel.lcd[0]<<"'/'"<<s.panel.lcd[1]<<"'"
          <<" wavActive="<<s.wavActive<<" success="<<s.wavSuccess
          <<" report="<<s.wavReport<<" sar="<<s.sampleReads
          <<" unknown="<<s.sampleUnknownReads<<" underruns="<<s.underruns
          <<" phase="<<s.wavStatus<<" error="<<s.panel.error<<"\n"<<std::flush;
}
struct Pcm {double peak=0,energy=0;uint64_t nonzero=0;std::vector<float> samples;};
static Pcm audition(eii::vst::PluginEngine& e,int key){
 std::array<float,512> l{},r{};Pcm o; o.samples.reserve(330*512);
 const std::array<uint8_t,3> on{0x90,uint8_t(key),100},off{0x80,uint8_t(key),0};
 e.queueMidi(0,on.data(),3);
 for(int b=0;b<330;++b){
  if(b==200)e.queueMidi(0,off.data(),3);
  e.render(l.data(),r.data(),512,true);
  for(int i=0;i<512;++i){
   require(std::isfinite(l[i])&&std::isfinite(r[i]),"non-finite audition PCM");
   const double peak=std::max(double(std::abs(l[i])),double(std::abs(r[i])));
   o.peak=std::max(o.peak,peak);o.nonzero+=peak>1e-8;o.energy+=l[i]*l[i]+r[i]*r[i];o.samples.push_back(l[i]);
  }
 }
 return o;
}
static void saveFloatWav(const std::filesystem::path& file,const std::vector<float>& mono){
 std::ofstream f(file,std::ios::binary);require(bool(f),"cannot write QA WAV");
 auto w16=[&](uint16_t n){const char b[2]={char(n&255),char(n>>8)};f.write(b,2);};
 auto w32=[&](uint32_t n){w16(uint16_t(n));w16(uint16_t(n>>16));};
 const uint32_t bytes=uint32_t(mono.size()*2);
 f.write("RIFF",4);w32(36+bytes);f.write("WAVEfmt ",8);w32(16);w16(1);w16(1);w32(48000);w32(96000);w16(2);w16(16);
 f.write("data",4);w32(bytes);
 for(float v:mono)w16(uint16_t(int16_t(std::lround(std::clamp(v,-1.f,1.f)*32767.f))));
}
int main(int argc,char**argv)try{
 require(argc==5,"usage: p037_probe ROM_DIR OS31_FLOPPY CHOIR_FLOPPY OUTPUT.wav");
 const auto rom=std::filesystem::path(argv[1]);const auto os=std::filesystem::path(argv[2]);
 const auto choir=std::filesystem::path(argv[3]);
 for(const auto f:{"main.bin","scanner.bin","ic135.bin","ic137.bin"})require(std::filesystem::is_regular_file(rom/f),"missing original ROM "+std::string(f));
 require(std::filesystem::file_size(os)==573440 && std::filesystem::file_size(choir)==573440,"wrong original media size");
 eii::vst::PluginEngine e;
 e.setupProcessing(48000,512);e.activate();
 eii::vst::PluginSettings settings;
 settings.romFolder=rom;settings.osImage=os;settings.floppy=choir;
 settings.audioMode=eii::analog::RuntimeAudioMode::BasicVoice;
 settings.directImageWrites=false;settings.memory1mb=false;settings.wavC3Keyboard=true;
 const auto start=Clock::now();e.boot(settings,true);
 eii::vst::EngineStatus s;bool ready=false;
 while(Clock::now()-start<240s){
  std::this_thread::sleep_for(100ms);s=e.status();
  if(s.boot.complete && s.boot.stage==eii::portable::BootStage::Ready&&!s.autonomousBoot){ready=true;break;}
  if(s.halted)break;
 }
 report(s,"P037 ORIGINAL ROM BOOT");require(ready,"original ROM never reached a playable Pxx");
 const auto baseline=audition(e,60);
 std::cerr<<"P037 Choir baseline key=60 nonzero="<<baseline.nonzero<<" peak="<<baseline.peak<<" energy="<<baseline.energy<<"\n";
 require(baseline.nonzero>2000,"original Choir playback baseline absent");
 // A user-supplied waveform enters original EII SAMPLE (not direct RAM injection)
 eii::wav::Wav w;w.rate=48000;w.channels=1;w.mono.resize(48000);
 for(size_t i=0;i<w.mono.size();++i)w.mono[i]=float(0.25*std::sin(2*pi*440.0*double(i)/48000.0));
 auto source=std::make_shared<eii::wav::Source>(std::move(w));
 const auto read0=s.sampleReads,rep0=s.wavReport;
 e.autoImportWav(source);
 std::array<float,512> l{},r{};
 std::string phase;
 const auto captureStart=Clock::now();
 bool finished=false;
 unsigned blocks=0;
 while(Clock::now()-captureStart<420s && blocks<26000){
  e.render(l.data(),r.data(),512,true);++blocks;
  if(blocks%25==0){
   s=e.status();
   if(s.wavStatus!=phase){phase=s.wavStatus;report(s,"P037 ORIGINAL RECORD");}
   if(s.wavReport>rep0 && !s.wavActive && (s.wavSuccess||s.wavStatus.find("cancelled")!=std::string::npos||s.wavStatus.find("failed")!=std::string::npos||!s.panel.error.empty())){
     finished=true;break;
   }
   if(s.halted)break;
  }
 }
 s=e.status();report(s,"P037 ORIGINAL RECORD RESULT");
 require(finished,"firmware capture/save did not finish within bounded host ticks");
 require(s.wavSuccess,"original firmware capture did not succeed: "+s.wavStatus);
 require(s.sampleReads>read0+25000,"original Z80 SAR read count did not show meaningful 3s capture");
 require(s.sampleUnknownReads==0,"original SAR recorded unknown bytes");
 require(source->started(),"real original firmware ADC never requested source");
 const auto recorded=audition(e,60);
 std::cerr<<"P037 RECORDED PLAYBACK nonzero="<<recorded.nonzero<<" peak="<<recorded.peak<<" energy="<<recorded.energy<<"\n";
 require(recorded.nonzero>2000 && recorded.peak>1e-3,"original recorded sample did not play");
 saveFloatWav(argv[4],recorded.samples);
 std::cout<<"P037 ORIGINAL-FIRMWARE NATIVE ENGINE SAMPLE/FORCE/STOP/DISK7 -> PLAYBACK PASS"
          <<" blocks="<<blocks<<" sar_added="<<(s.sampleReads-read0)
          <<" wav_report="<<s.wavReport<<" peak="<<recorded.peak<<" energy="<<recorded.energy
          <<"\n";
 return 0;
}catch(const std::exception& ex){std::cerr<<"P037 OWNER PRIVATE FAIL "<<ex.what()<<"\n";return 1;}
