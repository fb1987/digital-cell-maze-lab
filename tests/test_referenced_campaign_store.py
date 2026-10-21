import json,sqlite3
import pytest
from maze_evolution.referenced_campaign_store import Journal,load_layouts,write_reference,sha
from maze_evolution.deep_campaign_store import Journal as Old,packed,unpacked,hashed,writer_lock
from maze_evolution.foundation_study import compressed_json


def ledger(tmp_path,values):
    part=tmp_path/'base.json.gz';compressed_json(part,dict(hashes=sorted(values)))
    p=tmp_path/'base.json';p.write_text(json.dumps(dict(format='chunked-layout-hashes-v1',count=len(values),parts=[dict(path=str(part),sha256=sha(part),count=len(values))])))
    return p


def test_reference_integrity_overlap_and_missing_history(tmp_path):
    base=ledger(tmp_path,{'a'*64,'b'*64});p=tmp_path/'delta.json'
    write_reference(p,base,{'a'*64,'b'*64,'c'*64})
    assert load_layouts(p)=={'a'*64,'b'*64,'c'*64}
    with pytest.raises(FileExistsError):write_reference(p,base,set())
    with pytest.raises(ValueError):write_reference(tmp_path/'omission.json',base,{'c'*64})
    part=tmp_path/'delta.delta.json.gz';compressed_json(part,dict(hashes=['a'*64]))
    with pytest.raises(ValueError,match='hash'):load_layouts(p)
    m=json.loads(p.read_text());m['parts'][0]['sha256']=sha(part);p.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='Overlapping'):load_layouts(p)
    base.write_text('{}')
    with pytest.raises(ValueError,match='Base manifest hash'):load_layouts(p)


def test_crash_resume_charging_chain_and_backup(tmp_path):
    base=ledger(tmp_path,{'a'*64});run=tmp_path/'run';run.mkdir()
    config=dict(layout_base_manifest=str(base));state={'rng':[1,2],'population':['genome']}
    j=Journal(run);j.initialize(config,state,{'a'*64})
    assert j.db.execute('select count(*) from layouts').fetchone()[0]==0
    with pytest.raises(ValueError):j.prepare(dict(kind='train',generation=0,new_layouts=['a'*64]),[])
    data=dict(kind='train',generation=0,new_layouts=['b'*64]);tasks=[[{'queries':['maze'],'model':state}]]
    n=j.prepare(data,tasks);j.reserve(n,0,1,100);j.close()
    j=Journal(run);j.initialize(config,state,{'a'*64});assert j.pending()==(n,data)
    assert j.tasks(n)==[(0,tasks[0],'started')]
    j.reserve(n,0,1,100)
    receipt=dict(entries=[{'rows':[{'mask':[0,1]}]}],calls=1,work=20,cpu_seconds=.1,candidate_seconds=.09)
    j.receipt(n,0,receipt,100)
    with pytest.raises(ValueError):j.receipt(n,0,receipt,100)
    assert j.results(n)==[receipt]
    assert j.get('usage')['calls']==2 and j.get('usage')['work']==120 and j.get('usage')['uncertain_attempts']==1
    chain=j.commit(n,{'rng':[3,4]},dict(selected='child'))
    assert chain==j.verify_chain();assert j.layouts()=={'a'*64,'b'*64}
    with writer_lock(run):
        with pytest.raises(BlockingIOError):
            with writer_lock(run):pass
        dest=sqlite3.connect(tmp_path/'backup.sqlite');j.db.backup(dest)
        assert dest.execute('pragma integrity_check').fetchone()==('ok',)
        for table in ['settings','layouts','states','stages','tasks']:
            order='1' if table=='layouts' else '1,2'
            assert list(j.db.execute(f'select * from {table} order by {order}'))==list(dest.execute(f'select * from {table} order by {order}'))
        dest.close()
    j.close()
    j=Journal(run);assert j.verify_chain()==chain and j.state()=={'rng':[3,4]};j.close()
    base.write_text('{}')
    with pytest.raises(ValueError,match='base manifest'):Journal(run)


def test_old_and_new_decoded_records_equal(tmp_path):
    base=ledger(tmp_path,{'a'*64});state={'population':[1,2],'rng':[3,4]};journals=[]
    for cls,name in [(Old,'old'),(Journal,'new')]:
        p=tmp_path/name;p.mkdir();j=cls(p);j.initialize(dict(layout_base_manifest=str(base)),state,{'a'*64});journals.append(j)
        data=dict(kind='assessment',generation=0,new_layouts=['b'*64]);n=j.prepare(data,[[dict(model=state,queries=['x'])]])
        result=dict(entries=[{'rows':[{'mask':[1,2,3]}]}]*100,calls=100,work=100,cpu_seconds=1.,candidate_seconds=1.)
        j.reserve(n,0,100,100);j.receipt(n,0,result,100);j.commit(n,state,dict(nominees=[1]))
        j.verify_chain()
    a,b=journals
    assert a.state()==b.state() and a.layouts()==b.layouts() and a.results(0)==b.results(0) and a.tasks(0)==b.tasks(0)
    assert a.get('usage')==b.get('usage')
    assert b.db.execute('select length(result) from tasks').fetchone()[0]<a.db.execute('select length(result) from tasks').fetchone()[0]
    for j in journals:j.close()
