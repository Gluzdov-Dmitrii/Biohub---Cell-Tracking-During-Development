import pathlib,json,sys
sys.path.insert(0,'scripts');from monitor_exp213_job import ssh
src="""import pathlib,json
r=pathlib.Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
f=json.loads((r/'runs/exp214_gapfix_score175_20260914/output/new90/metrics.json').read_text())
names=sorted(x['dataset'] for x in f['rows']['public']);assert len(names)==len(set(names))==175
rows=[]
for name in names:
 assert name.startswith(('44b6_','6bba_'))
 p=r/'data/exp213_source_view_20260912'/(name+'.zarr')
 shape=json.loads((p/'0/zarr.json').read_text())['shape']
 rows.append({'dataset':name,'fold':0 if name.startswith('44b6_') else 1,'zarr':str(p),'shape':shape})
print(json.dumps(rows))
"""
a=ssh('nsu-quadro','python3 -',src)
p=pathlib.Path('reports/exp223_heldout175_manifest_20260921.json');p.write_text(json.dumps({'experiment':'EXP223','source':'EXP214 full175 immutable baseline cohort','arms':['selected50_20','fixedlast50_same_decoder'],'routing':'44b6->fold0;6bba->fold1;single_fold_only','rows':a},indent=2));print(json.dumps({'n':len(a),'frames':sum(r['shape'][0] for r in a),'fold0':sum(r['fold']==0 for r in a),'fold1':sum(r['fold']==1 for r in a)}))
