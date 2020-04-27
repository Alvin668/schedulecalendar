from schedule_calendar import SchedulerCalendar
from utils.log import Logger

if __name__ == '__main__':
    try:
        Logger.info('程序启动', module='main')
        sc = SchedulerCalendar()
        sc.show_calendar()
        Logger.info('程序终止', module='main')
    except Exception as e:
        print(e)
        Logger.error(e, module='main')