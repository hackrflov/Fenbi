#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    File Name: fetch.py
    Date: 11/22/2017
    Author: hackrflov
    Email: hackrflov@gmail.com
    Python Version: 2.7
"""

import os
import re
import pdb
import time
import json
from PyPDF2 import PdfFileMerger, PdfFileReader
import pdfkit
import urllib

from pymongo import MongoClient, UpdateOne, UpdateMany
client = MongoClient('mongodb://fenbi:fenbi123@localhost:27017/')
db = client.fenbi

class Util():

    def __init__(self):
        self.root = '/var/www/html/fenbi/'

    def start(self):
        docs = db.question.aggregate([
            { '$group': { '_id': '$path' } }
        ])
        paths = [doc['_id'] for doc in docs if doc['_id']]
        for path in paths:
            print path
            path = path.encode('utf-8')
            # test
            url = re.sub(' > ', '%20%3E%20', path)
            print 'Now outputing {}.pdf'.format(url)
            docs = [doc for doc in db.question.find({'path': path }).sort('correctRatio') ]
            merger = PdfFileMerger()
            for i, doc in enumerate(docs):
                print 'No.{} / {}'.format(i+1, len(docs))
                doc['content'] = '[p]{}. '.format(i+1) + doc['content'][3:]
                self.encode(doc)
                self.write(doc)
                filename = self.root + '{}.pdf'.format(doc['id'])
                merger.append(PdfFileReader(file(filename, 'rb')))
            # 集合同一类别
            combo_f = self.root + '{}.pdf'.format(path)
            merger.write(combo_f)
            # 及时删除过渡文件
            for doc in docs:
                filename = self.root + '{}.pdf'.format(doc['id'])
                os.remove(filename)

    def write(self, question):
        del question['_id']
        qid = question['id']
        #params = 'json={}'.format(json.dumps(question))
        f = open(self.root + 'tmp.txt', 'w')
        f.write(json.dumps(question))
        f.truncate()
        f.close()
        path = self.root + '{}.pdf'.format(qid)
        #url = 'http://localhost/fenbi/index.php?' + params
        url = 'http://localhost/fenbi/index.php'
        options = { 'quiet': '' }
        pdfkit.from_url(url, path, options=options)

    def encode(self, doc):
        l = [doc['solution'], doc['content']]
        for option in doc['accessories'][0]['options']:
            l.append(option)
        if doc.get('material'):
            l.append(doc['material']['content'])
        # 公式
        for i, part in enumerate(l):
            try:
                while True:
                    part = l[i]
                    pattern = '\[tex.*?\].*?tex\]'
                    tex = re.search(pattern, part).group()
                    size = re.search('(?<=tex\=).*?(?=\])', tex).group()
                    width, height = size.split('x')
                    width = float(width)
                    height = float(height)
                    ratio = width / height
                    h = min(max(20, height * 15), 30)
                    w = ratio * h
                    base = 'http://fb.fbstatic.cn/api/xingce/accessories/formulas?latex={}&fontSize=48'
                    url = base.format(re.search('(?<=\]).*?(?=\[)', tex).group())
                    block = '<img src="{}" width="{}" height="{}">'.format(url, w, h)
                    l[i] = part.replace(tex, block)
            except Exception as e:
                pass

        # 图片
        for i, part in enumerate(l):
            try:
                while True:
                    part = l[i]
                    pattern = '\[img.*?\].*?img\]'
                    img = re.search(pattern, part).group()
                    size = re.search('(?<=img\=).*?(?=\])', img).group()
                    width, height = size.split('x')
                    width = float(width) / 2
                    height = float(height) / 2
                    ratio = height / width
                    w = min(width, 600)
                    h = ratio * w
                    base = 'http://fb.fbstatic.cn/api/xingce/images/{}'
                    url = base.format(re.search('(?<=\]).*?(?=\[)', img).group())
                    block = '<img class="top-img" src="{}" width="{}" height="{}" style:"vertical-align:top">'.format(url, w, h)
                    l[i] = part.replace(img, block)
            except Exception as e:
                pass

        # 横线 & 空行 & 颜色 & 段落
        for i, part in enumerate(l):
            try:
                l[i] = re.sub('\[u.*?\].*?u\]', '__________', l[i])
                l[i] = re.sub('\[br.*?\].*?\]', '<br />', l[i])
                l[i] = re.sub('\[color.*?\]', '', l[i])
                if i >= 2:
                    if (not doc.get('material')) or i != len(l) - 1:
                        l[i] = re.sub('\[p\]', '', l[i])
                        l[i] = re.sub('\[/p\]', '', l[i])
                l[i] = re.sub('\[p=align:center\]', '<p align="center">', l[i])
                l[i] = re.sub('\[p.*?\]', '<p>', l[i])
                l[i] = re.sub('\[/p\]', '</p>', l[i])
                l[i] = re.sub('\[b.*?\]', '<strong>', l[i])
                l[i] = re.sub('\[/b\]', '</strong>', l[i])
                # 其他都删掉
                l[i] = re.sub('\[[a-z]+=.*?\]', '', l[i])
                l[i] = re.sub('\[/.*?\]', '', l[i])
            except Exception as e:
                pass

        doc['solution'], doc['content'] = l[0], l[1]
        if doc.get('material'):
            doc['accessories'][0]['options'] = l[2:-1]
            doc['material']['content'] = l[-1]
        else:
            doc['accessories'][0]['options'] = l[2:]
        '''
        if type(doc) == dict:
            for k, v in doc.items():
                if type(v) == dict:
                    self.encode(v)
                elif type(v) == list:
                    for i in v:
                        self.encode(i)
                elif type(v) == unicode:
                    doc[k] = v.encode('utf-8')
        '''

if __name__ == '__main__':
    util = Util()
    util.start()


