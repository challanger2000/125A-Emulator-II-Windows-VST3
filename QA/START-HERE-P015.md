# P015 – Original firmware media activity → safe song-bank warning

**Windows VST3 development build; not a final plugin.** Private ROM/OS and
user banks are not included.

P015 closes another gap in the P013/P014 project-state safety model:
original Emulator II bank loads can happen through the *front-panel*
DISK operations, independent of changing files in our Settings menu.

Once original firmware has reached its first Pxx performance display, the
machine owner watches **actual floppy SIO character completions** and
**actual HDD bytes read**, as well as entering the original SAMPLE mode.
A transfer after that point conservatively marks live sampler RAM as
potentially different from the most recently committed project bank.
**A disk read is not proof that a bank was fully loaded**; no automatic
bank commit is claimed. To capture the latest sound, use the P013
original-firmware DISK7 Save current RAM bank action, then save the song.

New external floppy/HDD media without a committed embedded bank are
marked pending on boot. Boot-OS reads before initial Pxx do not count
as a later bank switch. No direct chip state, RAM, disk or ROM mutation.

P014 guarantees the Studio One getState request remains valid and
carries the latest committed bank and a durable bankpending=1 warning
instead of silently failing the whole project save.

## Automated
Linux model tests for boot baseline, actual SIO/HDD reads, resetting
counters, sample mode, original performance/boot transitions; source
order and regression checks; Windows x64 VST3 build, Steinberg validator
and real COM IBStream project-state tests.

## Remaining
Not a proof of actual *completed* original bank-load detection or audio
identity. Original-ROM EII bank switching, HDD project storage/relocation,
Studio One saved-song reopening and multiple instances still require
appropriate private end-to-end testing. Turbo boot and disk operations,
C3 root-note setup and latency/UI optimization also remain open.

Development PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/13
