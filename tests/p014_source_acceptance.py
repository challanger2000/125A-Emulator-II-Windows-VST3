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
          'Capture via original DISK 7, then save the song again.'):
    has(engine,x)
for x in ('current.bankPendingCapture=engine_&&',
          'engine_->projectSaveBusy()||engine_->projectNeedsBankCapture()',
          'const auto settingsText=eii::vst::serializeSettings(current);',
          'eii::portable::encode(settingsText,*b)'):
    has(component,x)
fragment=component[component.index('tresult PLUGIN_API getState(IBStream* stream)override{',
                                    component.index('class Plugin final')):
                   component.index('// ---- IAudioProcessor ----')]
assert 'if(engine_&&(engine_->projectSaveBusy()||engine_->projectNeedsBankCapture()))return kResultFalse;' not in fragment
assert fragment.index('current.bankPendingCapture=engine_&&') < fragment.index('const auto settingsText=')
assert fragment.index('const auto b=engine_?engine_->projectBankSnapshot()') < fragment.index('current.bankPendingCapture=')
assert fragment.count('return kResultFalse;')==1, "Only actual stream I/O should report failed getState"
print("P014 persistent pending-bank host getState/source safety PASS")
