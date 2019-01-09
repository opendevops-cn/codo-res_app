#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 8/8/2018 4:00 PM
# @Author  : Fred Yang
# @File    : cvm.py
# @Role    : 开通腾讯云CVM机器（按需购买）

import os
import sys

Base_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(Base_DIR)

# print(Base_DIR)

from qcloud.qcloud_api import ApiOper
import time
import random
import requests
import json
from public import GenPassword, data_save
import fire


class CVM_API():
    def __init__(self, data):
        self.region = data.get('region')
        self.id = data.get('SecretId')
        self.key = data.get('SecretKey')
        self.vpc = data.get('vpc_id')
        self.subnet = data.get('subnet_id')
        self.ami = data.get('ami_id')
        self.instance_type = data.get('instance_type')

    # def check_instance_name(self,instance_name):
    #     '''检测hostname是否符合规范'''
    #     hostname = instance_name.split('-')
    #     if len(hostname) < 4:
    #         print('instance_name does not meet specifications，Use OPS-SH_TX-01-test01')
    #         exit(300)
    #     else:
    #         print('InstanceName:{}'.format(instance_name))

    def get_instances(self, instance_name):
        # 检测用户创建的instance_name是否存在，存在则退出
        api_url = 'cvm.tencentcloudapi.com/?'
        keydict = {
            # 公共参数部分
            'Timestamp': str(int(time.time())),
            'Nonce': str(int(random.random() * 1000)),
            'Region': self.region,
            'SecretId': self.id,
            'Version': '2017-03-12',
            # 'SignatureMethod': SignatureMethod,
            # 接口参数部分
            'Action': 'DescribeInstances',
            'Limit': '100',  # 默认为：20

        }

        try:
            result_url = ApiOper.run(keydict, api_url, self.key)
            response = requests.get(result_url)
            if response.status_code == 200:
                data = json.loads(response.text)
                ret = data['Response']['InstanceSet']
                if ret:
                    for i in ret:
                        if instance_name in i.get('InstanceName'):
                            print('[INFO]：Instance：{} 已经存在'.format(instance_name))
                            exit(-100)
                            return i.get('InstanceName')
                        # exit(304) #存在就退出
            return None

        except Exception as e:
            print('[INFO]: 你的Region：{}，SecretId：{}'.format(self.region, self.id))
            print('[Error]: 请检查填写信息是否正确，确保ID和Key有云服务器的权限，错误信息：{}'.format(e))
            exit(-1)

    def create_cvm(self, params):

        api_url = 'cvm.tencentcloudapi.com/?'
        try:
            result_url = ApiOper.run(params, api_url, self.key)
            # print(result_url)
            response = requests.get(result_url)
            if response.status_code == 200:
                data = json.loads(response.text)
                print(data)
                return data
        except Exception as e:
            print(e)
            print('[ERROR]：create_cvm instance falied.')
            exit(-2)

    def get_cvm_info(self, instance_id):
        '''获取机器信息'''
        api_url = 'cvm.tencentcloudapi.com/?'
        keydict = {
            # 公共参数部分
            'Timestamp': str(int(time.time())),
            'Nonce': str(int(random.random() * 1000)),
            'Region': self.region,
            'SecretId': self.id,
            'Version': '2017-03-12',
            # 'SignatureMethod': SignatureMethod,
            # 接口参数部分
            'Action': 'DescribeInstances',
            'Limit': '30',  # 默认为：20
            'InstanceIds.0': instance_id

        }
        result_url = ApiOper.run(keydict, api_url, self.key)
        response = requests.get(result_url)
        if response.status_code == 200:
            data = json.loads(response.text)
            ret = data['Response']['InstanceSet']
            return ret


def main(instance_name, instance_type, disk_size, project_id=None, securit_group_id=None):
    """
    购买腾讯云机器，默认按小时收费
    :param instance_name: 主机名，多个用逗号隔开
    :param instance_type: 实例类型，如：S3.SMALL1
    :param disk_size: 磁盘大小
    :param project_id: 项目ID，腾讯云有项目概念，你希望把机器开在哪个项目里面，不输则默认项目
    :param securit_group_id: 安全组ID，不输则默认安全组
    :return:
    成功返回实例ID
    {'Response': {'InstanceIdSet': ['ins-qg3235sb'], 'RequestId': 'bb2af389-5186-463b-a41b-3bb91d457dd4'}}
    """
    # 这里数据是从前端传过来的，现在前端还没有完善，暂时假数据
    data = {
        'SecretId': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        'SecretKey': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        'region': 'ap-shanghai',
        'vpc_id': 'vpc-iikzqifi',
        'subnet_id': 'subnet-ll604xp9',
        'ami_id': 'img-oikl1tzv',
        'zone_name': 'ap-shanghai-3'
    }

    for instance in instance_name.split(','):
        print('Instance: {}'.format(instance))
        obj = CVM_API(data)
        # 查询HOSTNAME实例是否存在
        obj.get_instances(instance)
        password = GenPassword(16)  # 随机密码

        data_info = {}
        # 购买机器并返回信息
        params = {
            # 公共参数部分
            'Timestamp': str(int(time.time())),
            'Nonce': str(int(random.random() * 1000)),
            'Region': data.get('region'),
            'SecretId': data.get('SecretId'),
            'Version': '2017-03-12',
            # 'SignatureMethod': SignatureMethod,
            # 接口参数部分
            'Action': 'RunInstances',
            'Placement.Zone': data.get('zone_name'),
            # 'Placement.ProjectId': str(project_id),
            'VirtualPrivateCloud.VpcId': data.get('vpc_id'),
            'VirtualPrivateCloud.SubnetId': data.get('subnet_id'),
            # 'SecurityGroupIds.0': securit_group_id,
            'InstanceChargeType': 'POSTPAID_BY_HOUR',
            'ImageId': data.get('ami_id'),
            'InstanceType': instance_type,
            'SystemDisk.DiskType': 'CLOUD_SSD',
            'SystemDisk.DiskSize': str(disk_size),
            'InternetAccessible.InternetChargeType': 'TRAFFIC_POSTPAID_BY_HOUR',
            'InternetAccessible.InternetMaxBandwidthOut': '100',
            'InternetAccessible.PublicIpAssigned': 'TRUE',
            'InstanceName': instance_name,
            'LoginSettings.Password': password,
            'EnhancedService.SecurityService.Enabled': 'TRUE',
            'EnhancedService.MonitorService.Enabled': 'TRUE',
            'InstanceCount': '1',
        }

        # 判断用户是否给了项目ID，没给机器开通在默认项目
        if project_id != None:
            params['Placement.ProjectId'] = str(project_id)
        # 判断用户是否给了安全组ID，没给机器开通在默认安全组
        if securit_group_id != None:
            params['SecurityGroupIds.0'] = str(securit_group_id)

        # 购买机器
        shop = obj.create_cvm(params)
        try:
            data1 = shop['Response']['InstanceIdSet']
            instance_id = data1[0]
            time.sleep(60)
            ret = obj.get_cvm_info(instance_id)[0]
            public_ip = ret.get('PublicIpAddresses')
            host = ret.get('InstanceName')
            data_info[host] = {
                'hostname': host,
                'public_ip': public_ip[0],
                'username': 'root',
                'password': password
            }
            data_save(data_info)
        except Exception as e:
            print('[Error]: 购买失败，信息：{}, {}'.format(e, shop))
            exit(-3)


if __name__ == '__main__':
    fire.Fire(main)

"""
Usage:       cvm.py INSTANCE_NAME INSTANCE_TYPE DISK_SIZE [PROJECT_ID] [SECURIT_GROUP_ID]
             cvm.py --instance-name INSTANCE_NAME --instance-type INSTANCE_TYPE --disk-size DISK_SIZE [--project-id PROJECT_ID] [--securit-group-id SECURIT_GROUP_ID]

示例：
开通机器在默认项目，关联默认安全组
python3 cvm.py --instance-name='yanghongfeitest' --instance-type='S3.SMALL1' --disk-size=50
开通机器在指定项目，关联指定安全组
python3 cvm.py --instance-name='yanghongfeitest02' --instance-type='S3.SMALL1' --disk-size=50 --project-id=1120490 --securit-group-id=sg-l6raxqpu
"""
