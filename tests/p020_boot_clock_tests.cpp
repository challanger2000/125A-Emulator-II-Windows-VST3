// SPDX-License-Identifier: GPL-3.0-only
#include "125a_boot_clock_diagnostics.h"
#include <cstdlib>
#include <iostream>
using namespace eii::portable;
static void need(bool b,const char* reason){
    if(!b){std::cerr<<"FAIL P020 "<<reason<<"\n";std::exit(1);}
}
int main(){
    BootClockDiagnostics b;
    need(b.snapshot().stage==BootStage::Idle,"initial state");
    b.begin(1000,150,500,200,500);
    auto x=b.observe(1000,150,500,200,500,false,false);
    need(x.stage==BootStage::Booting&&!x.complete,"initializing does not claim Pxx");
    x=b.observe(1500,2000150,2000500,200,500,false,false);
    need(x.stage==BootStage::Booting&&x.virtualTicks==2000000,
         "real Z80 ticks counted independently of host milliseconds");
    need(x.realtimePermille==1000,"4MHz / 1x real time is precisely 100 percent");
    x=b.observe(2000,4000150,4000500,1250,500,false,true);
    need(x.stage==BootStage::ReadingMedia&&x.floppyBytes==1050,
         "original SIO data received, distinct from elapsed wall time");
    x=b.observe(2400,5600150,5600500,1250,900,false,false);
    need(x.stage==BootStage::ReadingMedia&&x.hddBytes==400,
         "actual HDD received bytes are tracked");
    x=b.observe(4800,5600150,5600500,1250,900,false,false);
    need(x.stage==BootStage::AwaitingHostClock&&x.hostInactiveMs>=2000,
         "stopped DAW process clock cannot be mistaken for slow EII firmware");
    x=b.observe(4900,5600150,7000500,1250,900,false,false);
    need(x.stage==BootStage::EmulationBehind,
         "host advanced but owner CPU is starved, distinct from DAW pause");
    x=b.observe(6000,9000150,10000500,1250,900,false,false);
    need(x.stage==BootStage::Booting&&x.emulatorInactiveMs==0,
         "machine catches up after host stall and warning clears");
    x=b.observe(9000,15000150,16000500,2000,5000,true,false);
    need(x.stage==BootStage::Ready&&x.complete,
         "only original firmware playable Pxx proves boot complete");
    need(x.wallMs==8000 && x.virtualTicks==15000000,
         "boot elapsed is measured, not estimated from a fixed OS delay");
    auto after=b.observe(20000,60000150,80000500,3000,6000,false,false);
    need(after.wallMs==8000&&after.stage==BootStage::Ready,
         "time-to-first-Pxx frozen after completion");
    b.reset();
    need(b.snapshot().stage==BootStage::Idle,"fresh Machine reset clears boot report");
    b.begin(20000,0,0);
    x=b.observe(20001,0,0,0,0,false,false,true);
    need(x.stage==BootStage::Failed&&x.complete,
         "original machine halt distinguished from firmware waiting");
    b.begin(50000,0,0);
    x=b.observe(49999,0,0,0,0,false,false);
    need(x.wallMs==0,"clock anomaly never underflows elapsed");
    b.begin(0,0,0);
    x=b.observe(10000,0,0,0,0,false,false);
    need(x.stage==BootStage::AwaitingHostClock,
         "zero callbacks and zero hardware progress report DAW clock starvation");
    std::cout<<"P020 original boot clock: DAW stopped, CPU lag, HDD/floppy progress, true Pxx PASS\n";
}
