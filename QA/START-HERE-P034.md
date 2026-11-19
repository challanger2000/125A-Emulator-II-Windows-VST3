# P034 — Genuine Emulator II firmware MIDI OUT in Windows VST3

**Development, NOT FINAL.** Builds on P033 actual SCN2651 UART TX; this milestone connects the **original firmware-controlled outgoing MIDI** to one 16-channel VST3 event-output bus. It never echoes incoming host MIDI and never fabricates machine voice notes.

## Signal path

1. The authentic main Z80 firmware writes to SCN2651 I/O port 4.
2. The P033 UART shifts 8N1 at 31,250 baud: 1280 emulated 4MHz CPU ticks per character. Only physically completed characters are emitted, with firmware tick stamps.
3. The Machine owner forwards completed TX bytes to a bounded SPSC queue of 8192 bytes with epoch/generation and host-frame stamps. The host callback never accesses Machine, firmware, the filesystem, a mutex or the heap.
4. The host callback assembles valid outgoing channel messages including running status. MIDI realtime bytes may interleave without disrupting the parser.
5. Host VST3 outputEvents can receive NoteOn, NoteOff, PolyPressure and LegacyMIDICCOut messages for CC/ProgramChange/ChannelPressure/PitchBend. NoteOn with velocity zero is delivered as NoteOff. The output bus is named Original MIDI Out.
6. The original host audio latency and firmware CPU-to-host clock mapping determine bounded event sample offsets. Invalid old activation / boot generations are never replayed into a newly opened song.

No external MIDI program, driver or helper executable is a VST3 runtime dependency.

## Safety

- Unbooted/autonomous-boot MIDI is discarded. Boot/restart invalidates unfinished MIDI messages.
- A missing VST3 host outputEvents list drains events rather than replaying stale MIDI later.
- Queue-full events are counted instead of blocking the realtime audio callback.
- No proprietary original ROM, floppy, audio bank or OEM binary is committed or uploaded.
- Original analog core, sample ROM and bank/HDD project encoding are unchanged by P034.

## Protocol limits

VST3 legacy output event lists are not a general-purpose raw MIDI 1.0 wire stream. Unsupported system common, MIDI realtime, SysEx and malformed channel data are **not** fabricated as valid musical notes; system signals are still a separate original-hardware acceptance requirement. This milestone is not a full electrical TX/RX, SysEx or DIN MIDI-output emulation claim.

## Evidence

Native parser tests cover running status, NoteOn/Off, CC, program, pressure, 14-bit bend, interleaved realtime, SysEx, invalid data and reset, with ASan/UBSan. Windows tests compile and execute the same parser, and a **real Windows factory/COM** test inspects the exported output bus and confirms a nonbooted emulator cannot echo received host notes. Existing Steinberg and full product regressions must pass.

**Still NOT RUN:** authentic original-ROM and disk producing a nontrivial output MIDI sequence in the real Windows VST3; independent MIDI OUT timing at different DAW buffer sizes; actual Studio One MIDI OUT routing; physical EII DIN loopback; full raw MIDI system messages.

## Open overall emulator tasks

Finish original SSM2045/S3528 analog calibration and switched-capacitor/deglitch fidelity; complete record/SAR hardware; audit and correct LED fidelity in existing scanner latches and panel renderer; close full MIDI OUT system-message and electrical timing gaps; eventually run original Windows ROM/Choir, Studio One, real-time, project recall and 125A QA Tester final acceptance.

Only the P034 **channel voice VST3 bridge** can be accepted from its CI tests. This is not completion of the Emulator II project.
