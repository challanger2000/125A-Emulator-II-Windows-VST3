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
    // No artificial 10-second restriction: accept up to one original bank.
    a=f.begin(0,12*s);
    req(!a.completed&&a.action==CaptureAction::SampleDown,"12-second WAV accepted");
    a=f.begin(0,FirmwareCapture::maxDuration);
    req(!a.completed&&a.action==CaptureAction::SampleDown,"17.6-second WAV accepted");
    a=f.begin(0,FirmwareCapture::maxDuration+1);
    req(a.completed&&!a.success,"above 17.6 seconds rejected");
    // Original firmware may finish early if voices already occupy RAM.
    // A successful LCD must never mean a truncated WAV was imported.
    f.reset();f.begin(0,12*s);
    f.advance(h,"P01","",0,false,0,false);
    f.advance(2*s,"VOICE V01","",0,false,0,true);
    f.advance(2*s+h,"VOICE V01","",0,false,0,true);
    f.advance(3*s,"VOICE V01","",123,true,3*s,true);
    a=f.advance(8*s,"Sample is good","",12345,true,3*s,true);
    req(a.completed&&!a.success&&a.error,"early memory-full auto-stop rejected");
    // At the physical bank limit the firmware may stop naturally near
    // the end of the WAV, before the automatic STOP key would be pressed.
    f.reset();f.begin(0,FirmwareCapture::maxDuration);
    f.advance(h,"P01","",0,false,0,false);
    f.advance(2*s,"VOICE V01","",0,false,0,true);
    f.advance(2*s+h,"VOICE V01","",0,false,0,true);
    f.advance(3*s,"VOICE V01","",10,true,3*s,true);
    a=f.advance(3*s+FirmwareCapture::maxDuration-FirmwareCapture::endTolerance/2,
                "Sample is good","",490000,true,3*s,true);
    req(a.action==CaptureAction::SampleDown&&f.phase()==CapturePhase::ExitHeld,
        "natural full-bank completion accepted when source is complete");
    a=f.advance(3*s+FirmwareCapture::maxDuration+2*h,
                "P01 NULL PRESET","",490000,true,3*s,false);
    req(a.action==CaptureAction::SampleUp,"natural stop exit key released");
    a=f.advance(3*s+FirmwareCapture::maxDuration+3*h,
                "P01 NULL PRESET","",490000,true,3*s,false);
    req(a.completed&&a.success,"natural full-bank end returns to preset");
    // P037: a single SAR read followed by a fabricated firmware-complete
    // display is never evidence of a recorded waveform.
    f.reset();f.begin(0,s);
    f.advance(h,"P01","",0,false,0,false);
    f.advance(2*s,"VOICE V01","",0,false,0,true);
    f.advance(2*s+h,"VOICE V01","",0,false,0,true);
    f.advance(3*s,"VOICE V01","",1,true,3*s,true);
    a=f.advance(3*s+s,"Sample is good","",1,true,3*s,true);
    req(a.completed&&!a.success&&f.phase()==CapturePhase::Failed,
        "P037 firmware LCD good must not mask stalled original ADC");
    // P037: even after a STOP acknowledgement the volume of ADC reads
    // must match a nontrivial recording, rather than a stale RAM voice.
    f.reset();f.begin(0,s);
    f.advance(h,"P01","",0,false,0,false);
    f.advance(2*s,"VOICE V01","",0,false,0,true);
    f.advance(2*s+h,"VOICE V01","",0,false,0,true);
    f.advance(3*s,"VOICE V01","",1,true,3*s,true);
    a=f.advance(3*s+s+s/20,"VOICE V01","",1,true,3*s,true);
    req(a.completed&&!a.success,"P037 no progress fails before STOP action");
    // P037: source start cannot precede a future machine tick.
    f.reset();f.begin(0,s);
    f.advance(h,"P01","",0,false,0,false);
    f.advance(2*s,"VOICE V01","",0,false,0,true);
    f.advance(2*s+h,"VOICE V01","",0,false,0,true);
    a=f.advance(3*s,"VOICE V01","",1,true,4*s,true);
    req(a.action==CaptureAction::None && f.phase()==CapturePhase::AwaitFirstRead,
        "P037 reject future source start timestamp");
    std::cout<<"125A original-firmware SAMPLE/FORCE/STOP/preset controller: PASS\n";
}
