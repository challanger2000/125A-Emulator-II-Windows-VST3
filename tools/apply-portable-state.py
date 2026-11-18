#!/usr/bin/env python3
"""P004b VST3 host-state integration. Apply after pinned P001/P003 overlays."""
import argparse
from pathlib import Path
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"
ENGINE=UP/"src/vst3/plugin_engine.h"
VST=UP/"src/vst3/eii_vst3.cpp"
FLOPPY=UP/"src/floppy_image_backing.h"
def one(s, old, new, label):
    n=s.count(old)
    if n!=1: raise RuntimeError(f"P004 {label}: expected 1 anchor, found {n}")
    return s.replace(old,new,1)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN: raise RuntimeError("Wrong upstream EII core SHA "+sha)
    e=ENGINE.read_text(encoding="utf-8")
    v=VST.read_text(encoding="utf-8")
    f=FLOPPY.read_text(encoding="utf-8")
    if "restoreEmbeddedBank(" in e or "portable::decode(text)" in v:
        raise RuntimeError("P004 already present; never patch twice")
    f=one(f,
       ' std::filesystem::path path;bool direct=false,writable=true,dirty=false,imported=false,bankImport=false;',
       ' std::filesystem::path path;bool direct=false,writable=true,dirty=false,imported=false,bankImport=false;\n std::uint64_t writtenTracks=0;',
       "write counter")
    f=one(f,
       ' FloppyImageBacking(std::filesystem::path source,bool directWrites',
       ''' explicit FloppyImageBacking(std::vector<std::uint8_t> raw){
  if(raw.size()!=EmuiiImage::imageBytes)throw std::runtime_error("Invalid EII memory floppy image length");
  image=std::make_shared<EmuiiImage>(std::move(raw));
 }
 FloppyImageBacking(std::filesystem::path source,bool directWrites''',
       "in-memory raw EMUIIFD constructor")
    f=one(f,'  dirty=true;if(hfe)hfe->replaceSector(cylinder,side,data);',
          '  dirty=true;++writtenTracks;if(hfe)hfe->replaceSector(cylinder,side,data);',
          "track-write account")

    e=one(e,'#include "vst3/plugin_state.h"',
          '#include "vst3/plugin_state.h"\n#include "125a_portable_state.h"',
          "engine state include")
    e=one(e,'    void sampleSource(std::shared_ptr<analog::SampleInputSource> s){',
       '''    // Host and GUI only. Machine-owner executes the snapshot between quanta.
    std::future<std::vector<std::uint8_t>> embeddedSnapshot(){
        auto p=std::make_shared<std::promise<std::vector<std::uint8_t>>>();
        auto f=p->get_future();
        post([this,p]{try{
            if(wavCapture_.active())throw std::runtime_error("WAV recording in progress");
            if(floppyBacking_&&!floppyState().idle)
                throw std::runtime_error("EII floppy write still active");
            if(wavNeedsBankSave_){
                if(!floppyBacking_||floppyBacking_->writtenTracks<wavWriteBaseline_||
                   floppyBacking_->writtenTracks-wavWriteBaseline_<130)
                    throw std::runtime_error("WAV is only in RAM. Run original DISK 7 SAVE BANK before saving DAW project.");
                wavNeedsBankSave_=false;
            }
            if(!floppyBacking_){p->set_value({});return;}
            if(!floppyBacking_->image||floppyBacking_->hfe)
                throw std::runtime_error("Embedded state currently supports EMUIIFD only");
            const auto bytes=floppyBacking_->image->bytes();
            if(bytes.size()!=portable::bankBytes)throw std::runtime_error("Wrong EII floppy size");
            std::vector<std::uint8_t> bank(bytes.begin(),bytes.end());
            std::fill_n(bank.begin(),host::FloppyImageBacking::bankOffset,0);
            projectBank_=bank;
            p->set_value(std::move(bank));
        }catch(...){p->set_exception(std::current_exception());}});
        return f;
    }
    std::future<bool> restoreEmbeddedBank(PluginSettings s,std::vector<std::uint8_t> bank){
        auto p=std::make_shared<std::promise<bool>>();auto f=p->get_future();
        post([this,p,s,bank=std::move(bank)]()mutable{
            if(bank.size()!=portable::bankBytes||wavCapture_.active()){
                p->set_value(false);return;
            }
            const auto beforeSettings=settings_;auto beforeBank=projectBank_;
            const bool beforePending=wavNeedsBankSave_;
            const auto beforeWrites=wavWriteBaseline_;
            Machine* const before=machine_.get();
            settings_=s;settings_.directImageWrites=false;
            projectBank_=std::move(bank);wavNeedsBankSave_=false;wavWriteBaseline_=0;
            bootNow(false,true);
            const bool ok=machine_&&machine_.get()!=before;
            if(!ok){settings_=beforeSettings;projectBank_=std::move(beforeBank);
                wavNeedsBankSave_=beforePending;wavWriteBaseline_=beforeWrites;}
            p->set_value(ok);
        });
        return f;
    }
    void clearEmbeddedBank(){post([this]{
        if(wavCapture_.active())return;
        projectBank_.clear();wavNeedsBankSave_=false;wavWriteBaseline_=0;
    });}
    void sampleSource(std::shared_ptr<analog::SampleInputSource> s){''',
       "engine API")
    e=one(e,'    std::shared_ptr<wav::Source> autoWavSource_;',
       '    std::vector<std::uint8_t> projectBank_;\n'
       '    bool wavNeedsBankSave_=false;std::uint64_t wavWriteBaseline_=0;\n'
       '    std::shared_ptr<wav::Source> autoWavSource_;',
       "engine owner state")
    e=one(e,
       '                wavSuccess_=true;++wavReport_;wavRelease();',
       '                wavNeedsBankSave_=true;\n'
       '                wavWriteBaseline_=floppyBacking_?floppyBacking_->writtenTracks:0;\n'
       '                wavSuccess_=true;++wavReport_;wavRelease();',
       "require original firmware save after capture")
    e=one(e,
       '            const bool holdFloppy=hd&&!c.bootFloppy;\n            if(!c.floppy.empty()){\n'
       '                freshFloppy=std::make_shared<host::FloppyImageBacking>(c.floppy,c.directImageWrites,',
       '''            const bool holdFloppy=hd&&!c.bootFloppy;
            if(!projectBank_.empty()){
                if(hd)throw std::runtime_error("Embedded EII bank with HDD unsupported");
                const auto path=!c.osImage.empty()?c.osImage:c.floppy;
                if(path.empty())throw std::runtime_error("Original EII OS3.1 floppy path required for bank restore");
                host::FloppyImageBacking originalOs(path,false);
                const auto os=originalOs.image->bytes();
                if(os.size()<host::FloppyImageBacking::bankOffset)
                    throw std::runtime_error("Original EII OS area missing");
                auto disk=projectBank_;
                std::copy_n(os.begin(),host::FloppyImageBacking::bankOffset,disk.begin());
                freshFloppy=std::make_shared<host::FloppyImageBacking>(std::move(disk));
                installFloppy(*fresh,freshFloppy);
                media="125A embedded performance bank / original OS user file";
            }else if(!c.floppy.empty()){
                freshFloppy=std::make_shared<host::FloppyImageBacking>(c.floppy,c.directImageWrites,''',
       "in-memory bank boot")
    e=one(e,
       '        floppyBacking_=std::move(fresh);floppyLastSaved_.clear();settings_.floppy=path;',
       '        floppyBacking_=std::move(fresh);floppyLastSaved_.clear();settings_.floppy=path;\n'
       '        projectBank_.clear();wavNeedsBankSave_=false;wavWriteBaseline_=0;',
       "switch to new user floppy")

    v=one(v,'#include "vst3/plugin_editor.h"',
          '#include "vst3/plugin_editor.h"\n#include "125a_portable_state.h"',
          "VST3 state header")
    v=one(v,
       '        eii::vst::PluginSettings s;\n        try{s=eii::vst::parseSettings(text);}catch(...){return kResultFalse;}',
       '''        eii::portable::ProjectState packed;
        eii::vst::PluginSettings s;
        try{
            packed=eii::portable::decode(text);
            s=eii::vst::parseSettings(packed.settings);
            if(packed.hasBank()){
                if(!s.autoBoot||!s.hdd.empty())return kResultFalse;
                s.directImageWrites=false;
                auto f=engine_->restoreEmbeddedBank(s,std::move(packed.bank));
                if(f.wait_for(std::chrono::seconds(15))!=std::future_status::ready||!f.get())
                    return kResultFalse;
            }else engine_->clearEmbeddedBank();
        }catch(...){return kResultFalse;}''',
       "VST3 setState parse and stage")
    v=one(v,
       '        if(s.autoBoot&&!s.romFolder.empty())engine_->boot(s,false,true);else engine_->configure(s);',
       '''        if(!eii::portable::starts(text,std::string_view(eii::portable::magic.data(),
                eii::portable::magic.size()))){
            if(s.autoBoot&&!s.romFolder.empty())engine_->boot(s,false,true);
            else engine_->configure(s);
        }''',
       "avoid re-boot after successful restore")
    v=one(v,
       '''        const auto text=eii::vst::serializeSettings(settings());
        int32 written=0;return stream->write(const_cast<char*>(text.data()),int32(text.size()),&written)==kResultOk&&written==int32(text.size())?kResultOk:kResultFalse;''',
       '''        try{
            std::vector<std::uint8_t> bank;
            if(engine_){
                auto f=engine_->embeddedSnapshot();
                if(f.wait_for(std::chrono::seconds(5))!=std::future_status::ready)
                    return kResultFalse;
                bank=f.get();
            }
            const auto text=eii::portable::encode(eii::vst::serializeSettings(settings()),bank);
            int32 written=0;
            return stream->write(const_cast<char*>(text.data()),int32(text.size()),&written)==kResultOk
                &&written==int32(text.size())?kResultOk:kResultFalse;
        }catch(...){return kResultFalse;}''',
       "VST3 getState snapshot")
    if a.verify:
        print("P004b pinned host project-state integration anchors PASS");return
    shutil.copyfile(ROOT/"src/125a_portable_state.h",UP/"src/125a_portable_state.h")
    FLOPPY.write_text(f,encoding="utf-8",newline="\n")
    ENGINE.write_text(e,encoding="utf-8",newline="\n")
    VST.write_text(v,encoding="utf-8",newline="\n")
    print("P004b local VST3 owner-state integration patch applied")
if __name__=="__main__":main()
