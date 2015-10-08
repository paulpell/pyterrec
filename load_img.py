import wx
#import FreeImagePy
from PIL import Image
import numpy

# given a file path, load and return a PIL Image
def load_img(path):
    try:
        return Image.open(path)
    except:
        pass

    try:
        i = wx.Image(path, wx.BITMAP_TYPE_TIF)
        size=(i.GetWidth(),i.GetHeight())
        return Image.fromstring("RGB",size,i.GetData())
    except:
        pass

    # TODO: try using FreeImagePy, crashing for now, because of libtiff

def topil(np_img):
    return Image.fromarray(numpy.uint8(np_img))



def load_swisstopo(im_name_fmt, x1, x2, y1, y2, im_width = 256, im_height = 256):
    dx, dy = x2 - x1 + 1, y2 - y1 + 1
    w, h = im_width, im_height
    img_total = Image.new('RGB', (dx * w, dy * h))

    for x in range(x1, x2 + 1):
        for y in range(y1, y2 + 1):
            name = im_name_fmt % (y, x)
            im = Image.open(name)
            img_total.paste(im, (w * (x - x1), h * (y - y1)))
    return img_total
