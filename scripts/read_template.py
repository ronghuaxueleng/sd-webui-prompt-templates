import base64
import hashlib
import html
import json
import os
import pathlib
import time

import gradio as gr
from PIL import UnidentifiedImageError, Image

from scripts.db import Template
from modules import scripts, script_callbacks, ui, generation_parameters_copypaste, images

base_dir = scripts.basedir()
pics_dir_path = base_dir + r"/pics"
config_path = base_dir + r"/config.json"
headers = ["预览", "正向提示词", "负向提示词", "操作"]
paste_int_field_default_val_map = {}
paste_field_name_map = {}
convert_map = {}

with open(config_path, "r", encoding="utf-8-sig") as f:
    configs = json.loads(f.read())
    convert_map = configs['convert_map']
    paste_field_name_map = configs['paste_field_name_map']
    paste_int_field_default_val_map = configs['paste_int_field_default_val_map']


def make_thumb(image, filename):
    mode = image.mode
    if mode not in ('L', 'RGB'):
        if mode == 'RGBA':
            # 透明图片需要加白色底
            alpha = image.split()[3]
            bgmask = alpha.point(lambda x: 255 - x)
            image = image.convert('RGB')
            # paste(color, box, mask)
            image.paste((255, 255, 255), None, bgmask)
        else:
            image = image.convert('RGB')
    _height = 600
    width, height = image.size
    _width = int(width * _height / height)
    filename = pics_dir_path + "/" + filename
    thumb = image.resize((_width, _height), Image.BILINEAR)
    print(filename)
    thumb.save(filename, quality=100)  # 默认 JPEG 保存质量是 75, 不太清楚。可选值(0~100)


def loadjsonfile():
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
                    preview_img = f"""
                        <div class='preview-img'>
                            <img class="toEnlargeImg" src='data:image/jpg;base64,{imagestr}'>
                        </div>
                        """
                    temp_list.append(preview_img)
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
    print(paste_type + ' has labels:')
    for field, name in fields:
        try:
            print(field.label)
            paste_field_name_map.get(paste_type).get('names').append(name)
            paste_field_name_map.get(paste_type).get('fields').append(field)
        except:
            pass
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
    for name in paste_field_name_map.get(paste_type).get('names'):
        val = final_result.get(name)
        if val is None and name in paste_int_field_default_val_map.keys():
            val = paste_int_field_default_val_map.get(name)
        try:
            values.append(int(val))
        except:
            try:
                values.append(float(val))
            except:
                values.append(str(val))
    return tuple(values) or gr.update()


def send_txt2img_prompts(encodeed_prompt_raw):
    return send_prompts(encodeed_prompt_raw, 'txt2img')


def send_img2img_prompts(encodeed_prompt_raw):
    return send_prompts(encodeed_prompt_raw, 'img2img')


def refrash_list():
    return gr.Dataframe.update(value=loadjsonfile())


def show_detail(encodeed_prompt_raw, filename):
    decodeed_prompt_raw = base64.b64decode(encodeed_prompt_raw).decode('utf-8')
    params = generation_parameters_copypaste.parse_generation_parameters(decodeed_prompt_raw)
    with open(pics_dir_path + "/" + filename, "rb") as f:
        imagebytes = base64.b64encode(f.read())
        imagestr = imagebytes.decode('utf-8')
    html_conent = f"""
    <div class="info-content">
        <div class="row">
            <div id="preview-content">
                <img class="toEnlargeImg" src="data:image/jpg;base64,{imagestr}">
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
    pnginfo_encode = base64.b64encode(str(pnginfo).encode("utf-8")).decode('utf-8')
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
    return html_conent, gr.TextArea.update(value=pnginfo_encode)


def saveto_template(encodeed_prompt_raw, image):
    filename = hashlib.md5(encodeed_prompt_raw.encode()).hexdigest() + ".jpg"
    make_thumb(image, filename)
    decodeed_prompt_raw = base64.b64decode(encodeed_prompt_raw).decode('utf-8')
    params = generation_parameters_copypaste.parse_generation_parameters(decodeed_prompt_raw)
    Template.insert(
        prompt=params['Prompt'],
        negativePrompt=params['Negative prompt'],
        raw=decodeed_prompt_raw,
        filename=filename,
        state=0,
        timestamp=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    ).execute()


def saveto_template_success():
    return refrash_list()


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


def delete_template_by_id(template_id):
    templateObj = Template.get(Template.id == template_id)
    Template.delete().where(Template.id == template_id).execute()
    imgFile = pathlib.Path(pics_dir_path + '/' + templateObj.filename)
    if imgFile.is_file():
        try:
            imgFile.unlink()
        except Exception as e:
            print(e)
    return refrash_list()


def add_tab():
    with gr.Blocks(analytics_enabled=False, elem_id="prompt-templates") as tab:
        gr.HTML(f"""
            <!--黑色遮罩-->
            <div class="black_overlay" id="black_overlay"></div>
            <div class="enlargeContainer" id="enlargeContainer">
                <!-- 关闭按钮，一个叉号图片 -->
                <img src="data:image/jpeg;base64,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" class="close" id="close">
            </div>
        """, visible=False)
        template_id = gr.TextArea(elem_id='template_id', visible=False)
        delete_template_by_id_btn = gr.Button(elem_id='delete_template_by_id_btn', visible=False)
        with gr.Row():
            with gr.Tab(label='模版列表', elem_id="template_list_tab"):
                with gr.Row(elem_id="prompt_main"):
                    refrash_list_btn = gr.Button(elem_id='refrash_template_list', value='刷新')
                    delete_invalid_pre_image_btn = gr.Button(elem_id='delete_invalid_pre_image',
                                                             value='清除无效预览图')
                    selected_text = gr.TextArea(elem_id='prompt_selected_text', visible=False)
                    send_to_txt2img = gr.Button(elem_id='prompt_send_to_txt2img', visible=False)
                    send_to_img2img = gr.Button(elem_id='prompt_send_to_img2img', visible=False)
                with gr.Row():
                    datatable = gr.DataFrame(headers=headers,
                                             datatype=["html", "str", "str", "html"],
                                             interactive=False,
                                             wrap=True,
                                             max_rows=10,
                                             show_label=True,
                                             overflow_row_behaviour="show_ends",
                                             value=loadjsonfile(),
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

            delete_template_by_id_btn.click(fn=delete_template_by_id, inputs=template_id, outputs=datatable)
            save_to_template.click(fn=saveto_template, inputs=[png_info_text, img]).success(
                fn=saveto_template_success, outputs=datatable, _js="function(){alert('保存成功，请到模版列表查看');}")
            img.upload(fn=get_png_info, inputs=img, outputs=[img_info, png_info_text])
            detail_text_btn.click(fn=show_detail, inputs=[detail_text, prompt_detail_filename_text],
                                  outputs=[detail_info, send_detail_to_txt2img, send_detail_to_img2img])
            refrash_list_btn.click(fn=refrash_list, outputs=datatable)
            delete_invalid_pre_image_btn.click(fn=delete_invalid_pre_image, _js="function(){alert('清理完毕');}")
            send_to_txt2img.click(fn=send_txt2img_prompts, inputs=[selected_text],
                                  outputs=find_txt2img_prompts(ui.txt2img_paste_fields))
            send_to_img2img.click(fn=send_img2img_prompts, inputs=[selected_text],
                                  outputs=find_img2img_prompts(ui.img2img_paste_fields))
            send_detail_to_txt2img.click(fn=send_txt2img_prompts, inputs=[detail_text],
                                         outputs=find_txt2img_prompts(ui.txt2img_paste_fields), _js="switch_to_txt2img")
            send_detail_to_img2img.click(fn=send_img2img_prompts, inputs=[detail_text],
                                         outputs=find_img2img_prompts(ui.img2img_paste_fields), _js="switch_to_img2img")
            add_template_send_to_txt2img.click(fn=send_txt2img_prompts, inputs=[png_info_text],
                                               outputs=find_txt2img_prompts(ui.txt2img_paste_fields),
                                               _js="switch_to_txt2img")
            add_template_send_to_img2img.click(fn=send_img2img_prompts, inputs=[png_info_text],
                                               outputs=find_img2img_prompts(ui.img2img_paste_fields),
                                               _js="switch_to_img2img")

    return [(tab, "提示词模版", "prompt_template")]


script_callbacks.on_ui_tabs(add_tab)
