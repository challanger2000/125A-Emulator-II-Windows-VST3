# Source provenance and GPL-3.0 release traceability

**125A modification date:** 19 November 2026 (P047/P048). The software is a modified adaptation of [Tuth/eii-emu](https://github.com/Tuth/eii-emu), **original creator/maintainer: Tuth**. This is not an official E-mu Systems release.

## Precisely identified starting point

- Original source: [Tuth/eii-emu](https://github.com/Tuth/eii-emu).
- Pinned upstream Git commit: `e345bcf00af8a066ebace9168cf0b6c3a40ca164`.
- Pin is held by the `upstream/eii-emu` Git submodule and checked in build-time patch scripts. Never replace the pinned source silently.
- 125A source repository: [challanger2000/125A-Emulator-II-Windows-VST3](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3). The public source tree includes `src/`, `tools/`, `tests/`, `QA/`, `docs/` and `.github/workflows/`.

## What has been changed and where

| Area | Traceable 125A changes | Implementation and proof |
| --- | --- | --- |
| VST3 name and preserved class identity | P047 renames visible factory class, outer directory and Windows PE without changing FUID | `tools/apply-p047-eii-display-name.py`, `tests/p047_eii_name_source_acceptance.py`, `QA/P047-VST3-PRODUCT-NAME-AND-INSTALLATION.md` |
| Author attribution | P048 About/credits command, licence and origin notices | `tools/apply-p048-eii-credits-menu.py`, `tests/p048_credits_source_acceptance.py`, `CREDITS.md` |
| Original EII filter/audio defaults | P028/P032/P045 original SSM2045, S3528, native DAC and state/override rules | `tools/apply-p028-eii-default.py`, `tools/apply-p032-s3528-production-default.py`, `tools/apply-p045-native-dac-default.py` and relevant tests |
| Host MIDI, boot, recording and saved state | Earlier P001–P046 modifications | `src/125a_*.h`, `tools/apply-*.py`, `tests/`, `QA/`, `docs/` |
| Proprietary media loading | Module-relative ROM and OS discovery; private owner-only packager | `src/125a_bundle_resources.h`, `tools/apply-bundled-resources.py`, `tools/Package-Private-Emulator-II.ps1` |
| Public binary and Corresponding Source | P048 packs only tested ROM-free named binary + notices, and creates same-run full source archive and SHA256 record | `tools/package-public-release.py`, `.github/workflows/wav-bridge-qa.yml` |

**Build sequence is not just a list of patches:** the executable, deterministic application order, compiler/toolchain selection and validation commands are in `.github/workflows/wav-bridge-qa.yml`. Every `apply-*.py` script is distributed alongside the source, and upstream modified source files are also included in the public source bundle.

## Publicly publishable artifacts

1. `125A-E-MU-Emulator-II-P048-PUBLIC-VST3-NO-ROM.zip`: Windows x64 installable plugin with original developer/third-party credits, GPL licence, installation and source instructions. **No ROM, no OS or sample banks.**
2. `125A-E-MU-Emulator-II-P048-CORRESPONDING-SOURCE.zip`: original pinned upstream files plus applied 125A source modifications, all build tools, tests, vendor licence notices, change log and provenance documents from the **same CI checkout** as the binary.
3. `SHA256SUMS.txt`: hashes of the two ZIP files produced in the same job.

Keep both ZIPs together with the GitHub Release so recipients can obtain the complete source associated with the binary. GitHub's automatic default source ZIP *alone* may not contain the recursive Git submodule or applied source overlays.

## Important licence and distribution rules

The emulator and covered derivative source are GPL-3.0. Retain previous copyright/licence notices; clearly mark modification and date; provide Corresponding Source and build scripts under the applicable GPL terms when distributing the executable. Individual third-party components retain their upstream notices.

E-mu ROMs, OS disks and sample banks are **not provided by the GPL** and must not enter any public binary or source release. They must be supplied separately by a user with the requisite rights. The existing owner-only private ZIP is **not** the public release artifact.

The name E-MU describes the emulated instrument; the software is not affiliated with E-mu Systems. A successful Windows COM host/47 Steinberg test does not prove real Studio One/owner-firmware behavior. Until the latter is tested, label a public download a **release candidate**, not a fully DAW-validated final release.
