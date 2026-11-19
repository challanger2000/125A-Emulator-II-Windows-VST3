#!/usr/bin/env python3
"""P048: visible original developer acknowledgement in the EII settings menu.

Source-pinned, additive, GUI-only. Do not modify DSP, firmware, IDs, saved
state, VST3 vendor or the original upstream repository.
"""
import argparse
import subprocess
from pathlib import Path

PIN = "e345bcf00af8a066ebace9168cf0b6c3a40ca164"
ROOT = Path(__file__).resolve().parents[1]
UP = ROOT / "upstream/eii-emu"
SOURCE = UP / "src/vst3/plugin_editor.h"
OLD_MENU = '        AppendMenuW(menu,MF_STRING,60,L"Status...");'
NEW_MENU = OLD_MENU + '\n        AppendMenuW(menu,MF_STRING,9610,L"About / credits...");'
OLD_CASE = "        case 60:showStatus();break;"
NEW_CASE = r'''        case 60:showStatus();break;
        case 9610:ask(
            L"Original emulator software: Tuth (github.com/Tuth/eii-emu)\n"
            L"125A adaptation: Windows VST3 integration, packaging and QA.\n\n"
            L"Upstream contributors: ChatGPT / Codex and Claude Code.\n"
            L"Licence: GPL-3.0; see PROJECT-CREDITS.md in VST3 Resources.\n"
            L"Independent project; not affiliated with E-mu Systems.",
            L"About E-MU Emulator II",MB_ICONINFORMATION);break;'''

def patch(source):
    if source.count(OLD_MENU) != 1 or source.count(OLD_CASE) != 1:
        raise RuntimeError("P048 settings-menu source anchors missing or ambiguous")
    if "case 9610:" in source or "MF_STRING,9610," in source:
        raise RuntimeError("P048 settings-menu command ID 9610 already occupied")
    return source.replace(OLD_MENU, NEW_MENU).replace(OLD_CASE, NEW_CASE)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    revision = subprocess.check_output(
        ["git", "-C", str(UP), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != PIN:
        raise RuntimeError("P048 pinned upstream changed; no blind GUI patch")
    original = SOURCE.read_text(encoding="utf-8")
    result = patch(original)
    if not args.verify:
        SOURCE.write_text(result, encoding="utf-8", newline="\n")
    print("P048 original developer / About menu source: PASS")

if __name__ == "__main__":
    main()
