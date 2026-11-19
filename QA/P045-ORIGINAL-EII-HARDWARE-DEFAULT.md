# P045 – Native EII audio path as the actual first-run Windows VST3 default

**Approved by owner, 2026-11-19:** for a newly created 125A Emulator II Custom Windows VST3, **the original Emulator II** is the standard: SSM2045 Model 2 filter (`model=5`), native AM6072 DAC + switched LF13202/TL084 deglitch (`native=1`), original EII S3528 reconstruction (`s3528=1`). **EIII CEM3387 is NOT the fallback**; its `model=4` remains manually selectable.

This follows P043 96/192 kHz DPCM A/B and owner P044 genuine original OS3.1 Windows VST3 **five original-firmware cases, seven checks, zero failures**, with actual active `appliedmodel=5 appliednative=1 applieds3528=1`. Those results establish a working original-emulation chain, not silicon-measured exact fidelity.

## Actual product change

- P028 continues to set SSM2045 model 2; P032 continues to enable S3528.
- P045 sets `nativeAudio=true` on the newly created VST3 first-run path when the underlying standalone `NativeDacDeglitch` registry key is absent. Explicit standalone registry `NativeDacDeglitch=0` remains a deliberate user override, not mistaken for an unset fallback.
- The VST3 first-run `PluginSettings` serializer and `loadPluginDefaults` are **not changed**; saved DAW project state and explicitly saved user global VST3 defaults maintain the settings the user chose. This is defensive compatibility with any hypothetical prior songs; no existing songs are asserted to exist.
- EIII Model 4, bypass/native=0 settings remain available as *optional* diagnostic or user-defined modes; neither is selected automatically on a clean install.
- The native audio DSP equations, vendor upstream source revision, Steinberg FUIDs, binary interfaces, state schema and original-ROM package stay unchanged.

## QA gates

1. Source-pinned installation after P028/P029/P032, static tests and mutation negatives.
2. Actual Windows COM VST3 factory new-instance serializes `model=5,native=1,s3528=1`.
3. Existing explicitly stored `model=4,native=0,s3528=0` project must restore unchanged; terminating it must not modify the fresh built-in default.
4. Explicit saved user global preferences must continue to select `model=4,native=0,s3528=0`; removal restores new EII hardware default.
5. Full build, independent Steinberg validator, Windows runtime and original-media absence safety tests must continue to PASS.

There is no need to repeat P044 unless the DSP runtime itself changes. Studio One final practice and P037 remaining low-memory/cancellation cases remain separate.

**Status: WINDOWS CI PASS, 2026-11-19.** GitHub Actions [run #44564307167](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/actions/runs/44564307167) completed successfully with both `windows-vst3` and `native-wav` jobs. The installed CI-built Windows Custom VST3 passed the **Steinberg validator 47/47** and the **real Windows VST3 factory default test**; its logs explicitly show `PASS P045 ACTUAL WINDOWS VST3 NATIVE DAC DEFAULT ON with original EII model 2 and S3528`, with old project native-OFF, new instance ON after old project close, explicitly saved user native-OFF, and restored native-ON fallback after removal. `P029 ACTUAL WINDOWS VST3 DEFAULT PASS 0 failure(s)`. The 14/14 P045 source checks, negative mutants and P032 source-regression compatibility also pass.

The private owner original OS 3.1 native=1 test in P044 is already **PASS** on the previous build; the P045 default-only binary has **not** been re-run with owner original media or Studio One. No DAC/filter DSP equation has changed in P045. The verified P045 DLL SHA-256 in the personal delivery ZIP is `3203654B2CD2F640DD5328E59454FD16E920FFB1D12621E045F13BC73FC9B68A`; private ROM media stay outside GitHub.
