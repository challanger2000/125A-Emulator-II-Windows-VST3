#!/usr/bin/env python3
"""Source-verified P008 invariants; actual binary and private ROM acceptance are separate."""
from pathlib import Path
s=(Path(__file__).resolve().parents[1]/"upstream/eii-emu/src/vst3/plugin_engine.h").read_text()
def need(x):
    if x not in s:raise AssertionError(f"Missing P008 source policy: {x}")
# Ensure Eject only clears physical disk, NOT the independently committed project media.
a=s[s.index('std::string mountFloppyNow('):s.index('static std::filesystem::path recoveryFolder()')]
need('if(!path.empty()&&!sameImage(path,settings_.osImage))')
assert a.index('if(!path.empty()&&!sameImage(path,settings_.osImage))')<a.index('projectMedia_.reset()')
assert a.count('projectMedia_.reset()')==1
assert a.count('embeddedBank_.reset()')==1
# The WAV constructor must not require a mounted floppy and must prepare a
# private writable OS medium before pressing the actual firmware SAMPLE key.
w=s[s.index('void autoImportWav('):s.index('void cancelAutoWav()')]
assert '!floppyState().mounted' not in w
for v in ('settings_.osImage','host::FloppyImageBacking os','125A-Temporary-OS31.emuiifd','installFloppy(*machine_,temp)','wavAction(first.action)'):assert v in w
assert w.index('installFloppy(*machine_,temp)')<w.index('wavAction(first.action)')
# The original temporary disk is never written directly, project bytes are
# committed only after original firmware DISK7 completes, and old disk returns.
for v in ('void restoreWavOriginalFloppy()', 'restoreWavOriginalFloppy();',
          'if(bankSave_.active()||wavCapture_.active())','wavPreviousFloppy_=floppyBacking_',
          'std::fill_n(bankOnly->begin(),portable::bankDataOffset,0);'):need(v)
assert s.count('restoreWavOriginalFloppy();')>=2
print("P008 WAV auto OS / protected media / Eject recall SOURCE acceptance PASS")
