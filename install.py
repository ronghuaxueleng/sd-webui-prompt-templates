import launch

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