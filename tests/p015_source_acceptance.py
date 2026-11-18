#!/usr/bin/env python3
"""P015 observe actual original EII SIO and HDD received bytes, not image selection."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"upstream/eii-emu/src/vst3"
eng=(root/"plugin_engine.h").read_text(encoding="utf-8")
def need(marker):
    if marker not in eng:raise AssertionError("Missing P015 original firmware media policy: "+marker)
for marker in (
    '#include "125a_live_media_watch.h"',
    'portable::LiveMediaWatch bankMediaWatch_;',
    'void observeMediaReads(){',
    'machine_->diskSio.channels[0].rx.characters',
    'machine_->hardDisk->bytesRead',
    'presetDisplayed(),mode.known&&mode.high',
    'bankNeedsSnapshot_.exchange(true,std::memory_order_acq_rel)',
    'bankMediaWatch_.reset();',
    'if(!embeddedBank_&&(!c.hdd.empty()||!c.floppy.empty()))',
    'Original firmware accessed floppy/HDD or entered SAMPLE.',
):
    need(marker)
r=eng[eng.index('void runTicks('):eng.index('bool quitRequested()',eng.index('void runTicks('))]
assert r.index('machine_->run(n);')<r.index('observeMediaReads();')<r.index('bankStep();')
assert r.count('observeMediaReads();')==1
b=eng[eng.index('void bootNow(bool discard,bool fromState)'):eng.index('    // ---- input ----')]
assert b.index('bankMediaWatch_.reset();')<b.index('if(bootSelectedBank){')
assert b.index('if(!embeddedBank_&&(!c.hdd.empty()||!c.floppy.empty()))')<b.index('if(bootSelectedBank){')
assert 'projectMedia_.reset()' not in eng[eng.index('void observeMediaReads()'):eng.index('void bankStep()')]
print("P015 hardware-received floppy/HDD/SAR activity and original DISK7 ordering: PASS")
