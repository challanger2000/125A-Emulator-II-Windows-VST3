# P028 – Original Emulator II SSM2045 as new Custom instance default

**Development-only, derived from P027.** The 125A build still uses the complete
Tuth/eii-emu source pinned to `e345bcf00af8a066ebace9168cf0b6c3a40ca164`
as a Git submodule, plus all 125A source overlays. Original E-mu ROM/OS/media
are never committed.

## User-requested behavior

A new `Emulator II Custom` VST3 with no previously saved user defaults now
starts with **SSM2045 model 2 – block-diagram VCF/VCA (96 kHz)**, i.e. the
original EII filter family, not the EIII CEM3387 custom addition.

The optional EIII CEM3387 mode remains in the selector with the unchanged
VST3 class, parameter mapping, project state model index and calibration
profile. Existing projects and intentionally saved global defaults continue
to restore their selected model. In particular an existing saved CEM global
default can override the new built-in fallback; the user can select SSM2045
model 2 and use **Save settings as default for new instances** once.

The change does NOT claim to turn on the hardware DAC/deglitch or S3528 route:
those are separately stored options and require their own comparison tests.

## Provenance and limits

`tools/apply-p028-eii-default.py` patches only the original pinned
`src/vst3/eii_vst3.cpp` new-instance *fallback*, after the earlier 125A
overlays and before the existing Windows VST3 build. `--verify` fails closed
when original expected code/commit is missing.

`tests/p028_default_filter_tests.py` checks original SSM selection,
CEM availability, saved-defaults priority, project model recall and two
test-only wrong-source counterexamples. Actual Windows host load, per-user
defaults migration, preset audio, model fidelity and final Studio One host
acceptance remain **NOT RUN** until execution evidence is available.

There is no modified audio kernel, new VST3 class, change of plugin identity
or change to original user ROM/disk content.
