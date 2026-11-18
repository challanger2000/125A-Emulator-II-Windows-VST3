#!/usr/bin/env python3
"""P017 HDD project safety source invariants. Original ROM remains private."""
from pathlib import Path
base=Path(__file__).resolve().parents[1]/"upstream/eii-emu/src/vst3"
e=(base/"plugin_engine.h").read_text(encoding="utf-8")
c=(base/"eii_vst3.cpp").read_text(encoding="utf-8")
s=(base/"plugin_state.h").read_text(encoding="utf-8")
ed=(base/"plugin_editor.h").read_text(encoding="utf-8")
def need(t,v):
    if v not in t:raise AssertionError("P017 missing: "+v)
for v in (
    'std::shared_ptr<const std::vector<std::uint8_t>> embeddedHdd_,projectHdd_;',
    'std::future<bool> captureHddForProject(){',
    'bool projectNeedsHddCapture()const noexcept{',
    'machine_->hardDisk->phase!=HardDisk::Free',
    'auto copy=std::make_shared<const std::vector<std::uint8_t>>(image);',
    '{std::lock_guard l(projectMediaMutex_);projectHdd_=copy;',
    'void restoreProjectMedia(PluginSettings s,',
    'embeddedBank_=bank;embeddedHdd_=hdd;settings_=s;',
    'const bool hd=!c.hdd.empty()||bool(embeddedHdd_);',
    'fresh->installHardDisk(embeddedHdd_?',
    'if(c.directImageWrites&&!embeddedHdd_){',
    'hddNeedsSnapshot_.store(true,std::memory_order_release);',
    'projectHdd_,hddNeedsSnapshot_.load(std::memory_order_acquire)',
):
    need(e,v)
for v in (
    'eii::portable::PortableProject project;',
    'project=eii::portable::decodeProject(text);',
    'engine_->restoreProjectMedia(s,std::move(bank),std::move(hdd));',
    'const auto h=frame.hdd;',
    'current.hddPendingCapture=frame.hddPending||!hddComplete;',
    'eii::portable::encodeProject(settingsText,',
    'f.wait_for(std::chrono::seconds(2))',
    'if(text.size()>eii::portable::maxProjectStateBytes)',
):
    need(c,v)
for v in (
    'bool hddPendingCapture=false;',
    'if(s.hddPendingCapture)o<<"hddpending=1\\n";',
    'else if(key=="hddpending"){',
    'Corrupt pending-HDD project marker',
):
    need(s,v)
need(ed,'backend_.engine().projectNeedsHddCapture()')
need(ed,'UNSAVED/INCOMPLETE - finish HDD access and save song again')
a=e[e.index('std::future<bool> captureHddForProject()'):
    e.index('    // VST3 setState:',e.index('std::future<bool> captureHddForProject()'))]
assert a.index('phase!=HardDisk::Free')<a.index('make_shared<const std::vector<std::uint8_t>>(image)')
assert 'post([this,p]{' in a
assert 'p->set_value(false)' in a
assert 'projectHdd_=copy;' in a
h=e[e.index('void bootNow(bool discard,bool fromState)'):
    e.index('    // ---- input ----')]
assert h.index('fresh->installHardDisk(embeddedHdd_?')<h.index('quiesce();')
assert 'if(c.directImageWrites&&!embeddedHdd_)' in h
v=c[c.index('tresult PLUGIN_API getState(IBStream* stream)override{'):
    c.index('// ---- IAudioProcessor ----')]
assert v.index('captureHddForProject()')<v.index('projectSaveFrame()')
assert v.index('current.hddPendingCapture=')<v.index('encodeProject')
print("P017 HDD original owner capture / 40MiB state / embedded boot source PASS")
