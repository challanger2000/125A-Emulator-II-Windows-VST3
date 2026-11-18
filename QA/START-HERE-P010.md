# P010 – 125A Emulator II Windows VST3 – START HERE

**Status: DEVELOPMENT BUILD – NOT A RELEASE / NOT STUDIO ONE ACCEPTED.**

## What this build contains

- The P008 original-firmware WAV bridge and protected temporary OS3.1 import.
- P010: the selected, expanded .EII file bank is cloned to immutable
  original-system-bytes-stripped project media when mounted, or at boot selection.
- Eject does not erase this selected project bank. Full bank bytes are stored
  through the existing 125A VST3 IBStream project codec.
- Non-.EII media (HFE, EMUIIFD, HDD) and live sampler-RAM changes are **not**
  automatically captured by this P010 feature.

## Installation

Copy the entire VST3 bundle directory to your normal Windows VST3 location.
This public CI artifact intentionally **does not contain original E-mu ROM/OS**
or any private/user sound bank. A functional boot requires the owner's original
ROM and OS3.1 image in the plugin's private Contents/Resources layout described
in the P006 documentation and existing owner's private packaging procedure.

Do not replace your last known-good P008 plugin until private original-ROM and
Studio One song-save/reopen acceptance is complete. Keep a backup.

## Test gates not yet completed

1. Real original-firmware Choir .EII load -> Eject -> Studio One Save -> close ->
   reopen with external Choir .EII absent -> confirm identical sound/program.
2. Distinguish a mounted-but-not-yet-loaded .EII from changed live sample RAM.
   P010 saves the selected file, not current RAM; this remains an explicit gap.
3. WAV import while host saves; abort in each capture/save state; manual disk
   swaps and HDD-recalled voices.
4. Latency/underruns, 1/4/8 instances, original/Custom sound comparisons.

The CI below checks native source integration, immutable bank snapshots,
the real Windows VST3 build, Steinberg validator 47/47, and synthetic COM
IBStream round-trips. These do NOT constitute original-firmware/DAW acceptance.

## Source, branch and audit

- P010 development PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/8
- P009 audit PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/7
- Original upstream core: Tuth/eii-emu pinned at
  e345bcf00af8a066ebace9168cf0b6c3a40ca164
- No original E-mu ROM, OS disk, or user files are included in this artifact.
