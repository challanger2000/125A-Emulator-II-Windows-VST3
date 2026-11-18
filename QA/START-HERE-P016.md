# P016 – Bounded silence recovery after long host stalls

**Development VST3, NOT ready for Studio One acceptance.** No original
E-mu ROM, OS, HDD or user banks in the public build.

## Implemented
The plugin's 48 kHz main audio ring stores 131,072 frames (about 2.73 s).
Before P016, a host stall / rebase that required several minutes of silence
made the owner loop over **every** virtual missing frame, although only the
physically stored ring cells can ever be read. The individual jack-output
ring had an equivalent potentially unbounded gap-fill loop.

P016 bounds each silent fill to **at most 131,072 slots**, but still
advances the stream's absolute written-frame index by the entire original
gap. All main, stereo and 8 auxiliary channel values are zero for the
retained part of the silence, and first subsequent nonzero audio keeps its
exact stream index. The original EII CPU, Z80, ROM/OS, sample-RAM, MIDI,
filter and SSM2045/CEM DSP are untouched.

Tests use a synthetic **180 s callback interruption**, shorter silences,
a full/unread ring, resuming nonzero stereo and individual outputs. The
Windows VST3 build, Steinberg Validator and real VST3 project state host
probes run in CI, as do earlier P008-P015 regressions.

## Important scope limit
**This is faster recovery after a stalled host, not yet Turbo Boot.**
An original EII boot itself must still execute all 4 MHz ticks. Merely
increasing the CPU clock or skipping original disk times would change
emulation and is explicitly not done here. Safe boot acceleration requires
careful host MIDI, DSP ring, ADC and project-epoch synchronization with
original-ROM firmware tests before being enabled.

Other open work: HDD portable project recall, C2/C3 WAV root mapping,
real original-ROM capture/saved-bank checks, and Studio One performance
and offline bounce testing.

PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/14
