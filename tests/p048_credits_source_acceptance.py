#!/usr/bin/env python3
"""P048 source-only guard; CI must also compile/test the real Windows VST3."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "p048", ROOT / "tools/apply-p048-eii-credits-menu.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# CI has applied the P048 overlay before source tests. Reconstruct its
# input exactly, then check that replay produces the installed source.
installed = module.SOURCE.read_text(encoding="utf-8")
assert installed.count(module.NEW_MENU) == 1, "P048 menu not installed once"
assert installed.count(module.NEW_CASE) == 1, "P048 case not installed once"
src = installed.replace(module.NEW_MENU, module.OLD_MENU).replace(
    module.NEW_CASE, module.OLD_CASE
)
patched = module.patch(src)
assert patched == installed, "P048 source replay differs from installed source"
pack = (ROOT / "tools/Package-Private-Emulator-II.ps1").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
credits = (ROOT / "CREDITS.md").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/wav-bridge-qa.yml").read_text(encoding="utf-8")
checks = {
    "source patch only adds About/credits command": (
        patched.count('L"About / credits..."') == 1
        and patched.count('case 9610:ask(') == 1
        and src.replace(module.OLD_MENU, "").replace(module.OLD_CASE, "")
        == patched.replace(module.NEW_MENU, "").replace(module.NEW_CASE, "")
    ),
    "Tuth credited in actual plugin GUI": (
        'Tuth (github.com/Tuth/eii-emu)' in patched
        and "PROJECT-CREDITS.md" in patched
    ),
    "README prominently credits Tuth": (
        readme.startswith("# 125A E-MU Emulator II")
        and "Tuth / eii-emu" in readme[:450]
    ),
    "credits include original and third-party authors": (
        "Tuth" in credits and "Claude Code" in credits
        and "Codex" in credits and "Andre Weissflog" in credits
        and "GPL-3.0" in credits
    ),
    "owner bundle includes licensing and credits": (
        "PROJECT-CREDITS.md" in pack
        and "LICENSE-GPL-3.0.txt" in pack
        and "$target=Join-Path $Destination 'E-MU Emulator II.vst3'" in pack
    ),
    "Windows CI invokes actual GUI patch before compilation": (
        "python tools/apply-p048-eii-credits-menu.py --verify" in workflow
        and "python tools/apply-p048-eii-credits-menu.py\n" in workflow
    ),
}
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + " P048 " + name)
assert all(checks.values()), "P048 attribution/GUI/package source checks failed"
for broken in [
    patched,
    src.replace(module.OLD_MENU, "", 1),
    src.replace(module.OLD_CASE, "", 1),
    src.replace(module.OLD_CASE, module.OLD_CASE + "\n        case 9610:break;", 1),
]:
    try:
        module.patch(broken)
    except RuntimeError:
        pass
    else:
        raise AssertionError("P048 duplicate/missing-anchor mutant escaped")
print("P048 source checks 6/6 and negative mutants 4/4 PASS")
