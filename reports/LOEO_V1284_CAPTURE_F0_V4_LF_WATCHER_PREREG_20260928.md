# V1284 fold0 capture v4 — LF source and watcher-path correction preregistration

Written 2026-09-28 before successor code. This is a local-only correction to
the one-shot failed v3 attempt `loeo_v1284_capture_f0_v3_1de3d2be98c3`.
Preserve that attempt, the 27-file capture-v3 manifest SHA256
`bc2847fe7e142aa9a20b8abea6185d87fdae7d9fb184cb0eb784de0d90b60486`,
and control-v3 manifest SHA256
`e6c996f95f2c6eb191c37b0278aa343fa27daa48f67f1778bce1d507849e7ad8`
unchanged. The failed attempt exited before verified feature capture, and its
lease was independently observed RELEASED with no GPU process.

## Hypothesis and exact correction

The executed cell4 writes the patched predictor and
`v1284_coordinate_refinement.py` with `Path.write_text` using platform-default
newline translation. The Windows-tested predictor is CRLF (56,462 bytes;
SHA256 `7f0997565a26ec2f819039fd857f912cef03d72dd21c31d0167e004d596638b4`),
while the Linux runtime emitted LF (55,227 bytes; SHA256
`330b7407fbf8d0f89af22f8821dffc9bc17332d37179fd87f04dca9819b6c4e`).
The module has the same latent defect: Linux LF is 3,423 bytes/79 LF, SHA256
`940e6d18c4a2f93d5df43912b36d4dec308a3b551686285f25a351b1da354894`,
whereas the CRLF pin is
`db22bcf2cd7d54dda021302c281b224ef517508e53f2aaa7c75fd47b6fe11e8a`.
Write both final generated files as explicit UTF-8 LF bytes and bind the v4
plan/contract to the two LF hashes. An independent byte test must feed both LF
and CRLF inputs and prove identical LF outputs and exact hashes.

The v3 control launcher passed a relative `--config` path to a watcher whose
working directory is the sealed control package. `read_config` correctly
rejects any path inside that package, so the detached watcher exited before
observing the child. The v4 launcher shall resolve the external config to an
absolute path before launching the watcher. A local mock launch test from an
unrelated cwd must prove that the watcher argument is absolute and resolves to
the prepared config. Keep the external-config rejection and one-shot receipt
rules unchanged.

## Successor boundaries and gate

Create distinct v4 source and control packages, unique v4 plan/attempt and
package manifests. Pin the preregistration hash in the source contract and the
source manifest in the control contract. Preserve executed x138 cells 0–4,
source44b6-only image split, audited primary/secondary model pins, capture-only
graph boundary before GEFF serialization, access guard, one A100 lease,
watcher release, and independent runtime/shard audits. Existing v3 packages
and failed run are immutable. This work ends with local unit tests, AST and
manifest readback, and an independent second review request. No remote stage,
queue action, GPU launch, target GEFF read, submission, or score is authorized
by this preregistration.
