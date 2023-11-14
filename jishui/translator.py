import os
import transformers

from modules import scripts

base_dir = scripts.basedir()
models_dir = os.path.join(base_dir, "models")


# 英文->中文的翻译模型
class EnZhTranslator:
    def __init__(self, cache_dir=models_dir, model_name="Helsinki-NLP/opus-mt-en-zh"):
        self.model_name = model_name
        # 加载模型和tokenizer
        path = os.path.join(cache_dir, model_name)
        if os.path.exists(path):
            self.model = transformers.MarianMTModel.from_pretrained(path)
            self.tokenizer = transformers.MarianTokenizer.from_pretrained(path)
        else:
            self.model = transformers.MarianMTModel.from_pretrained(model_name, cache_dir=cache_dir)
            self.tokenizer = transformers.MarianTokenizer.from_pretrained(model_name, cache_dir=cache_dir)

    def translate(self, en_str: str) -> str:
        # 对句子进行分词
        input_ids = self.tokenizer.encode(en_str, return_tensors="pt", padding=True)

        # 进行翻译
        output_ids = self.model.generate(input_ids)

        # 将翻译结果转换为字符串格式
        return self.tokenizer.decode(output_ids[0], skip_special_tokens=True)


translator = EnZhTranslator()
