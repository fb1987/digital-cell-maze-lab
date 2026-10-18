"""V7 layouts exclude all V1–V6 layouts; independent construction-test seed."""
import gzip,json
from .beacon_data import BeaconData,prior_manifests as earlier_manifests


def prior_manifests(root):
    return earlier_manifests(root)+json.loads(gzip.open(root/'results/goal_beacon/mazes.json.gz','rt').read())


class BalanceData(BeaconData):
    pass
