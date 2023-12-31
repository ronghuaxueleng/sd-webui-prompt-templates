import base64
import hashlib
import html
import json
import os
import pathlib
import time

import gradio as gr
from PIL import UnidentifiedImageError

from jishui.db import Template
from jishui.utils import make_thumb
from jishui.translator import translator
from modules import scripts, ui, generation_parameters_copypaste, images

base_dir = scripts.basedir()
pics_dir_path = base_dir + r"/pics"
config_path = base_dir + r"/config.json"
headers = []
datatype = []
headers_with_translate = []
datatype_with_translate = []
paste_int_field_default_val_map = {}
paste_field_name_map = {}
convert_map = {}

with open(config_path, "r", encoding="utf-8-sig") as f:
    configs = json.loads(f.read())
    convert_map = configs['convert_map']
    headers = configs['tableInfo']['headers']
    datatype = configs['tableInfo']['datatype']
    paste_field_name_map = configs['paste_field_name_map']
    headers_with_translate = configs['tableInfo']['headers_with_translate']
    datatype_with_translate = configs['tableInfo']['datatype_with_translate']
    paste_int_field_default_val_map = configs['paste_int_field_default_val_map']


def load_template_list(show_translate_colum):
    try:
        templates = Template.select()
        if len(templates) > 0:
            template_values = []
            for templateObj in templates:
                try:
                    temp_list = list()
                    with open(pics_dir_path + "/" + templateObj.filename, "rb") as imgFile:
                        imagebytes = base64.b64encode(imgFile.read())
                    imagestr = imagebytes.decode('utf-8')
                    img_src = f"""data:image/jpg;base64,{imagestr}"""
                    preview_img = f"""
                        <div class="preview-img">
                            <img class="prompt_template_image_preview_tolargeImg" src="{img_src}">
                        </div>
                        """
                    temp_list.append(preview_img)
                    if show_translate_colum:
                        temp_list.append(templateObj.prompt + "\n" + translator.translate(templateObj.prompt))
                        temp_list.append(
                            templateObj.negativePrompt + "\n" + translator.translate(templateObj.negativePrompt))
                    else:
                        temp_list.append(templateObj.prompt)
                        temp_list.append(templateObj.negativePrompt)
                    raw_encode = base64.b64encode(templateObj.raw.encode("utf-8")).decode('utf-8')
                    jump_to_detail_onclick = f'''jump_to_detail("{raw_encode}", "{templateObj.filename}")'''
                    prompt_send_to_txt2img_onclick = f'''prompt_send_to_txt2img("{raw_encode}")'''
                    prompt_send_to_img2img_onclick = f'''prompt_send_to_img2img("{raw_encode}")'''
                    delete_template_onclick = f'''delete_template({templateObj.id})'''
                    buttons = f"""
                        <div style='margin-top: 3px; text-align: center;'>
                            <button style='width: 102px;' class='secondary gradio-button svelte-cmf5ev' onclick='{jump_to_detail_onclick}'>详情</button>
                        </div>
                        <div style='margin-top: 3px; text-align: center;'>
                            <button style='width: 102px;' class='secondary gradio-button svelte-cmf5ev' onclick='{prompt_send_to_txt2img_onclick}'>发送到文生图</button>
                        </div>
                        <div style='margin-top: 3px; text-align: center;'>
                            <button style='width: 102px;' class='secondary gradio-button svelte-cmf5ev' onclick='{prompt_send_to_img2img_onclick}'>发送到图生图</button>
                        </div>
                        <div style='margin-top: 3px; text-align: center;'>
                            <button style='width: 102px;' class='secondary gradio-button svelte-cmf5ev' onclick='{delete_template_onclick}'>删除</button>
                        </div>
                        """
                    temp_list.append(buttons)
                    template_values.append(temp_list)
                except Exception as e:
                    print(e)
            template_values.reverse()
            return template_values
    except Exception as e:
        print(e)


def find_prompts(fields, paste_type):
    if not paste_field_name_map.get(paste_type).get('isInit'):
        print(paste_type + ' has labels:')
        labels = []
        for field, name in fields:
            try:
                label = name if isinstance(name, str) else field.label
                labels.append(label)
                paste_field_name_map.get(paste_type).get('names').append(label)
                paste_field_name_map.get(paste_type).get('fields').append(field)
            except:
                pass
        print(labels)
        paste_field_name_map.get(paste_type).update({'isInit': True})
    return paste_field_name_map.get(paste_type).get('fields')


def find_txt2img_prompts(fields):
    return find_prompts(fields, 'txt2img')


def find_img2img_prompts(fields):
    return find_prompts(fields, 'img2img')


def send_prompts(encodeed_prompt_raw, paste_type):
    decodeed_prompt_raw = base64.b64decode(encodeed_prompt_raw).decode('utf-8')
    params = generation_parameters_copypaste.parse_generation_parameters(decodeed_prompt_raw)
    final_result = dict(paste_int_field_default_val_map)
    final_result.update(params)
    values = []
    type_map = paste_field_name_map.get(paste_type)
    names = type_map.get('names')
    fields = type_map.get('fields')
    for inx, name in enumerate(names):
        val = final_result.get(name)
        value = fields[inx].value
        if type(value) == int:
            values.append(int(val))
        elif type(value) == float:
            values.append(float(val))
        elif type(value) == bool:
            values.append(bool(val))
        elif type(value) == list:
            values.append(list(val))
        elif type(value) == str:
            values.append(str(val))
        else:
            values.append(str(val))
    return tuple(values) or gr.update()


def send_txt2img_prompts(encodeed_prompt_raw):
    return send_prompts(encodeed_prompt_raw, 'txt2img')


def send_img2img_prompts(encodeed_prompt_raw):
    return send_prompts(encodeed_prompt_raw, 'img2img')


def refrash_list(show_translate_colum):
    return gr.Dataframe.update(value=load_template_list(show_translate_colum))


def show_detail(decodeed_prompt_raw, filename):
    params = generation_parameters_copypaste.parse_generation_parameters(decodeed_prompt_raw)
    with open(pics_dir_path + "/" + filename, "rb") as f:
        imagebytes = base64.b64encode(f.read())
        imagestr = imagebytes.decode('utf-8')
    html_conent = f"""
    <div class="info-content">
        <div class="row">
            <div id="preview-content">
                <img class="prompt_template_image_preview_tolargeImg" src="data:image/jpg;base64,{imagestr}">
            </div>
            <div id="prompt-content">
                <h1>
                    提示词详细信息
                </h1>
    """
    for key, value in params.items():
        html_conent += f"""
                <label>
                    <span>{convert_map.get(key, key)}</span>
                    <span>{html.escape(str(value))}</span>
                </label>
        """
    html_conent += f"""
            </div>
        </div>
    </div>
    """
    return html_conent, gr.Button.update(visible=True), gr.Button.update(visible=True)


def get_png_info(image):
    try:
        pnginfo, items = images.read_info_from_image(image)
    except UnidentifiedImageError as e:
        pnginfo = None
    params = generation_parameters_copypaste.parse_generation_parameters(str(pnginfo))
    html_conent = f"""
    <div class="info-content">
        <div class="row">
            <div id="prompt-content">
                <h1>
                    提示词详细信息
                </h1>
    """
    for key, value in params.items():
        html_conent += f"""
                <label>
                    <span>{convert_map.get(key, key)}</span>
                    <span>{html.escape(str(value))}</span>
                </label>
        """
    html_conent += f"""
            </div>
        </div>
    </div>
    """
    return html_conent, gr.TextArea.update(value=str(pnginfo))


def saveto_template(prompt_raw, image):
    filename = hashlib.md5(prompt_raw.encode()).hexdigest() + ".jpg"
    make_thumb(image, pics_dir_path, filename)
    params = generation_parameters_copypaste.parse_generation_parameters(prompt_raw)
    Template.insert(
        prompt=params['Prompt'],
        negativePrompt=params['Negative prompt'],
        raw=prompt_raw,
        filename=filename,
        state=0,
        timestamp=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    ).execute()


def saveto_template_success(show_translate_colum_checkbox):
    return refrash_list(show_translate_colum_checkbox)


def delete_invalid_pre_image():
    try:
        templates = Template.select()
        filenames = set([template.filename for template in templates])
        for _filename in (set(os.listdir(pics_dir_path)).difference(filenames)):
            imgFile = pathlib.Path(pics_dir_path + '/' + _filename)
            if imgFile.is_file():
                try:
                    imgFile.unlink()
                except Exception as e:
                    print(e)
    except:
        pass


def delete_template_by_id(template_id, show_translate_colum_checkbox):
    templateObj = Template.get(Template.id == template_id)
    Template.delete().where(Template.id == template_id).execute()
    imgFile = pathlib.Path(pics_dir_path + '/' + templateObj.filename)
    if imgFile.is_file():
        try:
            imgFile.unlink()
        except Exception as e:
            print(e)
    return refrash_list(show_translate_colum_checkbox)


def save_all_flow_to_template():
    fields = ui.txt2img_paste_fields
    value_map = {}
    for field, name in fields:
        try:
            label = name if isinstance(name, str) else field.label
            value_map[label] = field.value
        except Exception as e:
            print(e)
    print(json.dumps(value_map))
    pass


def create_ui() -> gr.Blocks:
    template_path = pathlib.Path(base_dir + '/template.db')
    if not template_path.exists():
        from jishui.db import init_table

        init_table()
    with gr.Blocks(analytics_enabled=False) as tab:
        save_all_flow_to_template_btn = gr.Button(elem_id='save_flow_to_template_btn', visible=False)
        template_id = gr.TextArea(elem_id='template_id', visible=False)
        delete_template_by_id_btn = gr.Button(elem_id='delete_template_by_id_btn', visible=False)
        with gr.Row():
            with gr.Tab(label='模版列表', elem_id="template_list_tab"):
                with gr.Row(elem_id="prompt_main"):
                    show_translate_colum_checkbox = gr.Checkbox(label="翻译提示词", elem_id="show_translate_colum")
                    refrash_list_btn = gr.Button(elem_id='refrash_template_list', value='刷新')
                    delete_invalid_pre_image_btn = gr.Button(elem_id='delete_invalid_pre_image',
                                                             value='清除无效预览图')
                    selected_text = gr.TextArea(elem_id='prompt_selected_text', visible=False)
                    send_to_txt2img = gr.Button(elem_id='prompt_send_to_txt2img', visible=False)
                    send_to_img2img = gr.Button(elem_id='prompt_send_to_img2img', visible=False)
                with gr.Row():
                    datatable = gr.DataFrame(headers=headers,
                                             datatype=datatype,
                                             interactive=False,
                                             wrap=True,
                                             max_rows=10,
                                             show_label=True,
                                             overflow_row_behaviour="show_ends",
                                             value=load_template_list(show_translate_colum_checkbox),
                                             elem_id="prompt_template_list"
                                             )

            with gr.Tab(label='详情', elem_id="template_detail_tab"):
                with gr.Row():
                    with gr.Column(variant="compact"):
                        detail_text = gr.TextArea(elem_id='prompt_detail_text', visible=False)
                        prompt_detail_filename_text = gr.TextArea(elem_id='prompt_detail_filename_text', visible=False)
                        detail_text_btn = gr.Button(elem_id='prompt_detail_text_btn', visible=False)
                        with gr.Row(elem_id="detail_send_to_btns"):
                            send_detail_to_txt2img = gr.Button(elem_id='detail_send_to_txt2img', value='发送到文生图',
                                                               visible=False)
                            send_detail_to_img2img = gr.Button(elem_id='detail_send_to_img2img', value='发送到图生图',
                                                               visible=False)
                        html_content = f"""
                        <div class="info-content">
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

            with gr.Tab(label='添加模版', elem_id="add_template_tab"):
                with gr.Row():
                    with gr.Column(scale=4):
                        with gr.Row():
                            png_info_text = gr.TextArea(elem_id='png_info_text', visible=False)
                            img = gr.Image(type="pil", label="请上传图片", height=512)
                        with gr.Row():
                            add_template_send_to_txt2img = gr.Button(elem_id='add_template_send_to_txt2img',
                                                                     value='发送到文生图')
                            add_template_send_to_img2img = gr.Button(elem_id='add_template_send_to_img2img',
                                                                     value='发送到图生图')
                            save_to_template = gr.Button(elem_id='save_to_template', value='保存模版')
                    with gr.Column(scale=4):
                        img_info = gr.HTML()

            delete_template_by_id_btn.click(fn=delete_template_by_id,
                                            inputs=[template_id, show_translate_colum_checkbox], outputs=datatable)
            save_to_template.click(fn=saveto_template, inputs=[png_info_text, img]).success(
                fn=saveto_template_success, inputs=show_translate_colum_checkbox, outputs=datatable,
                _js="function(){alert('保存成功，请到模版列表查看');}")
            img.upload(fn=get_png_info, inputs=img, outputs=[img_info, png_info_text])
            detail_text_btn.click(fn=show_detail, inputs=[detail_text, prompt_detail_filename_text],
                                  outputs=[detail_info, send_detail_to_txt2img, send_detail_to_img2img])
            refrash_list_btn.click(fn=refrash_list, inputs=show_translate_colum_checkbox, outputs=datatable)

            show_translate_colum_checkbox.change(fn=refrash_list, inputs=show_translate_colum_checkbox,
                                                 outputs=datatable)

            delete_invalid_pre_image_btn.click(fn=delete_invalid_pre_image, _js="function(){alert('清理完毕');}")

            generation_parameters_copypaste.register_paste_params_button(generation_parameters_copypaste.ParamBinding(
                paste_button=send_to_txt2img, tabname="txt2img", source_text_component=selected_text,
            ))

            generation_parameters_copypaste.register_paste_params_button(generation_parameters_copypaste.ParamBinding(
                paste_button=send_to_img2img, tabname="img2img", source_text_component=selected_text,
            ))

            generation_parameters_copypaste.register_paste_params_button(generation_parameters_copypaste.ParamBinding(
                paste_button=send_detail_to_txt2img, tabname="txt2img", source_text_component=detail_text,
            ))

            generation_parameters_copypaste.register_paste_params_button(generation_parameters_copypaste.ParamBinding(
                paste_button=send_detail_to_img2img, tabname="img2img", source_text_component=detail_text,
            ))

            generation_parameters_copypaste.register_paste_params_button(generation_parameters_copypaste.ParamBinding(
                paste_button=add_template_send_to_txt2img, tabname="txt2img", source_text_component=png_info_text,
            ))

            generation_parameters_copypaste.register_paste_params_button(generation_parameters_copypaste.ParamBinding(
                paste_button=add_template_send_to_img2img, tabname="img2img", source_text_component=png_info_text,
            ))

        save_all_flow_to_template_btn.click(fn=save_all_flow_to_template)

    return tab
