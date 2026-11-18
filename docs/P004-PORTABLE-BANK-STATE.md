# P004a: portable original-bank project-state codec

**Status: native binary codec and negative tests ONLY, not integrated into VST3 project save/restore yet.**

Actual original EII firmware DISK 7 SAVE BANK was demonstrated with private ROMs and a protected working disk: 137 track writes, zero write errors. The saved full 573440-byte EMUIIFD was loaded by a **fresh** EII machine, restoring MIDI note 48 at 439.99 Hz (peak 0.131153, RMS 0.077740); local PASS. User-owned ROM and OS media remain private and untracked.

P004 codec packs the unmodified original EIIVST3 1 settings plus exactly one original-sized disk image into a compact binary IBStream envelope. Original plain states remain byte-identical. V1 binary format uses 16-byte magic, little-endian lengths, 64-bit FNV-1a *accidental-corruption* checksum, original settings bytes and original 573440 disk bytes. Total length is under 1 MiB; no file paths or external media are required for the **embedded data**. FNV is not security authentication.

Native regression tests cover legacy compatibility, 573440-byte lossless round trip, incorrect lengths, altered content, truncation, trailing bytes, foreign settings and separate independent banks.

**Remaining P004b:** wire original-firmware SAVE BANK to a machine-owner immutable snapshot, surface this to IComponent::getState, and make IComponent::setState parse/check settings+media before any mutation and boot the saved media in a new machine. Failure must preserve the previous instance. Tests must verify full VST3 host save/restore and MIDI48 audio, and Studio One only at final owner gate. Codec testing alone does not certify recall.

## P004c original-firmware disk-save + binary embedded state (candidate)

The source-pinned local build overlay tools/apply-project-state.py adds original DISK 7 SAVE BANK button automation after WAV capture, waits for >=130 actual sector-track writes with no write errors, returns to Pxx and only then publishes immutable complete EMUIIFD media to the project-bank snapshot. Never writes to original external disk: requires a writable **protected copy** with direct image writes disabled. Failures leave the previously committed bank in the project-state cache.

The VST3 component now serializes its original settings and original-sized project media through the P004 binary envelope. Parsing and checksum precede state mutation; a fresh original EII machine boots embedded media using an in-memory backing, with no extracted temporary floppy, and original ROM paths still required. Project getState rejects calls while a firmware WAV/write transaction is in flight, preventing half-saved banks.

**Acceptance pending CI/actual fresh VST3 host:** source-pinned patch compilation, the factory IBStream state roundtrip, actual P004 save inside VST3 (previous private P004 save+fresh reload was executed at original native Machine level), and final Studio One project save/reopen. Treat all of these as OPEN until recorded separately.
