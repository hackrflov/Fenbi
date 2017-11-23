#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    File Name: fetch.py
    Date: 11/22/2017
    Author: hackrflov
    Email: hackrflov@gmail.com
    Python Version: 2.7
"""

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
        docs = [doc for doc in db.question.aggregate([ { '$sample': { 'size' : 20 }}])]
        merger = PdfFileMerger()
        for doc in docs:
            self.encode(doc)
            status = self.write(doc)
            if status == False:
                continue
            filename = self.root + '{}.pdf'.format(doc['id'])
            merger.append(PdfFileReader(file(filename, 'rb')))
        path = self.root + 'sample.pdf'
        merger.write(path)

    def write(self, question):
        del question['_id']
        qid = question['id']
        #params = urllib.urlencode(question, doseq=True)
        params = 'json={}'.format(json.dumps(question))
        path = self.root + '{}.pdf'.format(qid)
        url = 'http://localhost/fenbi/index.php?' + params
        print len(url)
        if len(url) >= 6000:
            return False
        else:
            pdfkit.from_url(url, path)
            return True

    def encode(self, doc):
        print doc.keys()
        l = [doc['solution'], doc['content']]
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
                    base = 'http://fb.fbstatic.cn/api/xingce/accessories/formulas?latex={}'
                    url = base.format(re.search('(?<=\]).*?(?=\[)', tex).group())
                    block = '<img src="{}" width="{}" height="{}">'.format(url, float(width)*20, float(height)*20)
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
                    base = 'http://fb.fbstatic.cn/api/xingce/images/{}'
                    url = base.format(re.search('(?<=\]).*?(?=\[)', img).group())
                    block = '<img src="{}" width="{}" height="{}">'.format(url, float(width)/2, float(height)/2)
                    l[i] = part.replace(img, block)
            except Exception as e:
                pass

        doc['solution'], doc['content'] = l[0], l[1]
        if doc.get('material'):
            doc['material']['content'] = l[2]
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


