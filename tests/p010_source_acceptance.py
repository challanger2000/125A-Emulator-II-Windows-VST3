#!/usr/bin/env python3
"""P010 bank-file codec anchors and P013 safer delayed-commit compatibility."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"upstream/eii-emu/src/vst3/plugin_engine.h"
s=p.read_text(encoding="utf-8")
def need(needle):
    if needle not in s:raise AssertionError(f"Missing project bank source policy: {needle!r}")
for needle in ('#include "125a_selected_bank.h"',
               'backing&&backing->bankImport',
               'portable::cloneSelectedBank(backing->serialized())',
               'const auto selectedBank=selectedBankFromFloppy(fresh);',
               'const auto bootSelectedBank=!fromState?selectedBankFromFloppy(freshFloppy):',
               'std::lock_guard l(projectMediaMutex_);projectMedia_=bank;'):
    need(needle)
m=s[s.index('std::string mountFloppyNow('):s.index('static std::filesystem::path recoveryFolder()')]
assert m.index('const auto selectedBank=') < m.index('installFloppy(*machine_,fresh)')
assert 'if(!path.empty()&&!sameImage(path,settings_.osImage))' in m
assert m.count('projectMedia_.reset()')==1
b=s[s.index('void bootNow(bool discard,bool fromState)'):s.index('    // ---- input ----')]
assert b.index('const auto bootSelectedBank=') < b.index('quiesce();')
if 'void saveCurrentBankInProject()' in s:
    # P013: file selection is only a candidate, not proof the bank entered RAM.
    assert 'if(selectedBank)commitSelectedBank(selectedBank);' not in m
    assert 'if(bootSelectedBank)commitSelectedBank(bootSelectedBank);' not in b
    need('bankNeedsSnapshot_.store(true,std::memory_order_release);')
    need('void saveCurrentBankInProject()')
    print("P010 codec with P013 original-firmware-only publication: PASS")
else:
    assert 'if(selectedBank)commitSelectedBank(selectedBank);' in m
    assert 'if(bootSelectedBank)commitSelectedBank(bootSelectedBank);' in b
    print("P010 selected file-bank project snapshot source acceptance: PASS (firmware gate pending)")
