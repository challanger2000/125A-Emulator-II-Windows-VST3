#!/usr/bin/env python3
"""P039 fail-closed source acceptance of Windows owner-local playback pitch gate."""
from pathlib import Path
import re
import sys
source=Path(__file__).resolve().parents[1]/"tests/p038_windows_original_host_capture.h"
s=source.read_text(encoding="utf-8")
checks={
  "Windows COM owner state explicitly enables C3 remap":
      s.count('settings=replaceKey(settings,"wavmidic3","1");')==1,
  "Test MIDI C3 pitch is 60 (not undocumented raw 48)":
      s.count('note(true,60,0)')==1,
  "Recorded 440Hz frequency is independently measured":
      'const double f=p038Freq(pcm);' in s and
      'std::abs(f-440.0)<=5.0' in s,
  "Host input bus is actual VST3 ProcessData":
      'in.data.inputs[0].silenceFlags=0;' in s and
      'in.process()' in s,
  "Frequency analysis includes both 440 and wrong octave 880":
      'for(int f=200;f<=1200;++f)' in s,
  "Fresh VST3 project replay is still tested":
      'reopened.setState(stored)' in s and 'const auto second=play(reopened)' in s,
}
for name,ok in checks.items():
    print(("PASS " if ok else "FAIL ")+name)
if not all(checks.values()):
    sys.exit(1)
print("P039 Windows owner-local original firmware pitch contract: PASS (source, not original-ROM runtime)")
