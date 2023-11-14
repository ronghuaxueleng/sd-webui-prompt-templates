# -*- coding: UTF-8 -*-
import base64
import hmac
import time
from urllib.parse import quote

import modules.scripts as scripts
import gradio as gr
import os
import requests
import random
import hashlib
import json
import modules
from modules import script_callbacks
import lang_config as lang_config
from transformers import MarianMTModel, MarianTokenizer

trans_setting = {}

config_file_name = os.path.join(scripts.basedir(), "prompt_translator.cfg")

MarianMT_model_folder = os.path.join(scripts.basedir(), "models")
MarianMT_model_prefix = "Helsinki-NLP/opus-mt-"
active_MarianMT_model_dict = {}
active_MarianMT_tokenizer_dict = {}


def load_trans_setting():
    if not os.path.isfile(config_file_name):
        print("没有发现配置文件: " + config_file_name)
        return lang_config.trans_setting

    with open(config_file_name, 'r') as f:
        trans_setting = json.load(f)

    # check error
    if not trans_setting:
        print("加载配置文件失败")
        return

    for key in lang_config.trans_setting.keys():
        if key not in trans_setting.keys():
            trans_setting[key] = lang_config.trans_setting[key]
            print("无效的配置【 " + key + "】，使用默认配置")
    return trans_setting


trans_setting = load_trans_setting()

providers = list(lang_config.trans_providers.keys())
provider_name = "MarianMT"
for key in trans_setting.keys():
    if trans_setting[key]["is_default"]:
        provider_name = key
        break

# 目标语言
tar_langs = [""]
def_tar_lang = ""
if provider_name in lang_config.lang_code_dict.keys():
    tar_langs = list(lang_config.lang_code_dict[provider_name].keys())
    def_tar_lang = str(tar_langs[0])


def load_MarianMT_model(lang_pair):
    active_MarianMT_model = active_MarianMT_model_dict.get(lang_pair)
    active_MarianMT_tokenizer = active_MarianMT_tokenizer_dict.get(lang_pair)
    if not active_MarianMT_tokenizer and not active_MarianMT_model:
        model_name = MarianMT_model_prefix + lang_pair
        model_path = os.path.join(MarianMT_model_folder, model_name)
        print("MarianMT model_path: " + model_path)

        if not os.path.exists(model_path):
            print("Get tokenizer")
            active_MarianMT_tokenizer_dict[lang_pair] = MarianTokenizer.from_pretrained(model_name,
                                                                                        cache_dir=MarianMT_model_folder)
            print("Load Model")
            active_MarianMT_model_dict[lang_pair] = MarianMTModel.from_pretrained(model_name,
                                                                                  cache_dir=MarianMT_model_folder)
        else:
            print("Get tokenizer")
            active_MarianMT_tokenizer_dict[lang_pair] = MarianTokenizer.from_pretrained(model_path)
            print("Load Model")
            active_MarianMT_model_dict[lang_pair] = MarianMTModel.from_pretrained(model_path)


if provider_name == "MarianMT":
    tar_lang = lang_config.lang_code_dict[provider_name][def_tar_lang]
    load_MarianMT_model(tar_lang)


def baidu_trans(app_id, app_key, text, tar_lang):
    print("Getting data for baidu")
    # check error
    if not app_id:
        print("app_id can not be empty")
        return ""

    if not app_key:
        print("app_key can not be empty")
        return ""

    if not text:
        print("text can not be empty")
        return ""

    if not tar_lang:
        tar_lang = 'en'

    # set http request
    salt = str(random.randint(10000, 10000000))
    sign_str = app_id + text + salt + app_key
    sign_md5 = hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    request_link = lang_config.trans_providers["baidu"][
                       "url"] + "?q=" + text + "&from=auto&to=" + tar_lang + "&appid=" + app_id + "&salt=" + salt + "&sign=" + sign_md5

    print("Sending request")
    r = None
    try:
        r = requests.get(request_link)
    except Exception as e:
        print("request get error, check your network")
        print(str(e))
        return ""

    # try to get content
    content = None
    try:
        content = r.json()
    except Exception as e:
        print("Parse response json failed")
        print(str(e))
        print("response:")
        print(r.text)
        return ""

    # check content error
    if not content:
        print("response content is empty")
        return ""

    if "error_code" in content.keys():
        print("return error for baidu:")
        print(content["error_code"])
        if "error_msg" in content.keys():
            print(content["error_msg"])
        print("response:")
        print(r.text)

        return ""

    # try to get text from content
    translated_text = ""
    if "trans_result" in content.keys():
        if len(content["trans_result"]):
            if "dst" in content["trans_result"][0].keys():
                translated_text = content["trans_result"][0]["dst"]

    if not translated_text:
        print("can not read translated text from response:")
        print(r.text)
        return ""

    return translated_text


def tencent_get_url_encoded_params(secret_id, secret_key, text, tar_lang):
    action = 'TextTranslate'
    region = 'ap-guangzhou'
    timestamp = int(time.time())
    nonce = random.randint(1, 1e6)
    version = '2018-03-21'
    lang_from = 'auto'
    lang_to = tar_lang

    params_dict = {
        # 公共参数
        'Action': action,
        'Region': region,
        'Timestamp': timestamp,
        'Nonce': nonce,
        'SecretId': secret_id,
        'Version': version,
        # 接口参数
        'ProjectId': 0,
        'Source': lang_from,
        'Target': lang_to,
        'SourceText': text
    }
    # 对参数排序，并拼接请求字符串
    params_str = ''
    for key in sorted(params_dict.keys()):
        pair = '='.join([key, str(params_dict[key])])
        params_str += pair + '&'
    params_str = params_str[:-1]
    # 拼接签名原文字符串
    signature_raw = 'GETtmt.tencentcloudapi.com/?' + params_str
    # 生成签名串，并进行url编码
    hmac_code = hmac.new(bytes(secret_key, 'utf8'), signature_raw.encode('utf8'), hashlib.sha1).digest()
    sign = quote(base64.b64encode(hmac_code))
    # 添加签名请求参数
    params_dict['Signature'] = sign
    # 将 dict 转换为 list 并拼接为字符串
    temp_list = []
    for k, v in params_dict.items():
        temp_list.append(str(k) + '=' + str(v))
    params_data = '&'.join(temp_list)
    return params_data


def tencent_trans(secret_id, secret_key, text, tar_lang):
    print("Getting data for tencent")
    # check error
    if not secret_id:
        print("secret_id can not be empty")
        return ""

    if not secret_key:
        print("secret_key can not be empty")
        return ""

    if not text:
        print("text can not be empty")
        return ""

    if not tar_lang:
        tar_lang = 'en'

    url_with_args = 'https://tmt.tencentcloudapi.com/?' + tencent_get_url_encoded_params(secret_id, secret_key, text,
                                                                                         tar_lang)
    try:
        res = requests.get(url_with_args, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
        })
        json_res = json.loads(res.text)
        trans_text = json_res['Response']['TargetText']
        return trans_text
    except Exception as e:
        print("request get error, check your network")
        print(str(e))
        return ""


def MarianMT_trans(text, lang_pair):
    print("Getting data for MarianMT")
    # check error
    if not text:
        print("text can not be empty")
        return ""

    if not lang_pair:
        print("language pair can not be empty")
        return ""

    active_MarianMT_model = active_MarianMT_model_dict.get(lang_pair)
    active_MarianMT_tokenizer = active_MarianMT_tokenizer_dict.get(lang_pair)

    # load model
    if not active_MarianMT_model or not active_MarianMT_tokenizer:
        load_MarianMT_model(lang_pair)

    # get model path
    print("Translating")
    translated = active_MarianMT_model.generate(**active_MarianMT_tokenizer(text, return_tensors="pt", padding=True))
    tgt_text = [active_MarianMT_tokenizer.decode(t, skip_special_tokens=True) for t in translated]

    translated_text = ""
    if len(tgt_text) == 1:
        translated_text = tgt_text[0]
    elif len(tgt_text) > 1:
        for txt in tgt_text:
            translated_text += txt + ", "
    else:
        print("trasnlated tgt_text is empty")
        print(tgt_text)

    return translated_text


def do_trans(provider, app_id, app_key, text, tar_lang):
    print("====Translation start====")
    print("Use Serivce: " + provider)
    print("Source Prompt:")
    print(text)

    if provider not in trans_setting.keys():
        print("can not find provider in trans_setting: ")
        print(provider)
        return ""

    # get target language code
    tar_lang_code = ""
    if provider in lang_config.lang_code_dict.keys():
        if tar_lang in lang_config.lang_code_dict[provider].keys():
            tar_lang_code = lang_config.lang_code_dict[provider][tar_lang]

    # translating
    translated_text = ""
    if provider == "baidu":
        translated_text = baidu_trans(app_id, app_key, text, tar_lang_code)
    elif provider == "tencent":
        translated_text = tencent_trans(app_id, app_key, text, tar_lang_code)
    elif provider == "MarianMT":
        translated_text = MarianMT_trans(text, tar_lang_code)
    else:
        print("unsupported provider: ")
        print(provider)

    print("Translated result:")
    print(translated_text)

    return translated_text


def do_trans_js(provider, app_id, app_key, text, tar_lang):
    print("Translating requested by js:")

    translated_text = do_trans(provider, app_id, app_key, text, tar_lang)

    print("return to both extension tab and txt2img+img2img tab")
    return [translated_text, translated_text, translated_text]


# send translated prompt to txt2img and img2img
def do_send_prompt(translated_text):
    return [translated_text, translated_text]


def save_trans_setting(provider, app_id, app_key):
    print("Saving tranlation service setting...")

    # check error
    if not provider:
        print("Translation provider can not be none")
        return

    if provider not in trans_setting.keys():
        print("Translation provider is not in the list.")
        print("Your provider: " + provider)
        return

    # set value    
    trans_setting[provider]["app_id"] = app_id
    trans_setting[provider]["app_key"] = app_key

    # set default
    trans_setting[provider]["is_default"] = True
    for prov in trans_setting.keys():
        if prov != provider:
            trans_setting[prov]["is_default"] = False

    # to json
    json_data = json.dumps(trans_setting)

    # write to file
    try:
        with open(config_file_name, 'w') as f:
            f.write(json_data)
    except Exception as e:
        print("write file error:")
        print(str(e))

    print("config saved to: " + config_file_name)


def on_ui_tabs():
    txt2img_prompt = modules.ui.txt2img_paste_fields[0][0]
    txt2img_neg_prompt = modules.ui.txt2img_paste_fields[1][0]
    img2img_prompt = modules.ui.img2img_paste_fields[0][0]
    img2img_neg_prompt = modules.ui.img2img_paste_fields[1][0]

    def set_provider(provider):
        app_id_visible = lang_config.trans_providers[provider]['has_id']
        tar_langs = [""]
        def_tar_lang = ""
        if provider in lang_config.lang_code_dict.keys():
            tar_langs = list(lang_config.lang_code_dict[provider].keys())
            def_tar_lang = tar_langs[0]

        return [app_id.update(visible=app_id_visible, value=trans_setting[provider]["app_id"]),
                app_key.update(value=trans_setting[provider]["app_key"]),
                tar_lang_drop.update(choices=tar_langs, value=def_tar_lang)]

    def tar_lang_changed(provider, tar_lang):
        if provider == "MarianMT":
            if tar_lang:
                load_MarianMT_model(lang_config.lang_code_dict[provider][tar_lang])

    with gr.Blocks(analytics_enabled=False) as prompt_translator:
        with gr.Row():
            tar_lang_drop = gr.Dropdown(label="目标语言", choices=tar_langs, value=def_tar_lang,
                                        elem_id="pt_tar_lang")
        with gr.Row():
            prompt = gr.Textbox(label="正向提示词", lines=3, value="", elem_id="pt_prompt")
            translated_prompt = gr.Textbox(label="结果", lines=3, value="", elem_id="pt_translated_prompt")

        with gr.Row():
            trans_prompt_btn = gr.Button(value="翻译", elem_id="pt_trans_prompt_btn")
            trans_prompt_js_btn = gr.Button(value="Trans Js", visible=False, elem_id="pt_trans_prompt_js_btn")
            send_prompt_btn = gr.Button(value="发送到txt2img和img2img", elem_id="pt_send_prompt_btn")

        with gr.Row():
            neg_prompt = gr.Textbox(label="负向提示词", lines=2, value="", elem_id="pt_neg_prompt")
            translated_neg_prompt = gr.Textbox(label="结果", lines=2, value=json.dumps(tar_langs),
                                               elem_id="pt_translated_neg_prompt")

        with gr.Row():
            trans_neg_prompt_btn = gr.Button(value="翻译", elem_id="pt_trans_neg_prompt_btn")
            trans_neg_prompt_js_btn = gr.Button(value="Trans Js", visible=False, elem_id="pt_trans_neg_prompt_js_btn")
            send_neg_prompt_btn = gr.Button(value="发送到txt2img和img2img", elem_id="pt_send_neg_prompt_btn")

        gr.HTML("<hr />")

        gr.Markdown("翻译服务设置")
        provider = gr.Dropdown(choices=providers, value=provider_name, label="服务", elem_id="pt_provider")
        app_id = gr.Textbox(label="APP ID", lines=1, value=trans_setting[provider_name]["app_id"], elem_id="pt_app_id")
        app_key = gr.Textbox(label="APP KEY", lines=1, value=trans_setting[provider_name]["app_key"],
                             elem_id="pt_app_key")
        save_trans_setting_btn = gr.Button(value="保存设置")

        app_id.visible = lang_config.trans_providers[provider_name]['has_id']

        tar_lang_drop.change(fn=tar_lang_changed, inputs=[provider, tar_lang_drop])
        trans_prompt_btn.click(do_trans, inputs=[provider, app_id, app_key, prompt, tar_lang_drop],
                               outputs=translated_prompt)
        trans_neg_prompt_btn.click(do_trans, inputs=[provider, app_id, app_key, neg_prompt, tar_lang_drop],
                                   outputs=translated_neg_prompt)

        trans_prompt_js_btn.click(do_trans_js, inputs=[provider, app_id, app_key, prompt, translated_neg_prompt],
                                  outputs=[translated_prompt, txt2img_prompt, img2img_prompt])
        trans_neg_prompt_js_btn.click(do_trans_js,
                                      inputs=[provider, app_id, app_key, neg_prompt, translated_neg_prompt],
                                      outputs=[translated_neg_prompt, txt2img_neg_prompt, img2img_neg_prompt])

        send_prompt_btn.click(do_send_prompt, inputs=translated_prompt, outputs=[txt2img_prompt, img2img_prompt])
        send_neg_prompt_btn.click(do_send_prompt, inputs=translated_neg_prompt,
                                  outputs=[txt2img_neg_prompt, img2img_neg_prompt])

        provider.change(fn=set_provider, inputs=provider, outputs=[app_id, app_key, tar_lang_drop])
        save_trans_setting_btn.click(save_trans_setting, inputs=[provider, app_id, app_key])

    return (prompt_translator, "提示词翻译", "prompt_translator"),


script_callbacks.on_ui_tabs(on_ui_tabs)
