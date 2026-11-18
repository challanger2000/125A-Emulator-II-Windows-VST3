#!/usr/bin/env python3
"""P010 integration invariants, separate from Windows DAW acceptance."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"upstream/eii-emu/src/vst3/plugin_engine.h"
s=p.read_text(encoding="utf-8")
def need(needle):
    if needle not in s:raise AssertionError(f"P010 source policy missing {needle!r}")
for needle in ('#include "125a_selected_bank.h"',
               'backing&&backing->bankImport',
               'portable::cloneSelectedBank(backing->serialized())',
               'const auto selectedBank=selectedBankFromFloppy(fresh);',
               'if(selectedBank)commitSelectedBank(selectedBank);',
               'const auto bootSelectedBank=!fromState?selectedBankFromFloppy(freshFloppy):',
               'if(bootSelectedBank)commitSelectedBank(bootSelectedBank);',
               'std::lock_guard l(projectMediaMutex_);projectMedia_=bank;'):
    need(needle)
m=s[s.index('std::string mountFloppyNow('):s.index('static std::filesystem::path recoveryFolder()')]
assert m.index('const auto selectedBank=') < m.index('installFloppy(*machine_,fresh)')
assert m.index('if(selectedBank)commitSelectedBank(selectedBank)') > m.index('floppyBacking_=std::move(fresh)')
assert 'if(!path.empty()&&!sameImage(path,settings_.osImage))' in m
assert m.count('projectMedia_.reset()')==1
b=s[s.index('void bootNow(bool discard,bool fromState)'):s.index('    // ---- input ----')]
assert b.index('const auto bootSelectedBank=') < b.index('quiesce();')
assert b.index('if(bootSelectedBank)commitSelectedBank(bootSelectedBank)')>b.index('machine_=std::move(fresh)')
print("P010 EII file-bank project recall source acceptance: PASS (ROM/DAW acceptance pending)")
