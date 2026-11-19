# 125A E-MU Emulator II — Windows VST3

**Original emulator software: [Tuth / eii-emu](https://github.com/Tuth/eii-emu).** Tuth initiated and maintains the underlying hardware-level Emulator II emulator. This repository supplies a **125A Windows VST3 adaptation** of that project; it is not an official E-mu product. See [CREDITS.md](CREDITS.md) for the original developer and all upstream contributors.

## Public P048 release candidate and private P047 delivery (19 November 2026)

**P048 (public):** Windows x64 release-candidate package **without proprietary ROM/OS files**, paired with a complete corresponding-source ZIP, code diff, SHA-256 manifest and original developer credits. See [release notes](RELEASE-NOTES-P048.md), [installation](INSTALL-PUBLIC.md), [change log](CHANGELOG.md) and [source provenance](RELEASE-SOURCE-TRACEABILITY.md). The previously delivered P047 **private** owner ZIP is separate and is not a public downloadable artifact.

**P047 (private owner package):**

- **User-facing product name:** `E-MU Emulator II.vst3` for both the outer Windows bundle and `Contents/x86_64-win/` PE module; the VST3 host sees **E-MU Emulator II**. The pre-existing VST3 processor UID was preserved.
- **Original Emulator II signal path by default:** SSM2045 filter, native AM6072 DAC stage and S3528 reconstruction. The optional Emulator III CEM3387 Custom path is **not** the default.
- **Private owner-specific bundle:** original ROMs and Emulator II OS 3.1 live inside `Contents/Resources/ROM` and `Contents/Resources/OS`; no Choir or Factory bank. Firmware is not committed to this public repository.
- **Confirmed automated evidence:** Windows x64 renamed VST3 physical COM-host load, factory/display-name and state checks, and **47/47 Steinberg validator tests** in [GitHub Actions run 44571195085](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/actions/runs/44571195085). Relevant native/Linux CI also passed.
- **Separate acceptance still outstanding:** installing, booting with the owner's proprietary ROM/OS and playing/saving a project in **Studio One** from the final renamed private package. COM host and synthetic tests do *not* prove this last step.

See [P047 packaging/identity acceptance](QA/P047-VST3-PRODUCT-NAME-AND-INSTALLATION.md) for the exact bundle tree, hashes, and tests. The P047 owner ZIP was assembled separately and is **not** a public GitHub Actions artifact.

## Installation and engineering

For the existing **private owner package**, close Studio One and copy the entire `E-MU Emulator II.vst3` folder into the configured Windows VST3 directory. Do not install the former `EmulatorII-Custom.vst3` package alongside it; the processor identity overlaps. A rename is not a new instrument or new preset format.

For a **source build**, recursively check out `upstream/eii-emu` at the pinned commit `e345bcf00af8a066ebace9168cf0b6c3a40ca164`. Build-time source overlays and Windows CI are in `tools/` and `.github/workflows/wav-bridge-qa.yml`. The local-only packager `tools/Package-Private-Emulator-II.ps1` accepts the owner's original firmware and must never be run as a public release upload. The build uses the original emulator engine; it does not require a separate emulation host at runtime.

This adaptation also contains prior MIDI, WAV import, original firmware recording/SAVE BANK and project-state work. Those development stages and their narrower test claims are documented in `docs/` and `QA/`. Historical README text is preserved in [docs/README-HISTORY-P004-P008.md](docs/README-HISTORY-P004-P008.md); it is not the current completion status.

## Credits and licence

**Original developer/project creator: [Tuth](https://github.com/Tuth)** — original code and project leadership. Upstream credits also name ChatGPT/Codex, Claude Code and credited third-party components. Full attribution: [CREDITS.md](CREDITS.md), upstream [CONTRIBUTORS.md](https://github.com/Tuth/eii-emu/blob/main/CONTRIBUTORS.md).

The covered software is **GPL-3.0** (see [LICENSE](LICENSE)), with applicable third-party notices. Original E-mu firmware, operating-system disks and soundbanks are proprietary owner-supplied media, not public-source dependencies. The project is independent of and not endorsed by E-mu Systems.
