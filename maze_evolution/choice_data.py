"""V9 unchanged V8 sampling; exclude V1–V8 and V8A whole layouts."""
import gzip,json
from .junction_data import JunctionData,prior_manifests as earlier_manifests


def prior_manifests(root):
    rows=earlier_manifests(root)
    for name in ('junction_choice','junction_confirmation'):
        rows+=json.loads(gzip.open(root/f'results/{name}/mazes.json.gz','rt').read())
    return rows


class ChoiceData(JunctionData):
    pass
