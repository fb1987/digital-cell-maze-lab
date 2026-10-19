"""V12H audit entry point with a serialization-only diagnostic type repair.

The preregistered auditor stays byte-for-byte intact. Its trace_pair count can
be numpy.int64 because sum consumes NumPy booleans. JSON needs a Python int.
All original checks and replays run; no inference or assessment is modified.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from maze_evolution import routing_transfer_audit as frozen

original_trace_pair=frozen.trace_pair


def json_safe_trace_pair(*args,**kwargs):
    result=original_trace_pair(*args,**kwargs)
    result['strict_both_ticks']=int(result['strict_both_ticks'])
    return result


if __name__=='__main__':
    frozen.trace_pair=json_safe_trace_pair
    frozen.audit()
