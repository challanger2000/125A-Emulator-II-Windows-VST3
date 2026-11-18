# 125A Emulator II — Windows VST3

**Current: P003 WAV import — original firmware capture verified locally (DEV, not release).**
Hardware core: [Tuth/eii-emu](https://github.com/Tuth/eii-emu), locked to commit `e345bcf00af8a066ebace9168cf0b6c3a40ca164` (GPL-3.0). The pinned source is a **build-time dependency only**; the Windows VST3 itself does not require a separate 86Box/host.

## What already works

- A single Windows x64 **EmulatorII-Custom.vst3** built from the original EII hardware emulator, original ROM+OS at runtime (user supplied), original EIII-style CEM3387 **Custom** filter remains available.
- Settings menu: **125A: WAV automatisch aufnehmen...** accepts WAV PCM8/16/24/32 and IEEE Float32, mono/stereo 8–384 kHz, max 64 MiB and initial recording length **10 seconds**. Decoder rejects corrupt and >0 dBFS floating-point files, rather than normalizing or clipping.
- The plug-in's machine-owner state machine presses and releases the **original** firmware's SAMPLE, FORCE (9), STOP (0) and exit buttons. It waits for real LCD states / SAR reads. The source starts at the **real ADC recording request**, not during the pre-recording live monitor. No direct writes to guest sample RAM or fabricated sample/preset headers.
- USB/disk not required for **user interaction** during recording, but the emulator still needs its original **OS3.1 disk image mounted** at startup because the real firmware loads the SAMPLE overlay from it.
- Recorded voice is immediately auditionable at the original **MIDI note 48**. Other key ranges and sample mapping are not yet configurable via the importer.

**Critical remaining limit:** The recorded voice is currently **volatile RAM only**, and **is not embedded in DAW project state**. Saving a Studio One project does **not** yet save the new WAV/sampled bank. Restarting the instance loses this imported audio unless separately saved through the firmware. Do not treat P003 as a finished sampler or production release.

## Verified evidence

- [GitHub Actions P003 current branch: 44279490227](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/actions/runs/44279490227): Windows x64 Custom VST3 build PASS, existing runtime/audio/input tests PASS, Steinberg validator **47/47 PASS**, new native firmware-contact model, original Z80/SAR/DRAM WAV-vs-silence tests PASS.
- **Private local original-ROM/OS test, 2026-11-18**: original EII firmware OS3.1 boot P01; our P003 state machine handled SAMPLE/FORCE/STOP, firmware displayed **Sample is good**, exited to P01, 84,814 SAR reads; MIDI48 produced 120,000 frames (peak 0.140317, RMS 0.077757) in the original audio engine. An independent upstream analog SAMPLE probe with 440-Hz synthetic WAV yielded actual 440.00-Hz DRAM and 440.00-Hz audible playback, with zero significant phase discontinuities. Full evidence in `docs/P003-PRIVATE-FIRMWARE-ACCEPTANCE.md`.
- **Not yet tested**: automated importer inside real Studio One VST3, persistable host state/save/reopen, multi-import voice mapping, multiple concurrent instances.

## Developer setup

Checkout this repository with recursive submodules. CI reproduces build-only source overlays on the **pinned** upstream snapshot (never changes Tuth GitHub):

```bash
python3 tools/apply-wav-bridge.py --verify
python3 tools/apply-wav-bridge.py
python3 tools/apply-wav-auto.py --verify
python3 tools/apply-wav-auto.py
```

Then run the native/Windows CI tests in `.github/workflows/wav-bridge-qa.yml`. Windows uses `upstream/eii-emu/tools/build-win64-vst3.ps1` and the frozen LLVM-MinGW UCRT toolchain. Original private ROMs/disk are deliberately excluded from GitHub; the user-supplied firmware acceptance kit is built separately via `.github/workflows/firmware-local-qa-kit.yml`. For ongoing engineering, read the complete 125A [START-HERE](https://github.com/challanger2000/125A-Engineering/blob/main/START-HERE.md) and associated guardrails.

**License:** The upstream source is GPL-3.0. Retain its notices and applicable source-distribution obligations for modified, publicly distributed VST3 binaries. Do not commit, upload or include proprietary E-mu ROMs, OS disks, user samples, or private test assets.
