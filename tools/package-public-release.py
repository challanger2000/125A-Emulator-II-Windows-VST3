#!/usr/bin/env python3
"""P048: pair a firmware-free Windows VST3 with its exact corresponding source.

Run ONLY after all build-time patches, Windows COM tests and validator gates.
Source ZIP includes the actual patched upstream working tree, all 125A tracked
source/patch/test/build files, original notices, and per-file SHA-256 manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UP = ROOT / "upstream" / "eii-emu"
UPSTREAM_PIN = "e345bcf00af8a066ebace9168cf0b6c3a40ca164"
BIN_NAME = "125A-E-MU-Emulator-II-P048-PUBLIC-VST3-NO-ROM.zip"
SRC_NAME = "125A-E-MU-Emulator-II-P048-CORRESPONDING-SOURCE.zip"
SOURCE_PREFIX = "125A-E-MU-Emulator-II-P048-CORRESPONDING-SOURCE"
BUNDLE = "E-MU Emulator II.vst3"
BLOCKED_MEDIA_EXT = {
    ".bin", ".rom", ".raw", ".hfe", ".emuiifd", ".eii", ".img",
    ".sf2", ".sbk", ".iso", ".vhd", ".vhdx", ".wav", ".aif",
    ".aiff", ".flac", ".mp3", ".ogg",
}
BLOCKED_BUILD_DIRS = {
    ".git", "build", ".vs", "__pycache__", ".pytest_cache", ".mypy_cache",
    "dist", "out", "obj", "cmakefiles",
}
BLOCKED_BUILD_EXT = {".exe", ".dll", ".o", ".obj", ".a", ".lib", ".pdb", ".zip", ".7z"}
EXCLUDED_GENERATED = {".git", ".gitignore"}  # preserve .gitignore from root tracked files


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def safe_source_file(path: Path, base: Path) -> bool:
    """Reject proprietary media and non-source generated binary artifacts."""
    relative = path.relative_to(base)
    if any(part.lower() in BLOCKED_BUILD_DIRS for part in relative.parts[:-1]):
        return False
    if path.suffix.lower() in BLOCKED_MEDIA_EXT:
        raise RuntimeError(f"Refusing proprietary/possibly copyrighted audio media in source ZIP: {path}")
    if path.suffix.lower() in BLOCKED_BUILD_EXT or path.name == ".git":
        return False
    if path.is_symlink():
        raise RuntimeError(f"Refusing symlink for public source archive: {path}")
    return path.is_file()


def source_files() -> list[tuple[Path, str]]:
    if git("-C", str(UP), "rev-parse", "HEAD") != UPSTREAM_PIN:
        raise RuntimeError("Pinned upstream SHA changed; halt public package")
    pairs = []
    # Only versioned 125A files: never package untracked private user data.
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    for rel in (x.decode("utf-8") for x in tracked.split(b"\0") if x):
        if rel == "upstream/eii-emu":
            continue  # gitlink, not actual source file
        p = ROOT / rel
        if p.is_file() and safe_source_file(p, ROOT):
            pairs.append((p, rel.replace("\\", "/")))
    # Include the *working* patched upstream source, including files generated
    # by 125A overlays. Do NOT just zip a pristine pinned Git submodule.
    for p in UP.rglob("*"):
        if safe_source_file(p, UP):
            rel = p.relative_to(UP).as_posix()
            pairs.append((p, "upstream/eii-emu/" + rel))
    paths = [rel for _, rel in pairs]
    if len(paths) != len(set(paths)):
        raise RuntimeError("Duplicate archive source paths")
    critical = {
        "README.md", "LICENSE", "CREDITS.md", "CHANGELOG.md",
        "RELEASE-SOURCE-TRACEABILITY.md", "INSTALL-PUBLIC.md",
        "tools/apply-p047-eii-display-name.py",
        "tools/apply-p048-eii-credits-menu.py",
        ".github/workflows/wav-bridge-qa.yml",
        "upstream/eii-emu/src/vst3/eii_vst3.cpp",
        "upstream/eii-emu/src/vst3/plugin_editor.h",
        "upstream/eii-emu/LICENSE",
        "upstream/eii-emu/CONTRIBUTORS.md",
    }
    missing = sorted(critical - set(paths))
    if missing:
        raise RuntimeError(f"Missing GPL corresponding-source files: {missing}")
    return sorted(pairs, key=lambda x: x[1])


def binary_archive(binary: Path, output: Path) -> None:
    if not binary.is_file() or binary.stat().st_size < 100000:
        raise RuntimeError(f"Missing or implausibly small tested Windows VST3: {binary}")
    name = f"{BUNDLE}/Contents/x86_64-win/{BUNDLE}"
    resources = f"{BUNDLE}/Contents/Resources"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=8) as z:
        z.write(binary, name)
        for path, archive in [
            ("CREDITS.md", f"{resources}/PROJECT-CREDITS.md"),
            ("LICENSE", f"{resources}/LICENSE-GPL-3.0.txt"),
            ("upstream/eii-emu/CONTRIBUTORS.md", f"{resources}/UPSTREAM-CONTRIBUTORS.md"),
            ("INSTALL-PUBLIC.md", f"{resources}/INSTALL-PUBLIC.md"),
            ("CHANGELOG.md", f"{resources}/CHANGELOG.md"),
            ("RELEASE-SOURCE-TRACEABILITY.md", f"{resources}/SOURCE-TRACEABILITY.md"),
            ("RELEASE-NOTES-P048.md", "RELEASE-NOTES-P048.md"),
            ("INSTALL-PUBLIC.md", "INSTALL-PUBLIC.md"),
        ]:
            z.write(ROOT / path, archive)
        for empty in (f"{resources}/ROM/", f"{resources}/OS/"):
            z.writestr(empty, b"")
    with zipfile.ZipFile(output) as z:
        names = z.namelist()
        if z.testzip() is not None or name not in names:
            raise RuntimeError("Public VST3 ZIP integrity check failed")
        for n in names:
            if Path(n).suffix.lower() in BLOCKED_MEDIA_EXT:
                raise RuntimeError(f"Public release contaminated by ROM/media: {n}")
        if any("EmulatorII-Custom.vst3" in n for n in names):
            raise RuntimeError("Legacy-named plugin leaked into public package")


def source_archive(output: Path, inputs: list[tuple[Path, str]]) -> None:
    manifest = {
        "release": "P048 public ROM-free release candidate",
        "modification_date": "2026-11-19",
        "original_creator": "Tuth",
        "original_repo": "https://github.com/Tuth/eii-emu",
        "upstream_git_commit": UPSTREAM_PIN,
        "125a_repo": "https://github.com/challanger2000/125A-Emulator-II-Windows-VST3",
        "125a_build_commit": git("rev-parse", "HEAD"),
        "source_files": [],
    }
    # Exact pinned-upstream to 125A modifications for traceable distribution.
    upstream_diff = subprocess.check_output(
        ["git", "-C", str(UP), "diff", "--no-ext-diff", "--binary", "HEAD", "--"],
        cwd=ROOT,
    )
    if not upstream_diff:
        raise RuntimeError("No upstream diff: 125A patch application may have been skipped")
    tracked_raw = subprocess.check_output(
        ["git", "-C", str(UP), "ls-files", "-z"], cwd=ROOT
    )
    tracked_upstream = {p.decode("utf-8") for p in tracked_raw.split(b"\0") if p}
    additions = sorted(
        rel[len("upstream/eii-emu/"):]
        for _, rel in inputs
        if rel.startswith("upstream/eii-emu/")
        and rel[len("upstream/eii-emu/"):] not in tracked_upstream
    )
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=8) as z:
        z.writestr(f"{SOURCE_PREFIX}/UPSTREAM-125A-CHANGES.patch", upstream_diff)
        z.writestr(
            f"{SOURCE_PREFIX}/UPSTREAM-125A-ADDED-SOURCE-FILES.txt",
            "\n".join(additions) + "\n",
        )
        for path, relative in inputs:
            data = path.read_bytes()
            manifest["source_files"].append({"path": relative, "sha256": sha256(data), "size": len(data)})
            z.writestr(f"{SOURCE_PREFIX}/{relative}", data)
        z.writestr(
            f"{SOURCE_PREFIX}/SOURCE-SHA256-MANIFEST.json",
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        )
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None:
            raise RuntimeError("Corresponding source ZIP integrity failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = source_files()
    args.output.mkdir(parents=True, exist_ok=True)
    binary_zip = args.output / BIN_NAME
    source_zip = args.output / SRC_NAME
    binary_archive(args.binary, binary_zip)
    source_archive(source_zip, inputs)
    with (args.output / "SHA256SUMS.txt").open("w", encoding="utf-8", newline="\n") as f:
        for archive in (binary_zip, source_zip):
            f.write(f"{sha256(archive.read_bytes())}  {archive.name}\n")
    (args.output / "RELEASE-NOTES-P048.md").write_bytes(
        (ROOT / "RELEASE-NOTES-P048.md").read_bytes()
    )
    print(f"P048 PUBLIC ROM-FREE VST3 + corresponding source PASS ({len(inputs)} files)")
    print(f"Binary: {binary_zip} ({binary_zip.stat().st_size} bytes)")
    print(f"Source: {source_zip} ({source_zip.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
