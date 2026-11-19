# P032 — Use the existing original EII S3528 reconstruction on new 125A instruments

**Status:** development change / audio-fidelity work, not complete chip calibration.
Base: 125A \`main\` P031 (\`592e91c885498d6a75c9f4e285e78b745aa3e713\`), Tuth/eii-emu pinned \`e345bcf00af8a066ebace9168cf0b6c3a40ca164\`. No private ROM, OS, .EII disk, Choir sample or hardware measurement added.

## Important correction to the earlier completion assessment

The pinned Tuth engine is materially more advanced than the historical \`docs/ROADMAP.md\` paragraph from upstream v0.50:
- \`docs/SSM2045_MODEL2.md\`: an independently validated model 2 already includes a zero-delay/nonlinear OTA circuit, real EII control network and Q feedback, at selectable 96/192k. It has SPICE comparisons, *not exact original silicon calibration*.
- \`docs/S3528_RUNTIME_069.md\`: a host-rate nominal AMI-curve S3528 reconstruction stage is **already implemented** as a selectable live audio feature with firmware six-bit code and continuity across code updates. It was, however, **OFF by default** and may be turned on explicitly.
- The original analog work is **not finished**: S3528 is a fitted behavioral transfer, not recovered physical switched-capacitor topology; waveform timing, deglitch events, hardware calibration, SAR recording, MIDI OUT and front-panel LEDs have separate outstanding gates.

P032 does not re-implement these models and must not describe them as absent or completely calibrated.

## Actual product change

New 125A Windows **Custom** VST3 instances, without an explicitly saved 125A global preference, start with:
- **model=5** = original Emulator II SSM2045 Model 2 96k (already P028/P029);
- **s3528=1** = the existing S3528 nominal reconstruction enabled (P032).

This is the first actual sound-path default change toward the complete original EII output topology. It is deliberately **not** a claim of filter frequency/pin accuracy.

- Previously saved IComponent song state keeps its own \`s3528=0/1\`, including historical bypass projects.
- User-selected and explicitly saved plug-in defaults override the new fallback, including \`s3528=0\`.
- EIII CEM3387 Custom remains selectable; switching models in a saved project remains valid.
- No DSP source, firmware, FUID, plugin classes, ABI, project codec, analog circuit math or sample-rate processing changed. One Windows x64 VST3; no extra runtime program.

## Regression gates

1. Source-pinned overlay refuses unexpected upstream or a missing P029 implicit-default fix.
2. Source and negative mutants ensure 125A fallback is original model 2/S3528 ON, user defaults and serialized song state are left intact.
3. **Actual packaged Windows VST3 COM/factory** tests verify new EII \`model=5,s3528=1\`, old CEM song \`model=4,s3528=0\`, a second new EII still ON, explicit saved CEM/OFF default, and fallback ON again after the override is removed.
4. Existing Steinberg, native analog/runtime, host and lifecycle suites must continue to pass.
5. P030 owner-only positive Windows original-ROM/Choir host acceptance now **requires the enabled S3528 to be applied in both genuine render runs** and preserved in fresh saved project state. No proprietary media in CI. Positive owner run is **NOT RUN** unless actually executed with licensed original media.

## Remaining hardware work — do not mistake this change for completion

- **Output analog fidelity:** measure/derive the remaining exact S3528 switched-capacitor/clock and deglitch-stage effects, absolute filter calibration across cutoff/Q settings and actual hardware samples; quantify error against original EII, not just the fitted AMI typical plot.
- **Sample input / SAR:** finish firmware-driven original ADC/SAR hardware accuracy and original recording validation (WAV import alone does not close this).
- **MIDI OUT and LEDs:** restore the original outgoing UART and physical panel LED behavior, with authentic firmware tests.
- **Host acceptance:** Windows original ROM+Choir positive with S3528 ON, native ASIO/Studio One/realtime under load, 125A QA Tester. Defer Studio One end-user verification until hardware work is at the agreed final gate.

This note supersedes only the obsolete claim that the production audio path had no SSM2045 Q or no selectable S3528. It does not supersede Tuth's own physical calibration limits.
