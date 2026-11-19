// SPDX-License-Identifier: GPL-3.0-only
// P044: same actual Windows VST3 COM + original OS 3.1 + SAR/DISK7/PCM
// acceptance as P040/P041, but *native DAC/deglitch ON* and S3528 ON.
// No private ROM/OS/Choir is published. No synthetic positive in GitHub CI.
#pragma once
#include <filesystem>
#include <optional>
#include <iostream>
#include <vector>
#include <string>

static int p044WindowsNativeOriginalAdversarial(
    const VST3::Hosting::PluginFactory& factory,const VST3::UID& cid,FUnknown* host,
    const std::string& rom,const std::string& os31,const std::string& choir){
    namespace fs=std::filesystem;
    const fs::path dir(rom);
    for(const auto* name:{"main.bin","scanner.bin","ic135.bin","ic137.bin"}){
        if(!fs::is_regular_file(dir/name)) {
            std::cout<<"P044 BLOCKED ORIGINAL MEDIA MISSING (NO FAKE NATIVE-AUDIO PASS)\n"<<std::flush;
            return 3;
        }
    }
    if(!fs::is_regular_file(os31)||!fs::is_regular_file(choir)||
       fs::file_size(os31)!=573440||fs::file_size(choir)!=573440) {
        std::cout<<"P044 BLOCKED ORIGINAL OS/CHOIR MEDIA INVALID (NO FAKE PASS)\n"<<std::flush;
        return 3;
    }
    std::cout<<"P044 ORIGINAL OS3.1 WINDOWS VST3 NATIVE-DAC=1 S3528=1"
                " real guest SAR and DISK7, 44.1/48kHz, 1k/500Hz, silence, no bus\n"<<std::flush;
    std::optional<P040Metrics> hz1000_44,hz1000_48,hz500_48,silence_48,disconnected_48;
    int failures=0;
    auto run=[&](const P040Case& tc)->std::optional<P040Metrics> {
        try {
            const auto result=p040OwnerCase(factory,cid,host,rom,os31,choir,tc);
            std::cout<<"P044 CASE "<<tc.name<<" ORIGINAL_FIRMWARE_NATIVE_DAC_EXECUTED"
                     <<" sar="<<result.sarReads<<" snapshot="<<result.storedInProject
                     <<"\n"<<std::flush;
            return result;
        }catch(const std::exception& e){
            ++failures;
            std::cout<<"P044 CASE "<<tc.name<<" FAIL: "<<e.what()<<"\n"<<std::flush;
            return std::nullopt;
        }
    };
    hz1000_44=run({"NATIVE_POSITIVE_44100_1000HZ",44100,1000,false,true});
    hz1000_48=run({"NATIVE_POSITIVE_48000_1000HZ",48000,1000,false,true});
    hz500_48=run({"NATIVE_CHANGED_48000_500HZ",48000,500,false,true});
    silence_48=run({"NATIVE_SILENCE_48000",48000,0,false,true});
    disconnected_48=run({"NATIVE_DISCONNECTED_48000",48000,0,true,true});
    auto proof=[&](bool valid,const char* name){
        std::cout<<"P044 CHECK "<<name<<" "<<(valid?"PASS":"FAIL")<<"\n"<<std::flush;
        if(!valid)++failures;
    };
    proof(hz1000_44&&hz1000_44->amp1000>0.003,"NATIVE_44100_HAS_1KHZ");
    proof(hz1000_48&&hz1000_48->amp1000>0.003,"NATIVE_48000_HAS_1KHZ");
    proof(hz500_48&&hz500_48->amp500>0.003,"NATIVE_48000_HAS_500HZ");
    proof(bool(hz1000_48&&silence_48)&&
          silence_48&&silence_48->amp1000<hz1000_48->amp1000*0.12,
          "NATIVE_SILENCE_NO_STALE_1000HZ");
    proof(bool(hz500_48&&silence_48)&&
          silence_48&&silence_48->amp500<hz500_48->amp500*0.12,
          "NATIVE_SILENCE_NO_STALE_500HZ");
    proof(bool(hz1000_48&&disconnected_48)&&
          disconnected_48&&disconnected_48->amp1000<hz1000_48->amp1000*0.12,
          "NATIVE_DISCONNECTED_NO_STALE_1000HZ");
    const bool all=hz1000_44&&hz1000_48&&hz500_48&&silence_48&&disconnected_48;
    proof(all,"ALL_FIVE_APPLIED_NATIVE_DSP_S3528_CAPTURE_SAVED_AUDITIONED");
    std::cout<<"P044 ORIGINAL WINDOWS VST3 NATIVE DAC + S3528 OWNER-PRIVATE "
             <<(failures==0?"PASS":"FAIL")<<" failed_gates="<<failures
             <<" ; NOT ORIGINAL SILICON ACCURACY CALIBRATION\n"<<std::flush;
    return failures==0?0:1;
}
