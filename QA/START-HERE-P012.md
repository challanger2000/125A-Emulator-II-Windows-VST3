# 125A Emulator II – P012 – START HERE

**Development build, not final; do not replace P008 or your working installation.**

P012 adds original .EII bank file integrity checks (factory-size 485,887
bytes only; no silent padding of incomplete or unknown variants). The hard
disk importer now differentiates a raw, unformatted 20 MB image (zero usable
bank slots) from a formatted but full HDD. The creation dialog explicitly
instructs the original HD OS 3.1 SPECIAL 22 formatting procedure.

P011 safe WAV cancel, P010 embedded selected-file bank snapshots, and all
earlier original firmware bridge work are retained.

**Not done:** Turbo boot/import, user-friendly automatically guided complete
HDD setup, original ROM/OS cancel acceptance, arbitrary live RAM snapshots,
save-during-import handling, C3 mapping, host-performance tuning and final
Studio One save/close/reopen testing.

CI: C++ media tests, source integration, Linux native original SAR regressions,
Windows VST3 build/Steinberg validator/project-state host tests. The public
package has NO original E-mu ROM/OS and no private user sound banks.

Development PR: https://github.com/challanger2000/125A-Emulator-II-Windows-VST3/pull/10
