# P020 – Original Emulator II boot: actual wall clock and DAW clock diagnostics

**Developer build. Not yet final, and not yet original-ROM / Studio One accepted.**

P019 improved the machine owner's dispatch overhead, but this was **not**
proof of any reduction in the actual original EII boot time. In the
original VST3 engine, firmware CPU execution is paced by the **DAW's
audio sample counter**. When the host suspends process() callbacks while
stopped or an instance is sleeping, the emulated CPU may likewise stop.
More C++ batching alone cannot fix a frozen DAW clock.

## New built-in measurements (Settings → Status)

- **Original firmware state**: booting / actual floppy or HDD data /
  stopped DAW audio clock / CPU behind active host clock / ready Pxx /
  original emulator halted.
- **Wall-clock seconds** since the current cold boot started.
- **Emulated firmware seconds** (real Z80/hardware 4-MHz ticks).
- **Effective speed (%)** = original virtual firmware seconds divided by
  measured wall seconds. It is not guessed from a ROM delay constant.
- **Time with no host audio clock / no original CPU progress**, and
  actual floppy/HDD bytes received during the same boot.
- **True finish condition:** original LCD displays playable Pxx, never
  a synthetic timeout or mere disk mount. The measured time-to-Pxx
  freezes when reached.

The instrument keeps all original CPU, MIDI, SSM/CEM audio worker,
ADC/SAR, HDD, sample memory and 48 kHz playback behavior intact. No
separate VM, accelerator binary or additional VST3 has been added.

## Automated checks

- C++ clock-state tests for real time, floppy/HDD bytes, DAW suspended,
  CPU lagging active DAW, recovery, actual first Pxx and halt.
- Native 900,000-cycle synthetic Z80/SAR/DRAM hardware execution in
  old 20k/24k and P019 60k/48k batches. Prints actual wall-time
  throughput for each, with bit-identical hardware tests retained.
  GitHub runner timing is informative, **not the user's real boot
  speed** and not a pass/fail time guarantee.
- Windows x64 VST3 build, Steinberg Validator, real COM/IBStream song
  state tests, earlier P008–P019 regression tests.

## Still open

A real wall-clock ROM/OS baseline and an effective solution for a DAW
that suspends audio callbacks. The next performance phase needs to
decouple original firmware boot from host audio time safely or build a
validated original-hardware checkpoint. It must preserve synchronized
host MIDI events, output audio and all song state; **do not substitute a
faster emulated CPU clock or omit ROM disk operations blindly**.

Full private original-firmware test and final Studio One save/play/reopen
are NOT yet complete.

Development PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/18
