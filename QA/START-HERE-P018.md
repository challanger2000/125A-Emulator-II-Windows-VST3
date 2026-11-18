# P018 — Studio One C3 WAV keyboard position (development)

**Development build only; do not replace your working VST3.**

## Why
The P003 original-firmware WAV importer produced a new voice played from
original EII MIDI note 48. For Studio One users placing the imported sound
on **C3 / MIDI note 60**, this was twelve semitones away on the host
keyboard. Studio One note *labels* can differ with the DAW octave setting;
**MIDI note numbers are authoritative** here.

## What changed
When the user selects **125A: Import WAV**, the plugin enables a
**per-project host keyboard setting**: incoming MIDI 60 is sent to the
original Emulator II as MIDI 48, and other notes are offset by -12.
The original EII firmware, SAR capture, sample bytes, sample-rate
calculation, voice pitch tables, sound bank and DRAM are **unchanged**.

In Settings, **WAV keyboard C3 (MIDI 60 → EII MIDI 48)** is checked.
Uncheck it for the original, untransposed MIDI note mapping. Songs saved
before P018 default to the original mapping. P018 states persist the
mapping through Studio One project save and reopen.

The mapping preserves per-channel note-on/note-off pairs even when
the setting changes while a key is held. CC120/123 panic and reboot
clear tracking. Out-of-range notes are dropped, not clamped to an
incorrect pitch. MIDI program changes, controllers, sustain and pitch
bend pass through unchanged.

## Automated tests
- Native C++23 note-pair/channel/retrigger/velocity-zero/CC panic tests.
- Saved project state, legacy byte compatibility, corrupt C3 flag rejection.
- Windows x64 real VST3 build, Steinberg validator, real COM/IBStream host
  save+reload with a bank and portable HDD, plus earlier P008–P017 tests.

**Important:** C3 is a host MIDI assignment, **not a claim that the
original EII OS internally retuned the sample**. The real private
original-ROM C3 audition in Studio One remains part of final acceptance.

Further work: boot speed, actual original ROM/OS imported WAV pitch and
song audio recall verification, HDD write concurrency, long-running CPU
and latency tests, and the streamlined user interface.

PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/16
