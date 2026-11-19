# P031 — Binary-safe original Windows VST3 song reopen (P030 correction)

**Scope:** Development/QA only. P030 was merged at `99c21c0e9b3878f4eb8ea0562f91c51becb39970`. No product DSP, firmware, factory identity, audio filter, project serialization format, or license-bearing media changed.

## Root cause / failure mode

P030's owner-local authentic-ROM Windows host probe invoked `replaceKey()` on the **whole** restored `IComponent::getState()` string before feeding it back through `setState()`. That is correct for legacy plain `EIIVST3 1\n...` settings, but **incorrect** for projects containing embedded bank media (`125AEIIBANK...`) or embedded HDD media (`125AEIIHDD...`). Both formats contain a binary length/checksum envelope. Changing the interior settings bytes without updating the envelope's FNV checksum causes `setState` to reject an otherwise valid saved song.

The error affects the **P030 QA test harness**, not proof that the product's real project serializer is corrupt. The prior P017 host state test already preserved immutable synthetic media in its own path.

## Fix

- On **first** original-ROM host instance, parse `IComponent::getState()` with the actual P017 `decodeProject()` codec, modify **only decoded settings** (rom/floppy/model/route), and reassemble through `encodeProject()` with bank and HDD data retained.
- On **reopen**, validate the saved host stream via the codec and pass the exact bytes unchanged to the fresh Windows VST3 component. This matches ordinary DAW project recall, where the VST3 stream is not rewritten by the host test. Insist that the saved ROM and selected SSM2045 `model=5` settings are present.
- On **save**, independently verify the original Windows `IComponent::getState()` stream can be decoded before declaring it a recoverable project.

## Real Windows COM CI regression (no original ROMs)

New `original-windows-binary-recall` mode uses a synthetic full-size EII soundbank:
1. Two actual Windows VST3 factory instances are created.
2. Original `IComponent::setState/getState` accepts and preserves a checksummed bank song with model=5.
3. Altering the whole binary blob using the old `replaceKey` implementation is deliberately rejected due to checksum mismatch (**negative mutant**).
4. A fresh actual Windows VST3 instance accepts the **unchanged** stream and re-saves the identical bank data.
5. Plugin worker teardown and existing validator/native/COM tests remain required.

**Note:** Fake bank data is used only to test state integrity and is not presented as playable original audio.

## Evidence boundaries

- **Public Windows CI:** compile, Steinberg validator, existing tests, original-ROM-invalid negative and new binary-media positive/negative state tests.
- **Actual authentic EII ROM + Choir disk through Windows VST3:** NOT RUN until executed owner-locally using P030's private kit.
- **Original audio after a DAW song reopen with embedded media and relocated/removed external bank:** NOT RUN. P030 still reopens the same original floppy path, so this stronger portability claim remains unproven.
- **Studio One, ASIO, GUI, 125A Test Lab and analog hardware fidelity:** NOT RUN by this change.

The shipped deliverable remains a single Windows x64 VST3. The local owner-only test executable is QA infrastructure and never a runtime dependency. Never publish proprietary ROM/OS/floppy/sample files.
