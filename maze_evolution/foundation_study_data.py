"""Shared V12C founders and elementary task schedule; no solver-derived founders."""
import hashlib
import json
import random

from .datasets import seed_for
from .foundation_calibration import ROOT
from .foundation_data import FoundationData, prior_manifests
from .growth import Genome, random_genome
from .regulatory_search import tuple_tree


SEED = 2026101815


def exclusions():
    extras = [ROOT / 'results/foundation_calibration/mazes.json.gz',
              ROOT / 'results/foundation_calibration/fixtures.json.gz',
              ROOT / 'results/foundation_repair/mazes.json.gz',
              ROOT / 'results/foundation_study_profile/unit_fixtures/mazes.json.gz']
    return prior_manifests(ROOT, extras)


def founders(origin, topology, rep, seed=SEED, population=96):
    if origin == 'native':
        path = ROOT / f'results/capacity_growth/checkpoints/growth_{topology}_cap256_{rep}.json'
        state = json.loads(path.read_text())
        assert len(state['population']) == population
        genomes = [Genome.from_dict(i['genome']) for i in state['population']]
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        refs = [dict(path=str(path.relative_to(ROOT)), id=i['id'],
                     sha256=sha) for i in state['population']]
        rng_state = tuple_tree(state['rng_state'])
    elif origin == 'fresh':
        rng = random.Random(seed_for(seed, 'fresh-founders', rep, 0))
        genomes = [random_genome(rng, True) for _ in range(population)]
        refs = [dict(factory='growth.random_genome', seed=seed, replicate=rep, index=i) for i in range(population)]
        rng_state = random.Random(seed_for(seed, 'fresh-search-rng', rep, 0)).getstate()
    else:
        raise ValueError('Unknown origin')
    return genomes, refs, rng_state


def validation(data, rep, split='validation'):
    pairs = []
    for level in range(4):
        for family in ('perfect', 'random'):
            pairs.extend(data.group(split, rep, 0, level, family, 17 if level == 3 else 9).pairs)
    pairs.extend(data.disconnected_group(split, rep, 0).pairs)
    return pairs


def batch(data, rep, generation, level):
    """Four current rotations, one earlier-skill pair and one preview pair."""
    family = 'perfect' if generation % 2 == 0 else 'random'
    n = 17 if level == 3 else 9
    group = data.group('train_current', rep, generation, level, family, n)
    start = 4 * (generation % 2)
    pairs = list(group.pairs[start:start + 4])
    recall = generation % level if level else 0
    preview = min(3, level + 1)
    for name, stage in (('train_recall', recall), ('train_preview', preview)):
        if name == 'train_preview' and generation % 8 == 7:
            item = data.disconnected_group('train_mixed', rep, generation)
            pairs.append(item.pairs[generation % 8])
            continue
        item = data.group(name, rep, generation, stage, family, 17 if stage == 3 else 9)
        pairs.append(item.pairs[generation % 8])
    return pairs


def advance(levels, entered, generation, searches):
    result = []
    for rep in range(3):
        level = levels[rep]
        eligible = [s for s in searches if s.config['replicate'] == rep and str(level) in s.competence]
        if level < 3 and generation - entered[rep] >= 20 and eligible:
            certificate = eligible[0].competence[str(level)]
            levels[rep] += 1
            entered[rep] = generation
            result.append(dict(replicate=rep, generation=generation, level=level + 1,
                               condition=eligible[0].key, certificate=certificate))
    return result
