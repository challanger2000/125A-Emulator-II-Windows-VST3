// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// Original-ROM Pxx LCD appears shortly before its SCN2651 UART is enabled.
// Guest is playable only when both independent original-hardware facts hold.
// No emulator state, firmware or oscillator is altered.
namespace eii::portable {
constexpr bool firmwarePlayable(bool originalPresetDisplayed,
                                bool originalMidiUartEnabled) noexcept {
    return originalPresetDisplayed && originalMidiUartEnabled;
}
} // namespace eii::portable
