# V1284 control-v5 queue shape and unlaunched proof addendum

Written 2026-09-28 after the first local v5 test pass and before the
corresponding v5 code changes. This clarifies the existing preregistration
`LOEO_V1284_CAPTURE_CONTROL_V5_REQUEST_RECOVERY_PREREG_20260928.md`;
source-v4 and control-v4 seals remain unchanged.

The live queue's unallocated WAITING_RESOURCE and CANCELLED rows can carry
`alias=null` before GPU assignment. Treat `alias=null` or the planned
`nsu-a100` as valid only for those unallocated states, while still requiring
the exact lease ID, token, owner, project, run path, pool, resources,
`process=null`, and `gpus=[]`. RESERVED must carry the planned alias, one
allocated GPU, and `process=null`. RELEASED must retain the planned alias
and report `gpus=[]` for terminal readback. Any other shape is unresolved.

Before canceling WAITING or releasing an unlaunched RESERVED row, read the
remote planned run path and the current user's process command lines. Require
the run absent, no process command line containing the exact run path, and no
unreadable own process command line. For RESERVED, also require the assigned
GPU to be physically idle. Recheck the exact live queue row after this probe
and before fsyncing the one-shot mutation intent. This strengthens the
unlaunched proof without changing source science, queue mutations, or the
independent audit outcome identifier. Keep all testing local and mocked.
