#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/9 14:35
# @Author  : Fred Yang
# @File    : base.py
# @Role    : 阿里云BASE

from aliyunsdkcore.client import AcsClient

class BaseALY():
    def __init__(self, data):
        self.secret_id = data.get('SecretId')
        self.secret_key = data.get('SecretKey')
        self.region = data.get('region')
        self.con()

    def con(self):
        try:
            self.conn = AcsClient(self.secret_id, self.secret_key, self.region)
        except Exception as e:
            print(
                '[Error]: 区域：{}, SecretID: {} 连接失败，请检查你的SecretID 和 SecretKey是否正确。'.format(self.region, self.secret_id))
            print(e)
            exit(-1)
