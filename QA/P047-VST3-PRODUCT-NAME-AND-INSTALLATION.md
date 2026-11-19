# P047 – Consistent actual Windows VST3 name: E-MU Emulator II.vst3

**Owner request 2026-11-19:** match the naming of `E-MU Emulator III.vst3` exactly. `EmulatorII-Custom.vst3` is the upstream development artifact and **is not the correct name for the owner-facing installer**.

## What must match

1. Outer Windows VST3 **bundle directory**: `E-MU Emulator II.vst3`
2. Compiled VST3 **PE module in** `Contents/x86_64-win/`: `E-MU Emulator II.vst3`
3. VST3 `IPluginFactory` / `IPluginFactory2` class display name in DAW: **E-MU Emulator II**.

The original `tools/Package-Private-Emulator-II.ps1` from P006 **already handled requirements 1 and 2**, but the P045/P046 owner deliveries bypassed it and erroneously retained the upstream `EmulatorII-Custom` artifact basename. P047 restores the agreed original packaging contract and corrects the actual class display name, without touching the **processor UID**, per-song state format or DSP. The original upstream vendor attribution remains unchanged, avoiding any claim that the emulator is an official E-MU release.

## Complete private installable file layout

```
E-MU Emulator II.vst3/
  Contents/
    x86_64-win/
      E-MU Emulator II.vst3
    Resources/
      ROM/main.bin
      ROM/scanner.bin
      ROM/ic135.bin
      ROM/ic137.bin
      ROM/main21dm.bin
      ROM/main23.bin
      ROM/scanner21.bin
      OS/Emulator-II-OS31.emuiifd
      VST3-SDK-LICENSE.txt
```

No `Choir`/factory soundbank, no separate test executables and no external ROM folder. The original OS disk remains a boot dependency and is not a preloaded preset bank. This is a **one-directory VST3 install**, as with the Emulator III.

## Compatibility gates

- The original P006 `GetModuleFileNameW` loader obtains `Contents/Resources` **from the actual loaded DLL path**, independent of the directory basename. Internal ROM/OS are discovered after moving the entire `.vst3` directory.
- New instances continue to select `model=5` (EII SSM2045 Model2), `native=1` (EII original-DAC model), `s3528=1` (reconstruction), with the original EIII CEM model only selectable by the user.
- The stable processor class CID/FUID is **never renamed or regenerated**. DAW session state remains compatible as far as the same-CID VST3 contract allows. Existing host installation cache collisions when both names are installed simultaneously are a separate operational matter: users should install only the correctly named bundle.
- Windows CI must compile the actual renamed **internal class** and physically load a **renamed directory and PE file** in the real COM test host; both must report PASS. Running an unchanged upstream-named plugin does not satisfy the P047 name gate.
- Steinberg validator, native DSP and source tests continue to pass.
- Owner's original ROM and OS bytes stay private and are only included in the owner-specific ZIP, never public GitHub/CI.

A real Studio One UI/scan from the final owner-private renamed path is still a separate last-mile test; it must not be marked PASS based on source or generic COM verification.

## 2026-11-19 signed-off automation + private package

GitHub Actions [run #44571195085](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/actions/runs/44571195085) **PASS** in both Windows and Linux jobs. Actual Windows VST3 host opened the renamed **outer** `E-MU Emulator II.vst3` bundle and the renamed **inner** `E-MU Emulator II.vst3` PE file, confirmed the reported factory class name and performed the original factory/state regression (`P029 ACTUAL WINDOWS VST3 DEFAULT PASS 0 failure(s)`). The original Steinberg validator reported **47 tests passed, 0 failed**. Public source identity gates **7/7** and negative mutations **3/3** passed.

Owner-private deliverable `125A-E-MU-Emulator-II-P047-VST3-KOMPLETT-PRIVAT.zip` was locally built by taking the **new CI-built P047 PE binary**, renaming both its installed bundle directory and PE file to exactly the user-approved name, and adding the **four required ROMs, three optional ROM variants and one genuine OS 3.1 disk** under `Contents/Resources` from owner P046 material. Verified `ZipFile.testzip()`, all internal filenames, no factory/Choir, and all **five P044 owner SHA256 checks**. CI-built P047 PE binary SHA-256 `B9F0D6B7B1E413C9DB29FF3CE946A5E3EA2440B4F7631C89E184622229D507D5`. Private delivery ZIP SHA-256 `FD716FFE7922C88657D45A5D2427D04B05361A56C67DFBF4DF93492B1C5A4024`.

**Do not claim actual original-OS startup in Studio One from this renamed path was executed.** The real Windows COM host proves the renaming did not break plugin factory loading, and the original media were verified and packaged, but the end-user DAW scan/boot remains an explicit final-practice gate.
