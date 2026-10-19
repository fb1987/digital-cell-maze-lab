"""Regression for the post-freeze audit-only NumPy-count JSON repair."""
import json
import numpy as np
import pytest
from maze_evolution.routing_transfer_data import FIXTURES,load
from maze_evolution.routing_transfer import record
from maze_evolution.routing_transfer_audit import synthetic
from maze_evolution.foundation_study_verify_core import Checker
from tools.audit_routing_transfer import original_trace_pair,json_safe_trace_pair


def test_trace_count_preserves_value_and_serializes():
    cases,contexts,metadata=load(FIXTURES);pose=contexts[0]['poses'][0]
    a,b=[cases[cid] for cid in pose['cases']['fork']];checker=Checker(cases);histories=[]
    for o in (a,b):
        checker.row(record(synthetic(o,o.path),o,metadata[o.maze.case_id]),metadata[o.maze.case_id]['side'])
        history=np.zeros((2,8,len(o.maze.cells)),np.uint16)
        history[0,2,pose['meta']['decision']['prefix']]=1
        history[1,2,o.path]=1;histories.append(history)
    raw=original_trace_pair(*histories,a,b,checker)
    with pytest.raises(TypeError):json.dumps(raw)
    repaired=json_safe_trace_pair(*histories,a,b,checker)
    assert type(repaired['strict_both_ticks']) is int and repaired['strict_both_ticks']==1
    assert repaired==raw
    assert json.loads(json.dumps(repaired))==repaired
