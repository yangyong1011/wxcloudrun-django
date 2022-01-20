from datetime import datetime
import json
import logging
from socket import fromshare

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from wxcloudrun.models import Counters

from PIL import Image, ImageDraw
from django import forms

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()
    
logger = logging.getLogger('log')

WIDTH_1IN = 295
HEIGHT_1IN = 413

WIDTH_2IN = 413
HEIGHT_2IN = 626

WIDTH_5IN = 1500
HEIGHT_5IN = 1050

# 非全景6寸照片
WIDTH_6IN = 1950
HEIGHT_6IN = 1300

class PhotoLayout(object):

    def open(self, filename):
        self.im = Image.open(filename)
        print('open', self.im.size)
        self.__set_1_in()
        self.__set_2_in()

    def __cut(self, h, w):
        _height = self.im.height
        _width = self.im.width
        rate = _height / _width
        if rate < (h / w):
            _w = int(_height / (h / w))
            x1 = int((_width - _w) / 2)
            x2 = _width - int((_width - _w) / 2)
            print((x1, 0, x2, _height))
            return self.im.crop((x1, 0, x2, _height))
        else:
            _h = int((h / w) * _width)
            y1 = int((_height - _h) / 2)
            y2 = _height - int((_height - _h) / 2)
            print((0, y1, _width, y2))
            return self.im.crop((0, y1, _width, y2))
        
    def __set_1_in(self):
        self.im_1in = self.__cut(HEIGHT_1IN, WIDTH_1IN).resize((WIDTH_1IN, HEIGHT_1IN))
        print(self.im_1in.size, self.im_1in.height/self.im_1in.width, HEIGHT_1IN/WIDTH_1IN)

    def __set_2_in(self):
        self.im_2in = self.__cut(HEIGHT_2IN, WIDTH_2IN).resize((WIDTH_2IN, HEIGHT_2IN))
        print(self.im_2in.size, self.im_2in.height/self.im_2in.width, HEIGHT_2IN/WIDTH_2IN)

    def layout_photo_6_1(self):
        """
        在6寸照片上排版2寸照片
        :param photo: 待处理照片1寸
        :return: 处理后的照片
        """
        bk = Image.new("RGB", [HEIGHT_6IN,WIDTH_6IN], (255,255,255)) # 竖版排版
        # 创建画笔
        draw = ImageDraw.Draw(bk)
        draw.line([(0,WIDTH_6IN*0.25),(WIDTH_6IN,WIDTH_6IN*0.25)],fill=128) # 横线
        draw.line([(0,WIDTH_6IN*0.5),(WIDTH_6IN,WIDTH_6IN*0.5)],fill=128) # 横线
        draw.line([(0,WIDTH_6IN*0.75),(WIDTH_6IN,WIDTH_6IN*0.75)],fill=128) # 横线
        draw.line([(HEIGHT_6IN*0.25,0),(HEIGHT_6IN*0.25,WIDTH_6IN)],fill=128) # 竖线
        draw.line([(HEIGHT_6IN*0.5,0),(HEIGHT_6IN*0.5,WIDTH_6IN)],fill=128) # 竖线
        draw.line([(HEIGHT_6IN*0.75,0),(HEIGHT_6IN*0.75,WIDTH_6IN)],fill=128) # 竖线
        focus_point = [0.125 * HEIGHT_6IN, 0.125 * WIDTH_6IN]
        start_point = [focus_point[0] - 0.5 * WIDTH_1IN, focus_point[1] - 0.5 * HEIGHT_1IN]
        #print(focus_point,start_point)
        for i in range(0,4):
            for k in range(0,4):
                bk.paste(self.im_1in, (int(start_point[0] + (k * HEIGHT_6IN / 4)), int(start_point[1] + i * 0.25 * WIDTH_6IN )))
        return bk

from django.http import HttpResponseRedirect

def handle_uploaded_file(f):
    with open('some/file/name.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def upload_file(request):
    if request.method == 'POST':
        myfile = request.FILES
        logger.info('==>DEBUG: POST : {}'.format(request.FILES))
        image = request.FILES.get('image', None)
        if image:
            with open(r'wxcloudrun/static/photo.jpg', 'wb+') as d:
                for chunk in image.chunks():
                    d.write(chunk)
            pl = PhotoLayout()
            pl.open(r'wxcloudrun/static/photo.jpg')
            pl.layout_photo_6_1().save(r'wxcloudrun/static/photo_6_1.jpg')
            return render(request, 'photo.html', {'image':True})
    return render(request, 'photo.html')


def index(request, _):
    """
    获取主页

     `` request `` 请求对象
    """
    if request.method == 'POST' or request.method == 'post':
        logger.info('POST : {}'.format(request.data))
        myfile = request.FILES
        with open('test11.jpg', 'wb+') as d:
            #d.write(myfile)
            pass
    return render(request, 'index.html')


def counter(request, _):
    """
    获取当前计数

     `` request `` 请求对象
    """

    rsp = JsonResponse({'code': 0, 'errorMsg': ''}, json_dumps_params={'ensure_ascii': False})
    if request.method == 'GET' or request.method == 'get':
        rsp = get_count()
    elif request.method == 'POST' or request.method == 'post':
        logger.info('POST : {}'.format(request.FILES))
        myfile = request.FILES
        with open('test.jpg', 'wb+') as d:
            for chunk in myfile.chunk():
                d.write(chunk)
            d.close()
        rsp = update_count(request)
    else:
        rsp = JsonResponse({'code': -1, 'errorMsg': '请求方式错误'},
                            json_dumps_params={'ensure_ascii': False})
    logger.info('response result: {}'.format(rsp.content.decode('utf-8')))
    return rsp


def get_count():
    """
    获取当前计数
    """

    try:
        data = Counters.objects.get(id=1)
    except Counters.DoesNotExist:
        return JsonResponse({'code': 0, 'data': 0},
                    json_dumps_params={'ensure_ascii': False})
    return JsonResponse({'code': 0, 'data': data.count},
                        json_dumps_params={'ensure_ascii': False})


def update_count(request):
    """
    更新计数，自增或者清零

    `` request `` 请求对象
    """

    logger.info('update_count req: {}'.format(request.body))

    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    if 'action' not in body:
        return JsonResponse({'code': -1, 'errorMsg': '缺少action参数'},
                            json_dumps_params={'ensure_ascii': False})

    if body['action'] == 'inc':
        try:
            data = Counters.objects.get(id=1)
        except Counters.DoesNotExist:
            data = Counters()
        data.id = 1
        data.count += 1
        #data.createdAt = datetime.datetime
        data.save()
        return JsonResponse({'code': 0, "data": data.count},
                    json_dumps_params={'ensure_ascii': False})
    elif body['action'] == 'clear':
        try:
            data = Counters.objects.get(id=1)
            data.delete()
        except Counters.DoesNotExist:
            logger.info('record not exist')
        return JsonResponse({'code': 0, 'data': 0},
                    json_dumps_params={'ensure_ascii': False})
    else:
        return JsonResponse({'code': -1, 'errorMsg': 'action参数错误'},
                    json_dumps_params={'ensure_ascii': False})
