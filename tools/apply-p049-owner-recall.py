#!/usr/bin/env python3
"""P049 owner-local Windows COM samplebank audio recall host; build-only overlay."""
from pathlib import Path
import argparse,shutil
p=argparse.ArgumentParser()
p.add_argument('--verify',action='store_true')
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
up=root/'upstream/eii-emu'
host=up/'tools/vst3_host_test.cpp'
old=host.read_text(encoding='utf-8')
if 'original-windows-native-p044-matrix' not in old:
    raise RuntimeError('P049 requires P044 Windows host patch')
if 'original-windows-p049-audio-recall' in old:
    raise RuntimeError('P049 overlay already installed')
anchor='int main(int argc,char** argv)try{'
if old.count(anchor)!=1:raise RuntimeError('P049 main anchor changed')
new=old.replace(anchor,'#include "p049_windows_original_recall.h"\n\n'+anchor)
anchor='    if(argc>5&&std::string(argv[5])=="original-windows-native-p044-matrix"){'
if new.count(anchor)!=1:raise RuntimeError('P049 P044-dispatch anchor changed')
add='''    if(argc>5&&std::string(argv[5])=="original-windows-p049-audio-recall"){
        const auto r=p049OriginalChoirRecall(factory,cid,host,rom,floppy,
                                              argc>4?argv[4]:"",argc>6?argv[6]:".");
        module.reset();return r;
    }
'''
new=new.replace(anchor,add+anchor)
src=root/'tests/p049_windows_original_recall.h'
if not src.is_file():raise RuntimeError('P049 source header missing')
if not a.verify:
    host.write_text(new,encoding='utf-8',newline='\n')
    shutil.copyfile(src,up/'tools/p049_windows_original_recall.h')
print('P049 original-ROM owner-local Windows host patch:', 'PREFLIGHT PASS' if a.verify else 'INSTALLED')
