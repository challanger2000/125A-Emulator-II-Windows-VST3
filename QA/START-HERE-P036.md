# P036 — Real original Emulator II sampling / SAR recording across DAW sample rates

**Status: DEV — NOT FINAL.**

## Important evidence correction

The current pinned upstream code **already** includes a hardware-level input signal path. Older source roadmaps saying "SAR/recording unimplemented" predate the existing `SampleInputAnalog`, `SampleSar`, `HostSampleInput`, Z80 `IN 08h`, input-monitor IINT feedback and DRAM writes. Our own acceptance statements must distinguish these **implemented** facilities from missing *measured hardware calibration*, actual Windows DAW recording, and physical analog electrical equivalence.

## P036 contribution

P036 builds a new hard positive probe using the real, fully integrated original emulated Machine and Z80 execution engine, including:

- Original 4 MHz CPU `OUT` instructions configure 8254 channel-0 sample clock, amplitude DAC CV, original S3528 code `0x3b`, main PIO sampling bit 7, and the scanner gain switch.
- Actual sample input goes through **the production Windows VST3 host-audio input queue** (`HostSampleInput`), not `SampleInputSignal` or an injected SAR comparator.
- The original board-model IC86 S3528 anti-alias filter, IC96 input amplifier, channel-0 deglitch/IINT, sample-and-hold C40, comparator and MC14559B SAR encode the waveform.
- The main Z80 reads original `IN (08h)` through actual `-IWAIT` pacing and `INI` commands into original DRAM at `0x2100` onward.
- DPCM decode reconstructs the stored 1 kHz, 0.5 V peak sine signal. Checks: 512 known reads, at least 512 conversions, real asserted wait cycles, zero missing host samples, zero queue drops, physically plausible positive DPCM peak-to-peak and expected zero crossings.

Test matrices: 44,100 / 48,000 / 96,000 Hz production host input, 137 / 256 / 512-sample input blocks, multiple original machine 4 MHz dispatch quanta. Under two distinct 48 kHz chunk/clock quantum patterns the recorded 512 bytes must match **exactly**. Under other sample rates both amplitude and pitch must remain within bounded tolerances. A separate 48 kHz **silent** host input must not generate a false recorded 1 kHz tone.

The same probe compiles and executes under native Linux and **actual Windows x64 UCRT** in GitHub Actions. All old Windows VST3 factory/Steinberg/analog/MIDI/recall QA gates remain mandatory. This is **test coverage and validation** of a previously present hardware implementation, not a new analog circuit model.

## Remaining hardware-fidelity gates

The existence of a working schematic-derived recording path does not establish a complete original EII:
- Full analog DAC/filter cutoff and Q absolute calibration, reconstruction chip switched-capacitor edge artifacts, transistor/opamp nonlinearity, deglitch and individual board trim.
- True real-device input amplifier response, original sample gain tapers, recording/SAR calibration under signal extremes, overdrive, DC/offset and actual E-mu hardware capture comparisons.
- Real original OS3.0/3.1 overlay recording through a **Windows DAW VST3** with private original ROM/disk, positive PCM playback, 125A QA and Studio One final tests.
- MIDI OUT full system/SysEx handling and original DIN electrical/timing tests; original scanner LED behavior against physical panel measurements.

No proprietary original firmware, sample or media assets are bundled. User Studio One end acceptance remains deliberately reserved for the end.
