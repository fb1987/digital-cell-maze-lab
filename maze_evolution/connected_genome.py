"""M18 generic initialized channel copying; no maze-dependent variation."""
from dataclasses import dataclass
import hashlib,json
from .spare_genome import Genome as Body,embed as spare_embed,duplicate
from .modular_genome import Genome as Base,REFS
from .regulatory import Gene

DEFAULT=(1,2,0,0,0,0,0,0,0,0)
@dataclass(frozen=True)
class Genome:
    body: Body
    initialization: tuple=DEFAULT
    def __post_init__(self):
        if not isinstance(self.body,Body):raise ValueError('Expected bounded M17 body')
        if len(self.initialization)!=10 or self.initialization[:8]!=DEFAULT[:8]:raise ValueError('Legacy stimulus convention is fixed')
        if any(type(x)!=int or not 0<=x<=3 for x in self.initialization):raise ValueError('Only source/goal bit flags')
    def to_dict(self):return dict(version='M18',body=self.body.to_dict(),initialization=list(self.initialization))
    @classmethod
    def from_dict(cls,d):
        if set(d)!={'version','body','initialization'} or d['version']!='M18':raise ValueError('Expected M18 schema')
        return cls(Body.from_dict(d['body']),tuple(d['initialization']))
    @property
    def instructions(self):return self.body.instructions
    @property
    def digest(self):return hashlib.sha256(json.dumps(self.to_dict(),sort_keys=True,separators=(',',':')).encode()).hexdigest()[:20]


def embed(g):return Genome(spare_embed(g))


def edges(g):
    """Conservative live expression reads feeding the output/explicit halt interface.
    Structural only: no maze, evaluator or fitness. Includes both branches/gates.
    """
    graph=[]
    for k,block in enumerate(g.blocks):
        seen=set();channels=set();pending=[len(block)-1]
        while pending:
            i=pending.pop()
            if i in seen:continue
            seen.add(i);gene=block[i];row=gene.row()
            refs=[row[j] for j in REFS[gene.op]]+([gene.gate] if gene.gate!=64 else [])
            for r in refs:
                if r>=12:pending.append(r-12)
                elif r<8:channels.add(g.ports[k][r])
            if gene.op in (4,5,6,7,14,15,17):channels.add(g.ports[k][gene.a])
        graph.append(channels)
    cone={2,7}
    while True:
        updated=cone|{c for k in cone for c in graph[k]}
        if updated==cone:break
        cone=updated
    return [(reader,donor) for reader in sorted(cone) for donor in sorted(graph[reader])]


def clone(g,reader,donor,target,seeded,connected):
    if not (0<=reader<8 and 0<=donor<8 and target in (8,9)):raise ValueError('Original channel to spare slot only')
    if g.body.blocks[target]:raise ValueError('Target must be unused')
    body,event=duplicate(g.body,donor,target)
    if event['kind']=='bounded_noop':return g,dict(event,kind='bounded_noop',before=g.digest,after=g.digest)
    ports=list(body.ports)
    if connected:
        p=list(ports[reader]);a=p.index(donor);b=p.index(target)
        assert a<8 and b>=8,'Existing original reader and latent spare slot required'
        p[a],p[b]=p[b],p[a];ports[reader]=tuple(p)
    init=list(g.initialization)
    if seeded:init[target]=init[donor]
    child=Genome(Body(body.blocks,tuple(ports)),tuple(init))
    return child,dict(kind='connected_copy' if connected else 'disconnected_copy',reader=reader,donor=donor,target=target,
        inherited_initialization=bool(seeded),before=g.digest,after=child.digest)


def zero_copy(g,target):
    blocks=list(g.body.blocks);b=list(blocks[target]);last=b[-1]
    b[-1]=Gene(1,last.dst,0,0,0,0,64);blocks[target]=tuple(b)
    return Genome(Body(tuple(blocks),g.body.ports),g.initialization)
