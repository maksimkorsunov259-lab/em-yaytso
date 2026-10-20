from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parents[1]
files=['index.html','styles.css','app.css','family-ui.css','recipes.js','model.js','storage.js','app.js','runtime.js','manifest.webmanifest']+sorted(str(f.relative_to(p)) for f in (p/'assets').glob('*'))
build=hashlib.sha256(b''.join((p/f).read_bytes() for f in files)).hexdigest()[:12]
s=(p/'sw.js').read_text()
import re
s=re.sub(r"const CACHE=PREFIX\+'[^']+';","const CACHE=PREFIX+'"+build+"';",s);s=re.sub(r'const FILES=\[.*?\];','const FILES='+json.dumps(['./'+f for f in files])+';',s)
(p/'sw.js').write_text(s)
print('SW build',build,len(files),'resources')
