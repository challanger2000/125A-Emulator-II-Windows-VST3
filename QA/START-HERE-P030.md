# P030 — Genuine Windows Emulator II ROM / MIDI / PCM / fresh VST3 song recall

**Source baseline:** owner 125A Emulator II Windows VST3 development main P029
at \`0fea8937c8268c4d8088d3e3b484f6528fc55b0e\`; Tuth core remains
pinned to \`e345bcf00af8a066ebace9168cf0b6c3a40ca164\` (GPL-3.0).
Windows x64 VST3 instrument only. No DSP, FUID, program/state format,
product packaging or runtime extra executable changes.

## Why

Prior P025/P027 authentic owner ROM + Choir evidence ran against the patched
PluginEngine compiled for **Linux**. Prior P026/P029 real Windows VST3 host
COM tests ran with **no valid original ROM** (intentional negative/fault tests).
Green Steinberg 47/47 does NOT bridge the two proof boundaries. Do not
claim playable genuine Choir through Windows COM until a positive run.

## P030 Windows factory + original hardware + project restore test

The new optional \`original-windows-audio\` mode extends the **same actual
Windows VST3 Hosting::Module and factory** test executable used by P026/P029.

Positive owner-local test (private licensed original ROM+Choir image):
1. Validate the four authentic ROM sizes and original EII floppy input.
2. Create an actual Windows VST3 component/processor, set actual IBStream
   song state with EII \`model=5\` SSM2045 M2 96 kHz, DAC OFF and nominal S3528 ON (P032),
   then configure offline host 48 kHz/512.
3. Boot fully autonomously with **zero host audio callbacks**. Wait for
   genuine original Pxx LCD and loaded bank, or fail on true hardware error
   and bounded 240-second boot timeout.
4. Assert original SSM2045 and S3528 route actually applied; first pre-note buffers must
   be silent; note 60 On/Off routed through real VST3 ProcessData event list.
5. Check every output sample finite, >2000 nonzero audio frames, peak
   >0.001, energy >1, original MIDI UART read activity, no DSP/event drops,
   and no offline underruns. The source code itself cannot prove hearing.
6. Persist actual IComponent::getState; terminate the original component
   and verify zero leftover EII workers.
7. Create a **fresh VST3** component with the saved host project state,
   boot original ROM/Choir again, play same MIDI and demand nonzero PCM
   and bounded energy relative to the first original performance.
   P031 passes the checksummed original IBStream unchanged; P032 preserves the
   S3528 ON setting. This tests reloading the *same selected original floppy file*, not
   disk independence after removing it.

Public automated CI executes the same host mode with deliberately invalid
all-zero ROM and floppy. It must fail for the **actual original RFD
bus-driver hardware conflict**, and must not become a false green for
nonexistent firmware/PCM. No genuine original ROM, floppy or sampled audio
may be uploaded to Actions or to the QA artifact.

## Artifacts and signoff

- Normal VST3 artifact: still one Windows VST3, no extra helper program.
- Separate **owner-only QA tools** artifact contains the test executable,
  the same Windows VST3 and \`Test-Private-Original-EII.ps1\`. It is not an
  installer and not shipped with the plug-in. The owner runs the script
  privately against their licensed ROM/Choir disk only when final user
  host verification is required.
- Public CI/source/validator/negative test: record exact result only
  after completion. **Original ROM positive Windows test: NOT RUN
  without private assets.** Studio One actual interface, audio device,
  ASIO realtime under load, project relocate without selected floppy,
  and 125A Plugin Tester: also NOT RUN. This is DEV/NO FINAL.
