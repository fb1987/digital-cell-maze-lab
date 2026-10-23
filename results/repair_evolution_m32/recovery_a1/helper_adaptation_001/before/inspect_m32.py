"""Read-only M32 status/assessment export, never a scientific writer."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from maze_evolution.repair_evolution_m32 import OUT,RUN,readonly,unpacked,writej

def main():
    p=argparse.ArgumentParser();p.add_argument('--assessment',type=int);p.add_argument('--output',type=Path);a=p.parse_args()
    status=json.loads((RUN/'workflow_status.json').read_text());result=dict(workflow=status)
    if (RUN/'search/campaign.sqlite').exists():
        j=readonly('search');states=j.state();result['search']=dict(generation=states[0]['generation'],latest=j.get('latest'),pending=None if j.pending() is None else j.pending()[0],usage=j.get('usage'))
        if a.assessment is not None:
            record=j.db.execute("select n,decision from stages where kind='assessment' and generation=? and complete=1",(a.assessment,)).fetchone();assert record,'Assessment not completed'
            result['assessment']=dict(generation=a.assessment,stage=record[0],nominees=[dict(name=d['name'],roles=[dict(role=c['role'],id=c['item']['id'],entry=c['item']['entry'],depth=c['item']['depth'],changed_depth=c['item']['changed_depth'],controlled_pairs=c['development']['controlled_pairs'],controlled_individuals=c['development']['controlled_individuals'],raw_ordinary8=c['development']['endpoint']['raw_novel_complete8'],gated_score=c['development']['endpoint']['primary_score'],gate=c['development']['endpoint']['gate']) for c in d['nominees']]) for d in unpacked(record[1])],development_not_confirmation=True)
        j.close()
    if a.output:
        assert not a.output.exists();a.output.parent.mkdir(parents=True,exist_ok=True);writej(a.output,result)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
