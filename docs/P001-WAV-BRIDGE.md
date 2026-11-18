# P001 — WAV to original EII sample input

Source baseline: `Tuth/eii-emu@e345bcf00af8a066ebace9168cf0b6c3a40ca164`. Target 125A branch: `develop/wav-import-v0.1.0`. Windows x64 only, C++23 test target. No upstream source modified in Git history: overlay is a deterministic local build patch.

## Decision and independent references

The Vintage Sampler III D0 owner-approved architecture provides a firmware-mediated ADC import precedent. Its current source/QA baseline must be independently checked before any code reuse; this P001 copies **no EIII code**. Upstream Emulator II already exposes `analog::SampleInputSource`, `PluginEngine::sampleSource()`, and a measured SAR/analog `Machine::sampleInputLifecycleTick()` path. The WAV file is delivered as an analog voltage to that pathway. No direct sample RAM write or synthetic preset allocation is introduced. Original filters stay intact.

## Acceptance matrix

| Contract | P001 test/evidence | Status |
| --- | --- | --- |
| PCM8/16/24/32 and Float32 decode | Native C++23 deterministic fixtures and amplitude assertions | NOT RUN until workflow/test executed |
| invalid/missing/corrupt/truncated input | explicit rejection tests, no prior-source replacement in preparation | NOT RUN |
| 44.1/48/96 kHz input/time relation | 4 MHz machine-tick interpolation fixtures | NOT RUN |
| firmware IMODE starts imported waveform | source starts on first requested converter voltage, not idle; test checks source activation | PARTIAL: firmware not exercised |
| full WAV -> original SAR -> firmware DRAM -> audible MIDI sample | requires private ROM + OS + firmware SAMPLE command and independent PCM/DRAM reference | NOT RUN |
| one-click playable WAV keymap/preset | no automatic firmware sampling or mapping yet | NOT IMPLEMENTED |
| project save-close-reopen, embedded assets | upstream settings alone cannot preserve volatile sample RAM or prepared WAV input; design and tests required | NOT IMPLEMENTED |
| Windows VST3 build, 47/47 Validator, 125A Tester | Windows CI/test-lab and actual packaged artifact pending | NOT RUN |
| Studio One end-to-end save/reopen | owner-host gate, end of development | NOT RUN |

## Next implementation gates

1. Establish a deterministic ROM/OS-backed firmware SAMPLE test, with positive and negative PCM/original-DRAM evidence. Identify actual panel/threshold trigger before attempting automated keymap creation; preserve base firmware behaviour when WAV input is off.
2. Automate firmware capture and program allocation via its **real controls**, or derive a safely testable bank-image import path; never write guessed headers or bypass ROM-dependent behavior and call it hardware fidelity.
3. Preserve actual sampled instrument state: either versioned embedded media/RAM snapshot or explicit portable image with validated relink, plus transactional failed-restore rollback and new-instance audio comparison. External path alone does not qualify as project-portable.
4. Give user one clear WAV Import flow, suitable 125A GUI and correct names/IDs; no decorative buttons. Verify actual Windows bundled VST3 and real host.

## Rights, performance and QA

The upstream is GPL-3.0, the VST3 SDK subset has its own license. The 125A extension is GPL-3.0; retain original copyright/contributor attributions. No E-mu owned firmware/ROM/media in public source, CI, or package. File I/O/decoding/memory allocation only on GUI/control thread; waveform data immutable for machine-owner access. Decoder limit 64 MiB is a developer memory-budget cap, not a claim about EII hardware capacity. Anti-phase stereo sum can cancel; this is an intentional first-pass downmix and must be user-selectable or improved only with explicit reference/acceptance.

## Windows compiler diagnostic (2026-11-18)

Initial Windows CI run #44275768282 reproduced C++ duplicate switch cases: our WAV menu IDs 70/71 collided with the upstream safety-margin choices. The native decoder suite still passed. The correction reserves IDs 740/741, adds an upstream conflict preflight, and preserves the original 70..73 controls. The failed run is retained as RED evidence; Windows GREEN and firmware/DAW sound evidence require separate successful runs.

## P002 native hardware-path regression

Added `tests/wav_sar_machine_tests.cpp`: 1-kHz WAV and silence pass through the actual `Machine`, emulated S3528 analog chain, SAR and real synthetic Z80 INI instructions into 512 bytes of DRAM. The expected 27.778-kHz sample rate, 1-kHz zero crossings, level and content differences are independently asserted. This is NOT original ROM/OS firmware bank creation and NOT DAW recall.

P001 Windows CI at `c7157f4085ed795eb3a738b8f28417503c3caf8c` [run 44276046841](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/actions/runs/44276046841) completed **SUCCESS** with full Windows VST3, original engine/analog/host tests and Steinberg **47/47**. P002 new regression requires its own green CI.
