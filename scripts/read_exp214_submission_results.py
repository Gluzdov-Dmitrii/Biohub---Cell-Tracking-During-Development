"""Read only the two authorized EXP214 submissions; never mutate Kaggle."""
import datetime,json
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi

def main():
    api=KaggleApi();api.authenticate();items=api.competition_submissions('biohub-cell-tracking-during-development')
    refs={'public':56192907,'local':56192924,'EXP212':56181132,'COMPACT47_v20':56177715,'COMPACT47_v21':56187070}
    fields=('ref','date','description','status','public_score','private_score','error_description','total_bytes','url')
    records={}
    for name,ref in refs.items():
        matches=[x for x in items if x.ref==ref];assert len(matches)==1,(name,ref)
        records[name]={k:str(getattr(matches[0],k)) if k in ('date','status') else getattr(matches[0],k,None) for k in fields}
    anomalies=[];complete=[]
    for name in ('public','local'):
        r=records[name];state=r['status'].split('.')[-1]
        has_score=r['public_score'] is not None and str(r['public_score']).strip()!=''
        if r['error_description'] or state=='ERROR' or (state=='COMPLETE' and (not has_score or int(r['total_bytes'] or 0)<=0)):anomalies.append(name)
        elif state=='COMPLETE':complete.append(name)
    limits=api.competition_get_submission_limits('biohub-cell-tracking-during-development')
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ANOMALY_STOP_NO_FURTHER_POST' if anomalies else ('COMPLETE_BOTH_VALID_LB_RESULTS' if len(complete)==2 else 'PENDING_LB_RESULTS'),'submissions':records,'anomalies':anomalies,'quota':{**limits.to_dict(),'numAllowedNow':limits.num_allowed_now},'additional_submissions_authorized':False}
    path=Path('reports/exp214_submission_monitor_latest.json');part=path.with_suffix('.json.partial');part.write_text(json.dumps(result,indent=2)+'\n');part.replace(path)
    with Path('reports/exp214_submission_monitor_history.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
    if anomalies:
        p=Path('reports/exp214_lb_anomaly.json')
        if not p.exists():p.write_text(json.dumps(result,indent=2)+'\n')
    if len(complete)==2:
        p=Path('outputs/research/exp214_comparison_20260912/lb_results.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'utc':result['utc'],'submissions':{n:records[n] for n in ('public','local')},'quota':result['quota']},indent=2))
if __name__=='__main__':main()
