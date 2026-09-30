"""Prepare fixed cohort gates without opening any predictions or labels."""
import json
from pathlib import Path

def main():
    shards=json.loads(Path('reports/exp214_evaluation_shards_20260912.json').read_text())
    for count in (40,175):
        selected=[s for s in shards['shards'] if count==175 or s['diagnostic']]
        spec={'training_plan_sha256':shards['plan_sha256'],
              'movies':[n for s in selected for n in s['movies']],
              'scope':f'{count} full embryo-held-out movies; budgeted12epoch public-family refit vs matched-detector EXP209 graph, not published400epoch weights',
              'arms':{arm:[] for arm in ('public','local')}}
        assert len(spec['movies'])==len(set(spec['movies']))==count
        for arm,parts in spec['arms'].items():
            for s in selected:
                base=s['run']+'/output/'+arm
                parts.append({'receipt':base+'/inference_receipt.json','csv':base+'/submission.csv','movies':s['movies']})
        with Path(f'reports/exp214_score{count}_manifest_20260912.json').open('x') as f:
            json.dump(spec,f,indent=2);f.write('\n')
    root='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
    spec={'arms':{},'reduced60_training_status':root+'/runs/exp214_equal_time44b6_s2026_20260912/output/status.json'}
    for short in ('full12','reduced12','reduced60'):
        base=root+f'/runs/exp214_control_{short}_20260912/output'
        spec['arms'][short+'_same_single_detector_public_graph']={'receipt':base+'/inference_receipt.json','csv':base+'/submission.csv'}
    with Path('reports/exp214_data_control_score_manifest_20260912.json').open('x') as f:
        json.dump(spec,f,indent=2);f.write('\n')

if __name__=='__main__':main()
