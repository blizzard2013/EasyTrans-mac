# -*- encoding: utf-8 -*-

'''
@Author  :  yiding

@Contact :  yw2686a@student.american.edu

@Time    :  May 30,2022

@Desc    :  实现翻译的爬虫功能

'''

import urllib.request
import urllib.parse
import json
import requests   # pip intasll requests
import execjs  # 安装指令：pip install PyExecJS
import random
from hashlib import md5
from time import sleep, time
import re

from account import *


class CallingCounter(object):
    def __init__ (self, func):
        self.func = func
        self.count = 0
        self.time = [0,0,0,0,0]

    def __call__ (self, *args, **kwargs):
        self.count += 1
        return self.func(*args, **kwargs)


class Py4Js():
    def __init__(self):
        self.ctx = execjs.compile(""" 
        function TL(a) { 
        var k = ""; 
        var b = 406644; 
        var b1 = 3293161072; 

        var jd = "."; 
        var $b = "+-a^+6"; 
        var Zb = "+-3^+b+-f"; 

        for (var e = [], f = 0, g = 0; g < a.length; g++) { 
            var m = a.charCodeAt(g); 
            128 > m ? e[f++] = m : (2048 > m ? e[f++] = m >> 6 | 192 : (55296 == (m & 64512) && g + 1 < a.length && 56320 == (a.charCodeAt(g + 1) & 64512) ? (m = 65536 + ((m & 1023) << 10) + (a.charCodeAt(++g) & 1023), 
            e[f++] = m >> 18 | 240, 
            e[f++] = m >> 12 & 63 | 128) : e[f++] = m >> 12 | 224, 
            e[f++] = m >> 6 & 63 | 128), 
            e[f++] = m & 63 | 128) 
        } 
        a = b; 
        for (f = 0; f < e.length; f++) a += e[f], 
        a = RL(a, $b); 
        a = RL(a, Zb); 
        a ^= b1 || 0; 
        0 > a && (a = (a & 2147483647) + 2147483648); 
        a %= 1E6; 
        return a.toString() + jd + (a ^ b) 
    }; 

    function RL(a, b) { 
        var t = "a"; 
        var Yb = "+"; 
        for (var c = 0; c < b.length - 2; c += 3) { 
            var d = b.charAt(c + 2), 
            d = d >= t ? d.charCodeAt(0) - 87 : Number(d), 
            d = b.charAt(c + 1) == Yb ? a >>> d: a << d; 
            a = b.charAt(c) == Yb ? a + d & 4294967295 : a ^ d 
        } 
        return a 
    } 
    """)
    def getTk(self, text):
        return self.ctx.call("TL", text)

# 有道翻译方法，不支持一次翻译一大段文字
def youdao_translate(content):
    print(content)
    '''实现有道翻译的接口'''
    url = 'http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule&sessionFrom=https://www.baidu.com/link'
    data = {
        'from':'AUTO',
        'to':'AUTO',
        'smartresult':'dict',
        'client':'fanyideskweb',
        'salt':'1500092479607',
        'sign':'d9f9a3aa0a7b34241b3fe30505e5d436',
        'doctype':'json',
        'version':'2.1',
        'keyfrom':'fanyi.web',
        'action':'FY_BY_CL1CKBUTTON',
        'typoResult':'true'}
    data['i'] = content.replace('\n','')
    data = urllib.parse.urlencode(data).encode('utf-8')
    wy = urllib.request.urlopen(url,data)
    html = wy.read().decode('utf-8')
    ta = json.loads(html)
    res = ta['translateResult'][0][0]['tgt']
    return res

# 谷歌翻译方法
def google_translate(content):
    '''实现谷歌的翻译'''

    content = content.replace('\n','')
    print(content)
    js = Py4Js()
    tk = js.getTk(content)
    if len(content) > 4891:
        return '输入请不要超过4891个字符！'
    param = {'tk': tk, 'q': content}
    result = requests.get("""http://translate.google.cn/translate_a/single?client=t&sl=en 
        &tl=zh-CN&hl=zh-CN&dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=ss 
        &dt=t&ie=UTF-8&oe=UTF-8&clearbtn=1&otf=1&pc=1&srcrom=0&ssel=0&tsel=0&kc=2""", params=param)
    #返回的结果为Json，解析为一个嵌套列表  
    trans = result.json()[0]
    res = ''
    for i in range(len(trans)):
        line = trans[i][0]
        if line != None:
            res += trans[i][0]

    return res


# 百度翻译方法
@CallingCounter
def baidu_translate(content,boundary=0):
    if content.isspace():
        baidu_translate.count -= 1
        return ' '

    if boundary > 10:
        # print('Stop trying')
        return f"**** Translate {content} ERROR ****"

    if len(content) > 4891:
        half = content.find('.',4000)
        baidu_translate.count -= 1
        return baidu_translate(content[:half+1]) + baidu_translate(content[half+1:])

    content = re.sub(r'- ', '',content)

    salt = str(random.randint(32768, 65536))

    i = baidu_translate.count % len(appid)
    sign = appid[i] + content + salt + secretKey[i]
    sign = md5(sign.encode(encoding='UTF-8')).hexdigest()
    head = {'q': content,
            'from': 'en',
            'to': 'zh',
            'appid': appid[i],
            'salt': salt,
            'sign': sign}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    # Contral QPS (使用高级账号请注释下面4行代码)
    # time_interval = time() - baidu_translate.time[i]
    # if time_interval < 1.0:
    #     sleep(1.0 - time_interval)
    # baidu_translate.time[i] = time()   

    # Post
    j = requests.post('http://api.fanyi.baidu.com/api/trans/vip/translate', params=head, headers=headers)

    try:
        res = j.json()['trans_result'][0]['dst']
        print(' ')
        print(content)
        print(res)
    except:
        if boundary>9:
            print('\n********** ERROR **********')
            print(f"content: {content}")
            print(f"error_code: {j.json()['error_code']}")
            print(f"error_msg: {j.json()['error_msg']}")
            print(f'******** Try Again({boundary}) ********\n')
        baidu_translate.count -= 1
        baidu_translate.time[i] = 0
        res = baidu_translate(content,boundary+1)
    return str(res)
