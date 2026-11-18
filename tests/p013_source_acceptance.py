#!/usr/bin/env python3
"""P013 static safety acceptance (real original firmware/Studio One separate)."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"upstream/eii-emu/src/vst3"
e=(root/"plugin_engine.h").read_text(encoding="utf-8")
v=(root/"plugin_editor.h").read_text(encoding="utf-8")
c=(root/"eii_vst3.cpp").read_text(encoding="utf-8")
def need(s,v):
    if v not in s:raise AssertionError("Missing P013 gate: "+v)
for v0 in (
    "void saveCurrentBankInProject()",
    "bool projectNeedsBankCapture()const noexcept",
    "std::atomic<bool> bankNeedsSnapshot_{false};",
    "const bool savedLiveBank=manualBankCommit_;",
    "bankNeedsSnapshot_.store(false,std::memory_order_release);",
    "if(!machine_||!producing()||!presetDisplayed())",
    "host::FloppyImageBacking os(settings_.osImage,false);",
    'std::filesystem::path("125A-LiveBank-Temporary-OS31.emuiifd")',
    "installFloppy(*machine_,temporary);",
    "manualBankCommit_=true;",
    "bankAction(first.action);",
    "projectBusy_.store(true,std::memory_order_release);",
    "restoreWavOriginalFloppy();",
    "if(bootSelectedBank){",
):
    need(e,v0)
m=e[e.index("std::string mountFloppyNow("):e.index("static std::filesystem::path recoveryFolder()")]
b=e[e.index("void bootNow(bool discard,bool fromState)"):e.index("    // ---- input ----")]
assert "if(selectedBank)commitSelectedBank(selectedBank)" not in m
assert "if(bootSelectedBank)commitSelectedBank(bootSelectedBank)" not in b
assert "bankNeedsSnapshot_.store(true,std::memory_order_release)" in m
assert "bankNeedsSnapshot_.store(true,std::memory_order_release)" in b
w=e[e.index("void saveCurrentBankInProject()"):e.index("void cancelAutoWav()")]
assert w.index("host::FloppyImageBacking os") < w.index("installFloppy(*machine_,temporary)")
assert w.index("installFloppy(*machine_,temporary)") < w.index("manualBankCommit_=true;")
assert "saveCopy" not in w and "write(" not in w
need(c,"engine_->projectSaveBusy()||engine_->projectNeedsBankCapture()")
need(v,'Aktuelle RAM-Bank mit original DISK 7 im Song sichern')
need(v,'case 25:e.saveCurrentBankInProject();break;')
need(v,'LIVE RAM NOT SAVED')
print("P013 fail-closed selected-bank/boot/host save original firmware state guards: PASS")
