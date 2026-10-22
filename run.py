import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'finance.py'),run_name='__main__')
runpy.run_path(str(p/'build_dashboard.py'),run_name='__main__')
