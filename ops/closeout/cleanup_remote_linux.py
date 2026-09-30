"""User-authorized Biohub-only cleanup, after a verified local archive and Git push."""
import datetime
import getpass
import importlib.util
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path

slug = 'biohub-cell-tracking-during-development'
base = Path('/home/scientists/gluz_d_s/kaggle')
root = base / 'projects' / slug
assert socket.gethostname() == 'prepost'
assert getpass.getuser() == 'gluz_d_s'
assert root == Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
assert root.is_dir() and not root.is_symlink() and root.resolve() == root
assert root.parent.resolve() == base / 'projects'

process_checks = {}
for host in ('nsu-quadro','nsu-a100'):
 # The parent supplies the separately verified ngpu01 process check. This
 # script checks the actual shared-storage host again immediately before delete.
 if host == 'nsu-quadro':
  ps = subprocess.run(['ps','-u','gluz_d_s','-o','pid=,args='],capture_output=True,text=True,check=True)
  matches = [line for line in ps.stdout.splitlines() if slug in line.lower() or 'horaz' in line.lower()]
  assert not matches, matches
  process_checks['prepost_matching_processes'] = matches

control = base / '_control'
spec = importlib.util.spec_from_file_location('resource_queue',control / 'resource_queue.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
with module.transaction(control):
 state = module.Queue(control).read()
 removed = {k:v for k,v in state['requests'].items() if v.get('project') == slug}
 assert all(v['state'] in module.TERMINAL for v in removed.values()), 'Biohub lease not terminal'
 others = {k:v for k,v in state['requests'].items() if k not in removed}
 state['requests'] = others
 module.save(control / 'resource_queue_state.json',state)
 assert module.Queue(control).read()['requests'] == others

metadata = []
for directory in ('requests','diagnostics'):
 parent = control / directory
 for p in parent.iterdir():
  if 'biohub' in p.name.lower() and p.is_file() and not p.is_symlink():
   assert p.resolve().parent == parent.resolve()
   metadata.append(str(p)); p.unlink()

permission_repairs = []
def remove_owned_readonly(function, path, exc_info):
 if not isinstance(exc_info[1], PermissionError):
  raise exc_info[1]
 p = Path(path).absolute()
 assert p == root or p.is_relative_to(root)
 for candidate in (p.parent, p):
  if candidate == root.parent or candidate.is_symlink(): continue
  assert candidate == root or candidate.is_relative_to(root)
  assert candidate.stat().st_uid == os.getuid()
  os.chmod(candidate, candidate.stat().st_mode | 0o700)
  permission_repairs.append(str(candidate))
 function(path)
shutil.rmtree(root, onerror=remove_owned_readonly)
assert not root.exists()
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'hostname':socket.gethostname(),'removed_root':str(root),'root_absent':True,
 'removed_terminal_requests':list(removed),'other_requests_preserved':len(others),
 'removed_biohub_metadata':metadata,'process_checks':process_checks,
 'owned_readonly_repairs':permission_repairs},indent=2))
