# P027 – Genuine original-ROM restart and repeat-playback integrity

**Development only – one Windows VST3. Not final Studio One acceptance.**

P025 privately verified a real original-ROM/Choir floppy boots in the
actual patched Linux-built `PluginEngine` without DAW callbacks and
produces 166,085 nonzero PCM frames when host offline playback begins.
P026 independently verified real Windows COM audio callbacks with two
instances, bad ROM fault isolation, teardown and 47/47 Steinberg tests.

P027 closes a different gap: **rebooting the same VST3 after it already
rendered authentic original MIDI/PCM**. That can expose stale ring
buffers, incorrect host sample anchors, stuck MIDI and dirty floppy
state.

The private QA test, using licensed original firmware/floppy only in a
private local container, now:

1. Boots the actual source-pinned `PluginEngine` to fully original
   Pxx + enabled SCN2651 UART; no host audio callbacks during boot.
2. Plays original Choir MIDI NoteOn/NoteOff through the actual host
   MIDI queue and offline audio renderer and measures PCM amplitude.
3. Reboots the **same** engine with the same original hardware and
   Choir floppy, after it has already generated host audio.
4. Asserts that main stereo and 8 aux outputs remain silent during
   the new boot; queues an early MIDI NoteOn and checks it is dropped.
5. Waits for a real second Pxx+UART, not a fixed timer; checks
   original 4MHz clocks actually run during the reboot.
6. Plays another genuine original MIDI note through the same audio
   callback path and compares active PCM, peak, energy and underruns
   to the first performance.

No private firmware, floppy or original audio enters GitHub Actions,
the Windows VST3 bundle, or any uploaded executable. Public Linux CI
builds the real patched engine and tests invalid synthetic ROM fail
closed; Windows CI keeps the full dual-instance/Steinberg/COM checks.
Only a private local execution can prove steps 1–6 with original ROM.

This test does **not** equal a Windows Studio One host-reopen/song-restore
test, which is still a separate final acceptance requirement.

PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/25
