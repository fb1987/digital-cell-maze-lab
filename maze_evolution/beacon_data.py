"""V6 fresh layouts exclude all V1–V5 inputs, including inspected final sets."""
import gzip,json
from .factor_data import FactorData,prior_manifests as earlier_manifests


def prior_manifests(root):
    return earlier_manifests(root)+json.loads(gzip.open(root/'results/factor_curriculum/mazes.json.gz','rt').read())


class BeaconData(FactorData):
    pass
