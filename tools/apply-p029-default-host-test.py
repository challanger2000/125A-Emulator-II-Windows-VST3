#!/usr/bin/env python3
"""Install P029 actual Windows VST3 COM default/persistence regression.

The test exercises real factory instances and their real IBStream state, and
isolates LOCALAPPDATA so the runner's/human's defaults cannot be damaged.
"""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOST=ROOT/"upstream/eii-emu/tools/vst3_host_test.cpp"

def patch(s):
    if "P029 ACTUAL WINDOWS VST3 DEFAULT" in s:
        raise RuntimeError("P029 already integrated")
    if "P026 WINDOWS REAL VST3 COM" not in s:
        raise RuntimeError("P029 needs P026 actual COM hosting")
    marker="    auto host=owned(new HostApplication());"
    if s.count(marker)!=1:
        raise RuntimeError(f"P029 host insertion anchor count {s.count(marker)}, expected 1")
    block=r'''
    if(argc>5&&std::string(argv[5])=="default-filter"){
        namespace fs=std::filesystem;
        const auto isolated=fs::temp_directory_path()/
            ("eii_p029_settings_"+std::to_string(GetCurrentProcessId()));
        std::error_code ec;
        fs::remove_all(isolated,ec);
        fs::create_directories(isolated);
        if(_putenv_s("LOCALAPPDATA",isolated.string().c_str())!=0)
            throw std::runtime_error("P029 could not isolate LOCALAPPDATA");
        const auto defaults=isolated/"EmulatorII-VST3"/"plugin-defaults.txt";
        std::string fresh;
        {
            Instance in;
            if(!in.create(factory,cid,host))throw std::runtime_error("P029 cannot create actual VST3");
            fresh=in.getState();
            check(fresh.find("\nmodel=5\n")!=std::string::npos,
                  "P029 real fresh VST3 instance starts with original EII SSM2045 Model 2 (96k)");
            check(!fs::exists(defaults),
                  "P029 ordinary first initialization does not write global model defaults");
            const auto oldProject=replaceKey(fresh,"model","4");
            check(in.setState(oldProject),
                  "P029 existing EIII-CEM3387 project restores model 4 without migration");
            check(in.getState().find("\nmodel=4\n")!=std::string::npos,
                  "P029 saved project retains EIII-CEM3387 after host setState");
            in.shutdown();
        }
        check(!fs::exists(defaults),
              "P029 CEM project closing MUST NOT overwrite new EII instance default");
        {
            Instance in;
            if(!in.create(factory,cid,host))throw std::runtime_error("P029 second VST3 init failed");
            check(in.getState().find("\nmodel=5\n")!=std::string::npos,
                  "P029 second fresh instance remains EII after CEM project termination");
        }
        check(!fs::exists(defaults),
              "P029 ordinary EII instance close must not create global defaults");
        const auto intentionalCem=replaceKey(fresh,"model","4");
        fs::create_directories(defaults.parent_path());
        {std::ofstream f(defaults,std::ios::binary|std::ios::trunc);
         f.write(intentionalCem.data(),std::streamsize(intentionalCem.size()));
         if(!f)throw std::runtime_error("P029 cannot seed explicit global user preference");}
        {
            Instance in;
            if(!in.create(factory,cid,host))throw std::runtime_error("P029 saved-default VST3 init failed");
            check(in.getState().find("\nmodel=4\n")!=std::string::npos,
                  "P029 explicitly stored CEM user default is honored for fresh VST3");
            check(in.setState(replaceKey(fresh,"model","5")),
                  "P029 another EII project can be restored without changing explicit default");
            in.shutdown();
        }
        {std::ifstream f(defaults,std::ios::binary);
         std::string actual((std::istreambuf_iterator<char>(f)),std::istreambuf_iterator<char>());
         check(actual==intentionalCem,
               "P029 project recall and close preserve explicit CEM global preference byte-for-byte");}
        fs::remove(defaults);
        {
            Instance in;
            if(!in.create(factory,cid,host))throw std::runtime_error("P029 restored fresh VST3 init failed");
            check(in.getState().find("\nmodel=5\n")!=std::string::npos,
                  "P029 removing explicit override restores original EII built-in fallback");
            in.shutdown();
        }
        module.reset();
        fs::remove_all(isolated,ec);
        std::cout<<(failures?"P029 ACTUAL WINDOWS VST3 DEFAULT FAIL ":
                             "P029 ACTUAL WINDOWS VST3 DEFAULT PASS ")
                 <<failures<<" failure(s)\n";
        return failures?1:0;
    }
'''
    return s.replace(marker,marker+"\n"+block,1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify",action="store_true")
    args=p.parse_args()
    old=HOST.read_text(encoding="utf-8")
    new=patch(old)
    if args.verify:
        print("P029 original COM host factory/IBStream source anchor PASS")
    else:
        HOST.write_text(new,encoding="utf-8",newline="\n")
        print("P029 actual packaged Windows COM new-instance and legacy-global-default host regression installed")

if __name__=="__main__":
    main()
