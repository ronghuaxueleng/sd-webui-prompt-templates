from PIL import Image


def make_thumb(image, pics_dir_path, filename):
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
