#!/usr/bin/env python3
"""P022 autonomous original machine must keep media/DAW/clock housekeeping."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
e=(root/"upstream/eii-emu/src/vst3/plugin_engine.h").read_text(encoding="utf-8")
t=(root/"upstream/eii-emu/src/125a_autonomous_boot_timeline.h").read_text(encoding="utf-8")
header=(root/"upstream/eii-emu/src/125a_preboot_event_policy.h").read_text(encoding="utf-8")
m=(root/"upstream/eii-emu/src/machine.cpp").read_text(encoding="utf-8")
for expected in (
    '#include "125a_preboot_event_policy.h"',
    'bool advanceAutonomousBoot(){',
    'switch(portable::prebootAction(ev->kind))',
    'case portable::PrebootEventAction::ApplyControl:',
    'applyEvent(*ev);break;',
    'case portable::PrebootEventAction::DropMidi:',
    'bootMidiDiscarded_.fetch_add(1,std::memory_order_relaxed);',
    'while(consumed<256){',
    'flushThrottle();',
    'portable::insertDelayedFloppy(floppyHeld_,machine_->main.cpu.pc)',
    'if(floppyBacking_)installFloppy(*machine_,floppyBacking_);',
    'gatedThisAttempt=true;',
    'if(gatedThisAttempt){',
    'if(autonomousBoot_.active())handoffAutonomousBoot(false);',
    'else bootGate_.store(true,std::memory_order_release);',
    'Original EII boot failed:',
):
    assert expected in e,"P022 missing original-media/DAW gate: "+expected
a=e[e.index('bool advanceAutonomousBoot(){'):e.index('bool quitRequested()',e.index('bool advanceAutonomousBoot(){'))]
assert a.index('events_.pop();++consumed;')<a.index('flushThrottle();')<a.index(
    'portable::insertDelayedFloppy(')<a.index('if(originalPlayable()){')
assert a.index('if(floppyBacking_)installFloppy(*machine_,floppyBacking_);')<a.index(
    'runTicks(portable::AutonomousBootTimeline::quantum(nonlinear()));')
assert a.index('bootMidiDiscarded_.fetch_add(')<a.index('events_.pop();')
assert a.count('bootMidiDiscarded_.fetch_add(')==1
assert e.count('bootMidiDiscarded_.store(0,std::memory_order_relaxed);')==1
boot=e[e.index('void bootNow(bool discard,bool fromState){'):e.index('    // ---- input ----')]
assert boot.index('bool gatedThisAttempt=false;')<boot.index('bootGate_.store(false')
assert boot.index('gatedThisAttempt=true;')<boot.index('autonomousBoot_.begin(')
assert boot.index('autonomousBoot_.begin(')<boot.index('if(gatedThisAttempt){')
assert 'maxBootWallMs=300000' in t
assert 'insertDelayedFloppy(bool held,std::uint16_t mainPc)' in header
assert 'while(cycles--)' in m,"no original Z80 hardware clock skipped"
b=e[e.index('bool advance(){'):e.index('void publish(bool force)')]
assert 'if(floppyHeld_&&machine_&&machine_->main.cpu.pc>=0x2800)' in b, "normal fallback still injects media"
assert 'flushThrottle();' in b,"ordinary postboot automation unchanged"
run=e[e.index('void runTicks('):e.index('bool quitRequested()',e.index('void runTicks('))]
for side_effect in ('wavStep();','cancelWavStep();','observeMediaReads();','bankStep();',
                    'machine_->hardDisk->bytesWritten!=lastHddWrittenBytes_'):
    assert side_effect in run,"original disk/WAV safety missing in autonomous hardware: "+side_effect
print("P022 autonomous original HD-first ROM/DAW automation and recovery safety PASS")
