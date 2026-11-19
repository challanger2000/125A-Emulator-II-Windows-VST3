// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// 125A P006: original EII firmware discovered beside the VST3 module.
// Same physical bundle topology as 125A E-MU Emulator III.
// Original ROM/OS data is provided by the owner, never in public artifacts.
#include "vst3/plugin_state.h"
#include <algorithm>
#include <cctype>
#include <cstdint>
#include <filesystem>
#include <string>
#include <system_error>
#ifdef _WIN32
#include <windows.h>
#endif
namespace eii::vst::resources {
namespace fs=std::filesystem;
inline bool fileSize(const fs::path& path,std::uintmax_t n)noexcept {
    std::error_code ec;
    return fs::is_regular_file(path,ec)&&fs::file_size(path,ec)==n&&!ec;
}
inline bool goodRom(const fs::path& p)noexcept {
    return !p.empty()&&(fileSize(p/"main.bin",8192)||fileSize(p/"main21dm.bin",8192))&&
           fileSize(p/"scanner.bin",8192)&&fileSize(p/"ic135.bin",512)&&fileSize(p/"ic137.bin",512);
}
inline std::string lowercase(std::string s){
    std::transform(s.begin(),s.end(),s.begin(),
                   [](unsigned char c){return char(std::tolower(c));});return s;
}
inline bool possibleOsDisk(const fs::path& p)noexcept {
    std::error_code ec;
    if(!fs::is_regular_file(p,ec)||ec)return false;
    const auto ext=lowercase(p.extension().string());
    if(ext==".emuiifd")return fileSize(p,573440);
    if(ext==".hfe"){
        const auto n=fs::file_size(p,ec);
        return !ec&&n>=1024&&n<32u*1024u*1024u;
    }
    return false;
}
inline fs::path uniqueOsDisk(const fs::path& folder) {
    std::error_code ec;
    if(!fs::is_directory(folder,ec)||ec)return {};
    fs::path found;
    for(fs::directory_iterator it(folder,fs::directory_options::skip_permission_denied,ec),end;
        !ec&&it!=end;it.increment(ec)){
        const fs::path p=it->path();
        if(!possibleOsDisk(p))continue;
        if(!found.empty())return {}; // ambiguous OS folder, require one selected image
        found=p;
    }
    return ec?fs::path{}:found;
}
// Only this exact known factory floppy is auto-selected. Other owner disks
// remain user-selected, so adding a second bank cannot alter boot behavior.
inline fs::path bundledFactoryChoir(const fs::path& resources) {
    const auto choir=resources/"Factory"/"EII-Choir.emuiifd";
    return fileSize(choir,573440)?choir:fs::path{};
}
inline fs::path moduleResources(){
#ifdef _WIN32
    HMODULE mod=nullptr;
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|
                           GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                           reinterpret_cast<LPCWSTR>(&moduleResources),&mod)||!mod)return {};
    std::wstring path(32768,L'\0');
    const DWORD n=GetModuleFileNameW(mod,path.data(),DWORD(path.size()));
    if(n==0||n>=path.size())return {};
    path.resize(n);
    return fs::path(path).parent_path().parent_path()/"Resources";
#else
    return {};
#endif
}
// Preserve explicit usable user paths; migrate only empty/missing paths.
// OS media remains read-only at source, never direct-written.
inline void adopt(PluginSettings& s,const fs::path& resources) {
    if(resources.empty())return;
    const auto rom=resources/"ROM";
    if(!goodRom(s.romFolder)&&goodRom(rom))s.romFolder=rom;
    const auto os=uniqueOsDisk(resources/"OS");
    if(os.empty())return;
    if(!possibleOsDisk(s.osImage))s.osImage=os;
    const auto choir=bundledFactoryChoir(resources);
    if(s.hdd.empty()&&!possibleOsDisk(s.floppy)) {
        // Genuine P044 mode: original OS 3.1 for boot, original Choir bank
        // mounted as the factory floppy. Both live INSIDE the .vst3 bundle.
        s.floppy=choir.empty()?os:choir;
    }
    if(s.floppy==os||(!choir.empty()&&s.floppy==choir))
        s.directImageWrites=false;
}
inline void adopt(PluginSettings& s){adopt(s,moduleResources());}
}
