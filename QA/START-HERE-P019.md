# P019 — Original Emulator II boot CPU scheduling optimization

**Windows x64 VST3 development build. NOT READY for final Studio One acceptance.**

## Improvement

The machine-owner scheduler previously entered the original emulation core
every 5 ms (ordinary mono/basic model) or 6 ms (SSM/CEM audio worker)
during firmware startup. The developer's existing performance measurements
at 1 ms scheduling showed substantial per-entry overhead.

P019 uses **15 ms (basic)** or **12 ms (worker)** batches while the
original 4 MHz machine has not reached its first playable **Pxx**
display. This reduces unnecessary repeated C++ owner-thread
Machine::run() calls. **No original CPU, scanner, RAM, sample, ROM/OS,
HDD, MIDI, analog filter or hardware tick is skipped.**

The normal 5/6 ms schedule resumes permanently once the firmware reaches
Pxx. The original fine 1/2 ms urgent-audio scheduler still takes
precedence. WAV sampling, SAVE BANK, project-state operations and any
user panel press also disable the larger batching. MIDI note and
automation events still cut the quantum at their exact scheduled tick.

## What this does NOT promise

This is a **CPU scheduling optimization**, not a firmware disk/boot
shortcut, precalculated ROM snapshot, or faster virtual Z80 clock.
Original hardware boot may still need the same emulated clock duration.
Any actual end-to-end reduction in **wall-clock** boot time must be
measured with the user's licensed original ROM/OS; the synthetic
unit tests only establish the reduced number of C++ machine-owner
calls and tick/MIDI schedule fidelity.

## CI acceptance

- C++23 model tests: 48,000,000 exact original 4 MHz CPU clocks,
  nine odd-position MIDI event boundaries, reduced machine call counts,
  DSP block alignment, urgent audio and protected import guards.
- Source-pinned overlay and regression tests P008-P018.
- Real Windows VST3 build, Steinberg Validator 47 tests,
  actual VST3 COM/IBStream bank/HDD/C3 state tests.
- Original firmware content is NOT included in the bundle.

Still outstanding before a finished release: licensed original
ROM/OS boot and audio tests, actual Studio One project reopen
and export, load-time measurements, and final UI/UX optimization.

PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/17
