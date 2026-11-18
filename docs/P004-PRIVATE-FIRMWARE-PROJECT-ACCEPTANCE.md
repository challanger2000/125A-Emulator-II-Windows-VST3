# P004 — real original ROM and OS project-media end-to-end acceptance

Run date: 2026-11-18. Private original user-owned ROMs and EII OS 3.1 disk; no original firmware/OS/bank binaries uploaded to GitHub or CI. Source baseline: Tuth/eii-emu@e345bcf00af8a066ebace9168cf0b6c3a40ca164 with the source-pinned P001/P003/P004 125A build overlays; development head at source-test time 775691b7c1d34fa67816fbf6bd1b9a646800d63a.

## Independent preliminary source-level original disk save/reload

Original EII firmware booted with user ROM+OS3.1; the native hardware-emulated machine performed actual P003 WAV recording. A private **disposable protected performance-disk copy** (573440 bytes) was mounted. Original DISK -> option 7 SAVE BANK -> original YES (9) caused **137 successful write frames, 0 errors**, changing 415429 data bytes, returning to Disk [1-8] and then P01. The resulting bank image was saved under a new disposable test filename; source ROM/OS original unchanged.

A wholly NEW emulated original-firmware Machine booted from that saved image. MIDI 48 yielded **120000 frames, peak 0.131153, RMS 0.077740, measured 439.99 Hz**. Exit code 0. Separate original WAV capture and bank-save proofs were executed before integrated owner testing.

## Full P004 owner-engine to fresh owner-engine project-state test

A separate private Linux-native executable compiled the **actual P004 VST3 PluginEngine machine-owner source** (not a mock, no direct DRAM write, no guessed bank data); two independent PluginEngine instances were used sequentially. Using user ROMs and original OS3.1, with 48-kHz hardware audio processing and a generated 3-second 440-Hz WAV (peak0.4), the first engine:

1. Booted original EII OS3.1 to P01; no external floppy replacement was needed beyond selecting the owner's boot OS disk.
2. Invoked the actual P003/P004 one-command WAV routine. Original firmware showed Sample Armed; original hardware SAR recorded real 440-Hz input; firmware SAVE BANK controller automatically started after SAMPLE/FORCE/STOP and returned to P01.
3. P004 published the original **573440-byte** complete image after detecting final real disk writes and return to preset. Status reported 'Original EII recorded the WAV, saved full 573440-byte bank using DISK 7, and returned to Pxx.'
4. Host codec encoded original settings plus original bank in a compact **577066-byte** binary project-state blob, decoded it and compared the original bank bytes without loss.
5. DESTROYED the first engine and created a NEW PluginEngine. Loaded ONLY the decoded embedded bank + owner's original ROM directory using the engine's new restoreProjectBank path. Booted original OS3.1 from the **in-memory** embedded media and reached P01.
6. Sent original MIDI note 48. The new hardware engine rendered **143872 frames**, with **peak 0.131072, RMS 0.0857712, frequency 440.374 Hz**, 1173 positive crossings. Exit0 **PASS**.

All original ROM, OS, disk, private performance bank and executable probe data stayed in the private local model container; only this textual acceptance report is in GitHub.

## Independent Windows VST3 COM/Steinberg validation

- GitHub Actions 44284301455, source 3d87cbd9a790cc22fb16c81030e0db2f23cee2a8: actual Windows x64 VST3 compiled, all original engine/input tests PASS, official Steinberg Validator **47/47**. Actual loaded Windows VST3 host test of IComponent::setState/getState with 573440-byte embedded disk PASS, damage rejection (previous state stays), two isolated bank instances and legacy project compatibility PASS.
- GitHub Actions 44284743913, P004 source commit 775691b7c1d34fa67816fbf6bd1b9a646800d63a: Windows and native jobs PASS.
- GitHub Actions 44284744085: P004 source-only local firmware acceptance kit PASS; no original ROM or OS distributed.

## Release status / open gates

**P004 development acceptance: PASS** for private native original-ROM end-to-end firmware chain and independent Windows loaded-VST3 binary state host API. **NOT FINAL PRODUCT RELEASE**: Studio One actual GUI user acceptance, save/close/reopen in original user DAW, full 125A tester/realtime/multi-instance stress and packaging final audit remain open; they must not be inferred from source builds or native tests.
