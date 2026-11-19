# P042 — Emulator II analog-chain fidelity gap audit (source/data review, not hardware calibration)

**2026-11-19 — RESEARCH/AUDIT, NOT AN AUDIO RELEASE OR HARDWARE-ACCURACY PASS.**  
Production audio, original firmware, user projects and filter defaults remain **unchanged**. This audit is based on the pinned upstream source `Tuth/eii-emu@e345bcf00af8a066ebace9168cf0b6c3a40ca164`, the 125A source overlays, the upstream measurement reports and the owner-private P041 Windows result. No original-ROM or electronic measurement data is published here.

## Primary finding — what P041 did and did not test

The Windows original-firmware P040/P041 adversarial harness explicitly writes `state=replaceKey(state,"native","0");` before activating each real VST3. P041 therefore demonstrates original firmware SAMPLE/FORCE/STOP -> host SAR input -> DISK7 SAVE -> project snapshot -> reference-analog PCM at 44.1/48k, with causal 1k/500Hz/silence/no-bus controls. It **does not validate the native switched DAC/deglitch audio route**. Its owner transcript contains six aggregate CHECK/PASS lines but omits individual per-case SAR and spectral metrics; these must not be invented.

At the first-run 125A Custom VST3 fallback, P028 selects `RuntimeAudioMode::Ssm2Chip` and P032 enables `s.reconstruction=true`. However P032 expressly leaves `s.nativeAudio=p.nativeAudio` alone. The pinned `WindowsPanelPreferences` defaults `nativeAudio=false` and reads the absent registry value as 0. The initial 125A fallback therefore has **model=5, s3528=1, native=0** unless a user/registry/global-default or DAW project state overrides it. Existing-song and explicit user defaults must remain authoritative; no silent migration is authorized by this audit.

This is a **fidelity coverage gap**, not proof of a bug or an argument to turn on an uncalibrated route.

## What is already substantiated

| Stage | Independent evidence | Engineering confidence / limitation |
| --- | --- | --- |
| SSM2045 model 2 | `docs/SSM2045_MODEL2.md`, Fig.1-derived zero-delay nonlinear OTA/VCA model, independent ngspice macromodel, 162 fitted reference points at 192k; reported family RMS 0.137dB, max 0.78dB | Good agreement **with the project's own SPICE/datasheet model**, not measured EII silicon |
| S3528 | `src/s3528_runtime.h` and `docs/S3528_CURVE_FIT.md`: 1993 **S3528B** typical curve SOS with seven poles/two notches, actual six-bit firmware code and nominal 5MHz/(40N) | Mathematical transfer approximation; original EII S3528 revision equivalence and SC phase/hold/clock feedthrough/absolute hardware error unverified |
| S3528 fit residuals | Holdout from *same 1993 scanned curve*: max 2.06dB stopband (3 points), 12.28us delay (7 points); runtime reports 15.32/20.07us max delay at 96/192k | This does **not** measure EII hardware or provide 64-code hardware tolerances |
| DAC and deglitch | `docs/NATIVE_CALIBRATION_071.md`, `docs/OUTPUT_STAGE.md`, `src/deglitch.h`: 13202/TL084 charge-transfer / DPCM integration model | The switched topology is nominal; clock injection, finite bandwidth, tolerances and hardware waveform calibration remain open |
| Native/reference difference | `docs/NATIVE_CALIBRATION_071.md` raw companded sine isolation test: -3.63dB/100Hz, -21.17dB/1kHz, -30.54dB/3kHz, -36.06dB/6kHz | **Raw codes, not correctly differential-coded music**, and not real EII hardware; cannot use these numbers as a hardware-error metric |
| Owner Windows matrix | `QA/P041-PRIVATE-WINDOWS-ORIGINAL-MATRIX-RESULT.md`: 6/6 gates PASS, no modified private assets | Correct operational acceptance for the tested reference route only |

## Priority and decision

1. **P0 before analog accuracy claim:** acquire or establish an authentic original-EII **same-input/same-preset** reference for the relevant analog nodes and output jacks, with original hardware revision noted. A commercial recording or unrelated demo is not a valid A/B calibration reference.
2. **P0 next test:** measure **both** `native=0` and `native=1` using the *same* genuine-firmware test path and controlled saved calibration; log actual `appliedmodel`, `appliednative`, `applieds3528`, firmware S3528 code, host input, stereo/aux PCM, frequency, phase, THD, RMS and peak. Keep positive SAR/memory proof separate from audio-fidelity claims. The current P041 harness explicitly forces `native=0`.
3. **P1 hardware sweep:** for original hardware and emulator, separately measure FCV and QCV families, VCA/attack-release envelopes, alias/image rejection and clock spurs for S3528 codes including 0, 35, 57, 59, 63; at low- and high-frequency source samples and multiple input levels. Capture repeatability across channels and warm-up. Test the intermediate filter path if safe to instrument, otherwise define a constrained output-only system-identification test.
4. **P1 review of modeling assumptions:** 1993 S3528B transfer as surrogate for EII-era S3528, nominal 5MHz clock, gain/offset, continuous hold, code-switching settling, actual 13202 phase/capacitor variation, deglitch clipping, 96/192k warping and decimator. Match only justified parameters; no arbitrary EQ or gain changes.
5. **P2 defaults:** select `native=1` as the normal default **only after** controlled evidence shows it is the more faithful route and its CPU/real-time behavior is stable. Always preserve existing saved project and explicit global preferences.

## Evidence gates (never fabricate PASS)

- `P042-A` **SOURCE-VERIFIED:** source provenance and default-route inventory, 9/9 literal source checks against the live 125A repository and pinned upstream files (2026-11-19); no C++ DSP runtime executed in this audit.
- `P042-B` **DOCUMENTED / NOT RE-RUN:** existing upstream SSM2-versus-SPICE and S3528B plotted-curve comparison reports are present; this audit reads their stated values but has not reproduced their numerical runs. They do not constitute measured EII hardware acceptance.
- `P042-C` **NOT VERIFIED:** original EII measured filter frequency/Q/THD response compared to matching input.
- `P042-D` **NOT VERIFIED:** original EII S3528 clock phase/alias/settling versus current continuous-time fit.
- `P042-E` **NOT VERIFIED:** authentic native DAC/deglitch output versus reference hardware, across rates and dynamics.
- `P042-F` **WINDOWS OWNER-ROM VERIFIED (P044, 2026-11-19)** for the original-firmware 5-case matrix with `native=1`, S3528=1 at 44.1/48 kHz, full SAMPLE/FORCE/STOP, DISK7 bank snapshot and MIDI audition; **Studio One NOT RUN**. See [P044 positive results](P044-PRIVATE-ORIGINAL-FIRMWARE-WINDOWS-PASS.md). Original analog silicon accuracy also remains unverified.

## 2026-11-19 additional provenance check

The upstream GitHub `Tuth/eii-emu` public `main` contains the single initial published commit `e345bcf00af8a066ebace9168cf0b6c3a40ca164` as of this audit. There is no newer public upstream filter fix to import. The publicly available **1984 AMI S3528** catalogue describes the original six-bit switched-capacitor device, while the existing fitted profile references the later **1993 AMI S3528B** typical curves. The current upstream documentation itself explicitly does not assert that the two silicon revisions are identical.

There is currently **no quantitative hardware-derived correction** that can responsibly be made to the shipped filter coefficients, so this audit intentionally makes **no DSP or default-setting changes**. Revisit the original-engine source/measurements rather than adding a second approximate filter implementation.
