"""V12O reuses the declared elementary grammar with NEW seeds and all eight poses."""
from .foundation_calibration import ROOT
from .foundation_study import read_compressed
from .branch_pressure_data import create,query,load,exclusions as through_M

OUT=ROOT/'results/mutation_depth'
FIXTURES=ROOT/'results/mutation_depth_fixtures'
SEED=2026101910
FIXTURE_SEED=1294
ARMS=('depth1','depth4','depth16','single','resample')
TOPS=('local','evolved')
DEPTHS=(1,4,16)


def exclusions():
    rows=through_M()
    for name in ('branch_pressure_calibration_fixtures','branch_pressure_calibration/calibration','branch_pressure_calibration/validation','branch_pressure_calibration/confirmation'):
        rows+=read_compressed(ROOT/'results'/name/'mazes.json.gz')
    return rows
