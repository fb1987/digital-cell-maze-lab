from copy import deepcopy
import pytest
from maze_evolution.family_reservoir import retain,distance


def population():
    result=[]
    for i in range(96):
        family=i%8;variant=i//8
        genes=[[1,20,(j+variant)%64,0,0,0,64] for j in range(8)]
        result.append(dict(id=f'i{i}',family=f'f{family}',genotype=f'g{i}',
                           gene_ids=[f'f{family}/g{j}' for j in range(8)],
                           genes=genes,behavior=str(i%3)))
    return result


def test_common_capacity_protection_and_no_mutation():
    p=population();old=deepcopy(p);protected=[r['id'] for r in p[:20]]
    for policy in ('current','family'):
        chosen,event=retain(p,protected,policy)
        assert len(chosen)==44 and len({r['id'] for r in chosen})==44
        assert [r['id'] for r in chosen[:20]]==protected
        assert all(r==old[int(r['id'][1:])] for r in chosen)
    assert p==old


def test_family_slots_are_bounded_and_distinct_genotypes():
    p=population();chosen,event=retain(p,[],'family')
    reserved=[r for r in event['selection'] if r['reason']=='family_variant']
    assert len(reserved)==20 and len(event['families'])==5
    assert all(sum(r['family']==f for r in reserved)==4 for f in event['families'])
    assert len({r['genotype'] for r in chosen})==44


def test_identical_program_tags_do_not_create_distance_or_reserved_variants():
    p=population()
    for r in p:r['genotype']='same';r['genes']=p[0]['genes']
    assert distance(p[0],p[1])==0
    chosen,event=retain(p,[],'family')
    assert event['family_reserved']<=5 and len(chosen)==44


def test_farthest_first_prefers_diverged_related_variant():
    p=population()
    base=p[0];near=deepcopy(base);near['id']='near';near['genotype']='near'
    far=deepcopy(base);far['id']='far';far['genotype']='far'
    near['genes'][0][2]=60
    for row in far['genes']:row[2]=61
    assert distance(base,far)>distance(base,near)>0
    q=[base,near,far]+[r for r in p[1:] if r['family']!='f0']
    _,event=retain(q,[],'family',count=44,merit_slots=1,family_count=1,variants_per_family=1)
    assert next(r['id'] for r in event['selection'] if r['reason']=='family_variant')=='far'


def test_invalid_or_colliding_identities_are_rejected():
    p=population();p[1]['id']=p[0]['id']
    with pytest.raises(AssertionError):retain(p,[],'family')
    with pytest.raises(AssertionError):retain(population(),['missing'],'current')


def test_shared_retained_count_and_reproducibility():
    p=population()
    assert retain(p,[],'family')==retain(p,[],'family')
    assert len(retain(p,[],'current')[0])==len(retain(p,[],'family')[0])==44
