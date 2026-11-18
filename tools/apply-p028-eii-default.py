#!/usr/bin/env python3
"""P028: change only the new Custom VST3 fallback default to original EII SSM2045.
Existing host project state, explicit saved defaults and CEM model remain intact.
Patch the exact pinned upstream *checkout*, never the Tuth repository.
"""
import argparse
import subprocess
from pathlib import Path

PIN = "e345bcf00af8a066ebace9168cf0b6c3a40ca164"
ROOT = Path(__file__).resolve().parents[1]
UP = ROOT / "upstream" / "eii-emu"
TARGET = UP / "src" / "vst3" / "eii_vst3.cpp"
OLD = "s.audioMode=eii::analog::RuntimeAudioMode::EiiiCustom;"
NEW = "s.audioMode=eii::analog::RuntimeAudioMode::Ssm2Chip;"

def patch(text: str) -> str:
    if text.count(OLD) != 1:
        raise RuntimeError(f"P028 expected exactly one original Custom default; found {text.count(OLD)}")
    return text.replace(OLD, NEW, 1)

def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--verify", action="store_true")
    args = cli.parse_args()
    sha = subprocess.check_output(["git", "-C", str(UP), "rev-parse", "HEAD"], text=True).strip()
    if sha != PIN:
        raise RuntimeError(f"P028 upstream source mismatch: {sha}, wanted {PIN}")
    original = TARGET.read_text(encoding="utf-8")
    updated = patch(original)
    if args.verify:
        print("P028 pinned upstream and original EIII new-instance default: PASS")
    else:
        TARGET.write_text(updated, encoding="utf-8", newline="\n")
        print("P028 default now original EII SSM2045 model 2 96k; EIII remains selectable")

if __name__ == "__main__":
    main()
