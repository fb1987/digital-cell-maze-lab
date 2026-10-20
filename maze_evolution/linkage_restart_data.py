"""V12X-R1 feasibility inputs, excluding every whole layout through W."""
from .mutation_accessibility_data import AccessData as OldData,ROOT,seed_for,manifest,load,layout_hash
from .foundation_data import FoundationData
from .foundation_study import compressed_json,read_compressed
from .composition_data import ordinary,LENGTHS
OUT=ROOT/'results/linkage_restart'
FIXTURES=ROOT/'results/linkage_restart_fixtures'
SEED=2026102002
FIXTURE_SEED=1394

class Data(OldData):
    def __init__(self,seed,previous):
        FoundationData.__init__(self,seed);self.layouts=set(previous);self.previous_count=len(self.layouts);self.contexts=[];self.metadata={}

def exclusions():
    p=read_compressed(ROOT/'results/linkage_pilot/whole_layout_exclusions.json.gz')
    assert p['count']==len(set(p['hashes']))==253316
    return set(p['hashes'])

def fixture(previous):
    d=Data(FIXTURE_SEED,previous)
    for k,(length,shape,stress) in enumerate((((2,3),'straight',False),((3,4),'turning',False),((4,6),'straight',True),((6,4),'straight',True))):
        d.context('fixture',k,length,shape,(0,1,2,4),stress)
    ordinary(d,'fixture');return d

def training_batch(d,g):
    assert not d.cache and not d.metadata and not d.contexts
    stress=g%3!=0;length=((4,6),(6,4))[(g//3)%2] if stress else LENGTHS[(g//3)%6]
    shape='straight' if stress else ('straight','turning')[(g//18)%2]
    prefix=(1,2,4)[(g//3)%3];pose=(g//9)%8;graph=('fork','two_junction','cycle')[g%3]
    d.context('train',g,length,shape,(prefix,),stress)
    ids=[cid for cid,m in d.metadata.items() if m['pose']==pose and m['graph']==graph]
    assert len(ids)==6;return ids

def clear(d):
    d.cache={};d.metadata={};d.contexts=[];d.previous_count=len(d.layouts)
