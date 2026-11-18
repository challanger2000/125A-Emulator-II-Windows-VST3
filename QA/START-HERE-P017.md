# P017 — Portable original Emulator II HDD in Studio One song

**Development VST3 only. Original ROM/OS integration and Studio One acceptance still outstanding.**

Unlike earlier versions, a successfully snapshotted original HDD is now
embedded in the VST3 project state. The 20-MB EII HDD stores **22,597,632
bytes**. P017 compresses repetitive regions without adding external runtime
dependencies; the original bytes, bank directory and sample data remain
unchanged. Songs with attached HDDs can restore the exact saved disk
without needing its original file path, including on another Windows
installation with the user's compatible original main23.bin ROM.

**Song save:** The VST3 host requests an original HDD snapshot on the single
emulated-machine owner thread, only when disk operations are idle. A
bounded two-second wait keeps the DAW from hanging indefinitely. If the
HDD cannot be captured, the state still saves the last committed image
plus persistent **hddpending=1** warning; this is NOT a completed snapshot.
Wait for disk activity to stop and save the song again. No direct writes
to the original user HDD file occur on restore.

**Song reopen:** The state is fully validated before use; the selected
HDD image is reconstructed in memory before the original firmware boots.
HDD-containing projects use original main23.bin and original HDD access,
not a sample-player shortcut. The existing original DISK7 bank capture and
`bankpending=1` warning stay separate.

**Compatibility:** Old plain EIIVST3 settings, bank-only P004/P010 songs,
and P014 pending markers are retained. HDD images must be composed of
whole 512-byte sectors and no more than 32 MiB. Project state maximum
40 MiB, with no decompression beyond declared lengths. The system
contains no third-party compression library.

**Important:** Unlike the scrubbed floppy bank, a complete original HDD
may contain proprietary OS files. Do **not** distribute Studio One songs
containing a private original HDD or original E-mu content.

Automated CI tests synthetic 20-MB images, 46 bank-like regions,
random noncompressible sectors, corruption, missing/truncated data,
legacy state and real VST3 COM/IBStream multi-instance save/reopen.

Not yet verified: the actual original-ROM HDD song reopening and sound,
multi-bank HDD changes made by the firmware while host save begins,
Studio One save/close/reopen acceptance, actual HDD boot time, audio
latency and WAV C3 mapping.

Development PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/15
