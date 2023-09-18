import json
import base64

import gradio as gr

from modules import scripts, script_callbacks, ui, generation_parameters_copypaste

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
            raw_encode = base64.b64encode(template_dict['raw'].encode("utf-8"))
            onclick = 'prompt_send_to_txt2img("' + raw_encode.decode('utf-8') + '")'
            buttons = ("<div style='margin-top: 3px; text-align: center;'>"
                       "<button style='width: 102px;' class='secondary gradio-button svelte-cmf5ev'>详情</button>"
                       "</div>"
                       "<div style='margin-top: 3px; text-align: center;'>"
                       "<button style='width: 102px;' class='secondary gradio-button svelte-cmf5ev' onclick='" + onclick + "'>to txt2mig</button>"
                                                                                                                           "</div>")
            temp_list.append(buttons)
            template_values.append(temp_list)
        return template_values


def find_prompts(fields):
    field_prompt = [x for x in fields if x[1] == "Prompt"][0]
    field_negative_prompt = [x for x in fields if x[1] == "Negative prompt"][0]
    return [field_prompt[0], field_negative_prompt[0]]


def send_prompts(encodeed_prompt_raw):
    decodeed_prompt_raw = base64.b64decode(encodeed_prompt_raw).decode('utf-8')
    params = generation_parameters_copypaste.parse_generation_parameters(decodeed_prompt_raw)
    negative_prompt = params.get("Negative prompt", "")
    return params.get("Prompt", ""), negative_prompt or gr.update()


def refrash_list():
    return gr.Dataframe.update(value=loadjsonfile(template_path))


def add_tab():
    with gr.Blocks(analytics_enabled=False) as tab:
        with gr.Row():
            with gr.Tab('模版列表'):
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

            refrash_list_btn.click(
                fn=refrash_list,
                outputs=datatable
            )

            send_to_txt2img.click(
                fn=send_prompts,
                inputs=[selected_text],
                outputs=find_prompts(ui.txt2img_paste_fields)
            )

            send_to_img2img.click(
                fn=send_prompts,
                inputs=[selected_text],
                outputs=find_prompts(ui.img2img_paste_fields)
            )

    return [(tab, "提示词模版", "prompt_template")]


script_callbacks.on_ui_tabs(add_tab)
