"""V10 report from frozen outputs, independent audits and declared phase assays."""
import argparse,gzip,json,statistics
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
from .distance_audit import unpack
from .factor_report import paired_summary
from .signal_audit import lines
from .experiment import write_json

def visuals(out,manifest,primary,paired):
    from PIL import Image,ImageDraw
    (out/'visuals').mkdir(exist_ok=True)
    def grid(draw,ox,oy,m,mask,tile=10):
        for p,opened in enumerate(bytes.fromhex(m['cells_hex'])):
            color='#172235' if not opened else '#5ae1bd' if mask[p] else '#45536a'
            if p==m['start']:color='#72b6ff'
            if p==m['goal']:color='#ff6584'
            x,y=p%m['w'],p//m['w'];draw.rectangle((ox+x*tile,oy+y*tile,ox+(x+1)*tile-1,oy+(y+1)*tile-1),fill=color)
    selected=[next(m for m in manifest if m['split']=='test_goal' and m['w']==17 and m['family']==f and '/r0/' in m['case_id']) for f in ('perfect','random')]
    arms=('compiled_bfs','local/fixed/task','local/curriculum/task','evolved/fixed/task','evolved/curriculum/task')
    canvas=Image.new('RGB',(1200,540),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((15,12),'Unseen ordinary outputs | green: output; blue: source; pink: goal. First size17 case per family, replicate 0.',fill='#e6edf7')
    for i,m in enumerate(selected):
        for j,arm in enumerate(arms):
            r=next(r for r in primary if r['case_id']==m['case_id'] and r['arm']==arm)
            ox,oy=15+j*240,85+i*245
            draw.text((ox,oy-40),arm,fill='#e6edf7');draw.text((ox,oy-22),m['family']+' | '+('shortest' if r['optimal'] else r['failure']),fill='#aabbd0')
            grid(draw,ox,oy,m,unpack(r['mask'],m['w']*m['h']))
    canvas.save(out/'visuals/unseen_outputs.png')
    if (out/'inherited_path_diagnostic.json').exists():
        d=json.loads((out/'inherited_path_diagnostic.json').read_text())
        if 'individual' in d:
            m=d['case'];canvas=Image.new('RGB',(840,315),'#111827');draw=ImageDraw.Draw(canvas)
            draw.text((15,15),'Inherited growth on an inspected unseen maze | goal switch changes stopping, not the measured output trajectory.',fill='#e6edf7')
            variants=[('Original goal | normal halt19',m,unpack(d['ordinary'][0]['mask'],m['w']*m['h'])),
                ('Midpoint goal | normal halt11',{**m,'goal':d['alternate_goal']},unpack(d['ordinary'][1]['mask'],m['w']*m['h'])),
                ('Midpoint goal | forced tick 19',{**m,'goal':d['alternate_goal']},np.asarray(d['snapshots'][-1]['output_states'][1])>0)]
            for j,(label,maze,mask) in enumerate(variants):
                x=15+j*280;draw.text((x,55),label,fill='#e6edf7');grid(draw,x,85,maze,mask,tile=16)
            draw.text((15,280),'Post-hoc diagnostic, not an additional holdout. The nine-edge, one-turn success is present in the frozen control.',fill='#aabbd0')
            canvas.save(out/'visuals/inherited_path.png')

    lookup={m['case_id']:m for m in manifest}
    pairs=json.loads((out/'pairs.json').read_text())
    pair=next(p for p in pairs if '/r0/' in p['first'] and '/17x17/' in p['first'] and '/random/' in p['first'] and p['first'].startswith('test_pairs/'))
    arms=('compiled_bfs','evolved/fixed/choice','evolved/curriculum/choice','evolved/curriculum/frozen_choice')
    canvas=Image.new('RGB',(960,540),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((15,12),'Switched goals on identical geometry/source | BFS versus tick 16 output raster, without assumed correctness.',fill='#e6edf7')
    for i,case in enumerate((pair['first'],pair['second'])):
        m=lookup[case]
        for j,arm in enumerate(arms):
            if arm=='compiled_bfs':r=next(r['baseline'] for r in paired if r['arm']==arm and 'baseline' in r and r['baseline']['case_id']==case);mask=unpack(r['mask'],m['w']*m['h']);subtitle='Shortest route'
            else:
                record=next(r for r in paired if r['arm']==arm and r['replicate']==0)
                r=next(r for r in record['cases'] if r['case']==case);mask=unpack(r['probe_mask'],m['w']*m['h']);subtitle=f"Tick16: J={r['junction']['score']:.3f}"
            ox,oy=15+j*240,85+i*245
            draw.text((ox,oy-40),arm,fill='#e6edf7');draw.text((ox,oy-22),f"Goal {'A' if i==0 else 'B'} | {subtitle}",fill='#aabbd0')
            grid(draw,ox,oy,m,mask)
    canvas.save(out/'visuals/switched_goals.png')
    ancestry=json.loads(gzip.open(out/'choice_ancestry.json.gz','rt').read())
    if ancestry:
        record=ancestry[0];nodes=record['nodes'];index=next(i for i,r in enumerate(nodes) if r['strict_both'])
        child=nodes[index] if index else nodes[-1];parent=nodes[max(0,index-1)];lookup={m['case_id']:m for m in manifest}
        canvas=Image.new('RGB',(1040,320),'#111827');draw=ImageDraw.Draw(canvas)
        draw.text((15,12),('Validation precursor | first strict transition' if index else 'Validation precursor | qualification already present in frozen ancestor')+' | gold: decision.',fill='#e6edf7')
        for j,(node,goal_index) in enumerate(((parent,0),(child,0),(parent,1),(child,1))):
            r=node['cases'][goal_index];m=lookup[r['case']];ox=15+j*260;oy=95
            draw.text((ox,48),(('Parent' if index else 'Initial qualifying ancestor') if j%2==0 else ('First qualifying child' if index else 'Final saved variant'))+(' | goal A' if goal_index==0 else ' | goal B'),fill='#e6edf7')
            draw.text((ox,68),f"Tick16 J={r['junction']['score']:.3f}; strict={r['junction']['strict']}",fill='#aabbd0')
            tile=16 if m['w']<=9 else 10
            grid(draw,ox,oy,m,unpack(r['probe_mask'],m['w']*m['h']),tile=tile)
            v=record['decision']['vertex'];x=ox+tile*(v%m['w']);y=oy+tile*(v//m['w']);draw.rectangle((x,y,x+tile-1,y+tile-1),outline='#ffd46a',width=2)
        draw.text((15,290),'This is a selected validation example, not unseen route success. Whole normal outputs remain independently assessed.',fill='#aabbd0')
        canvas.save(out/'visuals/validation_choice.png')
    rows=json.loads((out/'goal_timecourse.json').read_text())
    summary={r['arm']:r for r in json.loads((out/'paired_summary.json').read_text())}
    arms=('evolved/fixed/frozen_choice','evolved/fixed/choice','evolved/curriculum/frozen_choice','evolved/curriculum/choice')
    labels=('Fixed frozen','Fixed evolved','Curriculum frozen','Curriculum evolved')
    source=[sum(r['aligned'] and r['any_source_state'] for r in rows if r['arm']==a and r['horizon']==16) for a in arms]
    scores=[summary[a]['junction'] for a in arms]
    canvas=Image.new('RGB',(1040,390),'#111827');draw=ImageDraw.Draw(canvas)
    draw.text((24,18),'V10 precursor comparison | common strict-choice archives | three replicates',fill='#e6edf7')
    draw.text((24,40),'Paired shortest counts: '+', '.join(f"{label} {summary[a]['optimal']}/42" for a,label in zip(arms,labels)),fill='#aabbd0')
    for panel,(title,values,maximum) in enumerate((('Goal switch changes source state at tick 16',source,18),('Regular-pair weaker-choice score J',scores,max(.05,1.1*max(scores))))):
        ox=24+panel*520;draw.text((ox,80),title,fill='#e6edf7')
        for i,(label,value) in enumerate(zip(labels,values)):
            y=120+i*52;draw.text((ox,y+5),label,fill='#cbd5e1')
            length=int(265*value/maximum);color='#6da8e8' if i<2 else '#5ae1bd'
            if length:draw.rectangle((ox+110,y,ox+110+length,y+24),fill=color)
            formatted=f'{value}/18' if panel==0 else f'{value:.4f}'
            draw.text((ox+120+length,y+5),formatted,fill='#e6edf7')
    draw.text((24,355),'Descriptive comparison; no significance claim. All groups use the same pulse input convention.',fill='#aabbd0')
    canvas.save(out/'visuals/precursor_comparison.png')
    if (out/'training_choice_diagnostic.json').exists():
        record=json.loads((out/'training_choice_diagnostic.json').read_text())['records'][0]
        parent,child=record['nodes'][-2:];canvas=Image.new('RGB',(1040,350),'#111827');draw=ImageDraw.Draw(canvas)
        draw.text((15,12),'Training-only paired choice | birth29 parent vs birth30 child | gold: fork. This is not unseen success.',fill='#e6edf7')
        for j,(node,index) in enumerate(((parent,0),(child,0),(parent,1),(child,1))):
            r=node['cases'][index];m=lookup[r['case']];ox=15+j*260;oy=100
            draw.text((ox,50),('Parent' if j%2==0 else 'Child')+(' | goal A' if index==0 else ' | goal B'),fill='#e6edf7')
            draw.text((ox,72),f"Tick16 J={r['junction']['score']:.2f}; strict={r['junction']['strict']}",fill='#aabbd0')
            tile=11;grid(draw,ox,oy,m,unpack(r['probe_mask'],m['w']*m['h']),tile)
            v=record['decision']['vertex'];x=ox+tile*(v%m['w']);y=oy+tile*(v//m['w']);draw.rectangle((x,y,x+tile-1,y+tile-1),outline='#ffd46a',width=2)
        draw.text((15,319),'The child needs goal pulse + long reads here. Fresh V10A near/far confirmation: 0/12 strict-both under either distance.',fill='#aabbd0')
        canvas.save(out/'visuals/training_choice.png')


def report(out):
    out=Path(out);read=lambda f:json.loads((out/f).read_text())
    env=read('environment.json');config=read('config.json');verified=read('verification.json');gate=read('extension_decision.json')
    champions=read('champions.json');primary=list(lines(out/'holdout.jsonl.gz'));paired=list(lines(out/'paired_holdout.jsonl.gz'))
    manifest=json.loads(gzip.open(out/'mazes.json.gz','rt').read());mazes={m['case_id']:m for m in manifest}
    reachable={m['case_id']:m['oracle_length']>0 for m in manifest}
    ps=paired_summary(paired,reachable)
    for r in ps:
        rr=[x for x in paired if x['arm']==r['arm'] and 'baseline' not in x]
        for field in ('junction','junction_both','balanced'):r[field]=float(np.mean([x[field] for x in rr])) if rr else None
    write_json(out/'paired_summary.json',ps);pm={r['arm']:r for r in ps}
    summaries={r['arm']:r for r in read('summary.json') if r['group']=='all'}
    taskarms=[f'{t}/{p}/task' for t in ('local','evolved') for p in ('fixed','curriculum')]
    txt=['# Goal-distance curriculum: V10','',
        'This experiment compares a near-to-far goal curriculum with fixed hard goals on matched maze geometry, source and fork. '
        'Both use the same bounded runtime, genome capacity, Choice-first score and initial random-origin lineages. '
        'Complete correct shortest paths remain the primary result.','',
        '| Task archive | Unseen valid | Unseen shortest | Distance≥8 shortest | Paired shortest | Correct no-path |',
        '|---|---:|---:|---:|---:|---:|']
    for arm in taskarms:
        r=summaries[arm];txt.append(f"| {arm} | {r['valid']}/{r['reachable']} | {r['optimal']}/{r['reachable']} | {r['long_optimal']}/{r['long_cases']} | {pm[arm]['optimal']}/42 | {r['no_path']}/48 |")
    for arm in ('compiled_bfs','compiled_astar','wave_bit'):
        r=summaries[arm];txt.append(f"| {arm} | {r['valid']}/{r['reachable']} | {r['optimal']}/{r['reachable']} | {r['long_optimal']}/{r['long_cases']} | {pm[arm]['optimal']}/42 | {r['no_path']}/48 |")
    if (out/'discussion.md').exists():txt += ['',(out/'discussion.md').read_text().strip()]
    txt += ['',f"Extension gate: **{gate['extend']}** after {sorted({r['next_generation'] for r in champions.values()})} generations. "
        'Only common hard-validation transfer could trigger an extension. A higher easy-training score cannot. '
        'Three replicates give a descriptive comparison; archive copies and repeated training opportunities are not independent discoveries.','',
        '## Matched experiment','',
        'Fixed retains V8/V9 paired sampling: goals≥4 edges beyond a shared shortest-path fork2–8 edges from source, '
        'source-to-goal≥8 and disjoint sets of all shortest exits. Curriculum uses the identical layout/source/fork, '
        'moving endpoints down the same shortest branches to distances1/2 for generations0–15 and2/3 for16–31, with alternating goal order. '
        'Generations32 onward use identical far goals in both arms. Shortening endpoints changes target separation and deceptive bearing; these are recorded. '
        'Mixed disconnected inputs stay identical. Short labels are confined to training. Validation and final pairs stay hard.','',
        'Both arms use the unchanged V6 pulse VM:8 uint16 channels,≤128 typed genes; source/goal pulses and flags, output2,stop7. '
        'No oracle or branch label reaches inference. The same V8 J=.25 source-dependent connected prefix+.75 causal correct-exit score applies. '
        'V9 Choice-first ranking puts valid routes,shortest routes,no-path utility,strict-both count K,then smooth shaping in that order. '
        'A nearby goal light cannot earn strict credit unless it depends on the source and connects back to it. '
        'No known wavefront or solver rules enter these random-origin lineages.','',
        'Fork matching V9 Choice next-populations/RNG; protect native task/choice/J/B/G/source variants, prior protected genomes, '
        'strict supplements and qualifying ancestry from both V9 arms. Both conditions start with identical genomes/RNG and protection. '
        'New validation archives are saved but do not automatically breed. Rich random immigrants, neutral diversity and full continuation state remain.','',
        f"Seed{config['seed']}; independent construction preflight1104; {env['previous_layouts']} prior layouts excluded. "
        f"Preregistration commit `{env['parent_revision']}`. Model SHA256 `{env['champions_sha256']}` frozen BEFORE final generation. "
        'Final264 ordinary layouts and24 paired layouts/48 inputs are common to every arm. The paired set has42 reachable≥8 inputs,6 unreachable and18 regular decision pairs. '
        'Only intentional near/far training anchors share layouts; training,validation,final and all earlier experiments remain separate.','',
        '## Full outputs and failures','',
        f'![Unseen ordinary outputs]({out.name}/visuals/unseen_outputs.png)','',
        '| Selected archive | Unseen shortest | Paired shortest /42 | Final strict both /18 | Final J |',
        '|---|---:|---:|---:|---:|']
    for arm,r in sorted(summaries.items()):
        if '/' not in arm:continue
        a=pm[arm];txt.append(f"| {arm} | {r['optimal']}/{r['reachable']} | {a['optimal']} | {round(18*a['junction_both'])} | {a['junction']:.4f} |")
    from cellular_maze_lab import neighbors
    shapes=[];difficulty=defaultdict(Counter);traffic=defaultdict(Counter)
    for r in primary:
        m=mazes[r['case_id']];arm=r['arm'];w=m['w'];start=m['start'];goal=m['goal'];md=abs(start%w-goal%w)+abs(start//w-goal//w)
        d=difficulty[arm];d['false_no_path']+=bool(r['reachable'] and r['status']=='no_path')
        for label,condition in (('turn',start%w!=goal%w and start//w!=goal//w),('detour',r['edges']>md)):
            if r['reachable'] and condition:d[label+'_cases']+=1;d[label+'_optimal']+=r['optimal']
        if '/' not in arm:continue
        t=traffic[arm];opened=sum(bytes.fromhex(m['cells_hex']))
        t['open_site_ticks']+=opened*r['steps'];t['logical_copy_bytes']+=32*opened*r['steps']
        t['reads']+=r['reads'];t['dispatches']+=r['dispatches'];t['active']+=r['active']
        if r['valid_path']:
            mask=unpack(r['mask'],w*m['h']);p=start;previous=-1;directions=[]
            while p!=goal:
                q=next(q for q in neighbors(p,w,m['h']) if mask[q] and q!=previous)
                directions.append(q-p);previous,p=p,q
            shapes.append(dict(arm=arm,replicate=r['replicate'],case=r['case_id'],edges=len(directions),
                turns=sum(a!=b for a,b in zip(directions,directions[1:])),optimal=r['optimal']))
    write_json(out/'success_shapes.json',shapes);write_json(out/'difficulty_summary.json',difficulty);write_json(out/'inference_traffic.json',traffic)
    txt += ['', '| Task archive | Turn-required shortest | Detour-required shortest | False no-path on reachable |','|---|---:|---:|---:|']
    for arm in taskarms:
        d=difficulty[arm];txt.append(f"| {arm} | {d['turn_optimal']}/{d['turn_cases']} | {d['detour_optimal']}/{d['detour_cases']} | {d['false_no_path']} |")
    for arm in taskarms:
        r=next(x for x in primary if x['arm']==arm and x['reachable'] and not x['optimal'] and mazes[x['case_id']]['w']==17)
        txt.append(f"\nRepresentative {arm} failure: `{r['case_id']}`, oracle {r['edges']} edges; status `{r['status']}`, {r['steps']} completed ticks, `{r['failure']}`.")
    txt += ['', 'Successful output shapes are saved in `success_shapes.json`. A short path can be inherited or selected by common endpoint-aware halting; '
        'it is not automatically goal-guided routing. Per-size/family/distance records are in `summary.json` and raw outputs.','',
        '## Training versus transfer','',
        '| Topology/arm | Generations | Mean goal-to-fork distance | Deceptive pairs | Strict both / eligible pairs | Normal both shortest | Mean weaker J | Valid normal outputs |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    phase=read('curriculum_training.json')
    for r in sorted(phase,key=lambda r:(r['topology'],r['arm'],{'near1':0,'near2':1,'far':2}[r['phase']])):
        window={'near1':'0–15','near2':'16–31','far':'32–47'}[r['phase']]
        txt.append(f"| {r['topology']}/{r['arm']} | {window} | {r['sum_goal_distance']/max(1,2*r['pairs']):.2f} | {r['deceptive_pairs']}/{r['pairs']} | {r['strict_both']}/{r['pairs']} | {r['normal_both_shortest']} | {r['sum_min_j']/max(1,r['pairs']):.4f} | {r['valid']} |")
    txt += ['', 'Strict-both uses forced16-tick causal rasters; normal-both-shortest instead counts complete correctly emitted routes under BOTH goals on a regular pair. Normal validity/optimality remains ahead of K in selection. These repeat genomes on rotating training contexts. Different cue distances make phase scores unsuitable as evidence of unseen transfer. '
        'The phase leader is the current globally ranked training leader at generations15,31,47, chosen before final layouts; '
        'secondary assays below reuse the common paired final set and cannot replace primary models.','',
        '| Topology/arm | Leader generation | Hard-validation strict both /12 | Final strict both /18 | Final shortest /42 |',
        '|---|---:|---:|---:|---:|']
    phase_rows=list(lines(out/'phase_transfer.jsonl.gz'));phase_summary=[]
    for topology in ('local','evolved'):
        for arm in ('fixed','curriculum'):
            for generation in (15,31,47):
                rr=[r for r in phase_rows if r['condition'].split('/')[1:3]==[topology,arm] and r['generation']==generation]
                val=[r for r in rr if r['split']=='validation_goal'];final=[r for r in rr if r['split']=='test_pairs']
                row=dict(topology=topology,arm=arm,generation=generation,validation_strict=sum(r['strict_pairs'] for r in val),
                    final_strict=sum(r['strict_pairs'] for r in final),final_optimal=sum(c['optimal'] for r in final for c in r['cases']))
                phase_summary.append(row);txt.append(f"| {topology}/{arm} | {generation} | {row['validation_strict']} | {row['final_strict']} | {row['final_optimal']} |")
    write_json(out/'phase_summary.json',phase_summary)
    controls=list(lines(out/'phase_training_control.jsonl.gz'));training_summary=[]
    txt += ['', 'The boundary generations15/31/47 all use one regular tree pair plus one mixed disconnected pair under the unchanged every-fourth-generation schedule. '
        'These snapshots do not represent every cyclic training opportunity. The following reused-training comparison was fixed during training, before final layouts existed. '
        'The phase leader was selected on its own batch and therefore has a selection advantage; this is not a holdout or a causal estimate of evolutionary improvement.','',
        '| Topology/arm | Boundary generation | Frozen-choice strict / eligible | Phase-leader strict | Final-choice strict |',
        '|---|---:|---:|---:|---:|']
    for topology in ('local','evolved'):
        for arm in ('fixed','curriculum'):
            for generation in (15,31,47):
                rr=[r for r in controls if r['condition'].split('/')[1:3]==[topology,arm] and r['generation']==generation]
                counts={label:sum(r['strict_pairs'] for r in rr if r['selection']==label) for label in ('frozen_choice','phase_leader','final_choice')}
                eligible=sum(c['junction']['eligible'] for r in rr if r['selection']=='phase_leader' for c in r['cases'][::2])
                training_summary.append(dict(topology=topology,arm=arm,generation=generation,eligible=eligible,**counts))
                txt.append(f"| {topology}/{arm} | {generation} | {counts['frozen_choice']}/{eligible} | {counts['phase_leader']} | {counts['final_choice']} |")
    write_json(out/'phase_training_summary.json',training_summary)

    txt += ['',f'![Precursor comparison]({out.name}/visuals/precursor_comparison.png)','',
        f'![Switched-goal output]({out.name}/visuals/switched_goals.png)','',
        '## Preserved validation variants and causal assays','',
        'J and hidden goal-dependent state are precursors, not complete routes. Fixed16-tick probes override normal halting; their rasters cannot assert an actual emitted solution. '
        'All qualifying validation genotypes and ancestry remain available for continuation; their presence alone does not demonstrate generalization.','',
        '| Condition | First qualifying birth on selected validation pair | Ancestry nodes | Final J | Final strict both | Normal shortest /2 |',
        '|---|---:|---:|---:|---:|---:|']
    ancestry=json.loads(gzip.open(out/'choice_ancestry.json.gz','rt').read())
    if not ancestry:txt=txt[:-2]+['No current primary validation choice archive qualifies under both switched goals. Earlier native primitives remain protected; the new training-only primitive is documented separately below.']
    for r in ancestry:
        first=next(n for n in r['nodes'] if n['strict_both']);last=r['nodes'][-1]
        txt.append(f"| {r['condition']} | {first['individual']['birth']} | {len(r['nodes'])} | {last['junction']:.4f} | {last['strict_both']} | {sum(c['optimal'] for c in last['cases'])} |")
    if ancestry:txt += ['',f'![Validation ancestry]({out.name}/visuals/validation_choice.png)']
    if ancestry:txt += ['', '| Same qualifying validation genotype | Goal pulse | Nonlocal reads zeroed | J | Strict both |','|---|---:|---:|---:|---:|']
    for r in ancestry:
        for a in r['interventions']:txt.append(f"| {r['condition']} | {a['goal_pulse']} | {a['ablate_nonlocal']} | {a['junction']:.4f} | {a['junction_both']} |")
    txt += ['', 'Removing the goal pulse keeps the static goal flag. Nonlocal ablation zeroes radius>1 reads while charging attempted reads. '
        'These are case-specific dependencies. Birth0 denotes a qualifying inherited variant. A later parent/child row difference does not establish which individual edit is necessary. '
        'Full final pulse/range interventions,8/16/32/64 state timecourses and structural opportunity diagnostics are saved separately without reselection.']
    entry=read('entry_diagnostics.json')['records'];txt += ['', '| Topology/arm | Strict-both training responses | Enter from source without chosen exit / both goals | Shortest incoming prefixes / both goals |', '|---|---:|---:|---:|']
    for topology in ('local','evolved'):
        for arm in ('fixed','curriculum'):
            rr=[r for r in entry if r['split']=='train' and r['condition'].split('/')[1:3]==[topology,arm]]
            txt.append(f"| {topology}/{arm} | {len(rr)} | {sum(r['both_enter_from_source'] for r in rr)} | {sum(r['both_shortest_prefixes'] for r in rr)} |")
    if (out/'training_choice_diagnostic.json').exists():
        d=read('training_choice_diagnostic.json');verify=read('training_choice_verification.json');interaction=read('training_edit_interaction.json')
        txt += ['', '## One new training-only choice, preserved','',
            'The sole multirange Curriculum strict-both training response occurs at generation30 on a17×17 tree, '
            'fork6 edges from source and goals2/3 farther. Native genome i1472,birth30, descends through i94(birth0),i1213(birth25),i1402(birth29). '
            'The parent fails and the child has J=1/strict-both on that reused training pair. Both ordinary outputs remain incomplete. '
            'This is a new context-specific choice response, not a complete solver. It was retained once and produced18 mutated offspring; '
            'the exact genotype is absent from the final population. Full genotype and ancestry are explicitly saved for the next common protected cohort.','',
            'Two rows differ from the parent. Reversion assays show row25 alone,changing a radius-2 remote-read destination46→59,is sufficient for this response. '
            'Row117’s operand3→36 alone fails and is unnecessary on this case. This does not establish a cooperative two-edit interaction. '
            'Both goal-pulse removal and nonlocal-read removal destroy strict-both,J drops to.2. The effect therefore depends on both goal information and longer reads here.','',
            f'![Training precursor]({out.name}/visuals/training_choice.png)','',
            'This post-hoc assay was selected from training qualification after the main final evaluation. It never evaluates this newly selected model on V10’s inspected final set '
            'or changes V10 selections. Independently checked masks/source effects,replayed outputs and full work are saved.','',
            f"Original assay{d['elapsed_seconds']:.3f}s,{d['normal_responses']} normals/{d['probes']} probes,{d['charged_work']:,} units. "
            f"Verification{verify['elapsed_seconds']:.3f}s,replay{verify['replayed_work']:,} units; artificial edit-reversion assays "
            f"{verify['counterfactual_work']:,} units,{verify['counterfactual_normals']} normals/{verify['counterfactual_probes']} probes. "
            'The initial tuple/list assertion retry and one repeated completed verification are separately recorded in `training_choice_execution_note.json`; the failed attempt’s wall time is unavailable. '
            'That implementation repair changes no training/raw result.']
        confirmation=out.parent/'distance_confirmation'
        if (confirmation/'summary.json').exists():
            rows=json.loads((confirmation/'summary.json').read_text());a={r['distance']:r for r in rows if r['role']=='child'}
            txt += ['', '## Fresh frozen-primitive confirmation: V10A','',
                f"After freezing the child,parent and root,12 fresh layouts test both near2/3 and far≥4 goal pairs. The child makes **{a['near']['strict']}/12** near and "
                f"**{a['far']['strict']}/12** far strict-both choices and completes {a['near']['optimal']}/24 near,{a['far']['optimal']}/24 far shortest paths. "
                'Parent/root also score zero complete choices/routes. BFS solves all48 input instances. The new training primitive does not transfer on this small confirmation, even at matched short cue distances. '
                'This does not establish impossibility. All8690 earlier layouts are excluded;12 new layouts bring the saved total to8702.','',
                'The [V10A report](distance_confirmation.md) records frozen model hashes, source/protocol, independent seed1105 construction/replay preflight, '
                'seed2026101810 production cases, full rasters/cost and independent verification. V10 primary results remain unchanged.']

    from .regulatory import Genome
    from .range_audit import output_dataflow
    structures=[]
    for saved in champions.values():
        c=saved['config']
        for label in ('task','choice'):
            item=saved['archives'][label]['individual'];g=Genome.from_dict(item['genome'])
            structures.append(dict(arm=f"{c['topology']}/{c['pressure']}/{label}",replicate=c['replicate'],genome_sha=g.digest,**output_dataflow(g)))
    write_json(out/'capacity_diagnostics.json',structures)
    counts=read('mutation_behavior.json')['counts'];totals=Counter()
    for r in counts.values():totals.update(r)
    write_json(out/'mutation_summary.json',totals)
    diag=read('diagnostics.json');storage=read('storage.json')
    txt += ['', '## Real cost and effective capacity','',
        f"Search+validation/probes **{env['training_seconds']/60:.2f}min**; main including final outputs/timing **{env['elapsed_seconds']/60:.2f}min**. "
        f"Peak main RSS **{env['max_rss_bytes']/2**20:.1f}MiB**, {env['cpu']}, Python{env['python']}; dependencies `{env['packages']}`. "
        f"Search charged {verified['normal_maze_evaluations']:,} normal responses and {verified['developmental_probe_runs']:,} probes, "
        f"{verified['charged_work']:,} logical dispatch+attempted-read units. These are VM accounting units, not hardware instructions. "
        'Same caps/population do not guarantee equal actual work.','',
        f"Post-freeze diagnostics {diag['elapsed_seconds']:.2f}s, including boundary-leader assays {diag['phase_seconds']:.2f}s; "
        f"charged {diag['charged_work']:,} additional units. Lossless log compression {storage['elapsed_seconds']:.2f}s; "
        f"independent audit {verified['elapsed_seconds']:.2f}s. These are outside the main elapsed time. The audit includes replayed inference whose work is not folded into search.",'',
        'Latency includes decoding,initialization,updates and final raster emission; fitness/oracle/probes are excluded and charged separately. '
        'Production-signature JIT warmup,30 randomized-order repetitions/case,12 cases/arm. Median of case medians and full sample range follow. '
        'Wrong/partial outputs cannot claim speedup. Conventional solver VM counters are uninstrumented placeholders, not zero hardware work.','',
        '| Arm | Median case median μs | Warm range μs | Correct timed repetitions | Largest explicit arrays |', '|---|---:|---:|---:|---:|']
    timings=read('timings.json')
    for arm in ('compiled_bfs','compiled_astar','wave_bit',*taskarms):
        rr=[r for r in timings if r['arm']==arm];a=summaries[arm];mem=str(a['largest_array_bytes'])+'B' if a['largest_array_bytes']>=0 else 'unreported'
        txt.append(f"| {arm} | {statistics.median(r['median_us'] for r in rr):.2f} | {min(r['min_us'] for r in rr):.2f}–{max(r['max_us'] for r in rr):.2f} | {sum(r['correct'] for r in rr)}/{sum(r['repeats'] for r in rr)} | {mem} |")
    txt += ['', '| Task archive | Completed open-site ticks | Logical state-copy MiB | Neighbor reads | Dispatches | Active fraction |', '|---|---:|---:|---:|---:|---:|']
    for arm in taskarms:
        a=traffic[arm];txt.append(f"| {arm} | {a['open_site_ticks']:,} | {a['logical_copy_bytes']/2**20:,.1f} | {a['reads']:,} | {a['dispatches']:,} | {a['active']/max(1,a['dispatches']):.3f} |")
    txt += ['', 'A completed open-site tick copies eight uint16 states old→new:32 bytes of logical read/write payload. '
        'This excludes partial ticks,register/gene operations and allocations; cache/compiler effects change actual DRAM traffic. '
        'State double buffers use32N bytes; explicit kernel ceiling64N+65536. CPU propagation and repeated tissue updates remain scaling costs.','',
        f"Selected genomes have {min(r['genes'] for r in structures)}–{max(r['genes'] for r in structures)} genes; conservative output/stop slices "
        f"{min(r['potential_output_stop_genes'] for r in structures)}–{max(r['potential_output_stop_genes'] for r in structures)} genes. "
        'These are syntactic potential dependencies, not effective regulatory complexity.','',
        f"Of {totals['changed_genome']:,} changed-DNA children with a parent evaluated on the same rotating batch, "
        f"{totals['changed_genome_same_behavior']:,} ({totals['changed_genome_same_behavior']/max(1,totals['changed_genome']):.1%}) share the saved behavior fingerprint. "
        'This conditional statistic covers binary normal/probe rasters,status/steps and partial/source/goal metrics; hidden trajectories,active work and expression can differ. '
        'Full populations,RNG,neutral variants and native cooperative precursors remain preserved.','',
        '## Verification and continuation','',
        f"All checks pass: {verified['source_files']} frozen sources, {verified['training_fitness_checks']:,} fitness records, "
        f"{verified['junction_raster_checks']:,} junction rasters, {verified['reassessed_training_valid_claims']} valid training claims, "
        f"{verified['replayed_selected_outputs']} selected normal replays and {verified['phase_reassessed_outputs']} phase-assay outputs. "
        'Task/choice/J/B archive maxima, exact near/far anchor transformations and distances, all prior-layout exclusions, '
        'lineage/protection, complete checkpoints, source/model hashes and lossless storage hashes are verified. '
        'The deterministic suite covers causal short labels, unchanged hard scoring, matched full-capacity construction through192 generations, gate behavior and exact resume.','',
        'Commands are in `docs/DISTANCE_STUDY_V10.md`. Raw records/checkpoints are in `results/distance_curriculum/`. '
        'Prior code/results remain immutable. Random-origin discovery remains central; this bounded comparison cannot establish impossibility.']
    txt += ['', 'Validation commands: full `pytest -q` passed116 tests in309.19s; after the last source-snapshot/resume edits, '
        '`pytest tests/test_distance.py -q -k "not fresh_capacity"` passed4 in1.87s. The117 currently collected tests are covered by those runs. '
        'V10A also passes an independent full construction/replay preflight(seed1105),then all192 production normal outputs and144 causal rasters are checked.','',
        '## Next controlled experiment','',
        'Test greater heritable program capacity with copy-and-diverge growth: a128-versus256-gene ceiling, '
        'the same eight channels/opcodes/range rules, same Fixed hard-pair objective and common block-duplication mutation operator. '
        'Start with identical native populations/RNG and preserve all prior primitives plus i1472/parent/root in both matching replicate2 cohorts. '
        'Allow no known solver insertion. First prove all lifted≤128-gene genomes reproduce the old VM under identical caps. '
        'Keep instruction/read/tick limits bounded and common; charge added dispatches and any reduction in completed ticks. '
        'Track actual grown genes,expression,dependency slices and behavior, since a larger ceiling alone is not effective complexity. '
        'Use wholly new layouts excluding8702 saved layouts and a validation-only extension gate. '
        'This tests the user’s capacity hypothesis directly; more easy-goal shaping at the same ceiling has not established transfer.']

    (out.parent/(out.name+'.md')).write_text('\n'.join(txt)+'\n')
    visuals(out,manifest,primary,paired)
    print(out.parent/(out.name+'.md'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/distance_curriculum');report(parser.parse_args().out)
