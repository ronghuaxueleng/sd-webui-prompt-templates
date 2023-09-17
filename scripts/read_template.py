import json

import gradio as gr

from modules import scripts, script_callbacks

base_dir = scripts.basedir()
template_path = base_dir + r"/template.json"
headers = ["正向提示词", "负向提示词", "操作"]


def loadjsonfile(template_path):
    with open(template_path, "r", encoding="utf-8-sig") as f:
        templates = json.loads(f.read())
        template_values = []
        for template_dict in templates:
            temp_list = list(template_dict.values())
            temp_list.append("<a href='http://www.baidu.com'>dss</a>")
            template_values.append(temp_list)
        return template_values


def refrash_list():
    return gr.Dataframe.update(value=loadjsonfile(template_path))


def add_tab():
    with gr.Blocks(analytics_enabled=False) as tab:
        with gr.Row():
            with gr.Tab('模版列表'):
                with gr.Row():
                    with gr.Column():
                        refrash_list_btn = gr.Button(elem_id='refrash_template_list', value='刷新')
                with gr.Row():
                    datatable = gr.DataFrame(headers=headers,
                                             datatype=["str", "str", "html"],
                                             interactive=False,
                                             wrap=True,
                                             value=loadjsonfile(template_path),
                                             elem_id="prompt_template_list"
                                             )

            refrash_list_btn.click(
                fn=refrash_list,
                outputs=datatable
            )

    return [(tab, "提示词模版", "prompt_template")]


script_callbacks.on_ui_tabs(add_tab)
