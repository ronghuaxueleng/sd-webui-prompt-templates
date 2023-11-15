from modules import script_callbacks  # type: ignore # SD-WebUI自带的依赖

import read_template
import prompt_translator
import deduplicate_images


def deduplicate_images_ui_tab():
    return deduplicate_images.create_ui(), deduplicate_images.title, deduplicate_images.title


def read_template_ui_tab():
    return read_template.create_ui(), "提示词模版", "prompt_template"


def prompt_translator_ui_tab():
    return prompt_translator.create_ui(), "提示词翻译", "prompt_translator"


def ui_tab():
    """注意，此函数要求能在 sys.path 已经被还原的情况下正常调用"""
    return [read_template_ui_tab(), prompt_translator_ui_tab(), deduplicate_images_ui_tab()]


script_callbacks.on_ui_tabs(ui_tab)
