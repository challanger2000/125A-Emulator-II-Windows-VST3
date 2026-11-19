# P033 — Genuine original SCN2651 MIDI transmitter (hardware layer)

**Development only.** This milestone adds the formerly missing genuine Z80 `OUT 4` → SCN2651 transmitter hardware path to the pinned Emulator-II core. It does **not** claim to complete DAW/WinMM MIDI OUT. One VST3 remains the end product; no additional runtime applications.

## Verified primary references

Philips SCN2651, 1994-04-27, register tables and transmitter text:
- https://www.alldatasheet.es/html-pdf/19126/PHILIPS/SCN2651CC1N28/1537/6/SCN2651CC1N28.html
- https://www.alldatasheet.es/html-pdf/19126/PHILIPS/SCN2651CC1N28/2051/8/SCN2651CC1N28.html
- https://www.alldatasheet.es/html-pdf/19126/PHILIPS/SCN2651CC1N28/2308/9/SCN2651CC1N28.html

Emulator-II service manual sheet 7-16 / MIDI input and output clock, original firmware register configuration MR1=4Eh, MR2=00h, CR=27h as recorded by upstream. Original transmitted bytes are emitted by *firmware* writes, not guessed from hosted incoming MIDI notes.

## Concrete hardware improvement

Before P033, the original Z80 OUT4 just appended unpaced bytes to a diagnostic string; SR0 TXRDY returned CR0 (TxEN) without checking any holding register. MIDI OUT could not model backpressure or transmission timing at all.

P033 introduces the SCN2651's two actual logical transmitter registers:
- An eight-bit transmit holding register (THR) and a separate shift register.
- Original TxEN from CR0, 8N1/external TxC mode, and transmit BREAK hold.
- **1280 Z80 CPU ticks per character** (10 bits × 4MHz/31250 baud), timestamped only when the shift completes.
- TXRDY SR0 true only if THR is available and TX is enabled. TXEMT SR2 true when *both* shift and holding registers are empty. Status remains compatible with original RX ready/error/DSR/DCD bits.
- TXEN disable completes an already transmitting character, and BREAK waits for the current character before holding the next.
- Non-8N1 diagnostic mode does not fabricate MIDI output. Prior generic UART diagnostic string remains unchanged.
- A bounded 512-completion ring preserves original completed bytes and CPU timestamps, with explicit rejection and overflow counters. Oldest completed *observation* is dropped only when this ring is full; it is not an unbounded TX FIFO.
- Original CPU `OUT 4` writes and original per-tick machine clock now drive this hardware model. No ROM patches, direct voice allocation, host-note shortcuts or standalone emulator runtime.

## Tests and negative controls

- Original register semantics, double-buffer, status, 1280-tick and 2×1280-tick deadlines, TxEN during active shift, BREAK/re-enable, malformed mode, one-byte-only completion, oldest-drop ring overflow, and independent RX: dedicated deterministic C++23 runtime test.
- Linux O2 + ASan/UBSan native; Windows LLVM-MinGW real x64 executable regression; full Windows VST3 core and Steinberg host checks retain their prior gates.
- Overlay preflight pins the upstream SHA; source contract ensures firmware `OUT4`, TX clock, diagnostic capture and the exact register status adapter exist. Duplicate/reordered source overlays fail preflight.
- No original licensed ROM/floppy needed for this synthetic hardware unit test. Real original firmware scheduling and VST3 outgoing MIDI events **are not tested** by a passing synthetic unit test.

## Remaining implementation

To obtain usable **MIDI OUT in Studio One**, a follow-up must connect the completed owner-thread SCN2651 byte stream to a bounded real-time host-output event bridge and expose a VST3 event-output bus with correct note/channel/controller semantics and timing. The host will not receive MIDI OUT until that is done. A hardware loopback comparison or real original MIDI sequence is still required.

The analog filter, recording/SAR, hardware noise/calibration, physical MIDI output pins and final Studio One verification remain separate OPEN items. The front-panel LED latches and VST3 vector rendering already exist; they should be audited for original behavior, not presented as absent source.
