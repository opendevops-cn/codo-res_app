#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 7/24/2018 10:29 AM
# @Author  : Fred Yang
# @File    : aliyun_sync_cmdb.py
# @Role    : 获取Aliyun资产信息推送到CMDB

import os
import sys

Base_DIR = os.path.dirname((os.path.dirname(os.path.abspath(__file__))))
sys.path.append(Base_DIR)

# print(Base_DIR)
import json
import time
from aliyun.base import BaseALY
from aliyun.eip import EIP_API
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526 import CreateInstanceRequest
from aliyunsdkecs.request.v20140526 import StartInstanceRequest
from aliyunsdkvpc.request.v20160428 import AllocateEipAddressRequest, AssociateEipAddressRequest
from public import GenPassword, data_save
import fire


class ECS_API(BaseALY):
    def __init__(self, data):
        super(ECS_API, self).__init__(data)

    def check_instance(self, instance_name):
        """
        # 检测用户创建的instance_name是否存在，存在则退出
        :param instance_name: 实例名称
        :return:
        """
        # 创建 request，并设置参数
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_PageSize(100)
        # 发起 API 请求
        response = self.conn.do_action_with_exception(request)
        data = json.loads(str(response, encoding="utf8"))
        ret = data['Instances']['Instance']
        if ret:
            for i in ret:
                if instance_name in i['InstanceName']:
                    print('[INFO]：Instance：{} 已经存在'.format(instance_name))
                    exit(-100)
                    return i.get('InstanceName')

    # def get_SecurityGroups(self, sec_group_name):
    #     '''获取所有security groups信息'''
    #     request = DescribeSecurityGroupsRequest.DescribeSecurityGroupsRequest()
    #     request.set_accept_format('json')
    #     request.add_query_param('RegionId', self.region)
    #     response = self.conn.do_action(request)
    #     response = json.loads(str(response, encoding="utf8"))
    #     SecurityGroupId = None
    #     for group in response['SecurityGroups']['SecurityGroup']:
    #         if group['SecurityGroupName'] == sec_group_name:
    #             SecurityGroupId = group['SecurityGroupId']
    #     if not SecurityGroupId:
    #         print('[Error] Not Found this SecurityGroup,Please Create %s' % sec_group_name)
    #         exit(402)
    #     print(SecurityGroupId)
    #     return SecurityGroupId

    def create_instance(self, params):
        """创建ECS实例"""
        response = self.conn.do_action(params)
        response = json.loads(str(response, encoding="utf8"))
        # print('response==>', response)
        if response.get('InstanceId') == None:
            print('[Error]: Instance create falied.')
            print('[Code]：{},[Message]: {}'.format(response.get('Code'),
                                                   response.get('Message')))
            exit(-101)

        return response.get('InstanceId')

    def start_instance(self, instance_id):
        """
        启动实例
        :param instance_id: 根据购买机器的实例ID启动
        :return:
        """
        try:
            request = StartInstanceRequest.StartInstanceRequest()
            request.set_accept_format('json')
            request.add_query_param('InstanceId', instance_id)
            response = self.conn.do_action(request)
            json.loads(str(response, encoding="utf8"))
        except Exception as e:
            # print(e)
            print('[Error]: 实例开启失败，也可登陆控制台查看状态，信息：{}'.format(e))
            exit(-3)

    def creat_eip(self):
        '''创建eip'''
        try:
            request = AllocateEipAddressRequest.AllocateEipAddressRequest()
            request.set_accept_format('json')
            request.add_query_param('RegionId', self.region)
            request.add_query_param('InternetChargeType', 'PayByTraffic')
            request.add_query_param('Bandwidth', '10')
            request.add_query_param('InstanceChargeType', 'PostPaid')
            response = self.conn.do_action(request)
            response = json.loads(str(response, encoding="utf8"))
            eip_id = response['AllocationId']
            eip_ip = response['EipAddress']
            # print(eip_id, eip_ip)
        except Exception as e:
            print(e)
            print('Create EIP Faild')
            exit(406)

        return eip_id, eip_ip

    def union_eip(self, eip, instance):
        '''实例关联eip'''
        try:
            request = AssociateEipAddressRequest.AssociateEipAddressRequest()
            request.set_accept_format('json')
            request.add_query_param('InstanceType', 'EcsInstance')
            request.add_query_param('AllocationId', eip)
            request.add_query_param('InstanceId', instance)
            self.conn.do_action(request)
        except Exception as e:
            print(e)
            print('Union EIP Faild')
            exit(407)

    def get_ecs_info(self, instance_id):
        """
        阿里云Name可以重复，这里根据实例ID，获取实例的相关信息
        :param instance_id:
        :return:
        """
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_PageSize(100)
        response = self.conn.do_action_with_exception(request)
        data = json.loads(str(response, encoding="utf8"))
        ret = data['Instances']['Instance']
        if ret:
            for i in ret:
                if instance_id in i['InstanceName']:
                    data_dict = dict(instance_id=i['InstanceId'], public_ip=i['EipAddress']['IpAddress'],
                                     private_ip=i['VpcAttributes']['PrivateIpAddress']['IpAddress'][0],
                                     state=i['Status'],
                                     ec2_type=i['InstanceType'], hostname=i['InstanceName'])

                    return data_dict


def main(instance_name, instance_type, disk_size, security_group=None):
    """
    开通阿里云ECS
    :param instance_name: 实例NAME，多台用半角逗号隔开，如：OPS-ALY-01-web01,OPS-ALY-01-web02
    :param instance_type: 实例类型, 如：	ecs.c5.large
    :param disk_size:     磁盘大小，建议不要小于50G,
    :param security_group:安全组ID，不输入则默认安全组
    :return:
    """

    # 这里前端传过来的，后续等前端完善，进行修改，目前假数据
    data = {
        'SecretId': 'xxxxxxxxxxx',
        'SecretKey': 'xxxxxxxxxxx',
        'region': 'cn-shanghai',
        'ami_id': 'centos_7_06_64_20G_alibase_20181212.vhd',
        'switch_id': 'vsw-uf6ocgoom79ceyvzdyls4',
    }

    for instance in instance_name.split(','):
        print('[INFO]: Instance: {}'.format(instance))
        obj = ECS_API(data)
        # 检测实例名称是否已经存在
        obj.check_instance(instance)

        # 随机密码
        password = GenPassword(16)

        # 基础参数
        request = CreateInstanceRequest.CreateInstanceRequest()
        request.set_accept_format('json')
        request.add_query_param('RegionId', data.get('region'))
        request.add_query_param('ImageId', data.get('ami_id'))
        request.add_query_param('InstanceType', instance_type)
        request.add_query_param('InstanceName', instance)
        request.add_query_param('InstanceChargeType', 'PostPaid')
        request.add_query_param('SystemDisk.Category', 'cloud_ssd')
        request.add_query_param('SystemDisk.Size', disk_size)
        request.add_query_param('VSwitchId', data.get('switch_id'))
        request.add_query_param('Password', password)

        # 判断是否输入了安全组ID
        if security_group != None:
            request.add_query_param('SecurityGroupId', security_group)

        # 创建实例
        instance_id = obj.create_instance(request)
        # 绑定EIP
        eip_id, eip_ip = obj.creat_eip()
        obj.union_eip(eip_id, instance_id)
        # print(bool(instance_id))
        # 启动实例
        time.sleep(5)
        obj.start_instance(instance_id)

        host_info = obj.get_ecs_info(instance)
        data_info = {}
        if host_info:
            host = host_info.get('hostname')
            public_ip = host_info.get('public_ip')
            private_ip = host_info.get('private_ip')
            data_info[host] = {
                'hostname': host,
                'public_ip': public_ip,
                'private_ip': private_ip,
                'username': 'root',
                'password': password
            }
            # print(data_info)
            data_save(data_info)


if __name__ == '__main__':
    fire.Fire(main)

"""
示例：
python3  ecs.py --instance-name=yanghongfeitest01 --instance-type=ecs.sn2ne.large --disk-size=50 --security-group=sg-uf67cs41ghs92106jgmq
python3  ecs.py --instance-name=OPS-ALY-01-test01,OPS-ALY-01-test02 --instance-type=ecs.sn2ne.large --disk-size=50 --security-group=sg-uf67cs41ghs92106jgmq

"""
