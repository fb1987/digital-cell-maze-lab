"""Write/check bounded future-run specifications. This command does not launch jobs."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/long_search_setup'
Y=ROOT/'results/mating_opportunity'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plans():
    audit=json.loads((Y/'audit.json').read_text())
    assert audit['passed'] and audit['candidate_calls']==0
    evidence={str(p.relative_to(ROOT)):sha(p) for p in (Y/'analysis.json',Y/'audit.json',
        ROOT/'results/linkage_restart/completion.json',ROOT/'maze_evolution/family_reservoir.py')}
    common=dict(status='prepared_specification_not_registered_or_launched',evidence=evidence,
        local_only=True,paid_services=False,origins=['carry','fresh'],replicates=3,population=96,
        max_genes=256,topology='local',exposure=7,known_solver_injection=False,
        seed_policy='Fresh random founders and fresh disjoint training/validation/final seeds; never resume a closed study.',
        protected_carry=20,protected_fresh=0,retained=44,births=52,immigrants=7,
        edits_per_mutant=1,mutation_births=45,merit_slots=4,
        family_policy=dict(max_families=5,reserved_variants_per_family=4,
            distance='Normalized mismatch on inherited gene loci; identical program genotypes never count as diversity.',
            family_ranking='Best current training rank; deterministic ties.',
            variant_choice='Farthest first from already selected family members; training rank breaks ties.',
            fallback='Common behavior-diverse then fitness-ranked fill to exactly44.'),
        archive_policy='Validation archives are preserved externally and never silently reinserted. Historical20 anchors remain protected in every carried arm.',
        search_wall_seconds=4500,candidate_seconds_cap=4500,final_candidate_seconds_cap=600,
        calibration_candidate_seconds_cap=180,audit_accounting='Separate measured wall/calls; never hidden in search budget.',
        max_generations=4096,min_complete_generations=96,peak_rss_bytes=4*2**30,
        artifact_bytes_cap=3*2**30,max_candidate_calls=40000000,max_charged_work=40000000000000,
        checkpoint_interval=32,validation_interval=32,validation_nominees_per_condition=2,
        whole_layout_exclusion_file='results/linkage_restart/whole_layout_exclusions.json.gz',
        known_excluded_layouts=255356,additional_exclusions='Every later fixture/preflight and prior run layout, including all unqueried variants/poses.',
        data=dict(training='Two matched contexts per generation: easy/short plus rotating prefix1/2/4 and genuine second-junction/alternative-cycle tasks,12inputs. Fixed common96-generation pose schedule.',
            validation='New broad independent contexts, all8poses, prefix0/1/2/4/8 with bends, real cycles, corridor and ordinary/nonisolated-disconnected retention controls.',
            final='A separate untouched corpus from the same registered strata; freeze/push all selections before generation.',
            planning='Exact context counts, grammar, schedule and timing-only sizing rule must be fixed during preflight before any validation calls.'),
        fitness='Use only current training rows for reproduction; common paired-first lexicase/10%uniform parent mixture. No reward for genome length or family count.',
        primary_selection='Validation archive rank begins with complete prefix>=4pairs, then true-cycle pairs, all positive-prefix pairs and retention metrics; deterministic digest/identity ties.',
        efficacy_gate=dict(replicates_per_origin=2,min_new_prefix4_pairs=16,min_advantage_over_each_control=16,
            independent_contexts=2,true_cycle_gain_pairs=8,minimum_retention_fraction=.95,
            retain=['paired','corridor','ordinary'],no_increase_false_no_path=True,
            must_pass_validation_and_untouched_final=True),
        readiness=dict(retention_policy_implemented=True,retention_unit_tests_passed=True,
            full_experiment_runner_integrated=False,protocol_registered=False,
            fixture_calibration_passed=False,short_end_to_end_replay_passed=False),
        before_launch=['Integrate the prepared selector with a separately namespaced runner and complete mutation/RNG audit.',
            'Freeze exact data grammar, validation ranking, controls and gates; calibrate unchanged production signatures.',
            'Run a short end-to-end software preflight with discarded births; test protected identities, equal budgets, checkpoints and exact replay.',
            'Freeze/push protocol, source and inputs before validation/training generation.'])
    a=dict(common,name='mutation_diversity_75m',seed=2026102004,
        question='Does retaining related genotypic variation improve transferable solving after sustained mutation and selection?',
        arms=['current_mutation','family_mutation','resample','frozen'],
        target='family_mutation',sexual_crossover=False,
        prerequisite='No sexual activation prerequisite: this is a separate asexual retention-policy comparison. Complete all software/timing preflight checks.',
        resampling='Retain44 with common current selector; draw52 new random genomes. Frozen arm evaluates unchanged founders on every common batch.',
        changes_from_X='Retained count44 and52births are common to both mutation arms, replacing old24/72. Only family-reserved selection differs between them. Compare within this new study.',
        conditions=24,organisms_per_matched_generation=2304,training_calls_per_generation=27648)
    b=dict(common,name='family_crossover_75m',seed=2026102005,
        question='Once real multigene activation is demonstrated, does immediate-gate linkage improve new solving abilities?',
        arms=['gate_linked','unlinked','gate_sham','mutation','resample','frozen'],
        target='gate_linked',sexual_crossover=True,
        prerequisite='A NEW separately preregistered activation pilot must pass>=10%retained multi-change births in>=8generations,2/3replicates persexual policy inBOTHorigins. Y static probabilities cannot satisfy this.',
        segment_lengths=[2,4,8,16,32],mating_attempts_per_generation=23,
        donor_rule='Freeze a common bounded donor rule across all sexual arms before activation. Never choose linkage-eligible donors only for the linked policy.',
        selector='The same previously specified related-variation policy applies to every evolving arm; the mutation reference is essential.',
        ancestry_requirement='Preserve both parents, exact transplanted rows and post-mutation retained changes. A useful child with sexual ancestry is not alone causal proof of composition.',
        conditions=36,organisms_per_matched_generation=3456,training_calls_per_generation=41472)
    return [a,b]


def validate(plan):
    assert plan['retained']+plan['births']==plan['population']==96
    assert plan['immigrants']+plan['mutation_births']==plan['births']
    assert plan['protected_carry']+plan['merit_slots']+5*4<=plan['retained']
    assert plan['conditions']==len(plan['origins'])*plan['replicates']*len(plan['arms'])
    assert plan['training_calls_per_generation']==plan['conditions']*96*12
    assert plan['search_wall_seconds']==4500 and plan['local_only'] and not plan['known_solver_injection']
    for name,h in plan['evidence'].items():
        assert sha(ROOT/name)==h,name
    assert plan['status']=='prepared_specification_not_registered_or_launched'
    return dict(name=plan['name'],conditions=plan['conditions'],
        minutes=plan['search_wall_seconds']/60,prepared=True,launch_ready=all(plan['readiness'].values()),
        outstanding=[name for name,ready in plan['readiness'].items() if not ready])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('prepare','check'))
    args=parser.parse_args()
    if args.action=='prepare':
        assert not OUT.exists(),'Refuse to overwrite prepared plans'
        OUT.mkdir()
        for plan in plans():
            validate(plan)
            (OUT/(plan['name']+'.json')).write_text(json.dumps(plan,indent=2)+'\n')
    results=[validate(json.loads(p.read_text())) for p in sorted(OUT.glob('*_75m.json'))]
    assert len(results)==2
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()
