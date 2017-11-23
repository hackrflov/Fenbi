#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    File Name: crawl.py
    Date: 11/21/2017
    Author: hackrflov
    Email: hackrflov@gmail.com
    Python Version: 2.7
"""

import pdb

import sys
import json
import time
import random
import requests
import pandas as pd
import numpy as np

from pymongo import MongoClient, UpdateOne, UpdateMany
client = MongoClient('mongodb://fenbi:fenbi123@localhost:27017/')
db = client.fenbi

import logging
logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger('fenbi')

class Fenbi():

    def __init__(self):
        self.cookies = {
            'sess': 'LqrKSMkyhKheWEeASUk3c7YKolUHHjapCa+Vj05RrFmDKHjsQtxjcjovhAKf2+wrKs901PFUf79pmpyDQm3/LhpGgTiPiElYCgJevL002sc=',
            'persistent': 'mBVQfLUzcIJbHeZ0rtlq7spUsQjxquftn5Rq6j2b+pieB9+TVMQK/i7sOexRmuEHy2K8EFy2f6MVIjoC0Zg64Q==',
            'userid': '51422034',
            'sid': '-4628916699835880651'
        }
        self.headers = {
            'User-Agent': 'fenbi-android'
        }
        self.reqs = []
        self.count = 0
        self.REQ_LIMIT = 100

        self.cmap = {}  # 类别对应关系
        self.fetch_category()
        self.category_map()

    def fetch_category(self):
        log.info('Start fetching category...')
        url = 'http://fenbi.com/android/xingce/categories'
        r = requests.get(url, headers=self.headers, cookies=self.cookies)
        data = json.loads(r.text)
        clist = data
        for cate in clist:
            db.category.update_one({'id': cate['id']}, { '$set': cate }, upsert=True)
        time.sleep(1)

    def category_map(self):
        docs = db.category.find()
        self.freq = {}
        for first in docs:
            name1 = first['name']
            for second in first['children']:
                name2 = second['name']
                # 分类，如果有children，则为三级目录，否则只有两级(综合分析)
                if second['children']:
                    for third in second['children']:
                        name3 = third['name']
                        path = '{} > {} > {}'.format(name1.encode('utf-8'), name2.encode('utf8'), name3.encode('utf-8'))
                        self.cmap[path] = {'level': 3, 'cate2': name2, 'cate1': name1, 'id': third['id'], 'count': third['count'],
                                'id2': second['id'], 'id1': first['id'], 'cate3': name3}
                        count = db.question.find({'path': path}).count()
                        print 'Category {} should have {} questions, now get {}'.format(path, third['count'], count)
                        if name3 in self.freq:
                            self.freq[name3] += 1
                        else:
                            self.freq[name3] = 1
                else:
                    path = '{} > {}'.format(name2.encode('utf8'), name3.encode('utf-8'))
                    self.cmap[path] = {'level': 2, 'cate1': name1, 'cate2': name2, 'id2': second['id'], 'id': second['id'], 'id1': first['id'], 'count': second['count']}
                    count = db.question.find({'path': path}).count()
                    print 'Category {} should have {} questions, now get {}'.format(path, second['count'], count)

    def fill_list(self):
        self.fetch_list(is_fill=True)

    def fetch_list(self, is_fill=False):
        url = 'http://fenbi.com/android/xingce/exercises'
        size = len(self.cmap.keys())
        kp_count = 0
        # 按照cmap进行搜索
        for path, kp_v in self.cmap.items():
            kp_name = path.split(' > ')[-1].decode('utf-8')
            level = kp_v['level']
            kp_id = kp_v['id']
            kp_total = kp_v['count']
            if kp_total == 0:
                continue
            kp_count += 1
            last_record = -1  # 记录上一次总数
            repeat_count = 0  # 总数连续未增长次数
            # 循环直到该考点结束
            while True:
                # 检查该考点是否全部录入
                p_key = 'cate2' if level == 3 else 'cate1'
                p_value = kp_v['cate2'] if level == 3 else kp_v['cate1']
                exist_list = [doc for doc in db.question.find({ 'path' : path })]
                # 检查是否进度完成
                progress = db.progress.find_one({'path': path})
                if progress and progress.get('finished') == True:
                    break
                exist_qlist = [doc['id'] for doc in exist_list]
                kp_num = len(exist_list)

                # 判断是否本轮是否有变化
                if kp_num == last_record:
                    repeat_count += 1
                else:
                    repeat_count = 0
                    last_record = kp_num
                # 如果未增长次数超过上限，则视为已解决
                repeat_limit = 30 if is_fill else 1
                if kp_num >= kp_total - 1 or repeat_count == repeat_limit:
                    log.info('Category {} is finished'.format(path))
                    if is_fill:
                        db.progress.update_one({'path': path }, { '$set' : {'path': path, 'finished': True } }, upsert=True)
                    break

                log.info('Start fetching category: {}, {}/{}, total: {}, having: {}'.format(path, kp_count, size, kp_total, kp_num))
                params = { 'keypointId': kp_id, 'type': 3, 'limit': 100 }
                r = requests.post(url, params=params, headers=self.headers, cookies=self.cookies)
                data = json.loads(r.text)
                tmp_qlist = data['sheet']['questionIds']
                qlist = [qt for qt in tmp_qlist if qt not in exist_qlist]  # 去掉已经存在的项

                # 存入mongo
                for q in qlist:
                    op = UpdateOne({'id': q}, { '$set': { 'id' : q } }, upsert=True)
                    self.add_req(op, write=False)
                self.write()

                # 录入详细数据
                cates = { 'cate1' : kp_v['cate1'], 'path' : path }
                if level == 3:
                    cates['cate3'] = kp_name
                    cates['cate2'] = kp_v['cate2']
                else:
                    cates['cate3'] = None
                    cates['cate2'] = kp_name
                self.fetch_detail(qlist, cates)
                time.sleep(2)

    def fetch_detail(self, qlist, cates):
        if not qlist:
            pass
            '''
            # check every document
            bulk_size = 100
            key_fields = [ 'cate1', 'cate2', 'cate3', 'content', 'solution', 'correctRatio']
            filt = [{ k : { '$exists' : False } } for k in key_fields]
            docs = db.question.find({ '$or': filt }, limit=bulk_size)
            qlist = [str(doc['id']) for doc in docs]
            '''
        else:
            qlist = [str(qid) for qid in qlist]

        params = { 'ids' : ','.join(qlist) }
        log.info('Now fetching {}'.format(qlist))
        #--- Content ---#
        url = 'http://fenbi.com/android/xingce/questions'
        r = requests.get(url, params=params, headers=self.headers, cookies=self.cookies)
        c_data = json.loads(r.text)
        time.sleep(0.5)
        #--- Solution ---#
        url = 'http://fenbi.com/android/xingce/pure/solutions'
        r = requests.get(url, params=params, headers=self.headers, cookies=self.cookies)
        s_data = json.loads(r.text)
        time.sleep(0.5)
        #--- Meta ---#
        url = 'http://fenbi.com/android/xingce/question/meta'
        r = requests.get(url, params=params, headers=self.headers, cookies=self.cookies)
        m_data = json.loads(r.text)
        time.sleep(0.5)
        #--- Keypoint ---#
        url = 'http://fenbi.com/android/xingce/solution/keypoints'
        r = requests.get(url, params=params, headers=self.headers, cookies=self.cookies)
        k_data = json.loads(r.text)
        # 存入mongo
        for i, q in enumerate(c_data):
            qid = q['id']
            q.update(s_data[i])
            q.update(m_data[i])
            q.update({'keypoint': k_data[i]})
            # 检查类目是否不符
            q_cates = [doc['name'] for doc in k_data[i]]
            kp_name = cates['path'].split(' > ')[-1].decode('utf-8')
            if kp_name == u'综合分析':
                q_cates.append(u'综合材料')
            if kp_name not in q_cates:  # 如果考点没有对上，则不录入
                continue
            else:
                q.update(cates)
                op = UpdateOne({'id': qid}, { '$set': q })
                self.add_req(op, write=False)
        self.write()  # 保证写入
        time.sleep(0.5)

    def add_req(self, operation, write=True):
        self.reqs.append(operation)
        self.count += 1
        if self.count >= self.REQ_LIMIT and write == True:
            self.write()

    def write(self):
        reqs = self.reqs
        self.count = 0
        self.reqs = []
        if reqs:
            db.question.bulk_write(reqs)
            count = db.question.count()
            log.info('Writed into MongoDB, having {} questions'.format(count))

    def clear_db(self):
        # 清除重复项
        docs = db.question.aggregate([
            { '$group' : { '_id' : '$id',
                           'count' : { '$sum' : 1 } } },
        ])
        clear_list = [doc['_id'] for doc in docs if doc['count'] > 1]
        for qid in clear_list:
            filt = { 'id' : qid }
            db.question.delete_many(filt)
            db.question.update_one(filt, { '$set' : filt }, upsert=True)
        docs = db.question.aggregate([
            { '$group' : { '_id' : '$id',
                           'count' : { '$sum' : 1 } } },
        ])
        clear_list = [doc['_id'] for doc in docs if doc['count'] > 1]

        # 特殊: 清除三级类目一样的
        """
        for k, v in self.freq.items():
            if v >= 2:
                db.question.delete_many({'cate3': k})
        """

    def modify_db(self):
        for path, kp_v in self.cmap.items():
            if kp_v['level'] == 3:
                old = '{}-{}-{}'.format(kp_v['cate1'].encode('utf-8'), kp_v['cate2'].encode('utf8'), kp_v['cate3'].encode('utf-8'))
                db.question.update_many({'path': old}, { '$set': { 'path' : path } })
            else:
                old = '{}-{}'.format(kp_v['cate1'].encode('utf8'), kp_v['cate2'].encode('utf-8'))
                db.question.update_many({'path': old}, { '$set': { 'path' : path } })

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        fenbi = Fenbi()
        job_name = 'fenbi.' + sys.argv[1] + '()'
        log.info('Now running {}'.format(job_name))
        eval(job_name)
    else:
        fenbi = Fenbi()
        fenbi.fetch_detail()

