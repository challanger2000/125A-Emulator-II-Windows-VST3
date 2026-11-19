# P043 — genuine differential-code DAC route A/B with actual pinned engine

**Date:** 2026-11-19. **ROM-free reproducible Linux audio diagnostic: PASS (10/10 checks across 96 and 192 kHz)**. [GitHub Actions #44537250713](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/actions/runs/44537250713). Exact harness: [tests/p043_dpcm_dac_route_probe.cpp](../tests/p043_dpcm_dac_route_probe.cpp). The run compiles one Linux test, **not** a whole Windows VST3. Machine-original VST3 P041 remains unaffected.

## Why this test matters

Original `Tuth/eii-emu` source contains two alternative paths before the SSM2045:

- Native switched DAC / LF13202–TL084 deglitch: `NativeDacChannel::advance`, clocked state/charge integration at genuine nominal resistor/capacitor values.
- Shortcut/reference: the current `RuntimeAudioEngine` uses a nominal `-R34/R26 = -50` deglitch gain applied directly to raw decoded DAC codes, followed by a `fastRouteMatch=0.08739944952996512` **chosen to match the native amplitude at 1 kHz only**.

Both enter the same SSM2045 and S3528 processing after the DAC. A one-frequency level match is **not** a spectral match.

P043 generates a 0.7 V peak bounded sine at actual DPCM code rate 120 MHz / 4320 = 27,777.78 codes/s. **Codes are chosen by the nominal 50/51 leaky-integrator recurrence, not by direct raw sine PCM quantization**. Each code passes through the real upstream native `NativeDacChannel`, real shortcut equations, and real `S3528Runtime` at code 35, for 100/500/1000/3000/6000/8000 Hz. The first half of each 1-second run is discarded; the second half is coherently demodulated at the source frequency. Code count: 27,778 each. Hardware-phase boundaries are 192, 384, 576, 768 of each 4320-tick code interval. No original ROM/OS or private data is required.

## Measured amplitude A/B at 96 kHz

| Source frequency | Fast amplitude | Native amplitude | Native minus fast |
|---:|---:|---:|---:|
| 100 Hz | 0.0928751 | 0.699965 | **+17.5435 dB** |
| 500 Hz | 0.354334 | 0.699554 | **+5.9082 dB** |
| 1,000 Hz | 0.698775 | 0.698701 | **−0.00093 dB** |
| 3,000 Hz | 2.016737 | 0.685837 | **−9.3686 dB** |
| 6,000 Hz | 3.555464 | 0.640561 | **−14.8867 dB** |
| 8,000 Hz | 4.193953 | 0.602643 | **−16.8513 dB** |

192 kHz reproduces these relative differences within 0.0002 dB. The exact generated CSV is attached to the GitHub workflow artifact `P043-ROM-FREE-DPCM-DAC-ROUTE-COMPARISON-96K-192K`.

The fast/native phase differs as expected for an integrator, including about −80.32 degrees at 1 kHz; a scalar gain correction cannot equalize it. S3528 code35 is effectively transparent at 100 Hz and suppresses 6 kHz by about −52 dB **in both routes**, so it is not the cause of the large low/high-frequency DAC differences.

## Interpretation and explicit limitations

1. The native path is **much closer to the intended 0.7 V synthetic DPCM sine** at the six test frequencies. The shortcut gives an unnatural spectral tilt for that nominal-DPCM stimulus.
2. That is physically plausible because the EII front-end is a **stateful switched/integrating reconstruction network**. Shortcut `-50` is not a mathematical substitute for its transfer function. At one frequency they can be level-matched, but not across the spectrum.
3. The DPCM encoder itself uses the **same nominal 50/51 leaky-integrator model**. Therefore the synthetic target is a model-conditioned stimulus, **not an independent oracle against actual original EII hardware, DAC silicon tolerances or externally captured recordings**.
4. This particular probe isolates the pre-SSM2045 DAC and S3528, not an entire bank/OS3.1/VST3 playback, and does not measure analog frequency/Q behavior or CPU scheduling. The unrelated owner P041 real-firmware VST3 matrix forced `native=0`. No new owner Windows tests were requested or performed.
5. A release-quality choice of default `native=1` still needs original-OS Windows VST3 capture/reopen at both sample rates, RAM/safety/real-time tests and ideally authentic EII output comparison. Without those, **do not silently change the existing default, alter the DSP coefficients, or claim hardware-perfect analog emulation**.

## Action / quality gate

- **P043-A original source pin and compilation: PASS**
- **P043-B differential-coded amplitude/phase A/B: PASS**
- **P043-C S3528 code35 stopband behavior both paths: PASS**
- **P043-D native=1 original firmware Windows VST3 capture and project recall: NOT RUN**
- **P043-E original EII hardware, matched stimulus, FCV/QCV, VCA, clock images and THD: NOT VERIFIED**

**Disposition:** Retain stable reference default in this checkpoint; prioritize measured Windows original-firmware native route before making a source-level default change. The pronounced multi-frequency mismatch is a verified **behavioral difference**, not proof of silicon error in the native model.
