import json
import base64

import gradio as gr
from modules import scripts, script_callbacks, ui, generation_parameters_copypaste

base_dir = scripts.basedir()
config_path = base_dir + r"/config.json"
detail_html_path = base_dir + r"/detail.html"
template_path = base_dir + r"/template.json"
headers = ["正向提示词", "负向提示词", "操作"]
paste_int_field_default_val_map = {}
paste_field_name_map = {}

with open(config_path, "r", encoding="utf-8-sig") as f:
    configs = json.loads(f.read())
    paste_field_name_map = configs['paste_field_name_map']
    paste_int_field_default_val_map = configs['paste_int_field_default_val_map']


def loadjsonfile(template_path):
    with open(template_path, "r", encoding="utf-8-sig") as f:
        templates = json.loads(f.read())
        template_values = []
        for template_dict in templates:
            temp_list = list()
            temp_list.append(template_dict['prompt'])
            temp_list.append(template_dict['NegativePrompt'])
            raw_encode = base64.b64encode(template_dict['raw'].encode("utf-8")).decode('utf-8')
            jump_to_detail_onclick = 'jump_to_detail("' + raw_encode + '")'
            prompt_send_to_txt2img_onclick = 'prompt_send_to_txt2img("' + raw_encode + '")'
            prompt_send_to_img2img_onclick = 'prompt_send_to_img2img("' + raw_encode + '")'
            buttons = f"""
            <div style='margin-top: 3px; text-align: center;'>
                <button style='width: 102px;' class='secondary gradio-button svelte-cmf5ev' onclick='{jump_to_detail_onclick}'>详情</button>
            </div>
            <div style='margin-top: 3px; text-align: center;'>
                <button style='width: 102px;' class='secondary gradio-button svelte-cmf5ev' onclick='{prompt_send_to_txt2img_onclick}'>to txt2mig</button>
            </div>
            <div style='margin-top: 3px; text-align: center;'>
                <button style='width: 102px;' class='secondary gradio-button svelte-cmf5ev' onclick='{prompt_send_to_img2img_onclick}'>to img2mig</button>
            </div>
            """
            temp_list.append(buttons)
            template_values.append(temp_list)
        return template_values


def find_prompts(fields, paste_type):
    for field, name in fields:
        if isinstance(name, str):
            paste_field_name_map.get(paste_type).get('names').append(name)
            paste_field_name_map.get(paste_type).get('fields').append(field)
    return paste_field_name_map.get(paste_type).get('fields')


def find_txt2img_prompts(fields):
    return find_prompts(fields, 'txt2img')


def find_img2img_prompts(fields):
    return find_prompts(fields, 'img2img')


def send_prompts(encodeed_prompt_raw, paste_type):
    decodeed_prompt_raw = base64.b64decode(encodeed_prompt_raw).decode('utf-8')
    params = generation_parameters_copypaste.parse_generation_parameters(decodeed_prompt_raw)
    values = []
    for name in paste_field_name_map.get(paste_type).get('names'):
        val = params.get(name)
        if val is None and name in paste_int_field_default_val_map.keys():
            val = paste_int_field_default_val_map.get(name)
        try:
            values.append(int(val))
        except:
            values.append(str(val))
    return tuple(values) or gr.update()


def send_txt2img_prompts(encodeed_prompt_raw):
    return send_prompts(encodeed_prompt_raw, 'txt2img')


def send_img2img_prompts(encodeed_prompt_raw):
    return send_prompts(encodeed_prompt_raw, 'img2img')


def refrash_list():
    return gr.Dataframe.update(value=loadjsonfile(template_path))


def show_detail(encodeed_prompt_raw):
    pass


def add_tab():
    with gr.Blocks(analytics_enabled=False) as tab:
        with gr.Row():
            with gr.Tab(label='模版列表', elem_id="template_list_tab"):
                with gr.Row(elem_id="prompt_main"):
                    with gr.Column(variant="compact"):
                        refrash_list_btn = gr.Button(elem_id='refrash_template_list', value='刷新')
                        selected_text = gr.TextArea(elem_id='prompt_selected_text', visible=False)
                        send_to_txt2img = gr.Button(elem_id='prompt_send_to_txt2img', visible=False)
                        send_to_img2img = gr.Button(elem_id='prompt_send_to_img2img', visible=False)
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

            with gr.Tab(label='详情', elem_id="template_detail_tab"):
                with gr.Row():
                    with gr.Column(variant="compact"):
                        detail_text = gr.TextArea(elem_id='prompt_detail_text', visible=False)
                        detail_text_btn = gr.Button(elem_id='prompt_detail_text_btn', value='刷新', visible=False)
                        html_content = f"""
                        <div class="basic-grey">
                            <div id="content">
                                <h1>
                                    提示词详细信息
                                </h1>
                                <label>
                                    <span style="color: #888">没有详情数据</span>
                                </label>
                            </div>
                        </div>
                        """
                        detail_info = gr.HTML(html_content)

            detail_text_btn.click(
                fn=show_detail,
                inputs=[detail_text],
                outputs=[detail_info]
            )

            refrash_list_btn.click(
                fn=refrash_list,
                outputs=datatable
            )

            send_to_txt2img.click(
                fn=send_txt2img_prompts,
                inputs=[selected_text],
                outputs=find_txt2img_prompts(ui.txt2img_paste_fields)
            )

            send_to_img2img.click(
                fn=send_img2img_prompts,
                inputs=[selected_text],
                outputs=find_img2img_prompts(ui.img2img_paste_fields)
            )

    return [(tab, "提示词模版", "prompt_template")]


script_callbacks.on_ui_tabs(add_tab)
