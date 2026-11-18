# 125A Emulator II – P011 – START HERE

**DEVELOPMENT ONLY – not a release; Studio One owner acceptance is the final gate.**

P011 builds on P010/P008 with controlled WAV cancel. On cancel, automatic
SAR input is disarmed, the original EII firmware receives its own STOP and
SAMPLE (exit) keys, and the original read-only disk is restored **only once
the firmware has returned to Pxx and the floppy is idle**. A timeout does
not pretend to have recovered. Cancelling while the original firmware writes
DISK7 is **deferred**, rather than corrupting a partly written bank.

P010 immutable .EII-bank project snapshots are retained. This does not
provide a full snapshot of live sample RAM, HDD-loaded banks or arbitrary
program edits. Save during WAV import remains a separate open project-safety
gate. Turbo boot/import, HDD setup and C3 root-note mapping are also open.

## Test boundaries

CI: source patch exact anchors; P011 firmware key-recovery model tests;
P010 original-bank serialization; actual Windows x64 VST3 compile; upstream
Steinberg validator; synthetic Windows VST3 IBStream project-state roundtrip.

NOT YET TESTED: private original ROM/OS firmware cancel during every actual
capture phase, subsequent audio identity, real Studio One save/reopen, and
multi-instance/hardware-latency soak. These gates must pass before delivery
as a final plugin.

Public CI intentionally excludes original E-mu ROM, OS and private banks.
Do not replace a known-good installation with this development artifact.
Source PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/9
