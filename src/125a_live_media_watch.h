// SPDX-License-Identifier: GPL-3.0-only
#pragma once
// P015: conservative observer of REAL firmware media-receive counters.
// It never claims a complete bank-load solely from bytes being read.
// It only invalidates the assertion that the last DISK7 snapshot is current.
#include <cstdint>

namespace eii::portable {
class LiveMediaWatch {
public:
    void reset()noexcept{
        ready_=false;seeded_=false;floppyBytes_=hddBytes_=0;
    }
    bool armed()const noexcept{return ready_;}
    bool observe(bool firmwarePreset,bool originalSampling,
                 std::uint64_t floppyReceived,std::uint64_t hddReceived)noexcept {
        if(!seeded_){
            floppyBytes_=floppyReceived;hddBytes_=hddReceived;seeded_=true;
            if(firmwarePreset)ready_=true;
            return originalSampling;
        }
        // Before original firmware has entered the performance Pxx display,
        // ignore boot-OS reads, which cannot describe a user bank change.
        if(!ready_){
            floppyBytes_=floppyReceived;hddBytes_=hddReceived;
            if(firmwarePreset)ready_=true;
            return originalSampling;
        }
        // These are real SIO decoder character completions and HDD bytes read
        // by the firmware, never merely drive spin/rotation or select pulses.
        // Counter decreases on reset are not evidence of new bank bytes.
        const bool transfer=floppyReceived>floppyBytes_||hddReceived>hddBytes_;
        floppyBytes_=floppyReceived;hddBytes_=hddReceived;
        return originalSampling||transfer;
    }
private:
    bool ready_=false,seeded_=false;
    std::uint64_t floppyBytes_=0,hddBytes_=0;
};
} // namespace eii::portable
