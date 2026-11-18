# P007 — Original maximum duration for Import WAV

The original E-mu Emulator II+ OS3.1 Owner's Manual, Sample Module function 5 (Sample Length), specifies **17.6 seconds per performance bank**, shared among voices. The 1 MiB EII+ expansion provides two separately selectable 512-KiB banks, not one continuous 35-second recording. Existing voices consume memory. The sample timer actually runs at approximately 27,777.78 Hz, while the manual's quoted duration and sample count are rounded.

The former 10-second software limit is removed. P007 now accepts up to 17.6 seconds. The firmware still decides if enough RAM is available. Need More Room is rejected. If the original OS reports Sample is good before the waveform is complete (outside a 50-ms terminal tolerance), the importer rejects the incomplete WAV instead of silently committing it. A normal original full-bank auto-stop near the waveform end is accepted without pressing a redundant STOP. Neither mode fabricates a voice, bypasses the SAR nor erases samples.

Deterministic controller tests cover 12 seconds, 17.6 seconds, over-maximum input, premature full-RAM stop, and natural completion at capacity. The original 64-MiB input WAV file cap remains a separate safety guard. Windows Steinberg validator and full original ROM sample save/restore are separate acceptance requirements; Studio One remains the final host test. Menus say Import WAV... and Import abbrechen.

Sources: original E-mu Emulator II+ OS3.1 Owner's Manual (Sample 5, Preset Definition 20), plus Tuth/eii-emu/docs/MEMORY_1MB.md.