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
            temp_list = list()
            temp_list.append(template_dict['prompt'])
            temp_list.append(template_dict['NegativePrompt'])
            buttons = ("<div style='margin-top: 3px; text-align: center;'>"
                       "<button style='width: 102px;' class='secondary gradio-button svelte-cmf5ev'>详情</button>"
                       "</div>"
                       "<div style='margin-top: 3px; text-align: center;'>"
                       "<button style='width: 102px;' class='secondary gradio-button svelte-cmf5ev'>发送到文生图</button>"
                       "</div>")
            temp_list.append(buttons)
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
                                             max_rows=10,
                                             show_label=True,
                                             overflow_row_behaviour="show_ends",
                                             value=loadjsonfile(template_path),
                                             elem_id="prompt_template_list"
                                             )

            refrash_list_btn.click(
                fn=refrash_list,
                outputs=datatable
            )

    return [(tab, "提示词模版", "prompt_template")]


script_callbacks.on_ui_tabs(add_tab)
