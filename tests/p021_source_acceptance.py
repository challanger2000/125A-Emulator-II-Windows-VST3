#!/usr/bin/env python3
"""P021 safety: original hardware runs full 4MHz ticks before real first Pxx,
then single-owner handoff remaps host PCM, MIDI and analog input clocks.
"""
from pathlib import Path
r=Path(__file__).resolve().parents[1]/"upstream/eii-emu/src/vst3"
e=(r/"plugin_engine.h").read_text(encoding="utf-8")
i=(r/"host_sample_input.h").read_text(encoding="utf-8")
p=(r/"rt_primitives.h").read_text(encoding="utf-8")
v=(r/"plugin_editor.h").read_text(encoding="utf-8")
m=(r.parent/"machine.cpp").read_text(encoding="utf-8")
for k in (
    'portable::AutonomousBootTimeline autonomousBoot_;',
    'bootGate_.store(false,std::memory_order_release);',
    'autonomousBoot_.begin(G_,bootStartMs);',
    'void handoffAutonomousBoot(bool playable){',
    'bool advanceAutonomousBoot(){',
    'runTicks(portable::AutonomousBootTimeline::quantum(nonlinear()));',
    'handoffAutonomousBoot(true)',
    'handoffAutonomousBoot(false)',
    'anchorHostPosLocal_=base;',
    'anchorTickLocal_=G_;',
    'hostInput_->discard(base);',
    'streamGeneration_.fetch_add(1,std::memory_order_release);',
    'bootGate_.store(true,std::memory_order_release);',
    'anchorEpoch_.store(localAnchorEpoch_,std::memory_order_release);',
    'if(!bootGate_.load(std::memory_order_acquire)){',
    's.autonomousBoot=autonomousBoot_.active();',
):
    assert k in e,"P021 original boot integration missing: "+k
a=e[e.index('bool advanceAutonomousBoot()'):e.index('bool quitRequested()')]
readiness=('if(portable::originalFirmwareMidiReady('
           if 'originalFirmwareMidiReady(' in e else 'if(presetDisplayed())')
assert a.index('events_.pop()') < a.index(readiness)
assert a.index(readiness) < a.index('runTicks(portable::AutonomousBootTimeline::quantum(nonlinear()));')
assert 'const auto target=tickOf(hostTarget_' not in a
assert 'machine_->run(' not in a, "original hardware only advances through same runTicks pipeline"
b=e[e.index('void handoffAutonomousBoot('):e.index('bool advanceAutonomousBoot()')]
assert b.index('ring_.discardPreviouslyRendered();') < b.index('streamGeneration_.fetch_add(')
assert b.index('anchorHostPos_.store(') < b.index('bootGate_.store(true')
assert b.index('anchorFrame_.store(') < b.index('bootGate_.store(true')
assert 'channelRing_.resetTo(streamBase)' in b
render=e[e.index('void render('):e.index('    // ---- Commands')]
assert render.index('if(!bootGate_.load(')<render.index('const std::uint64_t base=anchorFrame_')
assert 'if(channels)for(unsigned c=0;c<8;++c)' in render
assert 'consumerGeneration_!=gen' in render
assert 'std::int64_t(anchorHostPos_.load(' in render
assert i.count('double(hostOrigin_)')==2
assert e.count('anchorHostPosLocal_);')==2
assert 'void discardPreviouslyRendered()noexcept{' in p
assert 'void resetTo(std::uint64_t frame)noexcept{' in p
assert 'AUTONOMOUS ORIGINAL 4MHz (DAW-independent)' in v
assert 'MIDI during boot ignored' in v
assert 'void Machine::run(std::uint64_t cycles)' in m
assert 'while(cycles--)' in m
assert 'runTicks(limit-G_);' in e, "retained normal host-paced realtime engine"
print("P021 full original hardware boot with DAW-free timeline/realtime event safety: PASS")
