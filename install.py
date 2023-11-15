# installer script for some PyPI packages we need...
import pathlib

import launch
from modules import scripts

pkgs = [
    "peewee",
    ### for deduplicate ###
    "toml",
    "imagededup",
    ### for tagger ###
    "huggingface_hub",
    "\"opencv-python>=4.7.0.68\"",
    "onnxruntime-gpu",
]

for pkg in pkgs:
    if not launch.is_installed(pkg):
        launch.run_pip(f'install {pkg}', f"install {pkg} for sd-webui-prompt-templates")

base_dir = scripts.basedir()
template_path = pathlib.Path(base_dir + '/template.db')
if not template_path.exists():
    from jishui.db import init_table

    init_table()
