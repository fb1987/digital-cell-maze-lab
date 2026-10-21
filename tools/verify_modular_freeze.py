"""Independent bookkeeping checks of M1 frozen selection and exact ancestry records."""
import json,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.modular_pilot import RUN,OUT,readz,writej
from maze_evolution.deep_campaign_store import unpacked,hashed,packed
from maze_evolution.modular_pilot_search import genome
c=sqlite3.connect(f'file:{RUN}/campaign.sqlite?mode=ro',uri=True)
latest=unpacked(c.execute("select value from settings where key='latest'").fetchone()[0]);states=unpacked(c.execute('select value from states where stage=?',(latest,)).fetchone()[0])
assert all(s['generation']==s['assessment_generation']==128 for s in states)
choices=readz(OUT/'choices.json.gz');ancestry=readz(OUT/'ancestry.json.gz');needed=set(choices['items'])|set(ancestry);found={};events={};expected_roles={};expected_comparisons=[]
for s in states:
 for role in ('nominee','frozen'):
  for rank,i in enumerate(s['nominees' if role=='nominee' else 'frozen']):
   assert choices['items'][i['id']]==i
   expected_roles.setdefault(i['id'],[]).append([s['name'],role,rank])
   if role=='nominee':expected_comparisons.append(dict(condition=s['name'],rank=rank,child=i['id'],root=i['root'],parent=i['parent'],mutations=i['mutation_depth']))
assert choices['roles']==expected_roles and choices['comparisons']==expected_comparisons
initial=unpacked(c.execute('select value from states where stage=-1').fetchone()[0])
for s in initial:
 for i in s['population']:
  if i['id'] in needed:found[i['id']]=i;events[i['id']]=dict(item=i,event=None)
for blob, in c.execute('select decision from stages where complete=1 order by n'):
 for d in unpacked(blob):
  for b in d['births']:
   i=b['item']
   if i['id'] in needed:
    assert i['id'] not in found;found[i['id']]=i;events[i['id']]=b
assert set(found)==needed
for i,v in choices['items'].items():assert v==found[i];genome(choices['representations'][i],v['genome'])
for i,b in ancestry.items():assert b==events[i]
lengths=[]
for comp in choices['comparisons']:
 i=comp['child'];seen=set();depth=0
 while found[i]['parent']:
  assert i not in seen;seen.add(i);assert found[i]['root']==comp['root'];i=found[i]['parent'];depth+=1
 assert i==comp['root'] and depth==comp['mutations'];assert found[i]['mutation_depth']==0
 lengths.append(depth)
writej(OUT/'freeze_audit.json',dict(status='PASS',comparisons=len(lengths),panel_identities=len(choices['items']),ancestral_records=len(ancestry),mutation_births_in_selected_chains_including_shared=sum(lengths),all_choices_match_audited_state=True,all_panel_and_ancestry_records_match_journal=True,all_roots_random_founder_or_immigrant=True))
c.close();print('Freeze and ancestry bookkeeping PASS')
