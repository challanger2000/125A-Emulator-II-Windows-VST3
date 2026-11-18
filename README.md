# 125A Emulator II — Windows VST3

**Current: P004 WAV import + original DISK 7 SAVE BANK + project-embedded media — full native original ROM/OS engine replay PASS (DEV, not release).**
Hardware core: [Tuth/eii-emu](https://github.com/Tuth/eii-emu), locked to commit `e345bcf00af8a066ebace9168cf0b6c3a40ca164` (GPL-3.0). The pinned source is a **build-time dependency only**; the Windows VST3 itself does not require a separate 86Box/host.

## What already works

- A single Windows x64 **EmulatorII-Custom.vst3** built from the original EII hardware emulator, original ROM+OS at runtime (user supplied), original EIII-style CEM3387 **Custom** filter remains available.
- Settings menu: **125A: WAV automatisch aufnehmen...** accepts WAV PCM8/16/24/32 and IEEE Float32, mono/stereo 8–384 kHz, max 64 MiB and initial recording length **10 seconds**. Decoder rejects corrupt and >0 dBFS floating-point files, rather than normalizing or clipping.
- The plug-in's machine-owner state machine presses and releases the **original** firmware's SAMPLE, FORCE (9), STOP (0) and exit buttons. It waits for real LCD states / SAR reads. The source starts at the **real ADC recording request**, not during the pre-recording live monitor. No direct writes to guest sample RAM or fabricated sample/preset headers.
- USB/disk not required for **user interaction** during recording, but the emulator still needs its original **OS3.1 disk image mounted** at startup because the real firmware loads the SAMPLE overlay from it.
- Recorded voice is immediately auditionable at the original **MIDI note 48**. Other key ranges and sample mapping are not yet configurable via the importer.

**P004:** After the original firmware accepts a WAV, the machine-owner automatically opens the original DISK menu, performs option 7 SAVE BANK to a **protected in-memory floppy copy**, waits for >=130 actual sector-track writes without errors and returns to Pxx. It publishes the complete 573440-byte image into the binary VST3 IComponent project state; the fresh instance restores the image in memory, without an extracted floppy file. Saving during recording/firmware bank writing is refused rather than silently persisting a half-sample. **Still outstanding:** actual Studio One UI/project save/reopen acceptance, additional mapped multisamples and final safety QA.

## Verified evidence

- [GitHub Actions P003 current branch: 44279490227](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/actions/runs/44279490227): Windows x64 Custom VST3 build PASS, existing runtime/audio/input tests PASS, Steinberg validator **47/47 PASS**, new native firmware-contact model, original Z80/SAR/DRAM WAV-vs-silence tests PASS.
- **Private local original-ROM/OS test, 2026-11-18**: original EII firmware OS3.1 boot P01; our P003 state machine handled SAMPLE/FORCE/STOP, firmware displayed **Sample is good**, exited to P01, 84,814 SAR reads; MIDI48 produced 120,000 frames (peak 0.140317, RMS 0.077757) in the original audio engine. An independent upstream analog SAMPLE probe with 440-Hz synthetic WAV yielded actual 440.00-Hz DRAM and 440.00-Hz audible playback, with zero significant phase discontinuities. Full evidence in `docs/P003-PRIVATE-FIRMWARE-ACCEPTANCE.md`.
- **P004 fully integrated source with original user ROM/OS, native VST3 machine-owner test**: passed automatic WAV -> firmware SAMPLE/FORCE/STOP -> firmware DISK 7 SAVE BANK (protected copy) -> 577066-byte binary project state -> NEW independent engine booting embedded original image -> audible 440.374 Hz MIDI48 (peak 0.131072, RMS 0.0857712, 143872 frames). Full acceptance details in docs/P004-PRIVATE-FIRMWARE-PROJECT-ACCEPTANCE.md.
- **Real Windows VST3 host IComponent state QA**: exact binary set/get-state roundtrip, corrupt-state rejection, two different isolated bank instances and original state compatibility PASS; 47/47 Steinberg Validator in GitHub Actions run 44284301455 (commit 3d87cbd9...). The source code at P004 head 775691b... also passed native + Windows CI run 44284743913.
- **Not yet tested:** real Studio One GUI/host opening, bank save/reopen in Studio One, arbitrary root-note/multi-import key mapping; user-host acceptance remains a separate final gate.

## Developer setup

Checkout this repository with recursive submodules. CI reproduces build-only source overlays on the **pinned** upstream snapshot (never changes Tuth GitHub):

```bash
python3 tools/apply-wav-bridge.py --verify
python3 tools/apply-wav-bridge.py
python3 tools/apply-wav-auto.py --verify
python3 tools/apply-wav-auto.py
python3 tools/apply-project-state.py --verify
python3 tools/apply-project-state.py
```

Then run the native/Windows CI tests in `.github/workflows/wav-bridge-qa.yml`. Windows uses `upstream/eii-emu/tools/build-win64-vst3.ps1` and the frozen LLVM-MinGW UCRT toolchain. Original private ROMs/disk are deliberately excluded from GitHub; the user-supplied firmware acceptance kit is built separately via `.github/workflows/firmware-local-qa-kit.yml`. For ongoing engineering, read the complete 125A [START-HERE](https://github.com/challanger2000/125A-Engineering/blob/main/START-HERE.md) and associated guardrails.

**License:** The upstream source is GPL-3.0. Retain its notices and applicable source-distribution obligations for modified, publicly distributed VST3 binaries. Do not commit, upload or include proprietary E-mu ROMs, OS disks, user samples, or private test assets.

## P005 research — OS-free, portable user-bank DAW state

The experimental P005 branch makes project-state serialization omit the original E-mu system-area bytes: the fixed-size 573,440-byte image envelope now contains zeroes for the first 78,848 bytes and preserves the remaining 494,592 bank bytes exactly. On boot, the user's own OS3.1 disk is required at its configured osImage or floppy path; the OS region is reconstructed only inside the machine. Earlier P004 full-disk project states are still readable but sanitize when next saved. Missing original OS is an explicit boot error. Windows host, original-ROM playback and Studio One acceptance remain separate gates; P005 is not a release.

## P006 — Same private ROM/OS layout as our E-MU Emulator III

The single self-contained Windows plugin installs under `C:\Program Files\Common Files\VST3\Eigene\E-MU Emulator II.vst3`. EIII-style `Contents\Resources\ROM` contains the original owner-supplied EII ROM files `main.bin`, `scanner.bin`, `ic135.bin`, `ic137.bin`, plus optional `main21dm.bin` (1 MiB floppy) and `main23.bin` (HD). `Contents\Resources\OS` holds exactly one original EII OS 3.1 `.emuiifd` or `.hfe` image. On loading a new plugin instance, or a project copied from a former installation, the plugin locates these folders relative to its own Windows module (no hard-coded C: path). Valid user-selected external ROM/OS paths stay valid; only empty or stale paths fall back. OS media is never written directly; internal writable working copy preserves it.

**Owner-only packaging:** use `tools/Package-Private-Emulator-II.ps1` to create the bundle from your own ROM/OS and the tested Custom VST3. ROMs/OS never enter this repo or public GitHub Actions builds. A fully packaged private bundle need only be copied into the VST3 folder; its runtime requires no separate tool/host program. P006 is a development branch until native/Windows and real original ROM tests pass.
