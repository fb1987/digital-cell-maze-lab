"""Saved-only algebra check of the frozen output nominees and secondary C6 edit."""
import base64,hashlib,json,sys,zlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.output_access_m31 import OUT,readz,load,writej,check

def main():
    check();assert not (OUT/'readout_algebra_note.json').exists();assert json.loads((OUT/'trace_audit.json').read_text())['status']=='PASS'
    choices=readz(OUT/'choices.json.gz');pool=readz(OUT/'pool.json.gz');conditions={c['id']:c for c in pool['conditions']}
    output={c['id'] for c in choices['choices'] if c['arm']=='output'};secondary='m31/donor/C6/draw0013'
    data,rows,models,usage,chain=load('trace');mazes={m['case_id']:m for m in data['mazes']};checked={};secondary_values=0;secondary_cases=0
    for identity in output:
        e=conditions[identity]['event'];assert (e['kind'],e['block'],e['index'],e['replacement'])==('delete',2,0,2)
        checked[identity]=dict(cases=0,complete_tick_site_checks=0)
    for spec,r in models:
        relevant=output&set(spec['aliases']);special=secondary in spec['aliases']
        if not relevant and not special:continue
        for t in r['traces']:
            raw=zlib.decompress(base64.b64decode(t['history_b64']));assert hashlib.sha256(raw).hexdigest()==t['history_sha256'];h=np.frombuffer(raw,dtype='<u2').reshape(t['history_shape'])
            m=mazes[t['case']];cells=np.frombuffer(bytes.fromhex(m['cells_hex']),np.uint8);old=h[:-1].astype(np.int64)
            if relevant:
                predicted=np.where(old[:,1]>0,np.minimum(65535,old[:,2]+old[:,3]),0).astype(np.uint16)
                predicted[:,m['start']]=np.where(old[:,1,m['start']]>0,old[:,1,m['start']],0)
                predicted[:,cells==0]=0;assert np.array_equal(predicted,h[1:,2])
                for identity in relevant:checked[identity]['cases']+=1;checked[identity]['complete_tick_site_checks']+=(len(h)-1)*int(sum(cells))
            if special:
                predicted=old[:,2].astype(np.uint16);predicted[:,cells==0]=0;assert np.array_equal(predicted,h[1:,6])
                secondary_cases+=1;secondary_values+=(len(h)-1)*int(sum(cells))
    assert all(c['cases']==288 for c in checked.values()) and secondary_cases==288
    writej(OUT/'readout_algebra_note.json',dict(status='PASS',saved_only_posthoc=True,new_inference=0,selected_output_checks=checked,
        output_equation='Non-source: C2_next=0 if C1==0 else sat(C2+C3). Source: C2_next=C1. The common gene deletion replaces the old gated XOR increment with physical C3; it retains nonnegative accumulation.',
        secondary_C6=dict(id=secondary,cases=secondary_cases,complete_tick_site_checks=secondary_values,equation='C6_next=C2 (same site, PREVIOUS tick)',
            note='C2 remains its inherited gated XOR accumulator; this creates delayed local feedback, not a neighbor-predecessor map.'),
        limitation='Checked only the frozen nominees on their full actual controlled histories; no claim about untraced proposals or all possible inputs. Algebra interpreted from fixed genotypes, no reduced program used for inference.'))

if __name__=='__main__':main()
