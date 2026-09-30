import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('monitor',Path(__file__).parents[1]/'scripts/monitor_exp213_job.py')
monitor=importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


def test_only_verified_empty_process_tree_releases():
    good={'exit':{'returncode':0},'identity_alive':False,'group_alive':False,'gpu_pids':[]}
    assert monitor.releasable(good)
    for key,value in [('exit',None),('identity_alive',True),('group_alive',True),('gpu_pids',[42])]:
        assert not monitor.releasable({**good,key:value})
        uncertain=good.copy(); del uncertain[key]
        assert not monitor.releasable(uncertain)
