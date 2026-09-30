import pathlib,json,hashlib,tarfile
base=pathlib.Path('work/biohub_public_audit_20260921/weights_audit');out=pathlib.Path('outputs/research/exp223_horaz0_package_20260921');out.mkdir(exist_ok=True)
files={}
for slug,arm in [('biohub-top-cv-0803-artifact','selected'),('biohub-cfg-embryo-cv-last-folds','fixed_last')]:
 p=base/('horaz0__'+slug)
 for item in json.loads((p/'files.json').read_text())['datasetFiles']:
  name=item['name'];src=p/pathlib.Path(name).name;dest=out/arm/name
  dest.parent.mkdir(parents=True,exist_ok=True);data=src.read_bytes()
  if dest.exists():assert dest.read_bytes()==data
  else:dest.write_bytes(data)
  files[str(dest.relative_to(out)).replace('\\','/')]=hashlib.sha256(data).hexdigest()
(out/'package_manifest.json').write_text(json.dumps(files,indent=2))
with tarfile.open(out.with_suffix('.tar'),'w') as t:
 for p in out.rglob('*'):
  if p.is_file():t.add(p,arcname=str(p.relative_to(out)))
print(out.with_suffix('.tar'),hashlib.sha256(out.with_suffix('.tar').read_bytes()).hexdigest())
