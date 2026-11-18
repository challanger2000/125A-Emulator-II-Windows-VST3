// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// P012: distinguish a factory-sized .EII performance bank from an
// incomplete file, and distinguish blank, unformatted HDD media from free slots.
#include "eii_bank_format.h"
#include <cstddef>
#include <cstdint>
#include <span>

namespace eii::portable {
inline constexpr std::size_t originalEiiBankBytes=bank::eiiBytes;
inline bool canonicalEiiBankSize(std::size_t bytes)noexcept{
    return bytes==originalEiiBankBytes;
}
struct HddSlots{
    unsigned capacity=0,available=0;
    bool unformatted=false;
};
inline HddSlots inspectHdd(std::span<const std::uint8_t> image) noexcept{
    HddSlots s;
    s.capacity=bank::hddSlotCount(image.size());
    if(s.capacity==0)return s;
    bool namesAllZero=true;
    for(unsigned slot=0;slot<s.capacity;++slot){
        const std::size_t offset=bank::hddDirBase+bank::hddDirStride*slot;
        for(unsigned i=0;i<bank::nameBytes;++i)
            namesAllZero&=image[offset+i]==0;
        if(bank::hddSlotFree(image,slot))++s.available;
    }
    s.unformatted=namesAllZero;
    if(s.unformatted)s.available=0;
    return s;
}
} // namespace eii::portable
