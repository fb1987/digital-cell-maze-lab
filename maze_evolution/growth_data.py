"""V11 original hard-pair sampler; exclude all8702 layouts through V10A."""
import gzip,json
from .choice_data import ChoiceData
from .distance_data import prior_manifests as earlier_manifests


def prior_manifests(root):
    rows=earlier_manifests(root)
    for name in ('distance_curriculum','distance_confirmation'):
        rows+=json.loads(gzip.open(root/f'results/{name}/mazes.json.gz','rt').read())
    return rows


class GrowthData(ChoiceData):
    pass
