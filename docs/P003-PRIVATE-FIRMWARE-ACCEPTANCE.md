# P003 — private original firmware acceptance record

Date: **2026-11-18**. Source branch: `develop/wav-import-v0.1.0` at `eaf9f397b2e1ffdd018b7179c95bdfde8a1380f1`. EII core pinned to `Tuth/eii-emu@e345bcf00af8a066ebace9168cf0b6c3a40ca164`.

This note captures **two different local native original-firmware runs**; do not conflate them with an actual Studio One / plugin process test. Tests were run in the private container with user-supplied original ROMs and OS3.1 disk extracted **locally** from conversation-provided archives. **No ROM, floppy, private user audio, source file path, or proprietary binary has been uploaded to GitHub or its CI.**

## Run A — original firmware analog pathway (upstream probe)

Tool: pinned upstream `tools/sample_wav_probe.cpp`, compiled native C++20 / O2 with original machine/analog models and original OS3.1. Input: synthetic **440 Hz 48 kHz mono WAV** at 0.4 digital peak, full-scale mapping 1 V. Production controller, legacy voice, real machine CPU/firmware only.

- Original firmware boot: `P01 NULL PRESET`.
- Recorded using original **SAMPLE**, **FORCE**, **STOP**, original response: `Sample is good`.
- SAR: **88,416** sample reads, **0** unknown reads; **27,778 sample reads/s** during steady recording.
- Sample RAM: **85,908** bytes changed; sampled region approximately **84,978 bytes**, equivalent to 3.059 seconds.
- Independent offline DPCM decoder: **440.00 Hz**, amplitude **1.2802**, THD+N **−47.0 dB**; 0 sample-phase discontinuities above 0.25 rad.
- Playback with original firmware and MIDI **note 48**: **120,000 frames**, **440.00 Hz**, peak **0.1313**, 0 10-ms-block phase discontinuities above 0.25 rad.
- Process exit: **0 (PASS)**.

The input monitor spectrum was not accepted as identical to original playback; sample and final MIDI playback are the positive oracle.

## Run B — P003 automated original-panel sequence (new 125A controller)

Tool: local source built from current P003 `src/125a_wav_input.h`, `src/125a_firmware_capture.h` and the pinned core. Same private user firmware + OS and synthetic **440 Hz, 3-second WAV**. This directly exercises the **same P003 controller and gate logic** integrated into VST3, with a native `Machine` in place of a DAW. No guessed RAM writes or direct preset fabrication.

Observed emulated seconds and state:

| Time (s) | Original LCD | Automated action |
| --- | --- | --- |
| 50.000 | P01 NULL PRESET | original OS booted |
| 50.100 | P01 NULL PRESET | release SAMPLE after original press |
| 51.660 | VOICE V01 +0??? | arm WAV on first real SAR read; press FORCE (9) |
| 51.760 | Sample Armed | release FORCE; **2,022** reads, WAV running |
| 51.765 | Sample Armed | real firmware recording |
| 54.740 | Sample Armed | press STOP (0) after WAV/tail |
| 54.840 | Sample is good | release STOP; **84,814** SAR reads |
| 54.845 | Sample is good | press SAMPLE to leave |
| 54.945 | Sample is good / Just a Moment... | release SAMPLE |
| 55.205 | P01 NULL PRESET | complete; firmware accepted recorded voice |

Sample input began at **CPU tick 206,748,909**, after the real CPU requested sample bytes. After the firmware completed, independent MIDI note 48 audition through the pinned original EII engine produced **120,000 audio frames**, **peak 0.140317**, **RMS 0.077757**. Process result: **P003 PASS actual OS3.1 sample accept + original RAM + MIDI 48 sound**.

This is the first private original-ROM acceptance of the new controller logic. It **does not** certify that the VST3 itself has completed its menu/UI lifecycle under Studio One, nor that the recorded sample survives project save/reopen.

## Public CI regression

- [Source-only kit build](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/actions/runs/44279490533): PASS. Created a public-source bundle with generated 440-Hz synthetic WAV; **no original firmware** in artifact.
- [Real Windows VST3 build and native tests](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/actions/runs/44279490227): both Windows and native jobs PASS; **47/47** Steinberg Validator; P003 source-pinned GUI/engine overlay applies cleanly.
- No original ROM in GitHub CI. Reproduce firmware acceptance only in the private environment with owner-supplied ROMs/OS.

## Open gates

1. **P004** persist the bank/voice using original firmware save and versioned portable project media, with fresh-instance reload and audio hash; never accept a dangling external WAV path as recall.
2. Configurable root/key range and multiple independent sampled voices: not implemented. The original firmware's default placement is MIDI **48** on the measured test.
3. True Windows VST3 editor and DAW save/close/reopen under owner's Studio One: not performed; final acceptance only.
4. Preserve the 125A Engineering separation of native DSP/firmware proofs, validator, host lifecycle, project state, product release and user-facing QA.
