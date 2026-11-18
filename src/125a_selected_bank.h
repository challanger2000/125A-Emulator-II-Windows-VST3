// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// P010: immutable copy of a selected original EII bank image for VST3 recall.
// The source image can be ejected or edited without changing the committed copy.
// This is a FILE-bank snapshot, not a live sampler-RAM snapshot.
#include "125a_portable_state.h"
#include <memory>
namespace eii::portable {
inline std::shared_ptr<const std::vector<std::uint8_t>>
cloneSelectedBank(std::span<const std::uint8_t> image) {
    if(image.size()!=bankBytes)
        throw std::runtime_error("Selected EII bank has invalid expanded floppy image length");
    auto owned=std::make_shared<std::vector<std::uint8_t>>(image.begin(),image.end());
    // Never embed E-mu OS bytes into a DAW project.
    std::fill_n(owned->begin(),bankDataOffset,std::uint8_t{0});
    return owned;
}
} // namespace eii::portable
