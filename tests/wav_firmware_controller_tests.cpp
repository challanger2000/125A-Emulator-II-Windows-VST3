// SPDX-License-Identifier: GPL-3.0-only
#include "125a_firmware_capture.h"
#include <cstdlib>
#include <iostream>
using eii::wav::CaptureAction;using eii::wav::CapturePhase;using eii::wav::FirmwareCapture;
void req(bool b,const char* msg){if(!b){std::cerr<<"FAIL "<<msg<<"\n";std::exit(1);}}
int main(){
    constexpr auto s=FirmwareCapture::ticksPerSecond,h=FirmwareCapture::holdTicks;
    FirmwareCapture f;
    req(!f.active(),"idle before begin");
    auto a=f.begin(0,s);
    req(a.action==CaptureAction::SampleDown&&f.active(),"physical SAMPLE pressed");
    req(f.advance(h/2,"P01 NULL PRESET","",0,false,0,false).action==CaptureAction::None,"physical hold");
    req(f.advance(h,"P01 NULL PRESET","",0,false,0,false).action==CaptureAction::SampleUp,"release after 100ms");
    req(f.advance(h+s,"P01 NULL PRESET","",0,false,0,false).action==CaptureAction::None,"no premature FORCE");
    a=f.advance(h+2*s,"VOICE V01  +0???","",9,false,0,true);
    req(a.action==CaptureAction::ArmForceDown,"begin hardware FORCE when firmware VOICE ready");
    req(f.advance(h+2*s+h,"VOICE V01","",9,false,0,true).action==CaptureAction::ForceUp,"release FORCE");
    const auto first= h+3*s;
    req(f.advance(first,"VOICE V01","",15,true,first,true).action==CaptureAction::None,
        "SAR reads begin gated recording");
    a=f.advance(first+s+s/20,"VOICE V01","",12345,true,first,true);
    req(a.action==CaptureAction::StopDown,"STOP after all WAV ticks and tail");
    req(f.advance(first+s+s/20+h,"VOICE V01","",12345,true,first,true).action==CaptureAction::StopUp,"release STOP");
    a=f.advance(first+s+s/20+2*h,"Sample is good","",12345,true,first,true);
    req(a.action==CaptureAction::SampleDown,"firmware-good ACK required before exit");
    req(f.advance(first+s+s/20+3*h,"","",12345,true,first,true).action==CaptureAction::SampleUp,"exit sample module");
    a=f.advance(first+s+s/20+4*h,"P01 NULL PRESET","",12345,true,first,false);
    req(a.completed&&a.success&&!f.active(),"finish only upon real preset LCD");
    auto b=f.begin(0,s);
    req(b.action==CaptureAction::SampleDown,"restarts from idle");
    f.advance(h,"P01 NULL PRESET","",0,false,0,false);
    a=f.advance(46*s,"P01 NULL PRESET","",0,false,0,false);
    req(a.completed&&!a.success&&a.error,"missing OS SAMPLE overlay is failure");
    f.reset();f.begin(0,s);
    f.advance(h,"P01","",0,false,0,false);
    f.advance(2*s,"VOICE V01","",0,false,0,true);
    f.advance(2*s+h,"VOICE V01","",0,false,0,true);
    a=f.advance(5*s,"VOICE V01","",0,false,0,true);
    req(a.completed&&!a.success,"no actual ADC reads fails");
    f.reset();f.begin(0,s);
    a=f.advance(h,"Need More Room","",0,false,0,true);
    req(a.completed&&!a.success&&f.phase()==CapturePhase::Failed,"memory must not be erased automatically");
    f.reset();f.begin(0,s);
    a=f.advance(h,"Sample Overload","",0,false,0,true);
    req(a.completed&&!a.success,"clipping is not success");
    a=f.begin(0,11*s);
    req(a.completed&&!a.success,"duration too long is rejected before panel touch");
    std::cout<<"125A original-firmware SAMPLE/FORCE/STOP/preset controller: PASS\n";
}
