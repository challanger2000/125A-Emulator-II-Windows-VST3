// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Verified with the user's private original ROM and EII Choir floppy:
// the LCD first displays P01 before the original SCN2651 has enabled its
// MIDI mode/receiver. Host note playback must wait for BOTH signals.
namespace eii::portable {
constexpr bool originalFirmwareMidiReady(bool presetDisplayed,
                                         bool originalScn2651Enabled)noexcept{
    return presetDisplayed&&originalScn2651Enabled;
}
} // namespace eii::portable
