#!/usr/bin/env python3
"""P030: genuine owner-local Windows VST3 ROM/Choir/PCM/project recall probe.
No firmware is included in source, public CI or generated artifacts.
The same test code also runs a synthetic invalid-ROM negative control in CI.
"""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"upstream/eii-emu/tools/vst3_host_test.cpp"
MARKER='    auto host=owned(new HostApplication());'
BLOCK=r'''
    if(argc>5&&std::string(argv[5])=="original-windows-binary-recall"){
        // Fully deterministic real Windows factory/COM regression. Public CI
        // has no original EII ROM, but can prove why modifying a binary song
        // as plain text is invalid, and that unmodified media survive reopen.
        using namespace eii::portable;
        Instance first,second;
        if(!first.create(factory,cid,host)||!second.create(factory,cid,host)){
            std::cout<<"P031 WINDOWS BINARY RECALL FAIL: factory instantiation\n";
            return 1;
        }
        auto state=decodeProject(first.getState());
        auto settings=replaceKey(state.settings,"autoboot","0");
        settings=replaceKey(settings,"model","5");
        settings=replaceKey(settings,"rom","C:\\Owner\\EII\\ROM");
        std::vector<std::uint8_t> syntheticBank(bankBytes,0);
        for(std::size_t i=bankDataOffset;i<syntheticBank.size();++i)
            syntheticBank[i]=std::uint8_t((i*17u+(i>>7)+19u)&255u);
        const auto binaryState=encodeProject(settings,syntheticBank);
        check(first.setState(binaryState),
              "P031 original Windows VST3 accepts checksum-correct bank project");
        const auto stored=first.getState();
        check(stored==binaryState,
              "P031 original Windows VST3 preserves bank and state bytes");
        const auto decoded=decodeProject(stored);
        check(decoded.hasBank()&&decoded.bank.size()==bankBytes&&
                  decoded.settings.find("\nmodel=5\n")!=std::string::npos,
              "P031 full binary bank checksum and settings decode");
        auto damaged=replaceKey(stored,"rom","Z:\\Other\\ROM");
        check(damaged!=stored,
              "P031 legacy raw text substitution actually alters binary project");
        check(!second.setState(damaged),
              "P031 VST3 rejects raw-edited bank with stale checksum");
        check(second.setState(stored),
              "P031 fresh real Windows VST3 restores unmodified host IBStream");
        check(second.getState()==stored,
              "P031 fresh real Windows VST3 recalls identical embedded media");
        first.shutdown();second.shutdown();
        check(eiiThreads()==0,"P031 zero leaked EII worker threads");
        module.reset();
        std::cout<<(failures?"P031 WINDOWS BINARY RECALL FAIL ":
                             "P031 WINDOWS BINARY RECALL PASS ")
                 <<failures<<" failure(s)\n";
        return failures?1:0;
    }
    if(argc>5&&(std::string(argv[5])=="original-windows-audio"||
                std::string(argv[5])=="original-windows-negative")){
        namespace fs=std::filesystem;
        using ClockP030=std::chrono::steady_clock;
        const bool negative=std::string(argv[5])=="original-windows-negative";
        const fs::path scratch=fs::temp_directory_path()/
            ("eii_p030_original_"+std::to_string(GetCurrentProcessId()));
        fs::path privateRom=rom,privateFloppy=floppy;
        std::string failure;
        struct PcmP030{std::uint64_t active=0;double peak=0,energy=0;};
        auto requireP030=[](bool valid,const std::string& why){
            if(!valid)throw std::runtime_error("P030 "+why);
        };
        try{
            if(negative){
                fs::create_directories(scratch);
                auto synthetic=[&](const fs::path& file,std::size_t n){
                    std::ofstream out(file,std::ios::binary);
                    if(!out)throw std::runtime_error("P030 cannot create negative fixture");
                    std::vector<char> zero(n,0);
                    out.write(zero.data(),std::streamsize(zero.size()));
                    if(!out)throw std::runtime_error("P030 synthetic fixture truncated");
                };
                synthetic(scratch/"main.bin",8192);
                synthetic(scratch/"scanner.bin",8192);
                synthetic(scratch/"ic135.bin",512);
                synthetic(scratch/"ic137.bin",512);
                synthetic(scratch/"invalid.emuiifd",573440);
                privateRom=scratch;privateFloppy=scratch/"invalid.emuiifd";
            }
            for(const auto& romFile:std::array<std::pair<const char*,std::uintmax_t>,4>{
                    {{"main.bin",8192},{"scanner.bin",8192},{"ic135.bin",512},{"ic137.bin",512}}}){
                const auto p=privateRom/romFile.first;
                requireP030(fs::is_regular_file(p)&&fs::file_size(p)==romFile.second,
                           std::string("missing or wrong-size original ROM ")+romFile.first);
            }
            requireP030(fs::is_regular_file(privateFloppy),"missing original EII floppy");
            if(privateFloppy.extension()==".emuiifd")
                requireP030(fs::file_size(privateFloppy)==573440,
                           "original EMUIIFD floppy must be 573440 bytes");
            // Test the actual packaged VST3, original firmware machine and
            // host-owned ProcessData, not the standalone Machine() test.
            auto renderProject=[&](const std::string& restored,std::string* saved,
                                   const char* pass)->PcmP030{
                Instance in;
                requireP030(in.create(factory,cid,host),
                           "could not instantiate actual Windows Custom VST3");
                // The state is a *binary, checksummed* envelope when it has an
                // embedded bank or HDD. Never run replaceKey on the IBStream
                // bytes: that changes the payload without updating its hash.
                // A real DAW also reopens the exact saved IBStream, unchanged.
                std::string configured;
                if(restored.empty()){
                    auto original=eii::portable::decodeProject(in.getState());
                    auto settings=original.settings;
                    settings=replaceKey(settings,"rom",privateRom.string());
                    settings=replaceKey(settings,"floppy",privateFloppy.string());
                    settings=replaceKey(settings,"autoboot","1");
                    settings=replaceKey(settings,"model","5");
                    settings=replaceKey(settings,"native","0");
                    // P032: exercise the real nominal reconstruction filter
                    // after the original firmware has written its S3528 codes.
                    settings=replaceKey(settings,"s3528","1");
                    settings=replaceKey(settings,"memory1mb","0");
                    configured=eii::portable::encodeProject(settings,original.bank,original.hdd);
                }else{
                    const auto original=eii::portable::decodeProject(restored);
                    requireP030(original.settings.find("\nmodel=5\n")!=std::string::npos,
                               "reopened original project state lost SSM2045 model=5");
                    requireP030(original.settings.find("\nrom=")!=std::string::npos,
                               "reopened original project state lost the ROM reference");
                    requireP030(original.settings.find("\ns3528=1\n")!=std::string::npos,
                               "reopened original project state unexpectedly disabled S3528");
                    configured=restored; // strict, byte-for-byte host project recall
                }
                requireP030(in.setState(configured),
                           "original host IBStream project state rejected");
                requireP030(in.start(48000,kOffline,512),
                           "real Windows VST3 host process initialization failed");
                // P021/P024: no DAW callback at all during the independent
                // 4MHz original-ROM boot. Wait on the true Pxx LCD, not sleep.
                bool ready=false;
                const auto start=ClockP030::now();
                while(ClockP030::now()-start<std::chrono::seconds(240)){
                    const auto err=in.status("error");
                    if(!err.empty())throw std::runtime_error("P030 original boot halted: "+err);
                    if(in.ready()&&in.status("loaded")=="1"){ready=true;break;}
                    Sleep(75);
                }
                requireP030(ready,"original firmware never reached playable Pxx");
                requireP030(in.status("callbacks")=="0",
                           "host audio callbacks occurred during autonomous boot");
                requireP030(in.status("appliedmodel")=="5",
                           "original EII SSM2045 Model 2 (96k) was NOT applied");
                requireP030(in.status("appliednative")=="0"&&
                           in.status("applieds3528")=="1",
                           "original EII S3528 reconstruction was not enabled in the actual audio engine");
                const auto beforeRead=in.status("midiread");
                requireP030(!beforeRead.empty(),
                           "MIDI UART diagnostic unavailable on real Windows host");
                // Establish silence before deliberate NoteOn, so a failed
                // instrument cannot pass by playing stale firmware audio.
                double baselinePeak=0;
                for(int b=0;b<8;++b){
                    requireP030(in.process(),"pre-note COM audio callback rejected");
                    for(int i=0;i<in.block;++i){
                        requireP030(std::isfinite(in.left[i])&&std::isfinite(in.right[i]),
                                   "non-finite pre-note PCM");
                        baselinePeak=std::max(baselinePeak,
                            std::max(double(std::abs(in.left[i])),double(std::abs(in.right[i]))));
                    }
                }
                requireP030(baselinePeak<1e-4,
                           "pre-note output was not silent; audio oracle contaminated");
                PcmP030 result;
                for(int b=0;b<330;++b){
                    EventList events;
                    if(b==0){auto on=note(true,60,0);events.addEvent(on);}
                    if(b==200){auto off=note(false,60,0);events.addEvent(off);}
                    requireP030(in.process(b==0||b==200?&events:nullptr),
                               "actual Windows VST3 MIDI/PCM callback rejected");
                    for(int i=0;i<in.block;++i){
                        const double l=in.left[i],r=in.right[i];
                        requireP030(std::isfinite(l)&&std::isfinite(r),
                                   "original hardware produced NaN/Inf PCM");
                        const double amplitude=std::max(std::abs(l),std::abs(r));
                        if(amplitude>1e-8)++result.active;
                        result.peak=std::max(result.peak,amplitude);
                        result.energy+=l*l+r*r;
                    }
                }
                requireP030(result.active>2000&&result.peak>0.001&&result.energy>1.0,
                           "no genuinely audible original-ROM/Choir MIDI audio");
                requireP030(in.status("error").empty(),
                           "original EII hardware halted during actual host playback");
                requireP030(in.status("underruns")=="0",
                           "original-ROM offline Windows VST3 audio underrun");
                requireP030(in.status("dspdrops")=="0"&&in.status("eventdrops")=="0",
                           "original-ROM Windows VST3 lost DSP or MIDI events");
                requireP030(in.status("midiread")!=beforeRead,
                           "guest original MIDI UART did not consume host MIDI");
                if(saved){
                    *saved=in.getState();
                    requireP030(!saved->empty(),"VST3 returned an empty IBStream project");
                    const auto decoded=eii::portable::decodeProject(*saved);
                    requireP030(decoded.settings.find("\nmodel=5\n")!=std::string::npos,
                               "saved host state lacks selected original SSM filter");
                    requireP030(decoded.settings.find("\nrom=")!=std::string::npos,
                               "saved host state lost original firmware reference");
                    requireP030(decoded.settings.find("\ns3528=1\n")!=std::string::npos,
                               "saved host state lost original EII reconstruction route");
                }
                std::cout<<"P030 "<<pass<<" original Pxx="<<in.status("lcd0")
                         <<" model="<<in.status("appliedmodel")
                         <<" s3528="<<in.status("applieds3528")
                         <<" frames="<<330ull*512
                         <<" nonzero="<<result.active
                         <<" peak="<<result.peak
                         <<" energy="<<result.energy
                         <<" guest_midi_read="<<in.status("midiread")
                         <<" host_callbacks="<<in.status("callbacks")
                         <<"\n";
                in.shutdown();
                requireP030(eiiThreads()==0,
                           "original-ROM VST3 owner/DSP threads leaked after close");
                return result;
            };
            std::string saved;
            const auto first=renderProject({},&saved,"FIRST_INSTANCE");
            const auto second=renderProject(saved,nullptr,"PROJECT_REOPEN");
            requireP030(second.energy>first.energy*0.2&&
                        second.energy<first.energy*5.0,
                       "original Choir audible energy changed excessively on project reopen");
            requireP030(second.active>2000,
                       "original bank lost voices on fresh project recall");
            std::cout<<"P030 ACTUAL WINDOWS ORIGINAL ROM + SSM2045 + ORIGINAL "
                        "MIDI/PCM + FRESH VST3 PROJECT REOPEN PASS\n";
        }catch(const std::exception& ex){
            failure=ex.what();
            std::cout<<"P030 ORIGINAL ROM HOST FAILURE: "<<failure<<"\n";
        }
        if(negative){
            // This test MUST reject a fake ROM for the genuine original
            // hardware RFD-bus error, not merely for missing files.
            check(failure.find("conflicting RFD bus drivers")!=std::string::npos,
                  "P030 invalid synthetic ROM is rejected by the true original hardware bus");
            check(failure.find("genuinely audible")==std::string::npos,
                  "P030 negative controls cannot fake real instrument sound");
            std::error_code ec;fs::remove_all(scratch,ec);
            module.reset();
            std::cout<<(failures?"P030 WINDOWS ORIGINAL ROM NEGATIVE FAIL ":
                                 "P030 WINDOWS ORIGINAL ROM NEGATIVE PASS ")
                     <<failures<<" failure(s)\n";
            return failures?1:0;
        }
        module.reset();
        if(!failure.empty())return 1;
        return failures?1:0;
    }
'''
def patch(s):
    if "P030 ACTUAL WINDOWS ORIGINAL ROM" in s:
        raise RuntimeError("P030 was already applied")
    if "P029 ACTUAL WINDOWS VST3 DEFAULT" not in s:
        raise RuntimeError("P030 requires P029 and P026 host probes")
    if s.count(MARKER)!=1:
        raise RuntimeError(f"P030 host insertion anchor count {s.count(MARKER)}, wanted 1")
    return s.replace(MARKER,MARKER+"\n"+BLOCK,1)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    args=p.parse_args()
    s=TARGET.read_text(encoding="utf-8")
    out=patch(s)
    if args.verify:print("P030 pinned Windows COM source host probe anchors verified")
    else:
        TARGET.write_text(out,encoding="utf-8",newline="\n")
        print("P030 optional private positive Windows original-ROM MIDI+PCM+project reopen test installed")
if __name__=="__main__":main()
