"""Check migrations, seeding and every page in a clean temporary copy."""
from pathlib import Path
import tempfile,shutil,subprocess,sys,os,json
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='meridian8-clean-') as directory:
    target=Path(directory)/'project'
    shutil.copytree(ROOT,target,ignore=shutil.ignore_patterns('.git','.venv','venv','node_modules','__pycache__','evidence','media','staticfiles','*.sqlite3','.env'))
    env=os.environ.copy();env.pop('TRAVEL_DB',None)
    for args in [['manage.py','migrate','--noinput'],['manage.py','seed_demo'],['manage.py','check'],['tools/export_pages.py']]:
        result=subprocess.run([sys.executable,*args],cwd=target,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(' '.join(args)+'\n'+result.stdout,flush=True)
        if result.returncode:sys.exit(result.returncode)
    pages=json.loads((target/'evidence/pages.json').read_text());assert len(pages)==35
    print('Чистая копия: миграции, заполнение и 35 страниц успешно проверены.')
