# P004 Windows VST3 — START HERE (development / private test)

**Status:** Internal development build, not a public product release. Do not redistribute the plugin or bundled firmware. Original E-mu ROMs/OS are NOT included.

## Install

1. Copy the directory EmulatorII-Custom.vst3 into the usual Windows x64 VST3 directory (normally C:\Program Files\Common Files\VST3). Do not copy individual DLLs out of the VST3 bundle.
2. In your DAW, start Emulator II Custom as a VST3 instrument. Point Settings > ROM folder at the user's original Emulator II ROM set (main.bin, scanner.bin, ic135.bin, ic137.bin; main21dm.bin for optional 1MB boot). Select the original OS 3.1 floppy image (.emuiifd) in the Floppy menu and boot the EII; wait for P01 NULL PRESET.
3. In the EII plugin Settings menu select 125A: WAV automatisch aufnehmen... and choose an ordinary PCM/Float WAV, up to 10 seconds in this first version. The plug-in drives original SAMPLE, FORCE, STOP and DISK 7 SAVE BANK internally. Recording/Bank-Save can take substantial emulated time; do not interrupt project save while a bank is being written.
4. A successful completed import is playable on MIDI note 48 in the verified single-voice case. Saving the DAW project embeds the 573440-byte original-bank disk image; it should be recallable in a new plugin instance even without the source WAV. **The original ROM directory is still required.** No other runtime programs are needed.

## Warnings and expected limitations

- A protected *working-copy floppy* must be mounted; keep Direct image writes OFF so user OS/media cannot be overwritten. Do not insert/eject media while original firmware is writing.
- Do not interpret a successful UI menu click as successful recording. The plugin reports completion only after the original firmware's SAVE BANK has written its tracks and returned to Pxx.
- A sample imported mid-project while SAVE BANK is still active deliberately blocks state save; wait for the explicit success/failure indication in plugin Status.
- This build has not yet completed the final user Studio One project save/close/reopen and full 125A Plugin Tester release audit. Treat its use as a private acceptance test; report the DAW/project behavior and any original media changes.
- The first importer maps one original firmware-recorded voice and has no multi-sample root/keyrange editor yet. Additional imports should be checked carefully for bank voice allocation.

## Provenance, compliance and QA

Original hardware core: Tuth/eii-emu pinned at e345bcf00af8a066ebace9168cf0b6c3a40ca164 (GPL-3.0). 125A extensions and build instructions: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3 . This artifact contains the applicable GPL-3.0 license; see the VST3 SDK license bundled with the plugin.

Evidence: original ROM/OS native plugin-owner full-chain P004 PASS; actual Windows VST3 COM project-state binary roundtrip/corruption/two-instance isolation PASS; Steinberg validator 47/47 PASS. See docs/P004-PRIVATE-FIRMWARE-PROJECT-ACCEPTANCE.md in the source repository. **This does not replace owner Studio One QA.**

No original E-mu ROM, OS/floppy image or user sound bank is in this artifact.
