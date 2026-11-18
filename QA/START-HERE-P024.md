# P024 – Original Emulator II fully playable firmware state

**Development Windows VST3; not final Studio One acceptance.**

A REAL private original E-mu Emulator II ROM and the owner's original Choir
disk were executed in a separate controlled Linux test environment.

- The original LCD first displayed `P01 EII` after **49.01 s wall**
  (44.31 s simulated 4 MHz hardware time).
- The original SCN2651 MIDI receiver was NOT YET enabled at first P01.
- It enabled a moment later at `P01 EII Choir` (49.02 s wall,
  44.33 original virtual seconds). Firmware NoteOn 60 / NoteOff 60 then
  produced genuine original 48k PCM: 143,077 nonzero frames, 6 MIDI bytes
  read and no UART overruns. The private test exited successfully.

**Original private ROM, OS and instrument floppy are not in GitHub.**

## Fixed in P024

P021/P022 previously treated the first Pxx display as full playability.
P024 requires **both original Pxx and the actual firmware's MIDI UART
enabled state** before:
1. Releasing the DAW host-audio silence gate and re-anchoring audio/MIDI.
2. Sending a queued restored program change into the original SCN2651.
3. Freezing the "firmware ready" boot stopwatch in Status.

This is an actual original hardware condition, NOT a hardcoded delay or
a fake instant preset. It prevents lost first program changes and
premature note-ons while preserving the original full 4 MHz firmware
clock, HDD-first floppy handling and original DRAM/PCM sound.

Automated tests check the observed Pxx-without-UART case, UART-without-Pxx,
first fully ready state and original VST3 source injection. The real Windows
VST3 build, Steinberg Validator, real COM/IBStream bank+HDD save/reopen
tests and earlier P008–P022 regressions run in CI.

**Still open before the final Studio One test:** actual Windows plugin
boot against owner's original ROM/OS, host audio onset after this exact
handoff, save/reopen under Studio One, multiple instances, latency and
performance at real project load. The private Linux bench verifies
original firmware+PCM only, not Windows VST3 playback.

Research bench: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/21
Product fix: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/22
