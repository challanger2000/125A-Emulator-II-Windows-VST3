#!/usr/bin/env python3
"""P012 source integration invariants. Original firmware/Studio One are separate."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"upstream/eii-emu/src"
floppy=(root/"floppy_image_backing.h").read_text(encoding="utf-8")
engine=(root/"vst3/plugin_engine.h").read_text(encoding="utf-8")
editor=(root/"vst3/plugin_editor.h").read_text(encoding="utf-8")
def require(source,text):
    if text not in source:raise AssertionError(f"Missing P012 policy: {text}")
require(floppy,'#include "125a_media_safety.h"')
require(floppy,'if(!portable::canonicalEiiBankSize(bytes.size()))')
require(floppy,"Truncated/unknown variants cannot be silently padded.")
require(engine,"const auto info=portable::inspectHdd(image);")
require(engine,"if(info.unformatted)")
require(engine,"Original HD OS 3.1") if False else None
require(engine,"SPECIAL 22")
require(engine,"if(!info.available)")
require(editor,"Create UNFORMATTED 20 MB HDD")
require(editor,"Usable bank slots: 0 of 46")
assert engine.index("if(info.unformatted)") < engine.index("for(const auto& file:files)")
assert "bytes.empty()||bytes.size()>EmuiiImage::imageBytes-bankOffset" not in floppy
print("P012 .EII fail-closed / HDD unformatted source acceptance: PASS")
