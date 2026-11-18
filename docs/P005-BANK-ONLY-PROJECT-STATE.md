# P005 — Bank-only DAW project state (research)

The original hardware firmware SAVEBANK writes an entire 573440-byte disk image. The first 78848 bytes are the E-mu OS/system area, not user bank data. The P004 implementation stored this entire disk image in the DAW project. P005 changes that: codec serialization and machine-owner snapshot always erase the first 78848 bytes before producing a host state. The remaining 494592 sample/bank bytes are preserved exactly, without additional sample conversion.

At restore, an unmodified OS3.1 image selected by the user from the existing settings must be present. The owner merges the original system area with the embedded user-bank area into a purely in-memory floppy image. The DAW project neither embeds OS data nor requires an external runtime/helper program. Historical P004 full-media states continue to decode, and re-serialization strips their OS area. Bank offsets, binary framing and checksum remain compatible.

Acceptance gates: native codec round-trip, original VST3 host binary set/get state and two independent instances, strict errors for missing OS, private real-firmware capture and save with fresh engine boot and measured MIDI48 frequency, then Studio One at the final owner acceptance stage. P005 changes belong to a separate research branch and should not merge until acceptance passes.
