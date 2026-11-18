#!/usr/bin/env python3
"""P021 host-independent original EII firmware boot with explicit DAW re-anchor.

Never skips ANY original Machine::run clock, uses no second VM, guest snapshot,
external process, extra VST3 or synthesized preset. Before the real first Pxx
the host hears silence while the owner advances original hardware in 4MHz
quanta as fast as it can. Host MIDI received before ready is explicitly
dropped, never mis-timestamped into the finished preset.

At genuine Pxx (or bounded fallback), the owner resets ONLY host rendering
history, then maps the next DAW sample to the current original CPU tick and
ring frame, preserving the original realtime CPU/MIDI/DSP rate thereafter.
"""
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
ENG=UP/"src/vst3/plugin_engine.h"
INPUT=UP/"src/vst3/host_sample_input.h"
RING=UP/"src/vst3/rt_primitives.h"
EDITOR=UP/"src/vst3/plugin_editor.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(s,needle,new,label):
    n=s.count(needle)
    if n!=1:raise RuntimeError(f"P021 {label}: expected exactly one anchor, got {n}")
    return s.replace(needle,new,1)

def patch(e,i,r,v):
    for name in ("portable::BootClockDiagnostics bootClock_;","originalBootBatch_.quantum",
                 "void observeMediaReads()", "ProjectSaveFrame projectSaveFrame()const",
                 "bootClock_.observe("):
        if name not in e:raise RuntimeError("P021 requires full verified P020: "+name)
    if "advanceAutonomousBoot()" in e:raise RuntimeError("P021 applied twice")

    e=one(e,
        '#include "125a_boot_clock_diagnostics.h"',
        '#include "125a_boot_clock_diagnostics.h"\n#include "125a_autonomous_boot_timeline.h"',
        "boot timeline include")

    e=one(e,
        '    portable::BootClockSnapshot boot; // owner-produced, no RT work',
        '''    portable::BootClockSnapshot boot; // owner-produced, no RT work
    bool autonomousBoot=false;std::uint64_t bootMidiDiscarded=0;''',
        "display true autonomous stage / ignored preboot MIDI")

    e=one(e,
        '    portable::BootClockDiagnostics bootClock_;',
        '''    portable::BootClockDiagnostics bootClock_;
    portable::AutonomousBootTimeline autonomousBoot_;''',
        "independent machine-owner boot timeline")
    e=one(e,
        '''    std::atomic<std::uint64_t> epoch_{1},hostTarget_{0};''',
        '''    std::atomic<bool> bootGate_{true}; // RT returns silence until first real Pxx
    std::atomic<std::uint64_t> streamGeneration_{0},anchorHostPos_{0};
    std::atomic<std::uint64_t> bootMidiDiscarded_{0};
    std::atomic<std::uint64_t> epoch_{1},hostTarget_{0};''',
        "host safe boot gate and rendering generation")
    e=one(e,
        '    std::uint64_t hostPos_=0,consumerEpoch_=0,nextPull_=0;float gainNow_=1;',
        '''    std::uint64_t hostPos_=0,consumerEpoch_=0,nextPull_=0,consumerGeneration_=~std::uint64_t(0);float gainNow_=1;''',
        "independent stream generation on audio thread")
    e=one(e,
        '    std::uint64_t G_=0,gOffset_=0,pipeStartG_=0,pipeStartFrame_=0,localAnchorEpoch_=0,anchorTickLocal_=0;',
        '''    std::uint64_t G_=0,gOffset_=0,pipeStartG_=0,pipeStartFrame_=0,localAnchorEpoch_=0,anchorTickLocal_=0,anchorHostPosLocal_=0;''',
        "machine owner host cursor re-anchor")
    e=one(e,
        '''    std::uint64_t tickOf(std::uint64_t pos)const noexcept{return anchorTickLocal_+pos*cpuRate/rate_.load(std::memory_order_relaxed);}''',
        '''    std::uint64_t tickOf(std::uint64_t pos)const noexcept{
        const auto d=pos>=anchorHostPosLocal_?pos-anchorHostPosLocal_:0;
        return anchorTickLocal_+d*cpuRate/rate_.load(std::memory_order_relaxed);
    }''',
        "host position zero re-anchor after guest freewheel")

    e=one(e,
        '''        hostTarget_.store(hostPos_+std::uint64_t(n),std::memory_order_release);wake_.set();
        if(anchorEpoch_.load(std::memory_order_acquire)!=epoch&&offline)''',
        '''        hostTarget_.store(hostPos_+std::uint64_t(n),std::memory_order_release);wake_.set();
        if(!bootGate_.load(std::memory_order_acquire)){
            // The firmware advances independently on the owner thread.
            // Never expose pre-boot audio frames, future/old sample history,
            // or an incorrectly aligned current-DAW MIDI timestamp.
            silence(left,right,n);
            if(channels)for(unsigned c=0;c<8;++c)
                if(channels[c])std::fill_n(channels[c],n,0.0f);
            hostPos_+=std::uint64_t(n);
            return;
        }
        if(anchorEpoch_.load(std::memory_order_acquire)!=epoch&&offline)''',
        "strictly silent DAW render during autonomous original boot")
    e=one(e,
        '''        if(consumerEpoch_!=epoch){consumerEpoch_=epoch;nextPull_=base;history_.fill({});channelHistory_.fill({});}''',
        '''        const auto gen=streamGeneration_.load(std::memory_order_acquire);
        if(consumerEpoch_!=epoch||consumerGeneration_!=gen){
            consumerEpoch_=epoch;consumerGeneration_=gen;nextPull_=base;
            history_.fill({});channelHistory_.fill({});
        }''',
        "reset main and individual outputs at new host audio epoch")
    e=one(e,
        '''            const std::int64_t first=std::int64_t(hostPos_)-latency;''',
        '''            const std::int64_t first=std::int64_t(hostPos_)-
                std::int64_t(anchorHostPos_.load(std::memory_order_relaxed))-latency;''',
        "stereo 48k host base after independent original boot")
    e=one(e,
        '''                const std::int64_t rel=std::int64_t(hostPos_)+j-latency;if(rel<0)return false;''',
        '''                const std::int64_t rel=std::int64_t(hostPos_)+j-
                    std::int64_t(anchorHostPos_.load(std::memory_order_relaxed))-latency;
                if(rel<0)return false;''',
        "sample-rate-converted host base after independent original boot")

    e=one(e,
        '''    void sink(std::span<const host::StereoFrame> frames){
        if(samplingTraceRecording_''',
        '''    void sink(std::span<const host::StereoFrame> frames){
        // Original CPU/DSP still executes; the discarded preboot sound is
        // deliberately not part of the host song timeline.
        if(!bootGate_.load(std::memory_order_acquire)){dspSignal_.set();return;}
        if(samplingTraceRecording_''',
        "drop preboot renderer only, never skip original audio hardware clocks")
    e=one(e,
        '''            [this](std::span<const ChannelRing::Frame> frames){channelRing_.alignTo(ring_.written());channelRing_.push(frames);});''',
        '''            [this](std::span<const ChannelRing::Frame> frames){
                if(!bootGate_.load(std::memory_order_acquire))return;
                channelRing_.alignTo(ring_.written());channelRing_.push(frames);
            });''',
        "suppress preboot eight channel output too")

    e=one(e,
        '''            // Old pipeline drained, then destroyed (joins its DSP) before the new one exists.
            quiesce();''',
        '''            // The host stops observing DSP/ring frames BEFORE old
            // hardware is replaced. New guest boot proceeds independently.
            bootGate_.store(false,std::memory_order_release);
            // Old pipeline drained, then destroyed (joins its DSP) before the new one exists.
            quiesce();''',
        "audio gate before replacing original hardware")
    e=one(e,
        '''            gOffset_=G_;installAudio();''',
        '''            gOffset_=G_;
            const auto bootStartMs=std::uint64_t(std::chrono::duration_cast<
                std::chrono::milliseconds>(std::chrono::steady_clock::now().
                    time_since_epoch()).count());
            autonomousBoot_.begin(G_,bootStartMs);
            installAudio();''',
        "independent startup begins at original reset, not at DAW play")

    bind='hostInput_->bind(localAnchorEpoch_,rate_.load(),anchorTickLocal_,gOffset_,settings_.inputGain*std::pow(10.,settings_.sampleInputTrimDb/20));'
    if e.count(bind)!=2:
        raise RuntimeError("P021 owner input clock bind expected exactly two source calls")
    e=e.replace(bind,
        'hostInput_->bind(localAnchorEpoch_,rate_.load(),anchorTickLocal_,gOffset_,settings_.inputGain*std::pow(10.,settings_.sampleInputTrimDb/20),anchorHostPosLocal_);')

    e=one(e,
        '''    bool quitRequested(){std::lock_guard l(mutex_);return quit_;}''',
        '''    void handoffAutonomousBoot(bool playable){
        if(!autonomousBoot_.active())return;
        const auto base=hostTarget_.load(std::memory_order_acquire);
        const auto streamBase=ring_.written();
        // These are owner/consumer synchronization operations, NEVER
        // run on a host audio callback. During the gate the render callback
        // only outputs silence; it cannot access either ring.
        ring_.discardPreviouslyRendered();
        channelRing_.resetTo(streamBase);
        hostInput_->discard(base);
        restartPipe();
        autonomousBoot_.handoff(G_,base);
        originalBootBatch_.ready();
        anchorHostPosLocal_=base;
        anchorTickLocal_=G_;
        anchorHostPos_.store(base,std::memory_order_relaxed);
        anchorFrame_.store(streamBase,std::memory_order_relaxed);
        anchorTick_.store(G_,std::memory_order_relaxed);
        localAnchorEpoch_=epoch_.load(std::memory_order_acquire);
        streamGeneration_.fetch_add(1,std::memory_order_release);
        anchorEpoch_.store(localAnchorEpoch_,std::memory_order_release);
        if(!playable)
            error_="Original startup fell back to host pacing without a "
                   "playable Pxx. Check the boot clock/HDD/OS in Status.";
        bootGate_.store(true,std::memory_order_release);
        anchorSignal_.set();wake_.set();
    }
    bool advanceAutonomousBoot(){
        if(!autonomousBoot_.active())return false;
        // MIDI arriving before the original firmware has accepted its bank
        // cannot be replayed later at the wrong DAW position. Count and
        // discard it explicitly; project recall remains handled separately.
        while(events_.front()){
            events_.pop();eventDrops_.fetch_add(1,std::memory_order_relaxed);
            bootMidiDiscarded_.fetch_add(1,std::memory_order_relaxed);
        }
        // Drain host preboot audio input so a stopped DAW buffer cannot
        // saturate its SPSC queue while the original CPU starts.
        hostInput_->discard(hostTarget_.load(std::memory_order_acquire));
        if(!machine_||halted_){handoffAutonomousBoot(false);return false;}
        if(presetDisplayed()){
            // The native DSP worker's boot blocks must finish before the
            // host begins consuming the new original sound stream.
            if(nonlinear()){
                const auto stats=machine_->chipAudioStats();
                if(stats.queuedFrames||stats.queuedBlocks){dspSignal_.wait(2);return true;}
            }
            handoffAutonomousBoot(true);return true;
        }
        const auto wallMs=std::uint64_t(std::chrono::duration_cast<
            std::chrono::milliseconds>(std::chrono::steady_clock::now().
                time_since_epoch()).count());
        if(autonomousBoot_.exceeded(G_,wallMs)){
            handoffAutonomousBoot(false);return true;
        }
        // Run ACTUAL original hardware at most 12/15ms worth of 4MHz
        // clocks per dispatch, regardless of DAW callback activity.
        // No ROM instruction, disk sector, SAR read or DSP tick is skipped.
        runTicks(portable::AutonomousBootTimeline::quantum(nonlinear()));
        return true;
    }
    bool quitRequested(){std::lock_guard l(mutex_);return quit_;}''',
        "bounded independent original boot and reanchor handshake")

    e=one(e,
        '''        s.recallProgram=recallProgram_.load();s.recallPending=recallPending_;''',
        '''        s.recallProgram=recallProgram_.load();s.recallPending=recallPending_;
        s.autonomousBoot=autonomousBoot_.active();
        s.bootMidiDiscarded=bootMidiDiscarded_.load(std::memory_order_relaxed);''',
        "host-readable status for autonomous original bootstrap")

    e=one(e,
        '''            if(epoch!=localAnchorEpoch_){
                anchorTickLocal_=G_;anchorFrame_.store(expectedFrames(G_),std::memory_order_relaxed);anchorTick_.store(G_,std::memory_order_relaxed);
                localAnchorEpoch_=epoch;anchorEpoch_.store(epoch,std::memory_order_release);anchorSignal_.set();
            }
            bool behind=false;
            try{behind=advance();}catch(const std::exception& e){halt(e.what());}''',
        '''            if(epoch!=localAnchorEpoch_&&!autonomousBoot_.active()){
                anchorHostPosLocal_=0;anchorHostPos_.store(0,std::memory_order_relaxed);
                anchorTickLocal_=G_;anchorFrame_.store(expectedFrames(G_),std::memory_order_relaxed);anchorTick_.store(G_,std::memory_order_relaxed);
                localAnchorEpoch_=epoch;anchorEpoch_.store(epoch,std::memory_order_release);anchorSignal_.set();
            }
            bool behind=false;
            try{behind=autonomousBoot_.active()?
                advanceAutonomousBoot():advance();
            }catch(const std::exception& e){halt(e.what());}''',
        "machine owner runs real boot without audio host clock and rejoins epochs")

    i=one(i,
        'std::uint64_t epoch_=0,anchor_=0,offset_=0;double rate_=48000,gain_=1;',
        'std::uint64_t epoch_=0,anchor_=0,offset_=0,hostOrigin_=0;double rate_=48000,gain_=1;',
        "extend causal ADC host time origin")
    i=one(i,
        '''    void bind(std::uint64_t epoch,double rate,std::uint64_t anchor,std::uint64_t offset,double gain)noexcept {
        if(epoch!=epoch_){have_=false;epoch_=epoch;}rate_=rate;anchor_=anchor;offset_=offset;gain_=gain;
    }''',
        '''    void bind(std::uint64_t epoch,double rate,std::uint64_t anchor,std::uint64_t offset,
              double gain,std::uint64_t hostOrigin=0)noexcept {
        if(epoch!=epoch_){have_=false;epoch_=epoch;}
        rate_=rate;anchor_=anchor;offset_=offset;gain_=gain;hostOrigin_=hostOrigin;
    }''',
        "map original ADC input to post-boot DAW host sample origin")
    i=one(i,
        '''        const double p=(double(tick)+frac+double(offset_)-double(anchor_))*rate_/4000000.0-1;''',
        '''        const double p=(double(tick)+frac+double(offset_)-double(anchor_))*
            rate_/4000000.0+double(hostOrigin_)-1;''',
        "host ADC analog interpolation after first real Pxx")
    i=one(i,
        '''        advance((double(tick)+double(offset_)-double(anchor_))*rate_/4000000.0-1);''',
        '''        advance((double(tick)+double(offset_)-double(anchor_))*
            rate_/4000000.0+double(hostOrigin_)-1);''',
        "ADC idle/queue progress matches host epoch base")

    r=one(r,
        '''    std::uint64_t written()const noexcept{return w_.load(std::memory_order_acquire);}''',
        '''    std::uint64_t written()const noexcept{return w_.load(std::memory_order_acquire);}
    // Only the owner when bootGate is false: drain all irrelevant preboot
    // frames without changing their virtual indices or touching w_.
    void discardPreviouslyRendered()noexcept{
        r_.store(w_.load(std::memory_order_acquire),std::memory_order_release);
    }''',
        "release boot ring capacity at safe audio handoff")
    r=one(r,
        '''    ChannelRing():data_(capacity){}''',
        '''    ChannelRing():data_(capacity){}
    // Only when the host render gate is closed and the DSP is drained.
    void resetTo(std::uint64_t frame)noexcept{
        w_.store(frame,std::memory_order_release);
    }''',
        "align eight individual outs with final main ring after freewheel")

    v=one(v,
        '''         <<L"\\nFirmware boot: "<<wide(portable::bootStageName(s.boot.stage))''',
        '''         <<L"\\nBoot drive: "<<(s.autonomousBoot?
            L"AUTONOMOUS ORIGINAL 4MHz (DAW-independent)":
            L"HOST-PACED / READY")
         <<L"; MIDI during boot ignored: "<<s.bootMidiDiscarded
         <<L"\\nFirmware boot: "<<wide(portable::bootStageName(s.boot.stage))''',
        "visible autonomous boot and MIDI drop disclosure")
    return e,i,r,v

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--verify",action="store_true")
    args=ap.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P021 original 4MHz kernel SHA mismatch")
    targets=patch(ENG.read_text(encoding="utf-8"),
                  INPUT.read_text(encoding="utf-8"),
                  RING.read_text(encoding="utf-8"),
                  EDITOR.read_text(encoding="utf-8"))
    if args.verify:
        print("P021 DAW-independent original 4MHz boot / safe host reanchor anchors PASS")
        return
    shutil.copyfile(ROOT/"src/125a_autonomous_boot_timeline.h",
                    UP/"src/125a_autonomous_boot_timeline.h")
    for path,body in zip((ENG,INPUT,RING,EDITOR),targets):
        path.write_text(body,encoding="utf-8",newline="\n")
    print("P021 owner autonomous original firmware boot + DAW reanchor integrated")

if __name__=="__main__":main()
