from modules import script_callbacks  # type: ignore # SD-WebUI自带的依赖

import read_template


def read_template_ui_tab():
    return (read_template.create_ui(), "提示词模版", "prompt_template")


def ui_tab():
    """注意，此函数要求能在 sys.path 已经被还原的情况下正常调用"""
    return [read_template_ui_tab()]


script_callbacks.on_ui_tabs(ui_tab)
