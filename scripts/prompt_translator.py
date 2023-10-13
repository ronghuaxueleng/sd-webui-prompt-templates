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
from scripts.services import GoogleTranslationService
import scripts.lang_code as lang_code
from transformers import MarianMTModel, MarianTokenizer

# Translation Service Providers
trans_providers = {
    "deepl": {
        "url": "https://api-free.deepl.com/v2/translate",
        "has_id": False
    },
    "baidu": {
        "url": "https://fanyi-api.baidu.com/api/trans/vip/translate",
        "has_id": True
    },
    "tencent": {
        "url": "https://tmt.tencentcloudapi.com/?",
        "has_id": True
    },
    "google": {
        "url": "https://translation.googleapis.com",
        "has_id": False
    },
    "yandex": {
        "url": "https://translate.api.cloud.yandex.net/translate/v2/translate",
        "has_id": True
    },
    "MarianMT": {
        "url": "",
        "has_id": False
    }
}

# user's translation service setting
trans_setting = {
    "deepl": {
        "is_default": False,
        "app_id": "",
        "app_key": ""
    },
    "baidu": {
        "is_default": False,
        "app_id": "",
        "app_key": ""
    },
    "tencent": {
        "is_default": True,
        "app_id": "",
        "app_key": ""
    },
    "google": {
        "is_default": False,
        "app_id": "",
        "app_key": ""
    },
    "yandex": {
        "is_default": False,
        "app_id": "",
        "app_key": ""
    },
    "MarianMT": {
        "is_default": False,
        "app_id": "",
        "app_key": ""
    }
}

# user config file
# use scripts.basedir() to get current extension's folder
config_file_name = os.path.join(scripts.basedir(), "prompt_translator.cfg")

# scan MarianMT Model
MarianMT_model_folder = os.path.join(scripts.basedir(), "MarianMT")
MarianMT_model_prefix = "opus-mt-"
MarianMT_model_lang_pairs = []


# init setting
# load translation serivce setting
def load_trans_setting():
    # load data into globel trans_setting
    global trans_setting

    if not os.path.isfile(config_file_name):
        print("no config file: " + config_file_name)
        return

    data = None
    with open(config_file_name, 'r') as f:
        data = json.load(f)

    # check error
    if not data:
        print("load config file failed")
        return

    for key in trans_setting.keys():
        if key not in data.keys():
            data[key] = trans_setting[key]
            print("can not find " + key + " section in config file, use default")

    # set value
    trans_setting = data
    return


load_trans_setting()

# get provider
providers = list(trans_providers.keys())
provider_name = "deepl"
for key in trans_setting.keys():
    if trans_setting[key]["is_default"]:
        provider_name = key
        break

# target languages
tar_langs = [""]
def_tar_lang = ""
if provider_name != "MarianMT":
    if provider_name in lang_code.lang_code_dict.keys():
        tar_langs = list(lang_code.lang_code_dict[provider_name].keys())
        def_tar_lang = str(tar_langs[0])


# MarianMT_model
def scan_MarianMT_model():
    print("Scan MarianMT model")
    global MarianMT_model_lang_pairs

    if not os.path.isdir(MarianMT_model_folder):
        print("No MarianMT folder, no need scan")
        return

    for name in os.listdir(MarianMT_model_folder):
        item_path = os.path.join(MarianMT_model_folder, name)
        if os.path.isdir(item_path):
            # check name
            if name.startswith(MarianMT_model_prefix):
                # find model
                # get language pair
                lang_pair = name[len(MarianMT_model_prefix):]
                if lang_pair:
                    MarianMT_model_lang_pairs.append(lang_pair)

    print(f"find MarianMT_model language pair: {MarianMT_model_lang_pairs}")


# Scan local translation models
scan_MarianMT_model()


def load_MarianMT_model(lang_pair):
    global active_MarianMT_model
    global active_MarianMT_tokenizer

    model_name = MarianMT_model_prefix + lang_pair
    model_path = os.path.join(MarianMT_model_folder, model_name)
    print("MarianMT model_path: " + model_path)

    if not os.path.isdir(model_path):
        print("model_path is not a dir: " + model_path)
        return

    print("Get tokenizer")
    active_MarianMT_tokenizer = MarianTokenizer.from_pretrained(model_path)
    print("Load Model")
    active_MarianMT_model = MarianMTModel.from_pretrained(model_path)


# pre-load MarianMT Model
active_MarianMT_model = None
active_MarianMT_tokenizer = None
if provider_name == "MarianMT":
    # reset 
    tar_langs = [""]
    def_tar_lang = ""
    # use language pair as tar_lang list
    tar_langs = MarianMT_model_lang_pairs
    # get default value
    if len(MarianMT_model_lang_pairs):
        # use "-en" model as default value
        for lang_pair in MarianMT_model_lang_pairs:
            if lang_pair.endswith("-en"):
                def_tar_lang = lang_pair
                break

        # if there is no "-en" model, use first one
        if not def_tar_lang:
            def_tar_lang = MarianMT_model_lang_pairs[0]

    if def_tar_lang:
        load_MarianMT_model(def_tar_lang)


# deepl translator
# refer: https://www.deepl.com/docs-api/translate-text/
# parameter: app_key, text, target_language
# return: translated_text
def deepl_trans(app_key, text, tar_lang):
    print("Getting data for deepl")
    # check error
    if not app_key:
        print("app_key can not be empty")
        return ""

    if not text:
        print("text can not be empty")
        return ""

    if not tar_lang:
        tar_lang = "EN"

    # set http request
    headers = {"Authorization": "DeepL-Auth-Key " + app_key}
    data = {
        "text": text,
        "target_lang": tar_lang
    }

    print("Sending request")
    r = None
    try:
        r = requests.post(trans_providers["deepl"]["url"], data=data, headers=headers, timeout=10)
    except Exception as e:
        print("request get error, check your network")
        print(str(e))
        return ""

    print("checking response")
    # check error
    # refer: https://www.deepl.com/docs-api/api-access/general-information/
    if r.status_code >= 300 or r.status_code < 200:
        print("Get Error code from DeepL: " + str(r.status_code))
        if r.status_code == 429:
            print("too many requests")
        elif r.status_code == 456:
            print("quota exceeded")
        elif r.status_code >= 500:
            print("temporary errors in the DeepL service")

        print("check for more info: https://www.deepl.com/docs-api/api-access/general-information/")
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

    # try to get text from content
    translated_text = ""
    if content:
        if "translations" in content.keys():
            if len(["translations"]):
                if "text" in content["translations"][0].keys():
                    translated_text = content["translations"][0]["text"]

    if not translated_text:
        print("can not read tralstated text from response:")
        print(r.text)
        return ""

    return translated_text


# new srvice
# yandex translator
# refer: https://translate.api.cloud.yandex.net/translate/v2/translate
# parameter: app_id, app_key, text, tar_lang
# return: translated_text
def yandex_trans(app_id, app_key, text, tar_lang):
    target_language = 'en'
    if tar_lang:
        target_language = tar_lang

    folder_id = app_id
    texts = [text]
    body = {
        "targetLanguageCode": target_language,
        "texts": texts,
        "folderId": folder_id,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {0}".format(app_key)
    }
    response = requests.post('https://translate.api.cloud.yandex.net/translate/v2/translate',
                             json=body,
                             headers=headers
                             )
    translated_text = ""
    translated_text = response.text
    try:
        content = response.json()

    except Exception as e:
        print("Parse response json failed")
        print(str(e))
        print("response:")
        print(response.text)
        return ""

    # try to get text from content
    translated_text = ""
    if content:
        if "translations" in content.keys():
            if len(["translations"]):
                if "text" in content["translations"][0].keys():
                    translated_text = content["translations"][0]["text"]
    return translated_text


# baidu translator
# refer: https://fanyi-api.baidu.com/doc/21
# parameter: app_id, app_key, text, tar_lang
# return: translated_text
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

    request_link = trans_providers["baidu"][
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

    url_with_args = 'https://tmt.tencentcloudapi.com/?' + tencent_get_url_encoded_params(secret_id, secret_key, text,tar_lang)
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


# deepl translator
# refer: https://huggingface.co/docs/transformers/model_doc/marian
# parameter: app_key, text, language_pair(like zh-en)
# return: translated_text
def MarianMT_trans(text, lang_pair):
    print("Getting data for MarianMT")
    # check error
    if not text:
        print("text can not be empty")
        return ""

    if not lang_pair:
        print("language pair can not be empty")
        return ""

    if lang_pair not in MarianMT_model_lang_pairs:
        print(f"unknow language pair: {lang_pair}")
        return ""

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


# do translation
# parameter: provider, app_id, app_key, text
# return: translated_text
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
    if provider in lang_code.lang_code_dict.keys():
        if tar_lang in lang_code.lang_code_dict[provider].keys():
            tar_lang_code = lang_code.lang_code_dict[provider][tar_lang]

    # translating
    translated_text = ""
    if provider == "deepl":
        translated_text = deepl_trans(app_key, text, tar_lang_code)
    elif provider == "baidu":
        translated_text = baidu_trans(app_id, app_key, text, tar_lang_code)
    elif provider == "tencent":
        translated_text = tencent_trans(app_id, app_key, text, tar_lang_code)
    elif provider == "google":
        service = GoogleTranslationService(app_key)
        translated_text = service.translate(text=text, target=tar_lang_code)
    elif provider == "yandex":
        translated_text = yandex_trans(app_id, app_key, text, tar_lang_code)
    elif provider == "MarianMT":
        translated_text = MarianMT_trans(text, tar_lang)
    else:
        print("unsupported provider: ")
        print(provider)

    print("Translated result:")
    print(translated_text)

    return translated_text


# this is used when translating request is sending by js, not by a user's clicking
# in this case, we need a return like below:
# return: translated_text, translated_text, translated_text
# return it 3 times to send result to 3 different textbox.
# This is a hacking way to let txt2img and img2img get the translated result
def do_trans_js(provider, app_id, app_key, text, tar_lang):
    print("Translating requested by js:")

    translated_text = do_trans(provider, app_id, app_key, text, tar_lang)

    print("return to both extension tab and txt2img+img2img tab")
    return [translated_text, translated_text, translated_text]


# send translated prompt to txt2img and img2img
def do_send_prompt(translated_text):
    return [translated_text, translated_text]


# save translation service setting
# parameter: provider, app_id, app_key
# return:
# trans_setting: a parsed json object as python dict with same structure as globel trans_setting object
def save_trans_setting(provider, app_id, app_key):
    print("Saving tranlation service setting...")
    # write data into globel trans_setting
    global trans_setting

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
    # get prompt textarea
    # UI structure
    # check modules/ui.py, search for txt2img_paste_fields
    # Negative prompt is the second element
    txt2img_prompt = modules.ui.txt2img_paste_fields[0][0]
    txt2img_neg_prompt = modules.ui.txt2img_paste_fields[1][0]
    img2img_prompt = modules.ui.img2img_paste_fields[0][0]
    img2img_neg_prompt = modules.ui.img2img_paste_fields[1][0]

    # ====Event's function====
    def set_provider(provider):
        app_id_visible = trans_providers[provider]['has_id']
        # set target language list
        tar_langs = [""]
        def_tar_lang = ""
        # local translation model
        if provider == "MarianMT":
            # use language pair as tar_lang list
            tar_langs = MarianMT_model_lang_pairs
            # get default value
            if len(MarianMT_model_lang_pairs):
                # use "-en" model as default value
                for lang_pair in MarianMT_model_lang_pairs:
                    if lang_pair.endswith("-en"):
                        def_tar_lang = lang_pair
                        break

                # if there is no "-en" model, use first one
                if not def_tar_lang:
                    def_tar_lang = MarianMT_model_lang_pairs[0]

            # load model
            if def_tar_lang:
                load_MarianMT_model(def_tar_lang)

        # cloud translation service
        elif provider in lang_code.lang_code_dict.keys():
            tar_langs = list(lang_code.lang_code_dict[provider].keys())
            def_tar_lang = tar_langs[0]

        return [app_id.update(visible=app_id_visible, value=trans_setting[provider]["app_id"]),
                app_key.update(value=trans_setting[provider]["app_key"]),
                tar_lang_drop.update(choices=tar_langs, value=def_tar_lang)]

    def tar_lang_changed(provider, tar_lang):
        if provider == "MarianMT":
            # need to pre-load model
            if tar_lang:
                load_MarianMT_model(tar_lang)

    with gr.Blocks(analytics_enabled=False) as prompt_translator:
        # ====ui====        
        # Prompt Area
        with gr.Row():
            tar_lang_drop = gr.Dropdown(label="目标语言", choices=tar_langs, value=def_tar_lang,
                                        elem_id="pt_tar_lang")
        with gr.Row():
            prompt = gr.Textbox(label="正向提示词", lines=3, value="", elem_id="pt_prompt")
            translated_prompt = gr.Textbox(label="结果", lines=3, value="", elem_id="pt_translated_prompt")

        with gr.Row():
            trans_prompt_btn = gr.Button(value="翻译", elem_id="pt_trans_prompt_btn")
            # add a hidden button, used by fake click with javascript. To simulate msg between server and client side.
            # this is the only way.
            trans_prompt_js_btn = gr.Button(value="Trans Js", visible=False, elem_id="pt_trans_prompt_js_btn")
            send_prompt_btn = gr.Button(value="发送到txt2img和img2img", elem_id="pt_send_prompt_btn")

        with gr.Row():
            neg_prompt = gr.Textbox(label="负向提示词", lines=2, value="", elem_id="pt_neg_prompt")
            translated_neg_prompt = gr.Textbox(label="结果", lines=2, value=json.dumps(tar_langs),
                                               elem_id="pt_translated_neg_prompt")

        with gr.Row():
            trans_neg_prompt_btn = gr.Button(value="翻译", elem_id="pt_trans_neg_prompt_btn")
            # add a hidden button, used by fake click with javascript. To simulate msg between server and client side.
            # this is the only way.
            trans_neg_prompt_js_btn = gr.Button(value="Trans Js", visible=False, elem_id="pt_trans_neg_prompt_js_btn")
            send_neg_prompt_btn = gr.Button(value="发送到txt2img和img2img", elem_id="pt_send_neg_prompt_btn")

        gr.HTML("<hr />")

        # Translation Service Setting

        gr.Markdown("翻译服务设置")
        provider = gr.Dropdown(choices=providers, value=provider_name, label="服务", elem_id="pt_provider")
        app_id = gr.Textbox(label="APP ID", lines=1, value=trans_setting[provider_name]["app_id"], elem_id="pt_app_id")
        app_key = gr.Textbox(label="APP KEY", lines=1, value=trans_setting[provider_name]["app_key"],
                             elem_id="pt_app_key")
        save_trans_setting_btn = gr.Button(value="保存设置")

        # deepl do not need appid
        app_id.visible = trans_providers[provider_name]['has_id']

        # ====events====
        # Target languages
        tar_lang_drop.change(fn=tar_lang_changed, inputs=[provider, tar_lang_drop])
        # Prompt
        trans_prompt_btn.click(do_trans, inputs=[provider, app_id, app_key, prompt, tar_lang_drop],
                               outputs=translated_prompt)
        trans_neg_prompt_btn.click(do_trans, inputs=[provider, app_id, app_key, neg_prompt, tar_lang_drop],
                                   outputs=translated_neg_prompt)

        # Click by js
        trans_prompt_js_btn.click(do_trans_js, inputs=[provider, app_id, app_key, prompt, translated_neg_prompt],
                                  outputs=[translated_prompt, txt2img_prompt, img2img_prompt])
        trans_neg_prompt_js_btn.click(do_trans_js,
                                      inputs=[provider, app_id, app_key, neg_prompt, translated_neg_prompt],
                                      outputs=[translated_neg_prompt, txt2img_neg_prompt, img2img_neg_prompt])

        send_prompt_btn.click(do_send_prompt, inputs=translated_prompt, outputs=[txt2img_prompt, img2img_prompt])
        send_neg_prompt_btn.click(do_send_prompt, inputs=translated_neg_prompt,
                                  outputs=[txt2img_neg_prompt, img2img_neg_prompt])

        # Translation Service Setting
        provider.change(fn=set_provider, inputs=provider, outputs=[app_id, app_key, tar_lang_drop])
        save_trans_setting_btn.click(save_trans_setting, inputs=[provider, app_id, app_key])

    # the third parameter is the element id on html, with a "tab_" as prefix
    return (prompt_translator, "提示词翻译", "prompt_translator"),


script_callbacks.on_ui_tabs(on_ui_tabs)
