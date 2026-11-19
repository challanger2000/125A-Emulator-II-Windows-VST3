# P035 — Genuine 4 MHz Z80 → SCN2651 MIDI OUT positive hardware test

## Purpose and scope

Prior P033/P034 tests proved register-level UART TX and the real Windows VST3's output-event bus independently, but their product COM test was deliberately negative (no firmware → no fake output). P035 adds a **positive end-to-end CPU/hardware/channel-message proof** that the earlier milestones lacked.

The regression builds the **actual patched Machine, Z80 core, original I/O decoder and UART transmitter** and executes a tiny clean-room synthetic 8 KiB Z80 test program. The bytes originate solely from Z80 instructions `IN A,(1)` (SR0 ready), `OUT (6),A` (serial mode), `OUT (7),A` (TxEN/RxEN) and `OUT (4),A` (send). No external ROM, floppy, copyrighted firmware, fake voice allocation, test-only product hooks or host MIDI echo.

The CPU writes 20 authentic MIDI TX bytes including NoteOn/NoteOff, running status, interleaved realtime F8, sustain, ProgramChange, pitch bend and velocity-zero NoteOn. The P033 hardware shifts at **31,250 baud**, and the P034 channel parser must recover exactly seven channel messages, without interpreting realtime as a musical note.

## Adversarial gates

- Two independent scheduler conditions: one `Machine::run(130000)` call and many varying 1/47/123/307/4000-tick calls.
- Every original UART completion **byte and exact 4 MHz CPU tick** must be identical across those two runs. A CPU slicing/timing bug must fail, not simply produce a nonempty message count.
- The completed bytes must be at least 1280 CPU ticks apart (10 bits at 31,250 baud), and all 20 must arrive with no UART write rejection or completed-byte overflow.
- In an independent original Z80 program setting the same serial mode but **TxEN disabled**, 20 actual `OUT (4),A` instructions must create **zero outgoing UART bytes**. They still appear in the legacy diagnostic trace; this catches accidental faked TX from the old debug string.
- Synthesized code is only used as **test program bytes**. The actual emulation core is never modified or short-circuited.

## Product acceptance boundaries

This is a real original Z80/SCN2651 hardware positive test on the actual patched core, **not** a complete original Emu ROM/Choir positive test. It does not demonstrate original firmware emitting MIDI OUT with an actual bank or a DAW consuming the outgoing events. The P034 real Windows VST3 COM probe remains a no-fake-output negative test; both gates must be retained.

Native C++23 positive run and existing P033/P034 native+Windows, Windows VST3, Steinberg validator and original-ROM local-only acceptance kits are mandatory. No original ROM, sample, HDD or private OS image enters CI.

**Open:** Positive actual original ROM/Choir Windows VST3 audio+MIDI OUT evidence, Studio One MIDI routing, hardware DIN timing/electrical tests, remaining SysEx/system MIDI, and analog filter/recording/SAR calibration. The whole Emulator II project remains NOT FINAL.

## P035 additional production defect corrected: MIDI OUT overflow ghost notes

P034's 8192-byte owner→host SPSC queue originally counted dropped bytes but **did not invalidate partial MIDI channel messages**. If the host stalled long enough to overflow the byte queue during a NoteOn, surviving bytes before the gap and resumed bytes after it could join into an unintended NoteOn/CC event. A superficially correct MIDI parser unit test could not detect this.

The P035 production patch now remembers on the **owner thread** that one or more SCN2651 byte pushes were dropped. Its first subsequently accepted byte carries a tiny `gap` flag with the ordinary original UART time/epoch/generation stamp. The **host audio consumer resets its own parser only when it actually reaches that marked byte**. Therefore legitimate queued messages before the overflow remain valid, and bytes after an information loss cannot complete a stale running-status or incomplete note. Fresh status messages immediately recover. The pending gap is also cleared during guest reboot; normal epoch/generation resets remain in force.

A four-slot version of the same bounded SPSC primitive deliberately overflows, drops two real byte values, drains the intact earlier note, confirms the first resumed data byte is orphaned instead of creating a phantom note, and then completes new original messages. Linux O2 and ASan/UBSan, a native source insertion adversarial test, and a real Windows UCRT binary test are required. The fix remains allocation-free and lock-free on the DAW audio callback; no firmware/audio core changes and no false claim of original-ROM transmission.
