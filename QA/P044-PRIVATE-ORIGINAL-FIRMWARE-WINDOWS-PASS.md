# P044 – Owner-private original OS 3.1 native DAC Windows VST3 PASS

**Test date:** 2026-11-19, owner Windows x64; actual original E-mu OS 3.1, real ROMs and original Choir disk. **Result: 5/5 cases executed; 7/7 checks PASS; failed_gates=0; all six original media unchanged.**

Evidence: owner-submitted `P044-TEST-ERGEBNIS.txt` (158 physical lines, 2026-11-19 16:51:12 local header). The source log was examined. This is a **genuine owner-original Windows host run**, not a synthetic CI run. No original-ROM/OS/Choir bytes, local user paths, or raw private media are published in GitHub.

The actual VST3 DLL was fingerprinted SHA-256 `945FF16B2393B99E6FC9E8F047473BDF3221EBD26596901B66216C7A93FF05DB`; the Windows test host SHA-256 was `9BA0087DE21132D911427B980FA9A35502881A6DF6EB7D7489B41D7B990E7361`.

## Observed original-ROM Windows VST3 cases

Every case logged genuine OS boot `appliedmodel=5 appliednative=1 applieds3528=1`, original scanner SAMPLE/FORCE/STOP, >=27,000 original SAR reads, original firmware DISK7 save, a bank in the VST3 project snapshot and C3/MIDI sample audition, with `input_drops=0 missing=0`.

| Original-firmware case | SAR reads | Spectral amplitude at target | Peak | RMS | Bank snapshot |
| --- | ---: | ---: | ---: | ---: | --- |
| NATIVE_POSITIVE_44100_1000HZ | 33,054 | 1 kHz: 0.150135886 | 0.221971706 | 0.0591936893 | 1 |
| NATIVE_POSITIVE_48000_1000HZ | 32,614 | 1 kHz: 0.15018181 | 0.225271419 | 0.0613634759 | 1 |
| NATIVE_CHANGED_48000_500HZ | 32,606 | 500 Hz: 0.150657752 | 0.225772396 | 0.0615850554 | 1 |
| NATIVE_SILENCE_48000 | 32,603 | 1 kHz: 0.00000104048107; 500 Hz: 0.000000322747751 | 0.000226491786 | 0.0000363616728 | 1 |
| NATIVE_DISCONNECTED_48000 | 32,603 | 1 kHz: 0.000000976560387; 500 Hz: 0.000000312407777 | 0.000226491786 | 0.0000363383327 | 1 |

All seven `P044 CHECK` lines are `PASS`, including two samplerate positives, changed-frequency positive, three causal negative checks and all five real-native S3528 capture/save/audition executions. Overall line: `P044 ORIGINAL WINDOWS VST3 NATIVE DAC + S3528 OWNER-PRIVATE PASS failed_gates=0`, followed by the final launcher `P044 FINAL ORIGINAL-FIRMWARE NATIVE DAC WINDOWS VST3 MATRIX: PASS`.

Each private original file was SHA-256 checked and reported unchanged after the test (four ROMs, OS3.1 and Choir floppy). This is a strong result for operational stability and correct live routing of the native DAC in this test.

## Important evidence boundaries

- **P044 validates operational behavior of the native=1 sound path, not exact original-silicon analog timbre.** Matched hardware captures and original 1980s chip response measurements are still unavailable; reference P043 demonstrates the engineering advantage for the nominal DPCM test, not a measured match against an EII chassis.
- The host made and serialized bank snapshots but P044 did **not** explicitly terminate/reopen an independent DAW project to prove the entire song recall lifecycle in this run. Other project-state tests are separate.
- No original hardware phase, analog noise spectrum, S3528 true switched-capacitor clock feedthrough, multi-voice high-load Studio One real-time run or full P037 adversarial cancellation/low-memory matrix was performed as part of P044.
- Existing song/global-default preferences must not silently change as a side effect of documenting this result.

**Disposition:** P044 owner-original native DAC Windows acceptance matrix **COMPLETE**. No need to re-run P044 merely to reconfirm these cases. Any future change of the new-instance default from `native=0` to `native=1` must be separately reviewed and regression tested, and must preserve saved sessions.
