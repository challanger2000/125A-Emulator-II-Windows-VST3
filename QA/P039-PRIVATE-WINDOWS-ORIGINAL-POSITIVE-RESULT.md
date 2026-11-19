# P039 — Original E-mu OS3.1 recording and saved-project playback, Windows VST3

**User-run genuine original-ROM positive test on Windows: PASS.** Date: 2026-11-19. Evidence: user-provided `P039-TEST-ERGEBNIS(1).txt`, captured by the P039 owner-local `START-P039-TEST.bat` test kit. No private media attached to this repository.

## Executed test: results

- Host loaded a real Windows VST3 bundle through `VST3::Hosting::Module`: **PASS**. Reported class: `Emulator II Custom`, `Instrument|Sampler`, VST SDK 3.8.1.
- Genuine original firmware (owner-private original ROM, OS3.1 and Choir sample floppy) reached `P01 EII Choir`.
- Actual original guest SAMPLE/FORCE/STOP via the VST3 test harness: `Loading original SAMPLE module` → `Firmware FORCE / ADC start` → `Recording through original EII SAR` → `Firmware STOP / capture verification` → `Returning to playable preset` → `Firmware capture complete (RAM only)`.
- Original guest SAR reads: **32,665** at firmware return to the `P01` preset, with 290,304 host input frames reported at that phase.
- Measured recorded playback at host MIDI C3 remapped to EII note 48: **440 Hz** with measured peak **0.0802609**, as logged by the actual Windows VST3 test. Test input was a synthesized 440 Hz host-input bus sine wave.
- Original guest DISK7 bank-save and subsequent VST3 project state `IBStream` roundtrip: **PASS** as exercised by the test harness (the save step is not separately printed; successful progression to fresh-instance replay is enforced by the harness).
- Fresh VST3 component state restoration + original-firmware replay: **440 Hz** measured again, with peak **0.0749248**.
- Final owner Windows log exactly reports `P038 WINDOWS VST3 COM ORIGINAL OS31 HOST INPUT -> SAR -> DISK7 -> PROJECT IBStream -> FRESH PCM PASS original_hz=440 reopened_hz=440 host_frames=291328` and `P039 actual Windows VST3 original-firmware host input and project recall: PASS`.

This independently establishes the **real Windows VST3 COM original firmware positive capture/save/playback/recall path**. Prior P038 failed at its *pitch oracle*: sample replay at original note 60 produced 880 Hz rather than the expected 440 Hz. The P039 correction enabled the host MIDI C3 → original EII MIDI 48 remapping. Both current and fresh-instance 440 Hz readings now pass.

## Contract boundary: do not overclaim P037 full acceptance

The strict `QA/START-HERE-P037.md` contract requires **all eight** evidence gates. This single real owner Windows positive run establishes the central 48 kHz / 440 Hz path. **It is not a complete P037 FULL PASS**, because the submitted log does not show:

- Required 44.1 kHz and 48 kHz **1 kHz** positive recording matrix; this test used 48 kHz / 440 Hz.
- Owner-Windows **mute/silence** and **changed-frequency** negative control recordings with genuine firmware.
- Owner-Windows cancellation, low-memory, disconnected input bus controls protecting the currently selected bank.
- Full prescribed source/binary/ROM/media SHA-256 manifest, explicit guest IWAIT and DRAM address/segment-hash evidence, and a retained captured PCM waveform artifact.

Those gates are **NOT VERIFIED**, not PASS. This also does not replace the future final Studio One acceptance.

No private ROMs, OS floppies, Choir banks, input recordings or user paths are committed. 

**Milestone status: P039 Windows original-firmware end-to-end positive test PASS; full adversarial P037 contract remains DEV/PARTIAL until independent negative, rate and hash evidence.**
