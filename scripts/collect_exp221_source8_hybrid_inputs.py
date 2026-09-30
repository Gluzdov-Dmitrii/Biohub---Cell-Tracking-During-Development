"""One read-only source8 artifact/provenance export; performs no inference/scoring."""
import json
from pathlib import Path
from monitor_exp213_job import ssh
from prepare_exp221_source_graph import ROOT,RUN,CODE


def main():
    source='''import json,hashlib,sys
from pathlib import Path
r=Path(ROOT);run=Path(RUN);code=Path(CODE)
repo=r/'code/exp214_honest_refit_v4_20260912/tracking_repo'
sys.path[:0]=[str(repo/'src'),str(repo/'scripts')]
import zarr
from biohub_tracking.io import _parse_scale
from geff import GeffMetadata
def read(p):return json.loads(p.read_text())
def file(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
movies=read(code/'movies.json'); assert len(movies)==8
metrics_path=run/'score/metrics.json';metrics=read(metrics_path)
assert metrics['status']=='PASS_SOURCE_VALIDATION_PAIRED_GRAPH8'
bundle=read(code/'control_bundle.json')
primary_plan=read(r/'code/exp221_control_v1_20260921/plan.json')
secondary_plan=read(r/'code/exp214_strong60_v1_20260912/plan.json')
center_split=read(r/'runs/exp180_reciprocal_deepcenter_training_20260910/trainer_44b6_source.json')[0]
assert set(movies)==set(primary_plan['folds']['44b6']['validation'])==set(secondary_plan['folds']['44b6']['validation'])
assert not set(movies)&set(primary_plan['folds']['44b6']['train'])
assert not set(movies)&set(secondary_plan['folds']['44b6']['train'])
assert not set(movies)&{n.removesuffix('.zarr') for n in center_split['train']+center_split['test']}
for role in ['primary','secondary','center']: assert file(Path(bundle[role]['path']))['sha256']==bundle[role]['sha256']
out={'status':'PASS_FIXED_SOURCE8_HYBRID_INPUT_EXPORT','scope':'Source validation development only; no target6bba data',
     'root':str(r),'repo':str(repo),'python':str(r/'envs/prepost/py3.11-stdlib-v1/bin/python'),
     'data':str(r/'data/exp213_source_view_20260912'),'source_manifest':file(code/'movies.json'),
     'control_csv':file(run/'output/control/submission.csv'),'control_receipt':file(run/'output/control/inference_receipt.json'),
     'source_graph_metrics':file(metrics_path),'metrics':metrics,
     'prediction_gate':read(run/'output/status.json'),'no_metric_gate':read(run/'score/no_metric_gate.json'),
     'control_bundle':bundle,'source_provenance':{'primary_train_overlap':[],'secondary_train_overlap':[],'center_train_and_selection_overlap':[],
        'source_validation_movies':movies,'primary_plan':file(r/'code/exp221_control_v1_20260921/plan.json'),
        'secondary_plan':file(r/'code/exp214_strong60_v1_20260912/plan.json'),
        'center_split':file(r/'runs/exp180_reciprocal_deepcenter_training_20260910/trainer_44b6_source.json')},
     'datasets':{},'api':{'shape':'zarr.open_group(path, mode="r")["0"].shape is (T,Z,Y,X)',
      'scale':'biohub_tracking.io._parse_scale(group.attrs) is physical (z,y,x) micrometres per raw voxel',
      'geometry':'CSV nodes are raw float voxel (t,z,y,x); use exact float coordinates, do not round',
      'metric':'biohub_tracking.metrics.evaluate(graph, ds.tracks, scale=ds.scale); then per_sample_metrics(metric,estimated_nodes,node_recall) and summarise(rows)',
      'graph':'predict_unet_transformer.build_graph(coords[N,4], edges[(source_index,target_index,1.0,0.0)]); map original node IDs to array indices',
      'reader':str(code/'score_exp221_source_graph.py')+'::read_graphs validates exact CSV schema and DAG constraints',
      'scorer':str(code/'score_exp221_source_graph.py')},
     'cpu_bounded_helper_local':'scripts/launch_exp220_node_strata.py (reference wrapper; not a generic argument-compatible launcher)',
     'cpu_gated_wrapper_local':'scripts/migrate_exp221_source_supervision.py (subprocess timeout900s/taskset0-3/OMP4/MKL4/CUDA empty)',
     'cpu_allocation':'prepost/nsu-quadro; check live aggregate CPU/RAM;4threads, bounded timeout, no GPU lease'}
for name in movies:
 p=r/'data/exp213_source_view_20260912'/(name+'.zarr');g=zarr.open_group(str(p),mode='r')
 estimate=(GeffMetadata.read(p.with_suffix('.geff')).extra or {})['estimated_number_of_nodes']
 out['datasets'][name]={'zarr':str(p),'geff':str(p.with_suffix('.geff')),'shape_tzyx':list(g['0'].shape),
                        'voxel_scale_zyx_um':list(_parse_scale(dict(g.attrs))),'estimated_number_of_nodes':estimate}
print(json.dumps(out))
'''.replace('ROOT',repr(ROOT)).replace('RUN',repr(RUN)).replace('CODE',repr(CODE))
    result=ssh('nsu-quadro',ROOT+'/envs/prepost/py3.11-stdlib-v1/bin/python -',source)
    path=Path('reports/exp221_source8_hybrid_input_package_20260921.json')
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'package':str(path),'control_csv':result['control_csv'],
                      'summary':result['metrics']['summary'],'datasets':len(result['datasets'])},indent=2))


if __name__=='__main__':main()
