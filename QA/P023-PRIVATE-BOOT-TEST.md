# P023 – Local original-ROM boot/PCM acceptance (private test)

Research-only. The new `tests/p023_original_rom_boot_probe.cpp` compiles
on Linux using the real, unmodified Tuth EII machine source and does NOT
package or require the private original-ROM image in GitHub Actions.

The compiled test runner is available as a short-lived **Linux test
artifact only**, never installed beside the single Windows VST3.
With the owner-provided original `main.bin`, `scanner.bin`,
`ic135.bin`, `ic137.bin` and an original 573440-byte bootable
`.emuiifd` floppy located exclusively in a private local container:

- Power on the original emulated machine with the same deterministic
  DRAM/controller initialization and original 4 MHz clock as the VST3.
- Count REAL 4 MHz ticks and wall seconds, original floppy receive
  traffic, firmware LCD text and real first `Pxx` display (not a fake
  elapsed-time "success").
- If/when Pxx appears, send MIDI NoteOn/NoteOff 60 through the
  original SCN2651 and measure basic original controller/VCA sample
  output in memory, without exporting any copyrighted audio.
- A 240-second wall cap and 180-second virtual guest-clock cap prevent
  endless testing. Timeouts are explicit failures.
- This is a **real original-ROM firmware test**, not a Studio One
  project/load/transport test. It runs outside the final plugin and
  does not alone prove P021/P022 VST3 host-audio handoff.

The original ROM and private disk images are NOT committed, published,
or attached to this PR or to its CI artifact.

Dev branch: research/p023-private-original-rom-boot-20261118
