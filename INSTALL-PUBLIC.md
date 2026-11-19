# E-MU Emulator II — public Windows VST3 installation

**Original emulator by [Tuth](https://github.com/Tuth/eii-emu)**; 125A adaptation. Unofficial independent freeware under the GPL-3.0. This ROM-free public package does not include or authorize distribution of original E-mu software, firmware, OS disks, manuals or commercial sample libraries.

## Requirements

- Windows x64 VST3-compatible host.
- Legally obtained original E-mu Emulator II ROMs and a compatible OS disk image (the verified private setup used OS 3.1).
- Sample-bank images separately supplied by the user if desired.

## Installation

1. Close the VST3 host; extract the **whole** `E-MU Emulator II.vst3` folder to your configured VST3 directory (for example, `C:\Program Files\Common Files\VST3\`).
2. Into `E-MU Emulator II.vst3/Contents/Resources/ROM/`, supply `main.bin`, `scanner.bin`, `ic135.bin`, `ic137.bin` from your own legal source. Optional compatible ROM variants are not provided.
3. Into `E-MU Emulator II.vst3/Contents/Resources/OS/`, put your own compatible OS image (`.emuiifd` or `.hfe`). The public archive includes **no disk images**.
4. Scan the plugin in the host; select any user-bank disk as needed. Avoid installing the old `EmulatorII-Custom.vst3` 125A adaptation simultaneously since it has the same processor identity.
5. The first real Studio One user-install/boot/song-recall run of this exact P048 release candidate is a **separate acceptance**, not part of the existing 47/47 Steinberg result.

Full source, change history and original author attribution: [CREDITS.md](CREDITS.md), [CHANGELOG.md](CHANGELOG.md), [RELEASE-SOURCE-TRACEABILITY.md](RELEASE-SOURCE-TRACEABILITY.md). This is not an official or manufacturer-endorsed E-mu product.
