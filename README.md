# 125A Emulator II — Windows VST3 (development)

**Status: WAV input bridge P001; NOT a one-click playable WAV importer.**

Upstream hardware emulation: [Tuth/eii-emu](https://github.com/Tuth/eii-emu) at pinned commit `e345bcf00af8a066ebace9168cf0b6c3a40ca164` (GPL-3.0). This repository uses a source submodule for reproducible Windows VST3 builds. The final VST3 must be self-contained at runtime; a Git submodule is a build-time source dependency only.

## P001

The C++23 decoder accepts bounded RIFF WAV PCM8/16/24/32 or IEEE Float32, mono/stereo, 8–384 kHz. Float above digital full scale and malformed/corrupted files are **rejected** rather than normalized or silently clipped. Stereo is explicitly averaged to the original single-channel sample input. On first actual emulated SAMPLE-converter input request the WAV begins at machine time. The original SAR, antialias filter, ADC and firmware are not bypassed.

The Windows editor gets two non-realtime menu commands, **125A: WAV als SAMPLE-Eingang vorbereiten** and **deaktivieren**. User still needs original firmware SAMPLE and bank-save operation; automatically constructed playable presets and project-portable embedded sample-state are **NOT IMPLEMENTED**. Until firmware-triggered recording and bank persistence are measured this is a research candidate, not a replacement for virtual media.

## Developer preflight

- Checkout recursive submodules; upstream version is pinned.
- `python3 tools/apply-wav-bridge.py --verify` checks pinned upstream and patch anchors without changing files.
- `python3 tools/apply-wav-bridge.py` inserts the GUI bridge into the local upstream worktree and copies the header. No upstream GitHub repository is changed.
- `g++ -std=c++23 -O2 -Wall -Wextra -Werror -pedantic -I src -I upstream/eii-emu/src tests/wav_input_tests.cpp -o wav_input_tests && ./wav_input_tests`
- Windows build after local overlay: follow pinned upstream `tools/build-win64-vst3.ps1`; **Windows/Steinberg/Studio One results have not been established**.

## Engineering and legal boundaries

Read [125A-Engineering/START-HERE.md](https://github.com/challanger2000/125A-Engineering/blob/main/START-HERE.md), its complete mandatory references and [docs/P001-WAV-BRIDGE.md](docs/P001-WAV-BRIDGE.md) before editing. Use development branches, never direct changes to main. Reference 125A Vintage Sampler III firmware WAV-import *workflow concepts*, not copied proprietary/unverified code. Upstream GPL-3.0 terms and notices remain applicable, including to a distributed derivative binary.

**No original E-mu ROM, OS/sample disks, copyrighted banks or private user media in this repository or CI artifacts.**
