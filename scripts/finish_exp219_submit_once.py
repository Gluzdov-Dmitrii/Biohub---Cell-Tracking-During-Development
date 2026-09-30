"""Bounded clean-run audit and exactly one authorized guarded code submission."""
import datetime,hashlib,json,subprocess,sys,time
from pathlib import Path,PurePosixPath
import requests
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest
from submit_code_file_once import get_current_kernel,validate_remote_kernel_identity,read_with_retry
L=Path(__file__).resolve().parents[1]
KERNEL='dmitriigluzdov/biohub-exp219-frontier90-public'
COMP='biohub-cell-tracking-during-development'
SOURCE=L/'kaggle_notebooks/exp219_frontier90_public/exp219_runtime.py'
SHA='dcc140873e155862629f6294f5abdb745cb5d36f11b7b76c861e111134d7ba0a'
DESCRIPTION='EXP219 FRONTIER90 SINGLE_ROUTE PRIVATE_ROBUST SLOT3 v1 20260916'
PROGRESS=L/'reports/exp219_submission_progress_20260916.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(status,**values):
    r={'status':status,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**values}
    p=PROGRESS.with_suffix('.partial');p.write_text(json.dumps(r,indent=2)+'\n');p.replace(PROGRESS);print(json.dumps(r),flush=True)
def main():
    with (L/'reports/exp219_submit_claim_lf_20260916.json').open('x') as f:json.dump({'kernel':KERNEL,'description':DESCRIPTION,'source_sha':SHA,'scope':'One guardedPOST after cleanrun completeaudit, no autoretryPOST'},f)
    assert sha(SOURCE)==SHA
    api=KaggleApi();api.authenticate();deadline=time.monotonic()+5400
    while time.monotonic()<deadline:
        state=str(read_with_retry('kernel_status',lambda:api.kernels_status(KERNEL)).status)
        if state.endswith('.COMPLETE'):break
        assert state in ('KernelWorkerStatus.RUNNING','KernelWorkerStatus.QUEUED'),state
        save('WAITING_CLEAN_INTERNET_OFF_RUN',kernel_state=state);time.sleep(45)
    else:raise TimeoutError('Cleanrun deadline; no submission')
    remote=get_current_kernel(api,KERNEL);validate_remote_kernel_identity(remote,KERNEL,1,COMP,SHA)
    save('AUDITING_CLEAN_OUTPUT')
    out=L/'outputs/kaggle/exp219_frontier90_v1';out.mkdir(parents=True,exist_ok=False)
    files=[];token=None;tokens=set();logs=[]
    while True:
        request=ApiListKernelSessionOutputRequest();request.user_name='dmitriigluzdov';request.kernel_slug=KERNEL.split('/')[1]
        api._set_paging(request,100,token)
        with api.build_kaggle_client() as client:response=client.kernels.kernels_api_client.list_kernel_session_output(request)
        files.extend(response.files or [])
        if response.log:logs.append(response.log)
        token=response.next_page_token
        if not token:break
        assert token not in tokens;tokens.add(token)
    names=[x.file_name for x in files];assert len(names)==len(set(names))
    assert [n for n in names if PurePosixPath(n).name=='submission.csv']==['submission.csv']
    (out/'output_inventory.json').write_text(json.dumps({'files':names,'kernel':KERNEL,'version':1,'source_sha256':SHA},indent=2))
    (out/'kernel.log').write_text('\n'.join(logs),encoding='utf-8')
    required=['submission.csv','exp214_runtime_receipt.json']
    required += [n for n in names if n.endswith('/inference_receipt.json') or n.endswith('/spatial_boundary_receipt.json')]
    for name in required:
        assert name in names
        rel=PurePosixPath(name);assert not rel.is_absolute() and '..' not in rel.parts
        item=next(x for x in files if x.file_name==name);dest=out.joinpath(*rel.parts);dest.parent.mkdir(parents=True,exist_ok=True)
        for attempt in range(3):
            try:
                with requests.get(item.url,stream=True,timeout=(30,180)) as r:
                    r.raise_for_status()
                    with dest.with_suffix(dest.suffix+'.partial').open('wb') as f:
                        for chunk in r.iter_content(1024*1024):f.write(chunk)
                dest.with_suffix(dest.suffix+'.partial').replace(dest);break
            except requests.RequestException:
                if attempt==2:raise
                time.sleep(2)
    runtime=json.loads((out/'exp214_runtime_receipt.json').read_text());assert runtime['source_sha256']==SHA
    assert runtime['artifact_manifest_sha256']=='1695d69c70567b398714aabfa99d14691904dec83f7d4ff51fc1675aecc92d86'
    assert runtime['unknown_embryo_selector_oof'] is None
    audit=L/'reports/exp219_clean_output_audit_20260916.json'
    subprocess.run([sys.executable,'scripts/audit_exp214_kaggle_output.py',str(out),'--receipt',str(audit)],cwd=L,check=True)
    prepost={'status':'PASS_PREPOST','track':'PRIVATE_ROBUST','slot':3,'hypothesis':'Measure LB transfer of strongest clean90/60 OOF frontier with fixed single-route unknown inference','parent':'EXP214 gapfix90 publicOOF175=0.7427291486246141','kernel':KERNEL,'version':1,'source_sha256':SHA,'submission_sha256':sha(out/'submission.csv'),'audit_sha256':sha(audit),'runtime_receipt_sha256':sha(out/'exp214_runtime_receipt.json'),'inventory_sha256':sha(out/'output_inventory.json'),'description':DESCRIPTION,'unknown_routing_oof':None,'download_scope':'Complete remote filename inventory and critical CSV/runtime/fold receipts; intermediate model/cache files not redownloaded','promotion_gate':'Valid nonempty Kaggle score/nonzero bytes/noerror; assess versus prior ownLB0.718 and public0.947, no guaranteed score'}
    (L/'reports/exp219_prepost_20260916.json').write_text(json.dumps(prepost,indent=2)+'\n')
    save('PASS_AUDIT_SUBMITTING_ONCE',submission_sha256=prepost['submission_sha256'])
    command=[sys.executable,'scripts/submit_code_file_once.py','--competition',COMP,'--kernel',KERNEL,'--version','1','--file-name','submission.csv','--description',DESCRIPTION,'--source-file',str(SOURCE),'--source-sha256',SHA]
    result=subprocess.run(command,cwd=L,capture_output=True,text=True,timeout=300)
    (L/'reports/exp219_guarded_post_log_20260916.txt').write_text(result.stdout+'\n'+result.stderr)
    # Always reconcile full API after helper, even when its response was ambiguous.
    items=read_with_retry('submission_readback',lambda:api.competition_submissions(COMP))
    matches=[x for x in items if x.description==DESCRIPTION];assert len(matches)==1,(result.returncode,result.stdout,result.stderr)
    x=matches[0];fields=('ref','date','description','status','public_score','error_description','total_bytes','url')
    full={k:str(getattr(x,k)) if k in ('date','status') else getattr(x,k,None) for k in fields}
    quota=api.competition_get_submission_limits(COMP).to_dict()
    (L/'reports/exp219_submission_full_api_20260916.json').write_text(json.dumps({'submission':full,'quota':quota},indent=2)+'\n')
    anomaly=bool(full['error_description']) or (full['status'].endswith('.COMPLETE') and (not full['public_score'] or not full['total_bytes']))
    save('ANOMALY_NO_RETRY' if anomaly else 'SUBMITTED_EXACTLY_ONCE',submission=full,quota=quota)
if __name__=='__main__':
    try:main()
    except Exception as e:
        save('STOPPED_NEEDS_RECONCILIATION_NO_AUTO_POST_RETRY',error=str(e));raise
