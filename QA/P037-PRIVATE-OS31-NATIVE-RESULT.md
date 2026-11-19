# P037 — owner-private original Emulator II OS 3.1 firmware capture and playback

**Executed 2026-11-19. Scope: native Linux build of the *actual patched PluginEngine* and genuine original E-mu firmware. ORIGINAL-FIRMWARE NATIVE CAPTURE + PLAYBACK: PASS. FULL P037 WINDOWS-VST3 ACCEPTANCE: STILL OPEN.**

## Source and reproducibility

- 125A source base: `main@4d5ba15c296da3502bcf51965d82955204b7e6c7`, upstream `Tuth/eii-emu@e345bcf00af8a066ebace9168cf0b6c3a40ca164`; all production P003–P036 overlays applied in the prescribed workflow order.
- Owner-private original ROMs (SHA-256, no ROM bytes): `main.bin=5082f8f815e873803929dc570ab8e4083646c6d79368b17b931a0328f06de226`, `scanner.bin=478cf8e0956aadf27c51c58a26f24926d4e6f2658a991877dd3d0f3aa98a6227`, `ic135.bin=725cd24f9e98f201efcd7cfac4e07f38713495fa960b3f37664e76bd079927f5`, `ic137.bin=874b9ec1214977fb95fa77b337b7cb254d243c9a143547af3b440cd2d9ff9116`.
- OS 3.1 floppy SHA-256 `ef00043accab33496fce1975a89d9d05940a3a4d515ec382f13b4bed0019d83e`. Initial read-only Choir floppy SHA-256 `9ab17bb874290ed73651a8978337b0d6fa1adeeacc5c38800871b7949ef83a28`.
- Local test source: `tests/p037_private_firmware_recording_local.cpp`; SHA-256 `f455aa045bc0c7b436359717208d3bcad5b1c9ab733e9193ef009ebf02b4333d`. Built and executed with clang++ C++23, host x86_64 Linux; additional g++ C++23 `-O2 -Wall -Wextra -Werror -Wno-error=misleading-indentation` compile PASS.
- Native executable SHA-256 `3bf7bac696fbcbc3caeb8f392ebdb9a640ca7a4cf6794198e51e4f360376b464`.
- No private ROM, OS image, Choir floppy, private bank, or recorded audio was committed, uploaded to GitHub Actions or bundled into public artifacts.

## Actual original-firmware positive sequence

1. Boot genuine firmware with read-only original Choir floppy to genuine `P01 EII Choir` at original machine tick `177300000`; owner boot gate ready, no emulated bus fault. Confirm MIDI-triggered Choir baseline `166085` nonzero samples, output peak `0.764619`, energy `6034.47`.
2. Generate a *new* 1-second mono 440 Hz, 0.25 peak signal at 48 kHz. Feed through the production WAV-to-analog input source, not a preloaded bank, injected RAM bytes or synthetic Z80 program. Invoke `autoImportWav`, which actuates real guest SAMPLE / FORCE / STOP scanner contacts.
3. Observe actual original firmware LCD transitions `Sample Armed` -> `Sample is good` -> `Disk [1-8]` -> `This Will Take A While` -> `P01 EII Choir`; original firmware performs DISK 7 SAVE BANK to a writable protected floppy copy and registers saved bank state.
4. Observe `sampleReads=29245`, `sampleUnknownReads=0`, source requested by genuine firmware ADC, `wavSuccess=1`, `wavReport=1`, no reported host underruns. Original firmware reaches Pxx after bank save and automatically restores the read-only Choir floppy.
5. Audition the *newly recorded* voice on host MIDI note C3 (note 60 mapped to original EII MIDI 48) through the actual native PluginEngine PCM output: `56861` nonzero frames, peak `0.0836425`, energy `274.617`. Captured PCM is 48 kHz mono PCM16. Independent spectral verification: peak at **440.002 Hz** over 0.15–0.90 s windows; representative RMS 0.05355. Audio SHA-256 `a6e5125131caed25af5ca7e5fe3c47f4efd2c6597956ff9e911614f599e8c5ba`.

**Result: PASS for actual original-ROM/OS SAMPLE→SAR→DRAM→DISK7→audible newly recorded PCM via native patched PluginEngine.** This is substantially stronger than P036's synthetic Z80 fixture and does not depend on the original Choir audio as the post-recording oracle: dominant frequency matches the newly supplied 440 Hz sample.

## Adversarial real-firmware memory-limit control

A preceding 3-second 440 Hz take with the Choir bank already occupying RAM reached `Sample is good` too early at `sampleReads=70208` (insufficient for 3 seconds at approximately 27.8 kBytes/s). The P037 guard **correctly rejected** the truncated take, used original firmware cancellation and returned to `P01 EII Choir` with `wavSuccess=0` and no false success; uncommitted sample RAM was not claimed preserved. This is a legitimate native original-firmware negative result, not a successful full-length capture.

## Explicitly not established by this run

- This is **Linux native PluginEngine**, not the actual **Windows VST3 COM `ProcessData`** interface and not Studio One. P036 separately tested DAW HostSampleInput using synthetic Z80 firmware; the two proofs cannot be combined to claim a Windows original-ROM recording PASS.
- The new waveform was fed through the P003 production `eii::wav::Source` (WAV import), not a live DAW input audio bus. Live host-input recording with original OS3.1 remains open.
- Although original DISK7 bank save completed, a fresh Windows VST3 `IBStream` song reopen and the same recorded sample's playback in a **new Windows component** was not performed here.
- No measured physical hardware analog calibration, SSM2045 filter fidelity, realtime audio-host/ASIO soak or final manual Studio One acceptance is implied.
- Original private files remain owner-local. Never run this test in public CI with real firmware/media.

**Project remains DEV.** Native P037 original-firmware recording+playback sub-gate: **PASS**; entire P037 Windows VST3 contract: **NOT YET PASS**.
