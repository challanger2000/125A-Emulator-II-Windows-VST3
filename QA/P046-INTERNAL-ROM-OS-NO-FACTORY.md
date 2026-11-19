# P046 – real owner-private VST3 package with internal ROM + original OS3.1, no factory samples

**2026-11-19 – packaging correction for P045.** The P045 owner ZIP had a valid `EmulatorII-Custom.vst3` DLL but kept `Original-ROM` and `Original-Medien` **outside** the VST3 bundle. The existing P006 `GetModuleFileNameW` loader resolves ROM/OS specifically within `Contents/Resources`, so external test-directory media do not make an installed VST3 self-contained. The user correctly rejected that delivery.

## Real private deliverable

Locally assembled, private **`125A-Emulator-II-P046-VST3-ROM-OS31-INTERN-PRIVAT.zip`**, containing **exactly one installable `EmulatorII-Custom.vst3` directory**, no external dependencies and no test exe. This is a ZIP transport format for that one VST3 folder, not a Windows executable installer. Its internal layout:

```
EmulatorII-Custom.vst3/
  Contents/
    x86_64-win/EmulatorII-Custom.vst3
    Resources/
      ROM/main.bin             (8,192)
      ROM/scanner.bin          (8,192)
      ROM/ic135.bin            (512)
      ROM/ic137.bin            (512)
      ROM/main21dm.bin         (8,192; optional firmware variant)
      ROM/main23.bin           (8,192; optional firmware variant)
      ROM/scanner21.bin        (8,192; optional firmware variant)
      OS/Emulator-II-OS31.emuiifd (573,440)
      VST3-SDK-LICENSE.txt
```

**No `EII-Choir.emuiifd` and no sample bank / factory instrument is included.** The OS disk, required for original-firmware startup, is *not* a factory sample bank. User-owned sound banks are separately loaded by the instrument when desired. No empty sound floppy is pre-mounted because original firmware boots from its OS floppy; the user can create/use working media only if needed.

The source-integrated P006 resource helper `src/125a_bundle_resources.h` already supports module-relative `Contents/Resources/ROM` and exactly one OS image in `Contents/Resources/OS`. A fresh VST3 instance with empty paths selects the internal ROM + OS floppy; existing valid explicitly selected user paths stay untouched. Direct writes to the internal OS file remain disabled, with a separate working copy.

## Actual local packaging assertions

The private ZIP was **created**, `zip.testzip()` returned success, its exact layout was inspected, and all media were verified against SHA-256 hashes from the preceding P044 owner original-firmware test:

| Asset | SHA-256 | Status |
| --- | --- | --- |
| `main.bin` | `5082F8F815E873803929DC570AB8E4083646C6D79368B17B931A0328F06DE226` | Match |
| `scanner.bin` | `478CF8E0956AADF27C51C58A26F24926D4E6F2658A991877DD3D0F3AA98A6227` | Match |
| `ic135.bin` | `725CD24F9E98F201EFCD7CFAC4E07F38713495FA960B3F37664E76BD079927F5` | Match |
| `ic137.bin` | `874B9EC1214977FB95FA77B337B7CB254D243C9A143547AF3B440CD2D9FF9116` | Match |
| `Emulator-II-OS31.emuiifd` | `EF00043ACCAB33496FCE1975A89D9D05940A3A4D515EC382F13B4BED0019D83E` | Match |
| actual VST3 Windows DLL | `3203654B2CD2F640DD5328E59454FD16E920FFB1D12621E045F13BC73FC9B68A` | Same validated P045 build |

Seven ROM variant files were included, but only the four required main/scanner/PROM files are mandatory for the default ROM loader. The owner-private ROM bytes are **not** uploaded to GitHub or public CI.

## Regression checks and evidence boundaries

- The P046 source/test patch includes a **negative sample-bank gate**: even if a `Factory/EII-Choir.emuiifd` happens to be present, it is **never automatically mounted**. Boot selects internal OS only; absence of factory sample media is supported.
- The old P006 regressions cover correct ROM and OS sizes, idempotence, moved installs/invalid old paths, explicit user choices, invalid/ambiguous OS and read-only originals.
- P045 native switched DAC + SSM2045 model2 + S3528 first-run default remains unchanged. P044 independently established operational original-firmware native DAC Windows signal and disk storage on the *previous, external-path* layout.
- **NOT YET CONFIRMED:** Boot with the repackaged internal VST3 on the owner's actual Windows/Studio One installation. Do **not** falsely equate archive inspection or synthetic resource tests with an original-ROM boot; final owner host startup may still require troubleshooting.
- **This is an actual fully packed installation artifact**, not merely a package of source scripts and separate ROM folders.

**Install:** unpack ZIP and copy the entire `EmulatorII-Custom.vst3` directory (not only the inner DLL) into Windows' configured VST3 scan path; restart/re-scan the DAW. Do not re-extract ROMs separately; their relative in-bundle location is the validated install contract.
