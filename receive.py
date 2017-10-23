
import configparser
import datetime
import json
import logging

import os
import platform
from logging.handlers import TimedRotatingFileHandler

import requests

import time
from TimerTask import timer
from emailtool import send

conf = configparser.ConfigParser()
if platform.system() == 'Windows':
    conf.read('SMSReceive.conf', encoding="utf-8-sig")
else:
    conf.read('SMSReceive.conf')

# 文件路径
if not os.path.exists('log'):
    os.makedirs('log')
filename = 'log' + os.sep + "{day}.log".format(day=datetime.date.today())
# 创建一个记录器【warning】
logger = logging.getLogger("receive")
# 设置日志等级【大于debug等级】
logger.setLevel(logging.DEBUG)
# 设置 日志处理器 Handler ；分3中【固定文件】、【按照文件大小切割】、【按时间切割】
# fh = logging.FileHandler(filename=filename)
# fh = RotatingFileHandler(filename=filename, maxBytes=5*1024*1024, backupCount=5)
fh = TimedRotatingFileHandler(filename=filename, when="D", encoding="utf-8")
# 设置日志格式 【记录器名称 - 日期 - 等级 - 函数 - 消息】
formatter = logging.Formatter('%(name)s - %(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
fh.setFormatter(formatter)
# 设置过滤器【用"."分层】
lfilter = logging.Filter(name="receive")
logger.addHandler(fh)  # 为Logger实例增加一个处理器 handler
logger.addFilter(lfilter)   # 为Logger实例增加一个过滤器 filter
# logger.removeHandler(handler_name) # 为Logger实例删除一个处理器
# 禁止输出日志
# logger.disabled()


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
    #  定时器，开始时间
    times=conf.get(section="time", option="now")
    targettimestr = input('请输入定点时间，例如{times}'.format(times=times))
    if targettimestr == '':
        targettimestr = times
    targettime = datetime.time(int(targettimestr.split(':')[0]), int(targettimestr.split(':')[1]))
    if not os.path.exists('json'):
        os.makedirs('json')
    while True:
        logger.debug("时间判断")
        if datetime.datetime.now().hour == targettime.hour:
            #  如果发送数据不为空，循环获取接受数据，并将获取的数据通过 json 存储到硬盘 文件名称为【jsonjson/日期】，以附加的形式打开
            path = 'json' + os.sep + '{day}.txt'.format(day=datetime.date.today())
            while True:
                # 数据接收后删除，先保存
                jsondata = receive_date()
                if jsondata == '[]':
                    # assert jsondata != '[]', "返回值不能[]"
                    logger.debug("数据接受停止")
                    break
                json.dump(json.loads(jsondata), open(path, 'a'))
            #  读取 json 数据，查看是否存在异常信息，如果存在异常信息，通过邮件模块发送邮件
            logger.debug("开始读取数据")
            if os.path.exists(path=path):
                data = json.load(open(path, 'r'))
                htmlstart = r"""<h4>未发送的人员的手机号为<h4><ul>"""
                htmlend = r"""<ul>"""
                body = ""
                print(type(data))
                for one in data:
                    try:
                        # for key, value in one.items():
                        #     print(key,value)
                        if one.get('report_status', 'Fail') != "SUCCESS":
                            # print(one.get('mobile', '无电话'))
                            assert one.get('mobile', '无电话'), "无电话号码错误"
                            logger.info("{Tel} 电话号码错误".format(Tel=one.get('mobile', '无电话')))
                            body += "<li>{Tel}<li>".format(Tel=one.get('mobile', '无电话'))
                        else:
                            logger.debug("{mobile} 在 {user_receive_time} 发送成功".format(
                                mobile=one.get('mobile', '无电话'),
                                user_receive_time=one.get('user_receive_time', '无时间')))
                    except AssertionError:
                        logger.info("{sid}无电话号码".format(sid=one.get('sid', 'NULL')))
                if body != "":
                    simple_email(header="{today}发送失败人员名单".format(today=datetime.date.today()),
                                 body=htmlstart + body + htmlend)
                else:
                    logger.debug("无失败人员")
                #  无其他异常情况下进入休眠
            else:
                logger.debug("数据读取失败")
            print("执行完毕，开始休眠{second}秒".format(second=timer(targettime)))
            logger.debug("执行完毕，开始休眠{second}秒".format(second=timer(targettime)))
            time.sleep(timer(targettime))
        else:
            print("执行完毕，开始休眠{second}秒".format(second=timer(targettime)))
            logger.debug("执行完毕，开始休眠{second}秒".format(second=timer(targettime)))
            time.sleep(timer(targettime))
    pass
