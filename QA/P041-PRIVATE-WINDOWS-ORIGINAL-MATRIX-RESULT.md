# P041 — genuine original E-mu OS 3.1 Windows VST3 multi-rate / causal-negative result

**Owner-local test on 2026-11-19: P041 / P040 original-firmware matrix PASS, 0 failed gates.**

Evidence: user-supplied `P041-TEST-ERGEBNIS(2).txt` from the private `125A-Emulator-II-P041-PRIVATE-KOMPLETT` kit. The result file was inspected, not simulated by GitHub Actions. No private ROMs, OS media, Choir sample banks, Windows user profile, or original-media bytes are committed here.

## Observed result-file assertions

- VST3 binary SHA-256: `99E4D97B3958DE7280CC8544A1E73555746E1DA90A066C9EA88345508D27B2F5`.
- Original OS3.1, ROM and Choir hashes were printed for six private files; *all six* were also reported unchanged after execution.
- `P040 CHECK POSITIVE_44100_HAS_1KHZ PASS`
- `P040 CHECK POSITIVE_48000_HAS_1KHZ PASS`
- `P040 CHECK CHANGED_INPUT_HAS_500HZ PASS`
- `P040 CHECK MUTED_GUEST_HAS_NO_STALE_1000HZ PASS`
- `P040 CHECK MUTED_GUEST_HAS_NO_STALE_500HZ PASS`
- `P040 CHECK DISCONNECTED_GUEST_HAS_NO_STALE_1000HZ PASS`
- `P040 ORIGINAL WINDOWS VST3 OWNER-PRIVATE MULTIRATE + SILENCE + FREQUENCY CHANGE + NO-INPUT PASS failed_gates=0`
- `P040 WINDOWS VST3 ORIGINAL FIRMWARE MULTIRATE/CAUSAL NEGATIVE: PASS`
- `P040 FINAL ORIGINAL-FIRMWARE WINDOWS VST3 TEST: PASS`
- `P041 FINAL WINDOWS ORIGINAL FIRMWARE MATRIX: PASS`

The P040 C++ harness implements fresh original-firmware Windows VST3 cases at both rates, original scanner SAMPLE/FORCE/STOP, physical DISK7 save, VST3 project bank snapshot and MIDI C3 sample audition, with frequency and silence guards. The owner-only result is therefore meaningful evidence for that matrix. The previously failing 500 Hz step no longer caused a test failure in this run.

## Scope, transparency and limits

The **submitted transcript contains the aggregate CHECK/PASS results and private-media integrity results, but not each case's individual stage timestamps, SAR/host-frame counts, spectrum/PCM metrics, or separate waveforms**. These details must not be invented. In particular, this P041 result is not proof of bit-identical hardware analog/filter calibration.

P039 already supplied a separately documented Windows original-ROM 440 Hz recording, project-state round-trip and reopened playback positive. P041 now adds the two positive sample rates and causal negative controls. The broader **P037 FULL ACCEPTANCE remains incomplete**, including the required original-firmware cancellation / low-memory safety cases and guest IWAIT / DRAM changed-address evidence. Final Studio One acceptance also remains outstanding. Do **not** mark P037 or a whole-project FULL AUDIT as PASS merely because P041 succeeded.

The private source log should remain owner-local; this is an anonymized technical summary.
