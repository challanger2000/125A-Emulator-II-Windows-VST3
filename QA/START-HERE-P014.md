# P014 – Safe Studio One host project save during EII import

**Developer build, NOT final. No original ROM/OS or user banks included.**

## What P014 fixes

Previous P013 returned `kResultFalse` from VST3 `getState()` if a
bank import or original firmware SAVE BANK operation was active, or if
live EII sample RAM had not been captured. Some hosts do not retry a
failed state request when saving a song. This can lose the entire
instrument's updated settings in the project, not just the new sample.

P014 instead publishes an ordinary *valid* VST3 state containing:
1. The current instrument configuration, always.
2. The most recently verified original DISK7-committed performance bank,
   if there is one.
3. A persistent `bankpending=1` warning when the live sampler bank is
   unverified or a capture is still running.

On song reopening this warning remains visible in the plug-in status.
It means: the saved bank is the LAST COMMITTED bank and may not contain
unsaved changes heard before the last song save. **Complete original DISK7
capture and save the Studio One song again** to finalize the current bank.

When the new original bank is fully committed, `bankpending` disappears.
Older projects without this optional field remain binary and source
compatible; no new binary state version is required.

## Automated acceptance
- Linux native C++ pending-marker, malformed marker, original bank
  CRC/roundtrip and legacy-state tests.
- Real Windows x64 VST3 build and Steinberg Validator.
- Real VST3 COM component `getState/setState` host tests:
  legacy, pending with bank, pending without bank, corruption,
  multiple instances and later complete commit.

## Not yet proven
- The actual Studio One autosave/close/reopen behavior while real E-mu
  original ROM/OS is sampling, or the live-audio correctness of the bank
  after original DISK7, and the user's original ROM setup.
- A host may not display a plug-in's `bankpending` warning when closed.
  The presence of a valid song state does NOT mean its live bank was saved.
- Faster boot/import, full HDD project state, sample C2/C3 mapping,
  performance improvements and original hardware comparisons remain open.

**Do not replace P008 or your last known-good installation.**
Development PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/12
