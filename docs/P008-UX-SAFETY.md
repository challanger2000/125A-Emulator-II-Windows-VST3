# P008 — Safe project recall and automatic protected OS disk for Import WAV

Implementation after source-pinned P006/P007 overlays. This is a host-side policy modification only; original firmware, disk controller, SAR, analog audio and original ROM/OS images remain unchanged.

## Confirmed original P007 bug

The manual `Eject floppy` path erased `embeddedBank_` and `projectMedia_`, even though the original EII retains all voices in sample RAM. A user could successfully import a WAV, eject its virtual diskette, save the Studio One project and receive a project state with settings but no committed soundbank. P008 preserves a successfully committed embedded bank on Eject and when selecting the known OS image. Insertion of a DIFFERENT soundbank clears a stale snapshot (the machine may subsequently load a different performance), so the host will not silently serialize the wrong soundbank. Later work must support saving arbitrary manual disk-bank switches with original DISK7 for project recall.

## Automatic WAV import

If no floppy is present, or if the inserted disk is read-only (.EII), HFE, or direct-write, the importer takes the bundled OS3.1 from `settings_.osImage`, validates it, allocates a **private in-memory writable** `.emuiifd`, and mounts it into the running original machine before the hardware SAMPLE operation. The previously mounted disk backing is retained without mutation. Firmware SAMPLE/FORCE/STOP and original DISK7 SAVE BANK run unmodified; after SAVE BANK completes, the previously selected floppy is automatically restored or, if no floppy was mounted, the drive is ejected. The selected `settings_.floppy` is intentionally never replaced by the temporary OS path. If a failed recording leaves the firmware in a non-Pxx state, the automatic OS remains inserted so the plugin does not hot-swap during an active firmware operation; recovery may require returning to Pxx or resetting. A dirty or busy existing floppy is not silently discarded.

## Tests and limits

`tools/apply-ux-safety.py --verify` proves exact source-pinned anchors. `tests/p008_source_acceptance.py` checks policy application and ordering. Real Windows VST3 compilation, Steinberg validator, host IBStream state tests run on GitHub Actions; genuine OS-backed Studio One Save/Eject/Close/Reopen must be tested by the owner. No original ROM/OS/user bank may be uploaded to public CI. This is a non-release development candidate.

Other P008 audit items pending: configurable WAV root note C3/MIDI60 using original firmware editing, safe cancellation mid-SAMPLE, HDD formatting/setup wizard, boot/progress reporting, manual bank-switch project state, performance optimization.