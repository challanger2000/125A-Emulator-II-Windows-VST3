# P048 — E-MU Emulator II VST3 (public Windows x64 release candidate)

**Original emulator by Tuth:** https://github.com/Tuth/eii-emu  
**125A adaptation and full modified source:** https://github.com/challanger2000/125A-Emulator-II-Windows-VST3  
**Licence:** GPL-3.0 (with retained third-party notices)  
**Date:** 19 November 2026

An independent Windows VST3 adaptation of Tuth's original hardware-level Emulator II emulator. It uses the original EII SSM2045 filter model, native DAC stage and S3528 reconstruction as new-instance defaults. The optional Emulator III CEM3387 model remains selectable.

**P047:** consistent filename and host-visible name `E-MU Emulator II.vst3` / `E-MU Emulator II` with the original processor class ID preserved.  
**P048:** original author and upstream contributors acknowledged in project/package and GUI credits, public source/binary traceability, and an explicit ROM-free release package.

**Automated verification:** prior P047 renamed actual Windows VST3 COM loading, project-state tests and Steinberg validator 47/47 PASS. P048 release-candidate build results are shown separately in the relevant GitHub Actions workflow. **No claim of completed Studio One original-firmware playback testing for P048.**

### Files

- `125A-E-MU-Emulator-II-P048-PUBLIC-VST3-NO-ROM.zip` — installable Windows VST3 and notices; **does not contain ROM, OS, factory/Choir banks or sound presets**.
- `125A-E-MU-Emulator-II-P048-CORRESPONDING-SOURCE.zip` — matching complete upstream + modified 125A source, patch and build/test scripts from the same build.
- `SHA256SUMS.txt` — verify ZIP contents.

Download **both** binary and source archives when distributing a public GPL binary, and keep them together on the GitHub Release page. See INSTALL-PUBLIC.md for user-supplied ROM/OS placement. Do **not** upload the private `KOMPLETT-PRIVAT.zip` owner package to GitHub Releases.

Not associated with, approved by, or supported by E-mu Systems or any trademark holder.
