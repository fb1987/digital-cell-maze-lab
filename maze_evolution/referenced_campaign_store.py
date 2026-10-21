"""New journals reference immutable historical exclusions and store only deltas.

Old journals are never migrated. Receipts/specs use zlib level 9; decoded values,
transactional charging, state hashes, and chain construction retain the old format.
A backup depends on the explicitly checksummed base manifest and its parts.
"""
import hashlib,json,zlib
from pathlib import Path
from .deep_campaign_store import Journal as OriginalJournal,packed,unpacked,hashed
from .foundation_calibration import ROOT
from .foundation_study import read_compressed,compressed_json


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def path_for(value):return ROOT/Path(value)


def load_layouts(path, ancestors=()):
    path=Path(path).resolve()
    if path in ancestors:raise ValueError('Cyclic layout references')
    manifest=json.loads(path.read_text());values=set()
    if manifest.get('format')=='referenced-layout-hashes-v1':
        base=manifest['base'];p=path_for(base['path'])
        if sha(p)!=base['sha256']:raise ValueError('Base manifest hash mismatch')
        values=load_layouts(p,ancestors+(path,))
        if len(values)!=base['count']:raise ValueError('Base count mismatch')
    elif manifest.get('format') not in (None,'chunked-layout-hashes-v1'):
        raise ValueError('Unknown layout format')
    for part in manifest['parts']:
        p=path_for(part['path'])
        if sha(p)!=part['sha256']:raise ValueError('Layout part hash mismatch')
        rows=read_compressed(p)['hashes']
        if len(rows)!=part['count'] or len(set(rows))!=len(rows):raise ValueError('Invalid part count')
        if any(len(h)!=64 or any(c not in '0123456789abcdef' for c in h) for h in rows):raise ValueError('Invalid layout digest')
        if values.intersection(rows):raise ValueError('Overlapping layout parts/base')
        values.update(rows)
    if len(values)!=manifest['count']:raise ValueError('Layout total mismatch')
    return values


def write_reference(path,base_path,values):
    path=Path(path);base_path=Path(base_path).resolve();values=set(values)
    if path.exists():raise FileExistsError(path)
    base=load_layouts(base_path)
    if not base<=values:raise ValueError('Historical exclusions omitted')
    delta=sorted(values-base);part=path.with_suffix('.delta.json.gz')
    if part.exists():raise FileExistsError(part)
    def named(p):
        try:return str(p.relative_to(ROOT))
        except ValueError:return str(p)
    compressed_json(part,dict(hashes=delta))
    manifest=dict(format='referenced-layout-hashes-v1',count=len(values),
        base=dict(path=named(base_path),sha256=sha(base_path),count=len(base)),
        parts=[dict(path=named(part.resolve()),sha256=sha(part),count=len(delta))])
    with path.open('x') as f:json.dump(manifest,f,sort_keys=True,indent=2);f.write('\n')
    return manifest


def compact(value):
    return zlib.compress(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),9)


class Journal(OriginalJournal):
    def __init__(self,directory):
        super().__init__(directory)
        self.base=set()
        ref=self.get('layout_base')
        if ref:
            p=path_for(ref['path'])
            if sha(p)!=ref['sha256']:raise ValueError('Journal base manifest changed')
            self.base=load_layouts(p)
            if len(self.base)!=ref['count']:raise ValueError('Journal base count changed')

    def initialize(self,config,states,previous):
        p=path_for(config['layout_base_manifest']);base=load_layouts(p)
        if set(previous)!=base:raise ValueError('Initial corpus must exactly match referenced ledger')
        ref=dict(path=str(p.resolve()),sha256=sha(p),count=len(base))
        blob=packed(states);layout_hash=hashed(packed(sorted(base)))
        if self.get('config') is not None:
            if self.get('config')!=config or self.get('layout_base')!=ref:raise ValueError('Frozen configuration or reference differs')
            initial=self.db.execute('select value,hash from states where stage=-1').fetchone()
            if initial!=(blob,hashed(blob)) or self.get('initial_layout_hash')!=layout_hash:raise ValueError('Initial state/exclusions differ')
            self.base=base;return
        if self.db.execute('select count(*) from layouts').fetchone()[0]:raise ValueError('Not an empty new journal')
        with self.db:
            self.put('config',config);self.put('layout_base',ref);self.put('initial_layout_hash',layout_hash)
            self.put('latest',-1);self.put('usage',dict(calls=0,work=0,cpu_seconds=0.,candidate_seconds=0.,receipts=0,uncertain_attempts=0))
            self.db.execute('insert into states values(-1,?,?)',(blob,hashed(blob)))
        self.base=base

    def layouts(self):
        delta=super().layouts()
        if delta&self.base:raise ValueError('Journal delta overlaps historical base')
        return self.base|delta

    def prepare(self,data,tasks):
        assert self.pending() is None
        if self.base.intersection(data['new_layouts']):raise ValueError('Historical layout reused as new')
        n=self.get('latest')+1;blob=packed(data)
        with self.db:
            self.db.execute('insert into stages(n,kind,generation,input,input_hash) values(?,?,?,?,?)',(n,data['kind'],data['generation'],blob,hashed(blob)))
            self.db.executemany('insert into tasks(stage,n,spec) values(?,?,?)',((n,k,compact(task)) for k,task in enumerate(tasks)))
            self.db.executemany('insert into layouts values(?)',((h,) for h in data['new_layouts']))
        return n

    def receipt(self,n,k,result,reserved_work):
        status=self.db.execute('select status from tasks where stage=? and n=?',(n,k)).fetchone()[0]
        if status!='started':raise ValueError('Receipt must follow a reservation, never overwrite done')
        blob=compact(result);usage=self.get('usage')
        assert result['work']<=reserved_work
        usage['work']+=result['work']-reserved_work
        usage['cpu_seconds']+=result['cpu_seconds'];usage['candidate_seconds']+=result['candidate_seconds'];usage['receipts']+=1
        with self.db:
            self.put('usage',usage)
            self.db.execute("update tasks set status='done',result=?,result_hash=? where stage=? and n=?",(blob,hashed(blob),n,k))
