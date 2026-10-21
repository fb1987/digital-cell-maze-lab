"""M2 audit-only JSON normalization; scientific source and outputs stay frozen."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution import wave_accessibility as m


def main():
    repair=json.loads((m.OUT/'audit_repair.json').read_text())
    for p,h in repair['files'].items():assert m.sha(m.ROOT/p)==h,p
    m.pushed(m.OUT/'audit_repair.json');m.check()
    original=m.final_analysis
    # Canonicalize only the recomputed report's JSON representation. No values,
    # memberships, source, candidate responses, scoring or selection are changed.
    m.final_analysis=lambda:m.canonical(original())
    m.audit(True)


if __name__=='__main__':main()
