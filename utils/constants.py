# encoding: utf-8
'''
Author: Alvin
Contact: 673721260@qq.com
File: constants.py
Time: 2020/1/11 20:12
Desc:
'''
from datetime import datetime
class Constants(object):
    """常量类"""

    # color
    RED_COLOR = '#c62828'
    WHITE_COLOR = 'white'
    GREY_COLOR = 'grey'
    BLACK_COLOR = '#404040'
    ORANGE_COLOR = 'orange'
    GREEN_COLOR = 'green'
    F2_COLOR = '#F2F2F2'
    SCHEDULER_COLOR = '#99ccff'

    LABEL_WIDTH = 6

    LABEL_HEIGHT = 1
    WINDOW_WIDTH = 580
    WINDOW_HEIGHT = 888
    CHILD_WINDOW_WIDTH = 230
    CHILD_WINDOW_HEIGHT = 200

    DAY_INFO_MSG_WIDTH = 580
    DAY_INFO_MSG_HEIGHT = 400

    MSG_BOX_WIDTH = 350
    MSG_BOX_HEIGHT = 150

    BASE_YEAR = 2019
    MAX_YEAR = 2050

    MONTHES = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    WEEKS = ['一', '二', '三', '四', '五', '六', '日']
    YEARS = [str(y) for y in range(datetime.today().date().year - 1, MAX_YEAR + 1)]

    FONT = 'Microsoft YaHei'
    FONT_SIZE_20 = 18
    FONT_SIZE_14 = 14
    FONT_SIZE_12 = 12
    FONT_SIZE_10 = 10
    FONT_SIZE_9 = 9
    FONT_SIZE_8 = 8
    FONT_WEIGHT = 'bold'
    WEEK_COLOR = 'black'

    SPLIT_LINE = 71
    ICO_PATH = 'schedule.ico'
    TITLE = '日程万年历'

    # files
    SCHEDULE_FILE = 'json_files/schedule.json'
    SOLAR_FILE = 'json_files/solar_festivals.json'
    LUNAR_FILE = 'json_files/lunar_festivals.json'
    TWENTY_FOUR_FILE = 'json_files/twenty_four_festivals.json'
    PUBLIC_HOLIDAY_FILE = 'json_files/public_holiday_festivals.json'
    PARENTS_DAY_FILE = 'json_files/parents_day_festivals.json'

    LOG_FILE = 'log.txt'
