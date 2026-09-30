"""Regression for a formerly isolated node becoming an accepted gap endpoint."""
import ast
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment

def run_gap(fixed):
    source=(Path(__file__).parents[1]/'scripts/evaluate_synthetic_gap_deepcenter.py').read_text()
    if not fixed:
        source=source.replace(' and node not in incoming and node not in outgoing','')
    tree=ast.parse(source)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='close_synthetic_gaps')
    body=ast.unparse(function)
    ns={'np':np,'defaultdict':defaultdict,'Path':Path,'linear_sum_assignment':linear_sum_assignment,
        'GAP_CLOSE_UM':5.,'DEEPCENTER_THRESHOLD':.25,'DEEPCENTER_CONFIRM_MIN_SPAN_UM':8.5,
        'GAP_CLOSE_MAX_ADDED_FRAC':.05,'GAP_CLOSE_MAX_ADDED_ABS':2000,'GAP_CLOSE_REUSE_UM':3.2,
        'GAP_DENSITY_REFERENCE_UM':6.5,'GAP_DENSITY_GAIN':.04,'GAP_DENSITY_MAX_STEP_DELTA_UM':.125,
        '_frame_spacing':lambda pos,ids:{i:6.5 for i in ids},'read_zarr_meta':lambda p:((4,8,8,8),'uint16'),
        'get_frame':lambda *a:None,'refine_midpoint':lambda p,f,s:(p,'refined')}
    exec('from __future__ import annotations\n'+body,ns)
    coords=np.array([[0,0,0,0],[1,0,0,0],[1,2,0,0],[2,2,0,0],[3,2,0,0]],dtype=float)
    return ns['close_synthetic_gaps'](coords,[],np.ones(3),Path('unused'),None)

def test_reproduces_old_double_parent_and_fix_retains_two_paths():
    _,bad,_=run_gap(False)
    assert max(Counter(e[1] for e in bad).values())==2
    coords,edges,stats=run_gap(True)
    assert max(Counter(e[1] for e in edges).values())==1
    assert max(Counter(e[0] for e in edges).values())==1
    assert len(edges)==4 and stats['synthetic_added']==1
    assert all(coords[t,0]==coords[s,0]+1 for s,t,*_ in edges)
