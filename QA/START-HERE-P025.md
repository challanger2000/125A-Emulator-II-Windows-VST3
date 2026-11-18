# P025 – Original Emulator II first audible audio THROUGH ACTUAL PLUGIN ENGINE

**Windows VST3 development test build, not a final Studio One release.**

The P023 private Choir test ran the original `Machine::run()` core, but it
did NOT execute the VST3's own `PluginEngine` start, audio silence gate,
guest-to-host clock re-anchor, offline block processing, event queue,
10-bus renderer and bank playback.

P025 adds a single QA-only Linux binary that includes the **same
fully patched P008–P024 plugin_engine.h** built by the Windows VST3.
The public CI runs it against a synthetic Z80 NOP ROM and exercises:

- Real original 4 MHz machine clock progress with **zero host process
  callbacks** while the real plugin owner is active.
- All 10 audio outputs (main stereo + 8 firmware individual outputs)
  stay strictly silent before a genuinely playable Pxx+SCN2651 state.
- MIDI before boot-ready is dropped, never sent at the wrong song time.
- The synthetic ROM never fakes success, Pxx or a playable preset.
- The binary is uploaded separately as a QA fixture; the final user
  installation remains one normal VST3.

The same standalone QA executable can be run **in the local private
environment only** with the previously recovered genuine
`main.bin/scanner.bin/ic135.bin/ic137.bin` and Choir OS floppy.
It then waits for actual first Pxx+UART while host callbacks remain
stopped, processes original NoteOn 60/NoteOff through the *plugin*
event queue and renders the DAW-side stereo audio buffers offline.
It reports genuine emitted PCM energy, underruns and wall clock.

No original ROMs, floppy images, private HDD files or extracted PCM are
uploaded to GitHub, public Actions, or public release packages.

A successful native full-engine test is **not** proof of Windows
Studio One compatibility. Windows x64 VST3 build, Steinberg 47 tests
and COM/IBStream tests run independently. Full Studio One project
save/reopen and real system latency still require final acceptance.

PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/23
