// SPDX-License-Identifier: GPL-3.0-only
#include "125a_live_media_watch.h"
#include <cstdlib>
#include <iostream>
using eii::portable::LiveMediaWatch;
static void check(bool x,const char* what){if(!x){std::cerr<<"FAIL P015 "<<what<<"\n";std::exit(1);}}
int main(){
    LiveMediaWatch w;
    check(!w.armed(),"initially unarmed");
    check(!w.observe(false,false,0,0),"no media");
    check(!w.observe(false,false,24000,400000),"boot OS floppy/HDD reads ignored");
    check(!w.armed(),"boot is not performance mode");
    check(!w.observe(true,false,24010,400300),"first preset display only arms watch");
    check(w.armed(),"Pxx enables media tracking");
    check(!w.observe(true,false,24010,400300),"stationary counters do not flag sample");
    check(w.observe(false,false,24011,400300),"firmware received an SIO disk character");
    check(!w.observe(false,false,24011,400300),"no repeated warning without more bytes");
    check(w.observe(false,false,24011,400301),"firmware received HDD byte");
    check(!w.observe(true,false,0,0),"counter reset never fabricates transfer");
    check(w.observe(true,false,2,0),"new image's real SIO reads are observed");
    check(w.observe(false,true,2,0),"original SAR/SAMPLE mode dirties current RAM");
    w.reset();
    check(!w.armed(),"reset before each original machine reboot");
    check(!w.observe(false,false,500,300),"new boot receives expected OS bytes");
    check(!w.observe(true,false,800,400),"Pxx baseline after reboot");
    check(w.observe(true,false,800,401),"HDD read after Pxx warns");
    std::cout<<"P015 original firmware media change and sample-mode observability: PASS\n";
}
