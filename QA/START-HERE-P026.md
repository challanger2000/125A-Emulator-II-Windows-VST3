# P026 — Actual Windows VST3 COM audio and lifecycle acceptance

**Development version. The Studio One final user test is not due yet.**

The preceding P025 private original-ROM/Choir experiment established
**53.88 seconds** to first fully playable Pxx+SCN2651 and **166,085**
nonzero frames through the actual Linux-built PluginEngine with zero DAW
audio callbacks during boot. This does NOT establish actual Windows
VST3 audio/host behavior.

## New real Windows COM host test

Windows CI now loads the actual x64
`EmulatorII-Custom.vst3` bundle through Steinberg's VST3 Hosting API
and creates TWO independent VST3 component/processor instances:

- Instance A: 48 kHz, realtime, 512-frame buffers, deliberately
  invalid synthetic NOP ROM. The original production controller
  fails with its genuine RFD bus-driver collision on original clock 1.
  Check that the real error is preserved, no fake Pxx appears, COM
  processing continues safely and ALL main stereo samples are zero.
- Instance B: 44.1 kHz, realtime, 256-frame buffers, autoboot OFF;
  process callbacks alongside A, ensure independent audio/state,
  all finite and silent output, and no inherited failure.
- 160 actual COM processor blocks per instance, sampled MIDI event
  input to the failed original firmware, verified individual VST3
  state inspection, and both original machine owner threads shut down
  cleanly. No leaked EII threads after destruction.
- Previous Windows native project/HDD/bank/C3 state roundtrip,
  Steinberg 47/47 and original Z80/SAR/DRAM regressions retained.

All synthetic ROMs are created transiently under the Windows CI
runner and deleted. **No proprietary firmware or sound bank enters
GitHub or the public VST3.**

## Scope/limits

The Windows test is a *negative* hardware fault/recovery, host audio
callback, two-instance separation and host teardown test. The
private genuine ROM+Choir *positive audio* test remains Linux-native,
as above. This does **not** claim genuine original Choir audio has
already played through a Windows COM VST3, or that Studio One has been
fully tested. Both remain necessary for final acceptance.

No extra programs are shipped beside the single Windows VST3.

Development PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/24
