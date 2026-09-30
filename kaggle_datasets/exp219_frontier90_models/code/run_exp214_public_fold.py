"""Run frozen COMPACT47-v20 inference logic using only an explicit model bundle.

No dependency installation, all-train artifact discovery, metric reads, or
submission POST. Paths/checkpoints replace packaging; science cells are frozen.
The fold center may be the existing clean full teacher, explicitly recorded.
"""
import argparse
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil

SOURCE_SHA='5389953eb7c2f68b6e3664985ceb252d0eac391b65821b0ced692693003cbcba'
PREDICTOR_SHA='c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def environment_assignments(source):
    tree=ast.parse(source)
    return [node for node in tree.body if isinstance(node,ast.Assign)
        and len(node.targets)==1 and isinstance(node.targets[0],ast.Subscript)
        and ast.unparse(node.targets[0].value)=='os.environ']


def execute(nodes, namespace, label):
    module=ast.Module(body=nodes,type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module,label,'exec',flags=0x1000000),namespace)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--notebook',type=Path,required=True)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--data-dir',type=Path,required=True)
    p.add_argument('--movies',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    assert sha(args.notebook)==SOURCE_SHA
    assert sha(args.repo/'scripts/predict_unet_transformer.py')==PREDICTOR_SHA
    bundle=json.loads(args.bundle.read_text()); movies=json.loads(args.movies.read_text())
    assert isinstance(movies,list) and movies and len(movies)==len(set(movies))
    for role in ['primary','secondary','center']:
        assert sha(bundle[role]['path'])==bundle[role]['sha256'],role
    if 'source_embryo' in bundle:
        assert all(not name.startswith(bundle['source_embryo']+'_') for name in movies),'Target is source embryo'
    args.output.mkdir(parents=True,exist_ok=False)
    runtime_repo=args.output/'tracking_repo'
    runtime_repo.mkdir()
    for directory in ['src','scripts']:
        shutil.copytree(args.repo/directory,runtime_repo/directory,
            ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    # Read-only telemetry at the pre-ILP return; returned values are unchanged.
    candidate_dir=args.output.resolve()/'candidates'; candidate_dir.mkdir()
    os.environ['EXP214_CANDIDATE_CACHE']=str(candidate_dir)
    predictor=runtime_repo/'scripts/predict_unet_transformer.py'
    source=predictor.read_text()
    marker='    coords = coords.astype(np.int16)\n    return coords, all_edges'
    assert source.count(marker)==1
    source=source.replace(marker,'''    import os as _os
    _cache = Path(_os.environ['EXP214_CANDIDATE_CACHE'])
    np.savez_compressed(_cache / (ds_path.stem + '.npz'), coords=np.asarray(coords,dtype=np.int16),
                        edges=np.asarray(all_edges,dtype=np.float64).reshape((-1,4)))
'''+marker)
    predictor.write_text(source)
    weights=runtime_repo/'weights/unet_transformer/split_0'
    weights.mkdir(parents=True)
    shutil.copy2(bundle['primary']['path'],weights/'edge_predictor_best.pth')
    shutil.copy2(Path(bundle['primary']['path']).parent/'config.json',weights/'config.json')
    test=args.output/'runtime_test'; test.mkdir()
    for name in movies:
        source=(args.data_dir/(name+'.zarr')).resolve()
        assert source.is_dir()
        (test/(name+'.zarr')).symlink_to(source,target_is_directory=True)
    cells=json.loads(args.notebook.read_text())['cells']
    ns={'__name__':'exp214_frozen_public_runtime','os':os}
    execute(environment_assignments(''.join(cells[2]['source'])),ns,'v20_environment')
    os.environ['BIOHUB_DIAGNOSTIC_ARM']=''
    # Packaging cell's environment constants are scientific fusion settings.
    env_nodes=environment_assignments(''.join(cells[4]['source']))
    env_nodes=[n for n in env_nodes if isinstance(n.value,ast.Constant)]
    execute(env_nodes,ns,'v20_fusion_environment')
    os.environ['BIOHUB_SECONDARY_WEIGHTS']=str(Path(bundle['secondary']['path']).resolve())
    config_nodes=ast.parse(''.join(cells[3]['source'])).body
    config_nodes=[n for n in config_nodes if not
        (isinstance(n,ast.Import) and any(x.name=='pandas' for x in n.names)) and not
        (isinstance(n,ast.ImportFrom) and n.module=='IPython.display')]
    execute(config_nodes,ns,'v20_config')
    ns.update(TEST_DIR=test,WORKING_DIR=args.output.resolve(),REPO_DIR=runtime_repo.resolve(),
        SUBMISSION_PATH=args.output.resolve()/'submission.csv',RUN_STATS_PATH=args.output.resolve()/'run_stats.csv')
    # Entire detector-TTA, association-TTA, fusion and ILP cell is reused.
    prediction_source=''.join(cells[5]['source']).replace('/kaggle/working',str(args.output.resolve()))
    execute(ast.parse(prediction_source).body,ns,'v20_prediction')
    graph_nodes=ast.parse(''.join(cells[6]['source'])).body
    boundary=next(i for i,n in enumerate(graph_nodes) if isinstance(n,ast.Assign)
        and ast.unparse(n.targets[0])=='DEEPCENTER_VETO_DETECTOR')
    execute(graph_nodes[:boundary],ns,'v20_graph_definitions')
    # Only artifact resolution differs. Frozen loader supports full/factorized checkpoints.
    ns['_dc_checkpoint_candidates']=lambda:[Path(bundle['center']['path'])]
    # Pandas/IPython are only notebook display dependencies. Keep all scientific
    # graph code, CSV writes and output assertions; serialize telemetry with stdlib.
    presentation=next(i for i,n in enumerate(graph_nodes) if isinstance(n,ast.Assign)
        and ast.unparse(n.targets[0])=='stats' and 'pd.DataFrame' in ast.unparse(n.value))
    execute(graph_nodes[boundary:presentation],ns,'v20_graph_execution')
    stats=sorted(ns['stats_rows'],key=lambda r:r['dataset'])
    if stats:
        for row in stats:row.update(predict_minutes_total=ns['predict_seconds']/60.,experiment_tag=ns['EXPERIMENT_TAG'])
        with (args.output/'run_stats.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in stats for k in r)))
            writer.writeheader();writer.writerows(stats)
    from bound_exp214_submission import bound_submission
    import zarr
    shapes={name:tuple(zarr.open_group(str(args.data_dir/(name+'.zarr')),mode='r')['0'].shape) for name in movies}
    boundary=bound_submission(args.output/'submission.csv',shapes)
    receipt={'status':'PASS_FROZEN_PUBLIC_FAMILY_INFERENCE','notebook_sha256':SOURCE_SHA,
        'base_predictor_sha256':PREDICTOR_SHA,'patched_predictor_sha256':sha(runtime_repo/'scripts/predict_unet_transformer.py'),
        'bundle':bundle,'movies':movies,'submission_sha256':sha(args.output/'submission.csv'),
        'target_labels_read':False,'presentation_only_change':'Pandas/IPython display replaced by stdlib telemetry CSV',
        'spatial_boundary_serialization':boundary,
        'scope':'Family refit using supplied fold weights; not OOF of published all-train weights.'}
    (args.output/'inference_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__': main()
