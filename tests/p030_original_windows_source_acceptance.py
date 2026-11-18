#!/usr/bin/env python3
"""P030: source contract for positive private Windows VST3 host and public negative.
This test cannot prove genuine ROM/Choir audio without the owner's fixtures.
"""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
s=(p/"upstream/eii-emu/tools/vst3_host_test.cpp").read_text(encoding="utf-8")
for key in (
 'std::string(argv[5])=="original-windows-audio"',
 'std::string(argv[5])=="original-windows-negative"',
 'in.create(factory,cid,host)',
 'in.setState(configured)',
 'in.start(48000,kOffline,512)',
 'in.ready()&&in.status("loaded")=="1"',
 'in.status("callbacks")=="0"',
 'in.status("appliedmodel")=="5"',
 'baselinePeak<1e-4',
 'events.addEvent(note(true,60,0))',
 'events.addEvent(note(false,60,0))',
 'result.active>2000&&result.peak>0.001&&result.energy>1.0',
 'in.status("midiread")!=beforeRead',
 'in.status("underruns")=="0"',
 'in.status("dspdrops")=="0"&&in.status("eventdrops")=="0"',
 'second.energy>first.energy*0.2',
 'renderProject(saved,nullptr,"PROJECT_REOPEN")',
 'eiiThreads()==0',
 'failure.find("conflicting RFD bus drivers")',
 'P030 WINDOWS ORIGINAL ROM NEGATIVE PASS',
 'P030 ACTUAL WINDOWS ORIGINAL ROM + SSM2045',
):
    assert key in s,key
assert s.count('P030 ACTUAL WINDOWS ORIGINAL ROM + SSM2045')==1
print("P030 real packaged Windows VST3 private ROM/PCM/recall and negative controls SOURCE PASS")
