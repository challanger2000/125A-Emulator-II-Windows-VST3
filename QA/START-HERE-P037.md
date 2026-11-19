# P037 — Original firmware recording end-to-end acceptance (DEV / NOT PASSED)

## Evidence boundary

P036 validates a **synthetic Z80 program** driving the real emulated ADC/SAR/DRAM path with a production-style host input queue. It does not establish original E-mu OS recording, the real VST3 host input connection at runtime, or playback of the recorded sample. Do not infer P037 PASS from P036 tests, successful builds, Steinberg validation, or pre-existing WAV-import tests.

## Required positive acceptance (all must be observed in one original-firmware run)

1. Start the Windows x64 **real VST3** with user-supplied, legally held original EII ROM and OS 3.0 or 3.1 media. Record ROM/media SHA-256 hashes without uploading bytes. A synthetic Z80 fixture, fake ROM, or internal harness bypass must not satisfy this gate.
2. Confirm the guest original firmware reaches its recording UI/state, using firmware-visible LCD/status and Z80 I/O evidence. Failure to enter the recording path is **BLOCKED**, not PASS.
3. Supply a known, bounded 1 kHz PCM host input via the actual VST3 audio input bus at 44.1 kHz and 48 kHz. Record host callback counts and per-channel input-frame counts. Confirm original guest sampler clock, comparator/SAR conversion counts, IWAIT activity, and original guest DRAM writes.
4. Prove *causal* coupling: mute the host input on a new take and confirm no corresponding 1 kHz component; change host input frequency (for example to 500 Hz) and confirm the recorded waveform frequency changes accordingly. Merely observing non-zero DRAM or a preloaded sample is insufficient.
5. After recording, invoke actual guest firmware save/playback or sample audition. Verify the recorded sample is heard in the host PCM output, its pitch is consistent with the recorded input and its duration is nontrivial. Preserve a captured audio reference and numeric frequency/amplitude comparisons.
6. Capture a fresh instance / project state round-trip and verify original sample restoration and subsequent playback, if that operation is supported by the original OS workflow. Distinguish an unsaved RAM sample from a saved bank.
7. Test cancellation and an insufficient-RAM condition without corrupting the currently selected bank, and test a failed/absent input bus. No fabricated positive output may count as success.
8. Run Windows x64 tests with actual VST3 and original private media **owner-local**; no copyrighted ROM, OS image, samples or media may be committed or uploaded as CI artifacts. Studio One manual acceptance remains reserved for the final product sign-off.

## Evidence format (minimum)

- Exact source revision and native VST3 binary SHA-256
- OS/ROM media identity by hash (no media content)
- Windows host and VST3 test harness version, DAW sample rate, bus/channel and block size
- Guest firmware-visible start/record/stop/play actions and relevant event timeline
- Host input waveform parameters, supplied/missing/dropped frame counts
- SAR reads/conversions, wait clocks, DRAM changed-address count and segment hash
- Guest audition PCM with duration, dominant pitch and measured level
- Silence/frequency-change negative control evidence and explicit outcome
- Each individual gate: PASS, FAIL, or BLOCKED with reason

## Acceptance rule

**P037 PASS only when all eight gates are supported by executed original-firmware Windows VST3 evidence.** Otherwise label P037 **DEV / BLOCKED** or **FAIL** accurately. Synthetic fixture successes must remain reported as P036. This document is an acceptance contract, not a claim that these tests have been executed.
