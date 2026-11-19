# Change log — 125A E-MU Emulator II

This documents **modifications** to the original [Tuth/eii-emu](https://github.com/Tuth/eii-emu) emulator, rather than claiming authorship of Tuth's underlying software. The exact changed code and dates are traceable through the linked repository's commit history, its `src/`, `tools/apply-*.py` overlays, tests, and the reproducible build source archive.

## 2026-11-19 — P048: attribution, source traceability and public-release packaging

- Identified **Tuth** as original creator and maintainer; retained upstream ChatGPT/Codex, Claude Code, and third-party credits.
- Added an optional `About / credits...` settings-menu entry for the Windows VST3; no signal-processing, firmware, state-format or class-ID change.
- Replaced the obsolete P004 landing page with accurate P047/P048 build status and archived the former README.
- Added visible licence/source-origin information to private packaging and the **ROM-free public release candidate**.
- Added traceability documentation, an automated no-proprietary-media public packaging gate, and matching publicly distributable source bundle.

## 2026-11-19 — P047: consistent Windows VST3 product name

- Renamed the outer Windows VST3 folder and inner PE module to `E-MU Emulator II.vst3`.
- Updated the VST3 factory display class name to `E-MU Emulator II`.
- Kept original class ID/FUID, developer attribution in factory metadata and project state schema unchanged; no DSP/ROM modifications.
- Windows COM renamed-host validation, factory/state tests and Steinberg validator **47/47 PASS** recorded in [CI run 44571195085](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/actions/runs/44571195085).

## 2026-11-18–19 — Earlier 125A adaptation stages (P001–P046)

Earlier development was recorded as separate Git commits, source overlays, acceptance tests and QA documents rather than a single hand-edited fork. The user-facing changes addressed:

- Windows x64 VST3 packaging and loading original owner-provided ROM/OS media from module-relative paths.
- WAV host-input conversion via the **original emulator firmware** and SAR/DRAM path, bank saving and portable song-state handling.
- Autonomous original-ROM boot/timing; user bank, floppy and HDD safety; DAW note C3 mapping; original MIDI output.
- Windows VST3 lifecycle, original Emulator II SSM2045 filter as default, S3528 reconstruction, and native original-DAC route as default.
- Original-device integration and safety test coverage, including host tests, failures, and explicit blocked cases.

**Historic claims must be read with their exact QA evidence:** real Studio One boot and user-song recall of the **P048 public release candidate** have not yet been demonstrated. Upstream hardware-model accuracy limitations must not be represented as fully resolved by generic validator success.

## Source and original copyright

The primary/original implementation is **Tuth/eii-emu**, pinned for this adaptation at Git commit `e345bcf00af8a066ebace9168cf0b6c3a40ca164`. See [CREDITS.md](CREDITS.md), [RELEASE-SOURCE-TRACEABILITY.md](RELEASE-SOURCE-TRACEABILITY.md) and [LICENSE](LICENSE). GPL-3.0 notices and upstream third-party notices remain applicable.
