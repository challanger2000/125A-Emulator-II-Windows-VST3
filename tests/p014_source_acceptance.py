#!/usr/bin/env python3
"""P014 source integration: never fail whole song save for incomplete RAM."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"upstream/eii-emu/src/vst3"
engine=(root/"plugin_engine.h").read_text(encoding="utf-8")
state=(root/"plugin_state.h").read_text(encoding="utf-8")
component=(root/"eii_vst3.cpp").read_text(encoding="utf-8")
def has(s,x):
    if x not in s:raise AssertionError("P014 missing: "+x)
for x in ('bool bankPendingCapture=false;',
          'if(s.bankPendingCapture)o<<"bankpending=1\\n";',
          'else if(key=="bankpending"){',
          'throw std::runtime_error("Corrupt pending-bank project marker")'):
    has(state,x)
for x in ('bankNeedsSnapshot_.store(s.bankPendingCapture,std::memory_order_release);',
          'if(s.bankPendingCapture){',
          'SONG REOPENED WITH UNSAVED EII BANK',
          'original DISK 7 must'):
    has(engine,x)
for x in ('const auto frame=engine_?engine_->projectSaveFrame():',
          'const auto b=frame.bank;',
          'current.bankPendingCapture=frame.pending;',
          'const auto settingsText=eii::vst::serializeSettings(current);',
          'const auto settingsText=eii::vst::serializeSettings(current);'):
    has(component,x)
has(engine,'ProjectSaveFrame projectSaveFrame()const')
has(engine,'std::lock_guard l(projectMediaMutex_);\n        return {projectMedia_,')
has(engine,'projectBusy_.load(std::memory_order_acquire)||')
if 'projectHdd_,hddNeedsSnapshot_' in engine:
    has(engine,'bankNeedsSnapshot_.load(std::memory_order_acquire),')
    has(component,'eii::portable::encodeProject(settingsText,')
else:
    has(engine,'bankNeedsSnapshot_.load(std::memory_order_acquire)};')
    has(component,'eii::portable::encode(settingsText,*b)')
fragment=component[component.index('tresult PLUGIN_API getState(IBStream* stream)override{',
                                    component.index('class Plugin final')):
                   component.index('// ---- IAudioProcessor ----')]
assert 'if(engine_&&(engine_->projectSaveBusy()||engine_->projectNeedsBankCapture()))return kResultFalse;' not in fragment
assert fragment.index('const auto frame=engine_?engine_->projectSaveFrame():') < fragment.index('const auto settingsText=')
assert fragment.index('const auto b=frame.bank;') < fragment.index('current.bankPendingCapture=frame.pending;')
r=engine[engine.index('void restoreProjectBank('):engine.index('    // UI file decoding is complete',engine.index('void restoreProjectBank('))]
assert r.index('bankNeedsSnapshot_.store(true') < r.index('projectMedia_=bank;') < r.index('bankNeedsSnapshot_.store(s.bankPendingCapture')
m=engine[engine.index('std::string mountFloppyNow('):engine.index('static std::filesystem::path recoveryFolder()')]
assert m.index('bankNeedsSnapshot_.store(true') < m.index('projectMedia_.reset()')
b=engine[engine.index('void bootNow(bool discard,bool fromState)'):engine.index('    // ---- input ----')]
assert b.index('bankNeedsSnapshot_.store(true') < b.index('projectMedia_.reset()')
assert fragment.count('return kResultFalse;')==1, "Only actual stream I/O should report failed getState"
print("P014 persistent pending-bank host getState/source safety PASS")
