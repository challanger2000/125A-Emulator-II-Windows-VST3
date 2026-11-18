# P006 — Local firmware under VST3 Contents/Resources (same as Emulator III)

User-required Windows path: \`C:\Program Files\Common Files\VST3\Eigene\E-MU Emulator II.vst3\Contents\Resources\`.

- \`ROM/\` holds \`main.bin\` (8192 bytes), \`scanner.bin\` (8192), \`ic135.bin\` (512), \`ic137.bin\` (512). Optional: \`main21dm.bin\` (1 MiB floppy), \`main23.bin\` (HD), \`scanner21.bin\` alternatives.
- \`OS/\` holds **exactly one** owner-supplied original OS3.1 image \`.emuiifd\` (573440 bytes) or \`.hfe\`. No ROMs or proprietary OS data are in public GitHub/CI. Banked project-state saves P005 keep the OS region zero and reattach it from this local OS folder.
- The bundle's working binary lives under \`Contents/x86_64-win/E-MU Emulator II.vst3\`. The original compiled upstream \`EmulatorII-Custom.vst3\` is copied/renamed by local private packager, preserving its existing VST3 FUID and the internal EIII Custom filter.
- Startup: module location is found with \`GetModuleHandleExW\`/ \`GetModuleFileNameW\`, then \`Contents/Resources\` resolved relative to the module itself, not hard-coded. Previously stored explicit readable paths remain authoritative; missing/stale entries automatically resolve from the new bundle. Ambiguous OS directories are rejected rather than guessing at random which floppy boots.
- No original-OS writing: \`directImageWrites\` is forced false when the internal OS image is selected. The emulator still reads the original firmware via its normal paths and uses a protected working copy.

The P006 public tests create *synthetic fake-size* ROM and OS fixtures only and require correct fallback, non-override, idempotence, ambiguity rejection and invalid-size ROM rejection. A private ROM-backed boot and project restore remain separate acceptance gates. The private packaging script is never run in public CI and must not be added to any public artifact uploader.
