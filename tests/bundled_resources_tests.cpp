// SPDX-License-Identifier: GPL-3.0-only
#include "125a_bundle_resources.h"
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
namespace fs=std::filesystem;
namespace bund=eii::vst::resources;
void need(bool yes,const char* why){if(!yes){std::cerr<<"FAIL "<<why<<"\n";std::exit(1);}}
void make(const fs::path& p,std::size_t n) {
    fs::create_directories(p.parent_path());std::ofstream f(p,std::ios::binary);
    const std::vector<char> b(n,1);f.write(b.data(),std::streamsize(b.size()));
}
int main(){
    const auto root=fs::temp_directory_path()/
      ("125a-eii-bundle-test-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    struct Cleanup{fs::path p;~Cleanup(){std::error_code e;fs::remove_all(p,e);}} clean{root};
    const auto res=root/"E-MU Emulator II.vst3"/"Contents"/"Resources";
    const auto rom=res/"ROM",os=res/"OS"/"Emulator-II-OS31.emuiifd";
    eii::vst::PluginSettings fresh;
    bund::adopt(fresh,res);
    need(fresh.romFolder.empty()&&fresh.floppy.empty(),"empty package stays unconfigured");
    make(rom/"main.bin",8192);make(rom/"scanner.bin",8192);
    make(rom/"ic135.bin",512);make(rom/"ic137.bin",512);
    make(os,573440);
    need(bund::goodRom(rom),"complete main/scanner/PROM ROM set");
    need(bund::uniqueOsDisk(res/"OS")==os,"one EII OS candidate selected");
    bund::adopt(fresh,res);
    need(fresh.romFolder==rom&&fresh.floppy==os&&fresh.osImage==os,"same OS/ROM layout as EIII");
    need(!fresh.directImageWrites,"owner system file never direct-written");
    // P046: factory Choir is a second disk with a different role from OS31.
    // The installable VST3 bundle contains BOTH, without an external media
    // directory. Only the exact factory named disk is auto-mounted.
    const auto choir=res/"Factory"/"EII-Choir.emuiifd";
    make(choir,573440);
    eii::vst::PluginSettings factory;
    bund::adopt(factory,res);
    need(factory.romFolder==rom&&factory.osImage==os&&factory.floppy==choir,
         "P046 fresh VST3 automatically selects internal ROM + OS31 + Choir");
    need(!factory.directImageWrites,"P046 packaged factory disk is protected read only");
    const auto savedFactory=factory;
    bund::adopt(factory,res);
    need(factory==savedFactory,"P046 stable internal boot layout after repeated startup");
    eii::vst::PluginSettings explicitOs;
    explicitOs.romFolder=rom;explicitOs.osImage=os;explicitOs.floppy=os;
    bund::adopt(explicitOs,res);
    need(explicitOs.floppy==os,"P046 user explicitly selected OS floppy preserved");
    eii::vst::PluginSettings movedFactory;
    movedFactory.romFolder="C:/absent/old-rom";
    movedFactory.osImage="C:/absent/old-os";
    movedFactory.floppy="C:/absent/old-factory";
    bund::adopt(movedFactory,res);
    need(movedFactory.romFolder==rom&&movedFactory.osImage==os&&
         movedFactory.floppy==choir,
         "P046 stale external OS/ROM/factory paths repaired to internal media");
    const auto externalFactory=root/"other"/"user-sound.emuiifd";
    make(externalFactory,573440);
    eii::vst::PluginSettings userDisk;
    userDisk.floppy=externalFactory;
    bund::adopt(userDisk,res);
    need(userDisk.floppy==externalFactory,"P046 explicitly mounted external user bank stays mounted");
    fs::remove(choir);
    eii::vst::PluginSettings absentChoir;
    bund::adopt(absentChoir,res);
    need(absentChoir.floppy==os,"P046 absent factory disk fails back to one original OS");
    make(choir,42);
    eii::vst::PluginSettings corruptChoir;
    bund::adopt(corruptChoir,res);
    need(corruptChoir.floppy==os,"P046 invalid-size factory disk never selected");
    fs::remove(choir);
    const auto original=fresh;
    bund::adopt(fresh,res);
    need(fresh==original,"idempotent resource autodetection");
    eii::vst::PluginSettings stale;
    stale.romFolder="C:/missing/rom";stale.floppy="C:/missing/os";stale.osImage="C:/missing/os";
    stale.directImageWrites=true;
    bund::adopt(stale,res);
    need(stale.romFolder==rom&&stale.floppy==os&&stale.osImage==os&&!stale.directImageWrites,
         "old paths repaired when VST3 folder is moved");
    const auto external=root/"other";
    make(external/"main.bin",8192);make(external/"scanner.bin",8192);
    make(external/"ic135.bin",512);make(external/"ic137.bin",512);
    const auto other=os.parent_path().parent_path()/"user-disk.emuiifd";
    make(other,573440);
    eii::vst::PluginSettings chosen;chosen.romFolder=external;chosen.floppy=other;chosen.osImage=other;
    bund::adopt(chosen,res);
    need(chosen.romFolder==external&&chosen.floppy==other&&chosen.osImage==other,
         "existing explicit ROM/OS locations remain unchanged");
    make(res/"OS"/"second-bank.emuiifd",573440);
    need(bund::uniqueOsDisk(res/"OS").empty(),"ambiguous bundled OS is not auto-selected");
    eii::vst::PluginSettings ambiguous;
    bund::adopt(ambiguous,res);
    need(ambiguous.floppy.empty()&&ambiguous.osImage.empty(),"fail closed on ambiguity");
    make(rom/"scanner.bin",1);
    need(!bund::goodRom(rom),"invalid sized firmware is rejected");
    std::cout<<"125A EII VST3 Resources/OS + Resources/ROM discovery: PASS\n";
}
