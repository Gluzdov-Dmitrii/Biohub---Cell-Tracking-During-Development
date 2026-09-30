"""Apply the proven handoff to the one source8 inference monitor."""
from pathlib import Path

s=Path('scripts/handoff_exp221_supervision.py').read_text()
s=s.replace('from stage_exp221_supervision import CODE','from migrate_exp221_source_supervision import SUP as CODE')
s=s.replace("{'exp221-control-44b6-s2026-20260921','exp221-domain-44b6-s2026-20260921'}","{'exp221-source-graph8-20260921'}")
s=s.replace("@(@(10868, 'control'), @(29248, 'domain'))","@(,@(20452, 'source_graph8'))")
s=s.replace("'_44b6_s2026_20260921_config.json*'","'_20260921_config.json*'")
s=s.replace('[10868,29248]','[20452]')
s=s.replace('exp221_monitor_handoff_local_stop','exp221_source_monitor_handoff_local_stop')
exec(compile(s,'<source8_verified_monitor_handoff>','exec'))
