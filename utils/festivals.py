# encoding: utf-8
'''
Author: Alvin
Contact: 673721260@qq.com
File: festivals.py
Time: 2020/1/11 20:25
Desc:
'''
import json
from utils.constants import Constants
from datetime import datetime
from .log import Logger

class Festivals(object):
    """节日父类"""

    FESTIVALS = {}

    def __init__(self, file):
        with open(file, 'r', encoding='utf-8') as f:
            try:
                for fes in json.load(f):
                    self.FESTIVALS[fes.get('date')] = fes.get('name').encode('utf-8').decode('utf-8')
            except Exception as e:
                print(e)
                Logger.error(e, module='Festivals')

    def get_festivals(self, key):
        return self.FESTIVALS.get(key)

class SolarFestival(Festivals):
    """阳历节日类"""

    FESTIVALS = {}
    SOLAR_FESTIVALS_DESC = {}

    def __init__(self, file):
        with open(file, 'r', encoding='utf-8') as f:
            try:
                for fes in json.load(f):
                    self.SOLAR_FESTIVALS_DESC[fes.get('date')] = fes.get('describ')
            except Exception as e:
                print(e)
                Logger.error(e, module='SolarFestival')
        super(SolarFestival, self).__init__(file)

    def get_festivals_desc(self, key):
        return self.SOLAR_FESTIVALS_DESC.get(key)

class LunarFestival(Festivals):
    FESTIVALS = {}

class TwentyFourDays(Festivals):
    FESTIVALS = {}

class PublicHoliday(Festivals):
    FESTIVALS = {}

class ParentsDay(Festivals):
    FESTIVALS = {}

class Schedules(object):
    """日程类"""
    SCHEDULERS_LIST = []
    # {'date':'', 'scheduler':[{'title':'', 'describ':''}]}
    SCHEDULERS = {}

    def __init__(self, file):
        with open(file, 'r', encoding='utf-8') as f:
            try:
                self.SCHEDULERS_LIST = json.load(f)
                for j in self.SCHEDULERS_LIST:
                    self.SCHEDULERS[j.get('date')] = j.get('scheduler')
            except Exception as e:
                print(e)
                Logger.error(e, module='Schedules')
                self.SCHEDULERS_LIST = []

    def get_today_schedulers(self, key):
        return self.SCHEDULERS.get(key)

    def add_scheduler(self, key, values):
        if key not in self.SCHEDULERS.keys():
            self.SCHEDULERS[key] = []

        self.SCHEDULERS.get(key).append(values)

        if len(self.SCHEDULERS_LIST) == 0:
            self.SCHEDULERS_LIST.append({"date": key, "scheduler": self.SCHEDULERS.get(key)})
        else:
            is_exists = False
            for sch in self.SCHEDULERS_LIST:
                if sch.get('date') == key:
                    # key已经存在直接忽略
                    is_exists = True
                    break
            # key 不存在则添加新的日常到列表中
            if not is_exists:
                self.SCHEDULERS_LIST.append({"date": key, "scheduler": self.SCHEDULERS.get(key)})

        try:
            with open(Constants.SCHEDULE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.SCHEDULERS_LIST, f)
        except Exception as e:
            Logger.error(e, module='add_scheduler')