# installer script for some PyPI packages we need...
import pathlib

import launch
from modules import scripts

pkgs = [
    {"peewee": "peewee"}
]

for pkg in pkgs:
    key, val = next(iter(pkg.items()))
    if not launch.is_installed(key):
        launch.run_pip(f'install {val}', "requirements for sd-webui-prompt-templates")

base_dir = scripts.basedir()
template_path = pathlib.Path(base_dir + '/template.db')
if not template_path.exists():
    from scripts.jishui.db import init_table
    init_table()