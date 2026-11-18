# P029 – Correct new-instance EII default ownership and real Windows VST3 QA

**Development candidate; derived from main P028 at merge 191a90f.**
Original Tuth/eii-emu is still a pinned GPL-3.0 submodule, SHA
\`e345bcf00af8a066ebace9168cf0b6c3a40ca164\`. No ROM/OS/media files
are included or published.

## Root cause and requested behavior

P028 replaced the new Custom instance fallback with **Emulator II original
SSM2045 Model 2 96 kHz**. However original upstream EII VST3 still wrote
the current instance's entire settings to global \`plugin-defaults.txt\`
during \`terminate()\` and on each ordinary editor \`updateSettings()\`.
Loading an older EIII-CEM3387 DAW song and simply closing it therefore
silently changed the *next new instance* to CEM3387, defeating the owner's
requested EII default. The earlier P028 source-only test could never
detect this lifecycle regression.

P029 removes ONLY the two implicit cross-project writers. The original
explicit **Save settings as default for new instances** menu command
continues to write the global preference. Previously saved explicit
preferences still take precedence until changed/cleared. Host project
\`setState\`, state serialization, optional EIII CEM3387 and all original
filter/DAC/S3528 DSP algorithms remain unchanged. In particular, this
does not change the chosen analog DAC/S3528 defaults or prove hardware
fidelity.

## Regression and negative control

- P029 source test detects original implicit-write code and confirms
  exactly one global save call remains: the explicit user command.
- Real **packaged Windows VST3 factory/COM/IBStream** host mode
  \`default-filter\` uses a private temporary LOCALAPPDATA folder:
  1. First new Custom instance has \`model=5\`, original EII.
  2. The same instance restores a CEM \`model=4\` host project.
  3. Project close must not create global defaults.
  4. Another new instance must still report \`model=5\`.
  5. Explicit CEM global defaults persisted to disk are honored.
  6. Loading/clsoing an EII project must preserve those explicit bytes.
  7. Removing the explicit override returns to \`model=5\`.
- The two actual previously present implicit writes are the negative
  mutant: old code would fail checks 3–4 and 6 under the same host test.

## Evidence split

Static/source guards: evaluate in Linux and Windows CI.
Actual exported Windows VST3/default IO persistence: run in Windows CI
after SDK build and Steinberg Validator, with real host instantiation.
Original licensed EII ROM/floppy, genuine voiced PCM, Studio One user
project reopen/UI, native audio accuracy and 125A Plugin Test Lab:
**NOT RUN in the P029 host test** and still release blockers.

No product-version/FUID/parameter ID changes, no automatic user-settings
deletion, no changed original runtime hardware behavior.
