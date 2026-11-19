# P038 — real original OS3.1 recording through host audio input (owner-private)

**Date:** 2026-11-19. **Status:** native PluginEngine original-ROM host-input capture / DISK7 / PCM: PASS. **Actual Windows VST3 COM genuine-ROM positive: NOT RUN / DEV.** Never combine these separate layers into a fabricated full Windows acceptance.

## Executed original hardware/firmware acceptance

- Genuine original E-mu ROMs supplied locally by owner; original OS3.1 floppy image used for original SAMPLE and DISK7.
- Booted original firmware at `P01 EII Choir`, machine tick 177,300,000.
- Input: **new 440 Hz sine, 0.25 peak, 48 kHz**, pushed as **real 512-frame host buffers** through production `PluginEngine::pushInput()` and `render()`, i.e. the actual host-input queue, not `wav::Source` and not direct DRAM injection.
- Physical emulated scanner contact sequence: SAMPLE → FORCE → STOP → exit to Pxx, actuated through existing PluginEngine button path.
- Original Z80/SAR: 35,237 recorded sample reads; **0 unknown bytes, 0 missing host-input frames, 0 host-input drops**. Total supplied input frames at completion 290,816.
- Original firmware returned to Pxx, followed by **original DISK 7 SAVE BANK** to a protected original OS3.1 in-memory working floppy. Bank-save controller reached completion with `wavSuccess=1`.
- Actual host PCM audition of the newly recorded RAM voice after DISK7: **36,649 nonzero samples**, peak **0.0864391**, sample-energy sum **174.699**, without a reported underrun.
- Private executable exit status **0**, printed `P038 ORIGINAL_FIRMWARE_HOST_INPUT_NATIVE: PASS`. Local run log `p038-live-O2.log`. Test source reproducible in `tests/p038_private_live_input_native.cpp`.

## Windows VST3 COM owner-local test prepared, but not yet executed with original ROM

The new source-pinned Windows test mode (`original-windows-live-record`) uses `IComponent`/`IAudioProcessor::process` and genuine original OS3.1 in a **Windows x64** VST3 factory. It feeds the production audio-input bus, actuates scanner contacts via a narrow private QA interface, checks original hardware reads and input loss, demands actual DISK7 saved bank in IBStream, measures 440 Hz PCM and repeats after a fresh original-firmware VST3 instance.

**Only the real owner-local execution with original media can turn this Windows gate to PASS.** Public CI exercises build, Steinberg validation, and no-media negative scanner-COM checks, never authentic ROM/OS. The Windows positive has **not** been performed in this Linux tool environment, which cannot run the Windows VST3 component as native Windows.

## Explicitly still open

- Positive Windows VST3 COM recording and fresh saved-project playback with genuine original ROM.
- Distinct host 44.1/96k original-firmware positive tests, silent/frequency-change negative live-input recordings through Windows VST3.
- Final Studio One/ASIO performance acceptance, physical original hardware calibration and filter accuracy.

**Original ROM/media remain local. No copyrighted bytes in GitHub. Project remains DEV.**
