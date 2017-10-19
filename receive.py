
import configparser
import datetime
import json

import os
import platform

import requests

import time
from TimerTask import timer
from emailtool import send

conf = configparser.ConfigParser()
if platform.system() == 'Windows':
    conf.read('SMSReceive.conf', encoding="utf-8-sig")
else:
    conf.read('SMSReceive.conf')


def receive_date():
    params = {'apikey': conf.get(section="yunpianapikey", option="apikey"), 'page_size': '10'}
    # print(params)
    url = 'https://sms.yunpian.com/v2/sms/pull_status.json'
    req = requests.post(url, data=params)
    # print(req.url)
    # print(req.text)
    return req.text

def simple_email(header, body,):
    # 配置文件中换行后，要留一个空格" "
    cbody = '<html>' + body + conf.get(section="emailsignature", option="body")
    send(smtp_server=conf.get(section='SMSReciveemail', option='smtp_server'),
         smtp_port=conf.get(section='SMSReciveemail', option='smtp_port'),
         from_addr=conf.get(section='SMSReciveemail', option='from_addr'),
         from_addr_str=conf.get(section='SMSReciveemail', option='from_addr_str'),
         password=conf.get(section='SMSReciveemail', option='password'),
         to_address=conf.get(section='SMSReciveemail', option='error_email'),
         header=header, body=cbody,)
    pass


if __name__ == '__main__':
    # TODO 定时器，开始时间
    targettimestr = input('请输入定点时间，例如8:00')
    if targettimestr == '':
        targettimestr = conf.get(section='time', option='now')
    targettime = datetime.time(int(targettimestr.split(':')[0]), int(targettimestr.split(':')[1]))
    while True:
        if datetime.datetime.now().hour == targettime.hour:
            # TODO 如果发送数据不为空，循环获取接受数据，并将获取的数据通过 json 存储到硬盘 文件名称为【log/日期】，以附加的形式打开
            while True:
                # 数据接收后删除，先保存
                jsondata = receive_date()
                if jsondata == '[]':
                    # assert jsondata != '[]', "返回值不能[]"
                    break
                if not os.path.exists('log'):
                    os.makedirs('log')
                json.dump(json.loads(jsondata),
                          open('log' + os.sep + '{day}.txt'.format(day=datetime.date.today()), 'a'))
            # TODO 读取 json 数据，查看是否存在异常信息，如果存在异常信息，通过邮件模块发送邮件
            if os.path.exists('log' + os.sep + '{day}.txt'.format(day=datetime.date.today())):
                data = json.load('log' + os.sep + '{day}.txt'.format(day=datetime.date.today()))
                htmlstart = r"""<h4>未发送的人员的手机号为<h4><ul>"""
                htmlend = r"""<ul>"""
                body = ""
                for one in data:
                    # for key, value in one.items():
                    #     print(key,value)
                    if one.get('report_status', 'Fail') != "SUCCESS":
                        # print(one.get('mobile', '无电话'))
                        body += "<li>{Tel}<li>".format(Tel=one.get('mobile', '无电话'))
                if body != "":
                    simple_email(header="{today}发送失败人员名单".format(today=datetime.date.today()),
                                 body=htmlstart + body + htmlend)
            # TODO 无其他异常情况下进入休眠
            else:
                print(timer(targettime))
                time.sleep(timer(targettime))
    pass
