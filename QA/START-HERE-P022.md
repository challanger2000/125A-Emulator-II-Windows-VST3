# P022 – Original Emulator II autonomous boot service fixes

**Windows x64 VST3 development only. Do NOT replace your last known-good build.**

## Critical errors found and fixed in P021

P021's independent hardware clock bypassed a few vital tasks from the
normal emulation-owner advance path:

- **HDD-first original OS boot**: When `main23.bin` boots from HDD,
  the optional floppy is deliberately kept ejected until the original
  firmware reaches its resident code at PC 0x2800. P021 had skipped
  that delayed insertion while booting without host audio callbacks.
  P022 restores exactly the original 0x2800 gate.

- **DAW automation lost during boot**: P021 discarded every queued host
  event as though it were a MIDI message. P022 preserves slider and
  wheel/voltage automation (`kind=1`) and its original 25Hz scanner
  throttle, but intentionally drops preboot MIDI (`kind=0`) that
  cannot safely be timestamped before a playable bank is ready.
  Event processing is capped at 256 per machine quantum to ensure
  firmware progress during heavy host automation.

- **Silent VST3 after a failed boot**: When an error occurred after
  audio gating but before startup completed, the DAW output could
  remain muted. P022 guarantees a host-audio gate recovery path
  and reports the original exception.

- **Startup timeout too short**: The previous 90-second wall fallback
  could terminate autonomous startup before the user's historically
  slow original boot completed. The safety fallback is now **300 s
  wall time** or **240 virtual original seconds**, whichever occurs
  first. Falling back NEVER claims first-Pxx readiness.

The original Z80 machine, sample RAM, DAC/SSM audio, original DISK7
recording, HDD writes, firmware sample import, RAM bank, MIDI
playback and original controller timing remain unchanged.

## Verification

CI covers original delayed floppy PC threshold, distinction between
host MIDI and control messages, preboot buffer-pressure cap,
autonomous boot wall time, all P008–P021 source regressions,
native 900,000-clock genuine synthetic Z80/SAR/DRAM audio comparisons,
original firmware-state models, Windows VST3 build,
Steinberg Validator and real VST3 COM project state save/reopen.

**Private original-ROM/main23.bin HDD-first power-up, first-Pxx wall time,
real studio audio after Pxx, actual Studio One offline bounce and complete
DAW project recall remain unverified.** No private copyrighted E-mu
resources are redistributed.

PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/20
