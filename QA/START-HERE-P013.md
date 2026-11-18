# P013 – verified LIVE BANK project capture (Windows VST3 development)

**Development only. No Studio One acceptance and no private E-mu ROM/OS included.**

## Critical safety change
The previously implemented P010 shortcut assumed that merely selecting a .EII
file meant that the original Emulator II had loaded that exact bank into RAM.
That assumption is UNSAFE: the instrument can keep playing an older RAM bank
after media changes. P013 **does not silently commit on insertion/boot**.

A new SETTINGS action ("125A: Aktuelle RAM-Bank ... sichern") instructs the
original EII firmware itself to write the ACTUAL current live RAM performance
bank with DISK 7 to a protected RAM-only OS3.1 working disk. Only after
firmware-confirmed completion is that bank committed to Studio One project
state; the original selected floppy is restored. No direct RAM writes,
fake firmware success or external host file changes are used.

A mounted external bank which has not undergone a verified DISK7 snapshot
is flagged as not captured. Project getState returns failure instead of
silently storing incorrectly attributed audio. This is a deliberately
conservative safety gate and **does not guarantee that every host reports the
failed save to the user**. The VST3 status dialog shows the warning.

## Automated checks
P013 source integration and all prior native tests, real Windows VST3 build,
Steinberg validator and actual synthetic VST3 host IBStream checks run in CI.
Private original-ROM firmware DISK7 during live-bank capture, then project
save/reopen and measured audio in Studio One are NOT confirmed.

## Important remaining work
- True automatic detection of original bank-load completion is still missing.
- Host save/auto-save during import, HDD external-image recall, turbo boot/disk
  operations, C2/C3 original pitch assignment and audio latency remain open.
- Once all development and private original-firmware tests are passed, only
  then submit the built product for final Studio One owner acceptance.

PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/11
