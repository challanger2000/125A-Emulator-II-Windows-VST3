# Credits, provenance and licensing

**Original emulator software and project lead: [Tuth](https://github.com/Tuth).** Tuth initiated and maintains [eii-emu](https://github.com/Tuth/eii-emu), providing the reference material, hardware knowledge, tests and project direction. This 125A adaptation is built on that work; it must not be presented as a wholly independent 125A emulator implementation.

The upstream project's [CONTRIBUTORS.md](https://github.com/Tuth/eii-emu/blob/main/CONTRIBUTORS.md) also credits **ChatGPT / Codex (OpenAI)** and **Claude Code (Anthropic)** for AI-assisted engineering in collaboration with Tuth. Those contributions remain credited to the original project, not reassigned to 125A.

**125A adaptation:** Windows x64 VST3 integration, original-media loading and private packaging, selected firmware workflows, host integration, testing, and user-facing adjustments maintained in [125A-Emulator-II-Windows-VST3](https://github.com/challanger2000/125A-Emulator-II-Windows-VST3). It uses a pinned snapshot of Tuth's original source (commit `e345bcf00af8a066ebace9168cf0b6c3a40ca164`) plus documented build-time patches. The original VST3 class ID remains unchanged in P047.

**Third-party foundations:** Upstream credits [Andre Weissflog's floooh/chips](https://github.com/floooh/chips), [AJR's MAME Emulator II driver](https://github.com/mamedev/mame/blob/master/src/mame/emusys/emu2.cpp), the [Steinberg VST3 SDK](https://github.com/steinbergmedia/vst3sdk), and the EIII CEM3387 model from [Tuth/Emulated-3](https://github.com/Tuth/Emulated-3). Each component retains its applicable licence and notices in the original source tree.

**Licence:** GPL-3.0 for the covered emulator software, see [LICENSE](LICENSE) and the upstream repository. Redistribution of a modified binary entails the applicable GPL source and notice obligations; merely giving the VST3 a different name does not alter them. E-mu hardware names and trademarks belong to their respective holders. This unofficial project is **not affiliated with or endorsed by E-mu Systems**.

**ROM / OS / media:** Original E-mu ROMs, operating-system disk images and factory/sample banks are not licensed by this repository. They are **not present on public GitHub or in public CI artifacts**. An owner's separate private installation bundle may contain that owner's previously supplied files. Do not redistribute those proprietary files as part of a public freeware package.

When presenting the modified instrument, retain a visible reference to **Tuth/eii-emu** and these credits; do not replace the original developers' attribution with the 125A branding.
