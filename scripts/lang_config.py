# -*- coding: UTF-8 -*-
# always put en to the first
lang_code_dict = {
    # refer: http://api.fanyi.baidu.com/doc/21
    "baidu": {
        "英语": "en",
        "中文": "zh"
    },
    "tencent": {
        "英语": "en",
        "中文": "zh"
    },
    "MarianMT": {
        "中文": "en-zh",
        "英语": "zh-en"
    }
}

# Translation Service Providers
trans_providers = {
    "baidu": {
        "url": "https://fanyi-api.baidu.com/api/trans/vip/translate",
        "has_id": True
    },
    "tencent": {
        "url": "https://tmt.tencentcloudapi.com/?",
        "has_id": True
    },
    "MarianMT": {
        "url": "",
        "has_id": False
    }
}

# user's translation service setting
trans_setting = {
    "baidu": {
        "is_default": False,
        "app_id": "",
        "app_key": ""
    },
    "tencent": {
        "is_default": False,
        "app_id": "",
        "app_key": ""
    },
    "MarianMT": {
        "is_default": True,
        "app_id": "",
        "app_key": ""
    }
}

