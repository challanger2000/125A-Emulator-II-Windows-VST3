# P044 – Native DAC/Deglitch + S3528, original OS3.1 Windows x64 VST3 acceptance

**Status: OWNER-PRIVATE ORIGINAL-FIRMWARE WINDOWS TEST PASS on 2026-11-19.** All five cases executed and all seven native DSP/S3528 acceptance gates passed with no original media modification. See [exact private owner result summary](P044-PRIVATE-ORIGINAL-FIRMWARE-WINDOWS-PASS.md). Public CI still independently proves only source, Windows build, starter behavior and no-media negative gates.

P043 separately demonstrated a pronounced 100 Hz–8 kHz response difference between the native switched charge-transfer DAC and the 1-kHz-matched shortcut, using a deterministic DPCM sine generated with the nominal 50/51 recurrence. That provides motivation for P044, not independent hardware-calibration evidence.

## Noninvasive changes

- `tests/p040_windows_original_adversarial.h`: appended `P040Case.native=false` (no change to P040 default and its five existing test cases). An explicitly native case sets the real project's serialized `native=1,s3528=1,model=5`, then requires status `appliednative=1,applieds3528=1` after original OS boot **and** after recording/saving/MIDI audition.
- `tests/p044_windows_native_original_adversarial.h`: independent five-case runner using the exact P040 genuine scanner/SAR/audio host-bus -> disk7 -> serialized bank -> MIDI C3 chain. The five cases are new original OS boots, at 44.1/48 kHz, 1k/500 Hz, silence and disconnected DAW input; seven explicit checks must all pass.
- `tools/apply-p044-native-original-windows-matrix.py`: source-pinned, additive QA-only host `original-windows-native-p044-matrix` mode, preserves P040 dispatch and all VST3/DSP code.
- `tools/START-P044-TEST.bat` and `tools/Test-Private-Original-EII-P044-Windows.ps1`: one-click, owner-local native run; reads all original ROM/OS/Choir files **inside the same unpacked private ZIP**. No searching Windows folders and no downloading proprietary data. Displays full C++ native host logs live and writes `P044-TEST-ERGEBNIS.txt`, including full spectral/SAR metrics, without relying on the incomplete PowerShell `Start-Transcript` captured in P041.
- Original files are SHA-256 hashed before/after and the Windows `LOCALAPPDATA` is isolated and reverted.
- GitHub Windows CI checks compilation of actual plugin + host and rejects missing original ROM with exit 3. Separate Windows `cmd.exe`/PS 5.1 starter smoke likewise checks fail-closed behavior. **These are not equivalent to owner-original positive audio.**

## Owner original acceptance matrix

| Case | In/host | VST3 audio route | Required result |
| --- | --- | --- | --- |
| NATIVE_POSITIVE_44100_1000HZ | 44.1 kHz/1k tone | model 5, native 1, S3528 1 | Original OS3.1 SAMPLE/FORCE/STOP, >=27k SAR reads, bank saved, MIDI audio 1k component >0.003 |
| NATIVE_POSITIVE_48000_1000HZ | 48 kHz/1k tone | same | positive 1k |
| NATIVE_CHANGED_48000_500HZ | 48 kHz/500 Hz | same | 500 Hz component >0.003 |
| NATIVE_SILENCE_48000 | connected digital silence | same | no stale 1k or 500 Hz >12% of independently captured positives |
| NATIVE_DISCONNECTED_48000 | host `numInputs=0`, truly disconnected | same | no stale 1k >12% of native 1k reference |

Each test separately validates firmware boot, the genuine Windows VST3 `IAudioProcessor::process` callback, full bank snapshot and native DSP application through to end of audition. Original media hashes must remain unchanged. Any missing/failed gate yields nonzero exit and FAIL, never a fabricated PASS. No Studio One test until final sign-off.

**What P044 is not:** a precision measurement of physical SSM2045, original 1984 S3528 chip transfer, clock spurs, the original analog output's exact gain/polarity or full project P037 adversarial safety acceptance. Those hardware comparisons still need a true matched EII reference. Do not flip the new-instance `native` default from 0 to 1 on the basis of public CI alone.
