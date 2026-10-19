"""Read-only audit of preserved program interfaces; no candidate calls."""
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.foundation_calibration import ROOT,write_json
from maze_evolution.foundation_study import read_compressed,compressed_json
from maze_evolution.exposure_genome import Individual,Genome
from maze_evolution.growth import Genome as Program
from maze_evolution.composition_operator import rows,sites,interface
from maze_evolution.mutation_accessibility_study import PRIOR,sha

OUT=ROOT/'results/research_reset'

def panel():
    p={}
    def add(label,raw,origin):
        raw=dict(raw)
        if raw['genome']['version']!=4:raw['genome']=Genome(Program.from_dict(raw['genome']),7).to_dict()
        i=Individual.load(raw);p[label]=dict(item=i.save(),source=origin,genome_digest=i.genome.digest,
            static_interface=interface(rows(i.genome.program)),genes=len(i.genome.genes),runtime='M local/all-on for prospective comparisons')
    j=read_compressed(ROOT/'results/lineage_confirmation/panel.json.gz')
    for label in ('shared_ancestor','branch_narrow','branch_broad','local_long','local_cycle','resampled','k2_target','k2_entry'):
        add('historical/'+label,j[label]['item'],'results/lineage_confirmation/panel.json.gz:'+label)
    p0=read_compressed(ROOT/'results/mutation_transition/panel.json.gz')['items']
    for label in ('route/d9','reach1/d16','reach2/d16'):
        add('P/'+label,p0[label],'results/mutation_transition/panel.json.gz:'+label)
    q=read_compressed(ROOT/'results/shared_prefix/choices.json.gz')['items']
    for label in ('fresh/0/mixed/primary','fresh/1/current/primary','fresh/2/mixed/primary','carry/0/resample/primary'):
        add('Q/'+label,q[label],'results/shared_prefix/choices.json.gz:'+label)
    r=read_compressed(ROOT/'results/mutation_accessibility/pool.json.gz')
    label='accessibility/Qfresh0/1/walk2/d16';add('R/exception',r['entries'][label]['item'],'results/mutation_accessibility/pool.json.gz:'+label)
    return p

def main():
    assert not (OUT/'architecture.json').exists();OUT.mkdir(exist_ok=True)
    pp=panel();compressed_json(OUT/'panel.json.gz',pp);comparisons=[]
    for a,x in pp.items():
        for b,y in pp.items():
            if a==b:continue
            aa=rows(Individual.load(x['item']).genome.program);bb=rows(Individual.load(y['item']).genome.program)
            s=sites(aa,bb)
            comparisons.append(dict(recipient=a,donor=b,exact_rows_shared=len(set(aa)&set(bb)),compatible_sites=[list(q) for q in s]))
    prior=0
    for stage in (*PRIOR,'mutation_accessibility'):
        for path,h in json.loads((ROOT/'results'/stage/'completion.json').read_text())['source_and_artifact_sha256'].items():assert sha(ROOT/path)==h,path;prior+=1
    assert prior==2913
    out=dict(candidate_calls=0,prior_hashes=prior,models=len(pp),directed_pairs=len(comparisons),compatible_pairs=sum(bool(x['compatible_sites']) for x in comparisons),
        comparisons=comparisons,source_hashes={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'maze_evolution/exposure_runtime.py',ROOT/'maze_evolution/composition_operator.py',Path(__file__).resolve())},
        evidence_scope='Static structural compatibility only; no fitness or transfer evaluation; legacy V3 programs copied exactly into V4 wrapper, exposure7, originals unchanged.')
    write_json(OUT/'architecture.json',out)
    print({k:v for k,v in out.items() if k not in ('comparisons','source_hashes')})
    print([(x['recipient'],x['donor'],len(x['compatible_sites'])) for x in comparisons if x['compatible_sites']])
if __name__=='__main__':main()
