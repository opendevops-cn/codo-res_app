#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/7 13:19
# @Author  : Fred Yang
# @File    : public.py
# @Role    : public

import string
import random
import os
import sys
import re
import time
import json



def GenPassword(length):
    '''随机生成密码'''
    chars=string.ascii_letters+string.digits
    return ''.join([random.choice(chars) for i in range(length)])


def lock_json(script_name):
    pid_file = '/tmp/data_json.pid'
    lock_count = 0
    while True:
        if os.path.isfile(pid_file):
            ###打开脚本运行进程id文件并读取进程id
            with open(pid_file, 'r') as fp_pid:
                process_id =  fp_pid.read()

            ###判断pid文件取出的是否是数字
            if not process_id:
                break

            if not re.search(r'^\d', process_id):
                break

            ###确认此进程id是否还有进程
            lock_count += 1
            if lock_count > 30:
                print('1 min after this script is still exists')
                sys.exit(111)
            else:
                check_list = os.popen('/bin/ps %s|grep "%s"' % (process_id, script_name)).readlines()
                if check_list:
                    print('check_list--->',check_list)
                    print('cmd ----> /bin/ps %s|grep "%s"'%(process_id, script_name))
                    print("The script is running...... ,Please wait for a moment!")
                    time.sleep(5)
                else:
                    os.remove(pid_file)
        else:
            break

    ###把进程号写入文件
    with open(pid_file, 'w') as wp_pid:
        p_id = os.getpid()
        wp_pid.write(str(p_id))

def data_save(data_info,script_name):
    lock_json(script_name)
    file_name = 'data.json'
    if not os.path.exists(file_name):
        os.system("echo {} > %s" % file_name)
    with open(file_name, 'a+') as file:
        json.dump(data_info, file, sort_keys=True, indent=4)
