#!/usr/bin/env python3
"""P016: bound audio-ring silence writes during long host stalls.

The original source iterates over *every* missing 48-kHz frame, including
multi-minute host discontinuities, even after it has filled all 2.7 seconds
of the physically stored ring. Change only the redundant no-audio fill:
the virtual write index still advances by the entire original gap.
Non-silent frames, original CPU/DSP timing, and MIDI are unchanged.
"""
import argparse
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/"upstream/eii-emu"
RT=UP/"src/vst3/rt_primitives.h"
PIN="e345bcf00af8a066ebace9168cf0b6c3a40ca164"

def one(src,old,new,which):
    count=src.count(old)
    if count!=1:
        raise RuntimeError(f"P016 {which}: source anchor matches {count}, expected 1")
    return src.replace(old,new,1)

def patch(s):
    if "boundedSilence" in s:
        raise RuntimeError("P016 already installed")
    old='''    void pushSilence(std::uint64_t n)noexcept{
        auto w=w_.load(std::memory_order_relaxed);const auto r=r_.load(std::memory_order_acquire);
        for(std::uint64_t i=0;i<n;++i,++w)if(w<r||w-r<capacity)data_[w&(capacity-1)]={};
        w_.store(w,std::memory_order_release);wakeConsumer();
    }'''
    new='''    void pushSilence(std::uint64_t n)noexcept{
        // A silent host discontinuity can span millions of virtual frames.
        // Ring storage has only 'capacity' cells: writing any cell more
        // than once before advancing w_ is redundant. Crucially, the exact
        // original virtual frame count STILL advances by n.
        const auto w=w_.load(std::memory_order_relaxed);
        const auto r=r_.load(std::memory_order_acquire);
        const auto freeSlots=w>=r?(w-r<capacity?capacity-(w-r):0):
            capacity; // reader already ahead: every cell may be cleared
        const auto boundedSilence=std::min<std::uint64_t>(n,
            std::min<std::uint64_t>(capacity,freeSlots));
        for(std::uint64_t i=0;i<boundedSilence;++i)data_[(w+i)&(capacity-1)]={};
        w_.store(w+n,std::memory_order_release);wakeConsumer();
    }'''
    s=one(s,old,new,"FrameRing long empty rebase")
    old='''    void alignTo(std::uint64_t index)noexcept{auto w=w_.load(std::memory_order_relaxed);for(;w<index;++w)data_[w&(capacity-1)]={};w_.store(w,std::memory_order_release);}'''
    new='''    void alignTo(std::uint64_t index)noexcept{
        const auto w=w_.load(std::memory_order_relaxed);
        if(index<=w)return; // keep the channel writer index monotonic
        const auto gap=index-w;
        // After one full 2.7 s ring pass, all channel slots are zero.
        const auto boundedSilence=std::min<std::uint64_t>(gap,capacity);
        for(std::uint64_t i=0;i<boundedSilence;++i)data_[(w+i)&(capacity-1)]={};
        w_.store(index,std::memory_order_release);
    }'''
    s=one(s,old,new,"ChannelRing gap alignment")
    return s

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--verify",action="store_true")
    v=a.parse_args()
    sha=subprocess.check_output(["git","-C",str(UP),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN:raise RuntimeError("P016 original kernel SHA mismatch")
    src=RT.read_text(encoding="utf-8")
    dst=patch(src)
    if v.verify:
        print("P016 bounded silence frame/channel rings source anchors: PASS")
        return
    RT.write_text(dst,encoding="utf-8",newline="\n")
    print("P016 host-gap silence now bounded by physical ring storage")

if __name__=="__main__":main()
