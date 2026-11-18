# P004a: portable original-bank project-state codec

**Status: native binary codec and negative tests ONLY, not integrated into VST3 project save/restore yet.**

Actual original EII firmware DISK 7 SAVE BANK was demonstrated with private ROMs and a protected working disk: 137 track writes, zero write errors. The saved full 573440-byte EMUIIFD was loaded by a **fresh** EII machine, restoring MIDI note 48 at 439.99 Hz (peak 0.131153, RMS 0.077740); local PASS. User-owned ROM and OS media remain private and untracked.

P004 codec packs the unmodified original EIIVST3 1 settings plus exactly one original-sized disk image into a compact binary IBStream envelope. Original plain states remain byte-identical. V1 binary format uses 16-byte magic, little-endian lengths, 64-bit FNV-1a *accidental-corruption* checksum, original settings bytes and original 573440 disk bytes. Total length is under 1 MiB; no file paths or external media are required for the **embedded data**. FNV is not security authentication.

Native regression tests cover legacy compatibility, 573440-byte lossless round trip, incorrect lengths, altered content, truncation, trailing bytes, foreign settings and separate independent banks.

**Remaining P004b:** wire original-firmware SAVE BANK to a machine-owner immutable snapshot, surface this to IComponent::getState, and make IComponent::setState parse/check settings+media before any mutation and boot the saved media in a new machine. Failure must preserve the previous instance. Tests must verify full VST3 host save/restore and MIDI48 audio, and Studio One only at final owner gate. Codec testing alone does not certify recall.
