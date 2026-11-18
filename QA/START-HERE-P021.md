# P021 – Original EII boot without DAW audio callbacks

**Development-only Windows VST3. Not a verified release.**

## Implemented

During an original firmware startup, the VST3's single emulation owner
executes the genuine 4 MHz CPU, floppy/HDD, SAR, DRAM, Z80 and DSP clocks
without requiring any `process()` calls from Studio One. This allows
progress even when DAW playback is stopped or a project is loading.

The host audio callback returns **silence** during preboot instead of
mistakenly playing incomplete firmware audio. The machine still executes
every original hardware tick. Preboot DAW MIDI events are counted and
discarded, not replayed at the wrong musical time.

Only when the **real firmware shows a playable Pxx preset** does the
owner end preboot mode and atomically re-anchor the guest clock to the
current host sample index. Main/aux output ring buffers, interpolation,
host MIDI time, and SAR host-input time all use the new origin.
The original post-boot 4 MHz host-paced playback clock remains intact.

To prevent indefinitely hogging the DAW when original media/OS is
broken, there is a conservative fallback after **90 seconds of actual
wall time or 240 seconds of virtual firmware ticks**, whichever comes
first. This fallback is **not a success or fake Pxx**: Status displays
the warning and original hardware continues normally at host pace.

Settings → Status reports **AUTONOMOUS ORIGINAL 4MHz** while starting and
the number of MIDI events dropped before firmware readiness. No
separate emulator window, VM, firmware reimplementation or helper
program is required.

## What is and is not verified

Source, C++23 host-clock simulation, previous genuine synthetic
Z80/SAR/DRAM machine tests and real Windows VST3/Steinberg/COM
project-state regressions run in CI. The test sends **zero DAW
callbacks for 18 seconds of original hardware ticks**, then verifies
that subsequent MIDI, ADC and audio map to the correct new host base.
Original ROM/OS is never bundled.

An actual private original-ROM/HDD boot from power-on to the first Pxx
and real audio playback after the handoff still needs verified
end-to-end testing. We do NOT yet know the wall-clock startup time
improvement on the user's i9 Windows PC; it is limited by how fast the
original emulation can execute on that CPU. This is NOT an unconditional
instant boot, and offline bounce and multiple instances still require
final acceptance.

Earlier P017 portable HDD and P018 C3 host keyboard setting are
preserved, with no changes to original sample RAM or firmware.

PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/19
