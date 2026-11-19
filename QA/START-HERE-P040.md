# P040 — original OS3.1 Windows VST3 multi-rate and causal-negative acceptance

**DEV until an owner-private original-ROM Windows run reports every P040 case and CHECK as PASS.** Public GitHub Actions **compiles** the actual Windows VST3+host harness, runs an invalid-media negative gate, and validates source contracts. It never provides evidence of genuine-ROM private recording.

## Owner-local one-click test

Run `START-P040-TEST.bat` in the complete private Windows test kit. The included original ROM/OS3.1/Choir are owner-private; this ZIP must not be publicly distributed. No Studio One installation is required for this test.

Upload only `P040-TEST-ERGEBNIS.txt`, not ROMs/audio. The script records SHA-256 for the actual VST3 binary and each private ROM/floppy and checks no original media were modified. The test copies none of the owner's private media to GitHub, CI or external destinations.

## Genuine-original firmware cases

All cases boot a **fresh original OS3.1** through the **actual Windows VST3 factory/COM audio `IAudioProcessor::process`**. Each actuates original EII physical SAMPLE/FORCE/STOP scanner contacts, validates >=27,000 actual Z80/SAR reads and zero unknown bytes, demands firmware DISK7 BANK save and an actual project bank snapshot, then auditions via VST3 MIDI C3 mapped to EII original note 48. Source is a timestamped VST3 audio input bus, never a preloaded sampled bank.

- `POSITIVE_44100_1000HZ`: original recording of 1kHz input at 44,100 Hz host sample rate.
- `POSITIVE_48000_1000HZ`: same recording at 48,000 Hz host sample rate.
- `NEGATIVE_CHANGED_48000_500HZ`: newly recorded 500 Hz host input must produce real 500 Hz output, distinguishable from prior 1kHz test.
- `NEGATIVE_SILENCE_48000`: connected silent bus must not retain the prior 1kHz or 500 Hz tone (Fourier amplitude <12% of corresponding genuine positive).
- `NEGATIVE_DISCONNECTED_INPUT`: real VST3 ProcessData.numInputs=0, not just a zero-filled connected bus; must not produce 1kHz stale prior-sample tone. Intentional timestamped silent host frames are legal; "inputframes=0" is not required on disconnected bus.

Strict spectral acceptance: 1 kHz and 500 Hz positive-component amplitude >0.003 in the 0.15–0.90 sec mono host output window; silence/disconnected tone component <12% of independently captured positive. This is an engineering threshold, not physical-hardware calibration.

## Failure and evidence boundaries

- If OS/ROM/Choir absent, test returns **BLOCKED exit code 3** immediately, not a false success.
- An original firmware capture error, incomplete SAR read, stalled/failed DISK7, lost input frames or stale audio produces a nonzero exit. All five cases are attempted and separately logged, with aggregate `P040 ... PASS/FAIL`.
- Genuine Windows P039 positive 440 Hz original recording + fresh `IBStream` playback is already documented separately in `QA/P039-PRIVATE-WINDOWS-ORIGINAL-POSITIVE-RESULT.md`. P040 adds rate/input causality gates; it is not a replacement for P039 fresh recall.
- **Still outside P040:** original-firmware low-memory and cancellation state controls, true randomized hostile media faults, final Studio One acceptance, bit-identical hardware analog/filter calibration. The more comprehensive `QA/START-HERE-P037.md` gate cannot be FULL PASS until all its mandated evidence is actually produced.

No proprietary files or owner audio committed to GitHub.
