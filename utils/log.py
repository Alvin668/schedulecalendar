# encoding: utf-8
'''
Author: Alvin
Contact: 673721260@qq.com
File: log.py
Time: 2020/1/14 23:00
Desc:
'''
from .constants import Constants
from datetime import datetime as dt

class Logger(object):

    @classmethod
    def info(cls, info_msg, module='None'):
        with open(Constants.LOG_FILE, 'a', encoding='utf-8') as f:
            f.write('[INFO]%s-%s:%s\n' % (dt.now().strftime('%Y-%m-%d %H:%M:%S'), module, info_msg))

    @classmethod
    def error(cls, err_msg, module='None'):
        with open(Constants.LOG_FILE, 'a', encoding='utf-8') as f:
            f.write('[ERROR]%s-%s:%s\n' % (dt.now().strftime('%Y-%m-%d %H:%M:%S'), module, err_msg))

    @classmethod
    def warning(cls, war_msg, module='None'):
        with open(Constants.LOG_FILE, 'a', encoding='utf-8') as f:
            f.write('[WARNING]%s-%s:%s\n' % (dt.now().strftime('%Y-%m-%d %H:%M:%S'), module, war_msg))