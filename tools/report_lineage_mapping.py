"""Tables from sealed V12U records; no inference, selection or source changes."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.lineage_mapping_data import OUT,read_compressed
from maze_evolution.exposure_genome import Individual
from maze_evolution.regulatory import NAMES

def main():
    p=read_compressed(OUT/'panel.json.gz');m=read_compressed(OUT/'metrics.json.gz');a=read_compressed(OUT/'analysis.json.gz');out=[]
    out+=['# V12U data tables','', 'Generated from saved native emissions; no candidate calls. Poses/variants are correlated.', '', '| Identity | Genes | All pairs /1152 | Positive pairs /960 | All-eight-pose groups | Corridors /768 | Ordinary trees /192 | Ordinary cyclic /192 | No-path /768 |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,pid in p['aliases'].items():
        s=m[pid+'|normal'];f=s['families'];n=len(Individual.load(p['items'][name]).genome.program.genes)
        out.append(f"| {name} | {n} | {s['pairs']} | {s['positive']} | {s['full_groups']} | {f['corridor']['optimal']} | {f['ordinary_perfect']['optimal']} | {f['ordinary_random']['optimal']} | {f['disconnected']['no_path']+f['ordinary_disconnected']['no_path']} |")
    out+=['','All-eight-pose groups include prefix0; inspect metrics for prefix-specific success.','', '| Edit | Kind/index (zero-based) | Previous gene | New gene | Positive pairs gained/lost | Masks changed | Stops changed |','|---|---|---|---|---:|---:|---:|']
    edits=[]
    for before,after in zip(p['chain'],p['chain'][1:]):
        e=p['events'][after]['mutation'][0];g=Individual.load(p['items'][before]).genome.program.genes[e['index']];row=e.get('row');new=(NAMES[row[0]]+' '+str(row)) if row else e['kind']+(f" {e['count']} genes" if 'count' in e else '')
        c=a['comparisons'][before+'->'+after];gains=sum(v['gained'] for v in c['positive_by_context'].values());losses=sum(v['lost'] for v in c['positive_by_context'].values())
        old=NAMES[g.op]+' '+str(g.row())
        out.append(f"| {after} | {e['kind']} /{e['index']} | {old} | {new} | +{gains}/−{losses} | {c['changed_responses']['mask']} | {c['changed_responses']['steps']} |")
        edits.append(dict(before=before,after=after,mutation=e,old_gene=g.row(),new_gene=row,positive_gained=gains,positive_lost=losses,changed_responses=c['changed_responses'],birth=p['items'][after]['birth']))
    out+=['','Gene fields: opcode, destination, operand a, operand b, operand c, radius, gate. Gate64 means always. Local topology remains fixed, including for REMOTE_MIN. Edits are interpreted in their historical parent, not transplanted into the root.','', '| Identity | Normal pairs /96 | Pulse-off retained | Flag-off retained | Output-read-off retained | Halt-request-off retained |','|---|---:|---:|---:|---:|---:|']
    for name,ds in a['interventions'].items():
        if not ds:continue
        normal=ds['pulse_off']['normal_success'];vals=[ds[k]['retained'] for k in ('pulse_off','flag_off','output_feedback_off','halt_off')]
        out.append(f"| {name} | {normal} | "+' | '.join(map(str,vals))+' |')
    out+=['','Retention is conditional on normal successes in the fixed diagnostic subset. New diagnostic successes are separately preserved in analysis.json.gz. Interventions apply to all subset inputs, without success filtering.','']
    (OUT/'data_tables.md').write_text('\n'.join(out))
    (OUT/'edit_descriptions.json').write_text(json.dumps(dict(candidate_calls=0,edits=edits),indent=2)+'\n')

if __name__=='__main__':main()
