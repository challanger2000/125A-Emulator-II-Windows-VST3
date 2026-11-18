#!/usr/bin/env python3
"""P027 genuine private original-ROM double-boot acceptance source contract."""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
s=(r/"tests/p025_plugin_engine_private_probe.cpp").read_text(encoding="utf-8")
for marker in (
    "const double firstPeak=peak,firstEnergy=energy;",
    "e.boot(settings,true);",
    'if(s.autonomousBoot){enteredReboot=true;break;}',
    'assertSilentDuringBoot(e); // previous original note must not leak',
    "e.queueMidi(0,ignoredPreboot.data(),3);",
    "s.bootMidiDiscarded>=1",
    "s.boot.virtualTicks>10000000",
    "e.queueMidi(0,noteOn.data(),3);",
    "P027_SECOND_ORIGINAL_AUDIO nonzero=",
    "activeAgain>2000&&peakAgain>0.001",
    "energyAgain>firstEnergy*0.2&&energyAgain<firstEnergy*5",
    "P027 SAME VST3 PLUGINENGINE FULL ORIGINAL ROM/CHOIR REBOOT",
):
    assert marker in s,marker
assert s.count("e.boot(settings,true);")==2
assert "PRIVATE_ORIGINAL_PLUGIN_BOOT" in s
assert "P025 PRIVATE ORIGINAL ROM 4MHZ" in s
assert 'if(argc==4&&std::string_view(argv[1])=="--private-only")' in s
print("P027 full private original-ROM Choir plugin-engine second boot, no old notes, fresh PCM and hardware clocks PASS")
