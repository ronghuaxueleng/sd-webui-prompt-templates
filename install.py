# installer script for some PyPI packages we need...
import pathlib

import launch
from modules import scripts

pkgs = [
    "peewee",
    ### for deduplicate ###
    "toml",
    "imagededup",
]

for pkg in pkgs:
    if not launch.is_installed(pkg):
        launch.run_pip(f'install {pkg}', "requirements for sd-webui-prompt-templates")

base_dir = scripts.basedir()
template_path = pathlib.Path(base_dir + '/template.db')
if not template_path.exists():
    from jishui.db import init_table

    init_table()
