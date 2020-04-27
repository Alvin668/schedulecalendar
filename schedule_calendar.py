# encoding: utf-8
'''
Author: Alvin
Contact: 673721260@qq.com
File: schedule_calendar.py
Time: 2020/1/11 20:09
Desc:
'''
import tkinter as tk
from datetime import datetime as dt
from tkinter import ttk
from utils.constants import Constants
import calendar
from borax.calendars.lunardate import LunarDate
from utils.festivals import LunarFestival, PublicHoliday, SolarFestival, TwentyFourDays, ParentsDay, Schedules
from apscheduler.schedulers.background import BackgroundScheduler
from utils.sys_tray_icon import SysTrayIcon
from tkinter import messagebox
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from utils.log import Logger

class SchedulerCalendar(object):
    """万年历"""
    SCREEN_WIDTH = 0
    SCREEN_HEIGHT = 0

    def __init__(self):

        self.today = dt.today().date()
        self.window = tk.Tk()
        self.window.title(Constants.TITLE)
        self.window.resizable(False, False)
        self.window.attributes("-topmost", 1)  # 设置窗口为置顶模式
        self.window.protocol('WM_DELETE_WINDOW', self.__minix_window)  # 点击关闭时最小化
        self.window.iconbitmap(Constants.ICO_PATH)

        # 设置窗体的大小和位置
        self.SCREEN_WIDTH = self.window.winfo_screenwidth()
        self.SCREEN_HEIGHT = self.window.winfo_screenheight()
        position_x = (self.SCREEN_WIDTH - Constants.WINDOW_WIDTH) / 2
        position_y = (self.SCREEN_HEIGHT - Constants.WINDOW_HEIGHT) / 2
        self.window.geometry('%dx%d+%d+%d' % (Constants.WINDOW_WIDTH, Constants.WINDOW_HEIGHT, position_x, position_y))

        # 创建静态frame用于保存查询条件和星期标题等固定不变的内容
        self.static_frame = tk.Frame(self.window)
        self.static_frame.grid(row=0, column=0)

        # 创建动态的frame用于保存动态生成的日期等
        self.dynamic_frame = tk.Frame(self.window)
        self.dynamic_frame.grid(row=1, column=0, padx=3)

        # 顶部查询条件控件
        self.cmb_year = ttk.Combobox(self.static_frame, width=8,
                                     font=(Constants.FONT, Constants.FONT_SIZE_14, Constants.FONT_WEIGHT))
        self.cmb_year.grid(row=0, column=0, columnspan=2)
        self.cmb_year['value'] = Constants.YEARS
        self.cmb_year.current(self.today.year - Constants.BASE_YEAR)
        self.cmb_year.bind("<<ComboboxSelected>>", self.__month_select)

        self.cmb_month = ttk.Combobox(self.static_frame, width=8,
                                      font=(Constants.FONT, Constants.FONT_SIZE_14, Constants.FONT_WEIGHT))
        self.cmb_month.grid(row=0, column=2, columnspan=2)
        self.cmb_month['value'] = Constants.MONTHES
        self.cmb_month.current(self.today.month - 1)
        self.cmb_month.bind("<<ComboboxSelected>>", self.__month_select)

        # 窗体按钮初始化
        # 上一月按钮
        tk.Button(self.static_frame, relief=tk.GROOVE, text='<', width=2, height=1,
                  font=(Constants.FONT, Constants.FONT_SIZE_12, Constants.FONT_WEIGHT),
                  command=self.__last_month).grid(row=0, column=2, sticky=tk.W)

        # 下一月按钮
        tk.Button(self.static_frame, relief=tk.GROOVE, text='>', width=2, height=1,
                  font=(Constants.FONT, Constants.FONT_SIZE_12, Constants.FONT_WEIGHT),
                  command=self.__next_month).grid(row=0, column=3, sticky=tk.E)

        # 今天按钮
        tk.Button(self.static_frame, relief=tk.GROOVE, text='today', width=8, height=1,
                  font=(Constants.FONT, Constants.FONT_SIZE_12, Constants.FONT_WEIGHT),
                  command=self.__go_back_to_today).grid(row=0, column=4, columnspan=2)

        # 生成周标题
        week_color = Constants.BLACK_COLOR
        for w in Constants.WEEKS:
            if w == '六' or w == '日':
                week_color = Constants.RED_COLOR
            tk.Label(self.static_frame, text=w, fg=week_color, font=(Constants.FONT, Constants.FONT_SIZE_14, Constants.FONT_WEIGHT), width=Constants.LABEL_WIDTH, height=Constants.LABEL_HEIGHT).grid(row=1, column=Constants.WEEKS.index(w))

        self.sch_window = None

        # 初始化节日类
        self.lf = LunarFestival(Constants.LUNAR_FILE)
        self.tf = TwentyFourDays(Constants.TWENTY_FOUR_FILE)
        self.sf = SolarFestival(Constants.SOLAR_FILE)
        self.ph = PublicHoliday(Constants.PUBLIC_HOLIDAY_FILE)
        self.sl = Schedules(Constants.SCHEDULE_FILE)
        self.pd = ParentsDay(Constants.PARENTS_DAY_FILE)

        self.row = 2
        self.last_month_year = 0
        self.last_month_month = 0
        self.next_month_year = 0
        self.next_month_next = 0

        # 定时任务，每天定时执行某任务
        # 每天0点1分切换的新的一天
        self.bs = BackgroundScheduler()
        try:
            self.bs.add_job(self.__move_to_new_today, trigger=CronTrigger(day_of_week='*', hour=0, minute=1, second=0))
            # 每天上午10点提醒今日日期，待办事项及节假日信息
            self.bs.add_job(self.__show_day_info_msg, trigger=CronTrigger(day_of_week='*', hour=10, minute=0, second=0))
            # self.bs.add_job(self.__show_day_info_msg, trigger=IntervalTrigger(seconds=20))
            self.bs.start()
        except Exception as e:
            Logger.error(e, module='BackgroundScheduler')

        # 程序运行时检索一次今日的待办事项并添加到提醒任务中
        self.__add_schedule_background_tasks()

        # 设置窗体最小化到右下角托盘中
        icons = Constants.ICO_PATH
        hover_text = Constants.TITLE  # 悬浮在图标上时显示提示的文本
        self.sys_tray_icon = SysTrayIcon(icons, hover_text, menu_options=(), on_quit=self.__exit_main_window,
                                         default_menu_index=1, main_window=self.window)
        self.window.bind("<Unmap>", lambda event: self.__unmap() if self.window.state() == 'iconic' else False)

    def __show_msg(self, title, desc):
        Logger.info('待办事项【%s】提醒' % title, module='__show_msg')
        msg = tk.Tk()
        msg.title(title)
        msg.resizable(False, False)
        msg.iconbitmap(Constants.ICO_PATH)
        position_x = (self.SCREEN_WIDTH - Constants.MSG_BOX_WIDTH) / 2
        position_y = (self.SCREEN_HEIGHT - Constants.MSG_BOX_HEIGHT) / 2
        msg.geometry('%dx%d+%d+%d' % (Constants.MSG_BOX_WIDTH, Constants.MSG_BOX_HEIGHT, position_x, position_y))
        msg.attributes('-topmost', 2)

        tk.Label(msg, text='您有如下待办事项需处理：', font=(Constants.FONT, Constants.FONT_SIZE_14, Constants.FONT_WEIGHT)).grid(row=0, column=0)

        tk.Label(msg, text=desc, fg=Constants.WHITE_COLOR, bg=Constants.SCHEDULER_COLOR,
                 font=(Constants.FONT, Constants.FONT_SIZE_10)).grid(row=1, column=0,
                                                                     sticky=tk.NW, padx=30)

        msg.mainloop()

    def __show_day_info_msg(self):
        try:
            Logger.info('每天上午10点定时提醒', module='__show_day_info_msg')
            msg = tk.Tk()
            msg.title(Constants.TITLE)
            msg.resizable(False, False)
            msg.iconbitmap(Constants.ICO_PATH)
            position_x = (self.SCREEN_WIDTH - Constants.DAY_INFO_MSG_WIDTH) / 2
            position_y = (self.SCREEN_HEIGHT - Constants.DAY_INFO_MSG_HEIGHT) / 2
            msg.geometry('%dx%d%+d+%d' % (Constants.DAY_INFO_MSG_WIDTH, Constants.DAY_INFO_MSG_HEIGHT, position_x, position_y))
            msg.attributes('-topmost', 2)

            info_frame = tk.Frame(msg)
            info_frame.grid(row=0, column=0, columnspan=7)
            self.__render_one_day_info(row=0, date=self.today, info_frame=info_frame)
            msg.mainloop()

        except Exception as e:
            Logger.info(e, module='__add_schedule')

    def __unmap(self):
        self.window.withdraw()
        self.sys_tray_icon.show_icon()

    def __month_select(self, evt):
        year = self.cmb_year.current() + Constants.BASE_YEAR
        month = self.cmb_month.current() + 1
        self.__generate_calendars(year, month)

    def __last_month(self):
        index = self.cmb_month.current() - 1
        if index < 0:
            # 切换到上一年的12月份
            index = 11
            year_index = self.cmb_year.current() - 1
            if year_index < 0:
                # 超出最小年限后切回到当前年
                year_index = self.today.year - Constants.BASE_YEAR
            self.cmb_year.current(year_index)

        self.cmb_month.current(index)
        self.__month_select(None)

    def __next_month(self):
        index = self.cmb_month.current() + 1
        if index == 12:
            # 切换到下一年的1月份
            index = 0
            year_index = self.cmb_year.current() + 1
            if year_index == Constants.MAX_YEAR:
                # 超出最大年限后切回到当前年
                year_index = self.today.year - Constants.BASE_YEAR
            self.cmb_year.current(year_index)

        self.cmb_month.current(index)
        self.__month_select(None)

    def __go_back_to_today(self):
        # 这里需要重新给self.today赋上新的一天的值
        self.today = dt.today().date()
        year_index = self.today.year - Constants.BASE_YEAR
        month_index = self.today.month - 1
        self.cmb_year.current(year_index)
        self.cmb_month.current(month_index)
        self.__month_select(None)

    def __move_to_new_today(self):

        self.__go_back_to_today()

        # 检索新的一天有没有待办事项并添加到日程提醒任务中
        self.__add_sechedule_background_tasks()

    def __generate_calendars(self, year, month):
        # 先刷新控件，然后重新渲染
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        # 重新渲染需要恢复初始值
        self.row = 2

        # 计算当前月份的天数
        month_days = calendar.monthrange(year, month)[1]
        days = [d for d in range(1, month_days + 1)]

        for day in days:
            every_day = dt(year=year, month=month, day=day).date()
            wk_day = every_day.weekday()
            font_color = Constants.BLACK_COLOR
            lunar_font_color = Constants.GREY_COLOR
            festival_font_color = Constants.RED_COLOR
            if wk_day == 5 or wk_day == 6:
                font_color = Constants.RED_COLOR

            bg_color = Constants.WHITE_COLOR
            if self.today == every_day:
                bg_color = Constants.ORANGE_COLOR
                font_color = Constants.WHITE_COLOR
                lunar_font_color = Constants.WHITE_COLOR
                festival_font_color = Constants.WHITE_COLOR

            # 渲染阳历日期（主日期）
            btn = tk.Button(self.dynamic_frame, text=day, relief=tk.GROOVE, bg=bg_color, fg=font_color,
                            font=(Constants.FONT, Constants.FONT_SIZE_14, Constants.FONT_WEIGHT),
                            width=Constants.LABEL_WIDTH, height=Constants.LABEL_HEIGHT, anchor=tk.N, pady=20,
                            activebackground=bg_color, activeforeground=font_color)
            btn.grid(row=self.row, column=wk_day)

            # 绑定鼠标单击事件
            btn.bind('<Button-1>', self.__click_date_button)
            btn.bind('<Double-Button-1>', self.__open_this_month_schedule)

            # 处理第一行空缺部分，用上个月的日期补齐
            if month == 1:
                # 上一年12月
                self.last_month_year = year - 1
                self.last_month_month = 12
            else:
                # 本年上月
                self.last_month_year = year
                self.last_month_month = month - 1
            last_month_last_day = calendar.monthrange(self.last_month_year, self.last_month_month)[1]

            # 根据本月第一天的位置计算应补齐上个月几天的日期
            if day == 1:
                for i in range(wk_day):
                    last_month_day = last_month_last_day - wk_day + i + 1
                    btn = tk.Button(self.dynamic_frame, text=str(last_month_day), relief=tk.GROOVE,
                                    bg=Constants.F2_COLOR,
                                    fg=Constants.GREY_COLOR,
                                    font=(Constants.FONT, Constants.FONT_SIZE_14, Constants.FONT_WEIGHT),
                                    width=Constants.LABEL_WIDTH, height=Constants.LABEL_HEIGHT, anchor=tk.N, pady=20,
                                    activebackground=Constants.F2_COLOR, activeforeground=Constants.GREY_COLOR)
                    btn.grid(row=2, column=i)
                    btn.bind('<Button-1>', self.__click_date_button_for_last_month)

                    last_month_every_day = dt(year=self.last_month_year, month=self.last_month_month,
                                              day=last_month_day).date()
                    self.__render_lunar_day_and_festival(last_month_every_day, lunar_font_color, Constants.F2_COLOR, 2, i, festival_font_color)

            if month == 12:
                # 下一年12月份
                self.next_month_year = year + 1
                self.next_month_month = 1
            else:
                # 本年上个月
                self.next_month_year = year
                self.next_month_month = month + 1

            # 根据最后一天的位置计算应该补充下个月日期的天数
            if day == month_days:
                for i in range(1, 7 - wk_day):
                    btn = tk.Button(self.dynamic_frame, text=str(i), relief=tk.GROOVE, bg=Constants.F2_COLOR,
                                    fg=Constants.GREY_COLOR,
                                    font=(Constants.FONT, Constants.FONT_SIZE_14, Constants.FONT_WEIGHT),
                                    width=Constants.LABEL_WIDTH, height=Constants.LABEL_HEIGHT, anchor=tk.N, pady=20,
                                    activebackground=Constants.F2_COLOR, activeforeground=Constants.GREY_COLOR)
                    btn.grid(row=self.row, column=wk_day+i)
                    btn.bind('<Button-1>', self.__click_date_button_for_next_month)
                    btn.bind("<Double-Button-1>", self.__open_next_month_schedule)

                    next_month_every_day = dt(year=self.next_month_year, month=self.next_month_month, day=i).date()
                    self.__render_lunar_day_and_festival(next_month_every_day, Constants.GREY_COLOR, Constants.F2_COLOR, self.row, wk_day + i, festival_font_color)

            self.__render_lunar_day_and_festival(every_day, lunar_font_color, bg_color, self.row, wk_day, festival_font_color)

            if wk_day == 6:
                self.row += 1

        self.info_frame = tk.Frame(self.dynamic_frame)
        self.info_frame.grid(row=self.row + 1, column=0, columnspan=7)

        self.__render_one_day_info(self.row, self.today)

    def __render_lunar_day_and_festival(self, every_day, lunar_font, bg_color, row, wk_day, festival_font_color):
        # 渲染公历节日
        solar_day = self.sf.get_festivals(every_day.strftime('%m-%d'))
        if solar_day:
            tk.Label(self.dynamic_frame, text=solar_day, fg=festival_font_color, bg=bg_color,
                     font=(Constants.FONT, Constants.FONT_SIZE_10, Constants.FONT_WEIGHT)).grid(row=row, column=wk_day,
                                                                                               sticky=tk.N, pady=4)

        # 渲染农历日期
        lunar_date = LunarDate.from_solar(every_day).strftime('%D')
        if lunar_date == '初一':
            lunar_date = LunarDate.from_solar(every_day).strftime('%M') + '月'

        tk.Label(self.dynamic_frame, text=lunar_date, fg=lunar_font, bg=bg_color,
                 font=(Constants.FONT, Constants.FONT_SIZE_9, Constants.FONT_WEIGHT)).grid(row=row, column=wk_day,
                                                                                          sticky=tk.S, pady=15)

        # 渲染农历节日
        lunar_day = LunarDate.from_solar(every_day).strftime('%M%D')
        lunar_festival = self.lf.get_festivals(lunar_day)
        if lunar_festival:
            tk.Label(self.dynamic_frame, text=lunar_festival, fg=festival_font_color, bg=bg_color,
                     font=(Constants.FONT, Constants.FONT_SIZE_10, Constants.FONT_WEIGHT)).grid(row=row, column=wk_day,
                                                                                               sticky=tk.N, pady=4)
        str_every_day = every_day.strftime('%Y-%m-%d')
        # 渲染24节气
        twenty_four_day = self.tf.get_festivals(str_every_day)
        if twenty_four_day:
            twenty_four_day = twenty_four_day[0] + '\r' + twenty_four_day[1]
            tk.Label(self.dynamic_frame, text=twenty_four_day, fg=Constants.WHITE_COLOR, bg=Constants.GREEN_COLOR,
                     font=(Constants.FONT, Constants.FONT_SIZE_9, Constants.FONT_WEIGHT)).grid(row=row, column=wk_day,
                                                                                              sticky=tk.E, padx=2)


        # 母亲节 父亲节 感恩节 如果与阳历节日冲突则覆盖掉阳历节日
        parents_day = self.pd.get_festivals(str_every_day)
        if parents_day:
            tk.Label(self.dynamic_frame, text=parents_day, fg=festival_font_color, bg=bg_color,
                     font=(Constants.FONT, Constants.FONT_SIZE_10, Constants.FONT_WEIGHT)).grid(row=row, column=wk_day,
                                                                                               sticky=tk.N, pady=4)

        # 渲染日程
        if self.sl.get_today_schedulers(str_every_day) and len(self.sl.get_today_schedulers(str_every_day)) > 0:
            sch_text = '待'
            sch_bg = Constants.SCHEDULER_COLOR
            # 今天以前的事项标记为已办
            if every_day < self.today:
                sch_text = '已'
                sch_bg = Constants.GREY_COLOR

            tk.Label(self.dynamic_frame, text=sch_text, fg=Constants.WHITE_COLOR, bg=sch_bg,
                     font=(Constants.FONT, Constants.FONT_SIZE_8)).grid(row=row, column=wk_day, sticky=tk.SE, padx=2,
                                                                       pady=4)

        # 渲染调休/上班标记
        public_holiday = self.ph.get_festivals(str_every_day)
        if public_holiday:
            ph_bg = Constants.RED_COLOR
            if public_holiday == '班':
                ph_bg = Constants.BLACK_COLOR

            tk.Label(self.dynamic_frame, text=public_holiday, fg=Constants.WHITE_COLOR, bg=ph_bg,
                     font=(Constants.FONT, Constants.FONT_SIZE_9)).grid(row=row, column=wk_day, sticky=tk.NW, padx=2,
                                                                       pady=2)

    # 分别定义用于区分年份或月份
    def __open_this_month_schedule(self, evt):
        sch_day = evt.widget.cget('text')
        # 本月度对应的年份和月份
        sch_year = self.cmb_year.current() + Constants.BASE_YEAR
        sch_month = self.cmb_month.current() + 1
        self.sch_date = dt(sch_year, sch_month, int(sch_day)).date()
        if self.sch_date >= self.today:
            self.__open_schedule()

    # 分别定义用于区分年份或月份
    def __open_next_month_schedule(self, evt):
        sch_day = evt.widget.cget('text')
        # 下个月对应的年份和月份
        self.sch_date = dt(self.next_month_year, self.next_month_month, int(sch_day)).date()
        if self.sch_date >= self.today:
            self.__open_schedule()

    def __open_schedule(self):
        if self.sch_window:
            self.sch_window.destroy()

        c_window = tk.Toplevel(self.window)
        c_window.resizable(False, False)
        c_window.title('万年历--添加日程')
        c_window.attributes('-topmost', 1)
        c_window.attributes('-toolwindow', 2)

        #
        position_x = (self.SCREEN_WIDTH - Constants.CHILD_WINDOW_WIDTH) / 2
        position_y = (self.SCREEN_HEIGHT - Constants.CHILD_WINDOW_HEIGHT) / 2
        c_window.geometry(
            '%dx%d+%d+%d' % (Constants.CHILD_WINDOW_WIDTH, Constants.CHILD_WINDOW_HEIGHT, position_x, position_y))

        tk.Label(c_window, text='日程标题(5字以内)：', font=(Constants.FONT, Constants.FONT_SIZE_8)).grid(row=0, column=0, columnspan=6, sticky=tk.W)
        self.s_title = tk.Entry(c_window, font=(Constants.FONT, Constants.FONT_SIZE_10, Constants.FONT_WEIGHT))
        self.s_title.grid(row=1, column=0, columnspan=6, sticky=tk.W)
        tk.Label(c_window, text='日程描述(不要太长)：', font=(Constants.FONT, Constants.FONT_SIZE_8)).grid(row=2, column=0, columnspan=6, sticky=tk.W)
        self.s_desc = tk.Entry(c_window, width=25, font=(Constants.FONT, Constants.FONT_SIZE_10, Constants.FONT_WEIGHT))
        self.s_desc.grid(row=3, column=0, columnspan=6, sticky=tk.W)
        tk.Label(c_window, text='提醒时间：', font=(Constants.FONT, Constants.FONT_SIZE_8)).grid(row=4, column=0, columnspan=6, sticky=tk.W)
        tk.Label(c_window, text='时：', font=(Constants.FONT, Constants.FONT_SIZE_8)).grid(row=5, column=0, sticky=tk.W)
        self.hour = ttk.Combobox(c_window, width=2, font=(Constants.FONT, Constants.FONT_SIZE_9, Constants.FONT_WEIGHT))
        self.hour.grid(row=5, column=1, sticky=tk.W)
        self.hour['value'] = [h for h in range(25)]

        tk.Label(c_window, text='分：', font=(Constants.FONT, Constants.FONT_SIZE_8)).grid(row=5, column=2, sticky=tk.W)
        self.minute = ttk.Combobox(c_window, width=2, font=(Constants.FONT, Constants.FONT_SIZE_9, Constants.FONT_WEIGHT))
        self.minute.grid(row=5, column=3, sticky=tk.W)
        self.minute['value'] = [m for m in range(60)]

        # 默认设置15分钟后提醒
        m = dt.now().minute + 15
        h = dt.now().hour
        if m > 59:
            m = m - 59
            h = h + 1
            if h > 23:
                h = 0

        self.hour.current(h)
        self.minute.current(m)
        tk.Button(c_window, text='添  加', command=self.__add_schedule).grid(row=6, column=0, columnspan=6)

        self.sch_window = c_window

    def __add_schedule(self):
        key = self.sch_date.strftime('%Y-%m-%d')
        s_title = self.s_title.get()
        s_desc = self.s_desc.get()
        hour = int(self.hour.get())
        minute = int(self.minute.get())
        if not all([s_title, s_desc]):
            messagebox.showerror('提示', '标题和描述不能为空！')
            return

        values = {'title': s_title, 'describ': s_desc, 'hour': hour, 'minute': minute}
        self.sl.add_scheduler(key, values)

        self.__render_one_day_info(self.row, self.sch_date)

        # 如果添加的是今日的日程安排，并且提醒时间大于当前时间，则需将该日程添加到日程提醒中
        if self.sch_date == self.today:
            tell_time = dt(self.today.year, self.today.month, self.today.day, hour, minute, 0)
            # 如果提醒时间在当前时间之后则添加到提醒任务中
            if tell_time > dt.now():
                self.bs.add_job(self.__show_msg, trigger=DateTrigger(run_date=tell_time), args=[s_title, s_desc])

        # 关闭添加日程窗口
        self.__close_add_schedule_window()
        Logger.info(self.bs.get_jobs(), module='__add_schedule')

    def __render_one_day_info(self, row, date, info_frame=None):
        if info_frame is None:
            info_frame = self.info_frame

        for widget in info_frame.winfo_children():
            widget.destroy()

        str_date = date.strftime('%Y-%m-%d')
        # 渲染某个日期的基本信息
        tk.Label(info_frame, text='-' * Constants.SPLIT_LINE,
                 font=(Constants.FONT, Constants.FONT_SIZE_14, Constants.FONT_WEIGHT)).grid(row=row + 1, column=0,
                                                                                            columnspan=7, sticky=tk.N)

        tk.Label(info_frame, text=date.day, width=2, height=1, fg=Constants.WHITE_COLOR, bg=Constants.ORANGE_COLOR,
                 font=(Constants.FONT, 50, Constants.FONT_WEIGHT)).grid(row=row + 2, column=0, rowspan=3,
                                                                        columnspan=2, sticky=tk.W, padx=3)

        solar_date = date.strftime('%Y{0}%m{1}%d{2} {3}{4}').format('年', '月', '日', '星期', Constants.WEEKS[date.weekday()])
        tk.Label(info_frame, text=solar_date, fg=Constants.BLACK_COLOR,
                 font=(Constants.FONT, Constants.FONT_SIZE_12, Constants.FONT_WEIGHT)).grid(row=row + 2, column=1,
                                                                                            columnspan=6,
                                                                                            sticky=tk.NW, padx=20)

        lunar_date = LunarDate.from_solar(date)
        lunar_date = lunar_date.strftime('{0}%M{1}%D %G'.format('农历：', '月'))
        tk.Label(info_frame, text=lunar_date, fg=Constants.BLACK_COLOR,
                 font=(Constants.FONT, Constants.FONT_SIZE_10, Constants.FONT_WEIGHT)).grid(row=row + 3, column=1,
                                                                                            columnspan=6,
                                                                                            sticky=tk.NW, padx=21)

        # 渲染24节气
        twenty_four_day = self.tf.get_festivals(str_date)
        if twenty_four_day:
            twenty_four_day = twenty_four_day[0] + '\r' + twenty_four_day[1]
            tk.Label(info_frame, text=twenty_four_day, fg=Constants.WHITE_COLOR, bg=Constants.GREEN_COLOR,
                     font=(Constants.FONT, Constants.FONT_SIZE_10)).grid(row=row + 4, column=1, sticky=tk.NW, padx=22)

        # 渲染农历节日
        lunar_day = LunarDate.from_solar(date).strftime('%M%D')
        lunar_festival = self.lf.get_festivals(lunar_day)
        if lunar_festival:
            tk.Label(info_frame, text=lunar_festival, fg=Constants.WHITE_COLOR, bg=Constants.ORANGE_COLOR,
                     font=(Constants.FONT, Constants.FONT_SIZE_10, Constants.FONT_WEIGHT)).grid(row=row + 4, column=1,
                                                                                                sticky=tk.E)

        # 母亲节 父亲节 感恩节 如果与公历节日冲突则覆盖公历节日
        parents_day = self.pd.get_festivals(str_date)
        if parents_day:
            tk.Label(info_frame, text=parents_day, fg=Constants.WHITE_COLOR, bg=Constants.RED_COLOR,
                     font=(Constants.FONT, Constants.FONT_SIZE_10, Constants.FONT_WEIGHT)).grid(row=row + 4, column=2,
                                                                                                sticky=tk.W)

        # 渲染公历节日
        solar_day = self.sf.get_festivals_desc(date.strftime('%m-%d'))
        if solar_day:
            tk.Label(info_frame, text=solar_day, fg=Constants.WHITE_COLOR, bg=Constants.RED_COLOR,
                     font=(Constants.FONT, Constants.FONT_SIZE_10, Constants.FONT_WEIGHT)).grid(row=row + 4, column=3,
                                                                                                sticky=tk.W,
                                                                                                columnspan=4)

        # 渲染日程信息
        tk.Label(info_frame, text='-' * Constants.SPLIT_LINE,
                 font=(Constants.FONT, Constants.FONT_SIZE_14, Constants.FONT_WEIGHT)).grid(row=row + 6, column=0,
                                                                                            columnspan=7, sticky=tk.N)

        sch_list = self.sl.get_today_schedulers(str_date)
        if sch_list and len(sch_list) > 0:
            index = 7
            sch_bg = Constants.SCHEDULER_COLOR
            if date < self.today:
                sch_bg = Constants.GREY_COLOR

            tk.Label(info_frame, text='待办事项：', fg=Constants.WHITE_COLOR, bg=Constants.SCHEDULER_COLOR,
                     font=(Constants.FONT, Constants.FONT_SIZE_10)).grid(row=row + index, column=0, columnspan=6,
                                                                         sticky=tk.NW, padx=3)

            for sch in sch_list:
                sch_info = '%02s:%02s - %s：%s' % (
                str(sch.get('hour')), str(sch.get('minute')), sch.get('title'), sch.get('describ'))
                tk.Label(info_frame, text=sch_info, fg=Constants.WHITE_COLOR, bg=sch_bg,
                         font=(Constants.FONT, Constants.FONT_SIZE_10, Constants.FONT_WEIGHT)).grid(row=row + index +
                                                                                                    1,
                                                                                                    column=1,
                                                                                                    columnspan=6,
                                                                                                    sticky=tk.W,
                                                                                                    pady=3)

                index += 1

    # 本月度日期单击事件
    def __click_date_button(self, evt):
        year = self.cmb_year.current() + Constants.BASE_YEAR
        month = self.cmb_month.current() + 1
        # evt.widget 表示当前事件发生在那个控件上
        day = evt.widget.cget('text')
        click_date = dt(year, month, int(day)).date()
        self.__render_one_day_info(self.row, click_date)
        evt.widget['highlightcolor'] = Constants.ORANGE_COLOR

    # 上个月日期单击事件
    def __click_date_button_for_last_month(self, evt):
        day = evt.widget.cget('text')
        click_date = dt(self.last_month_year, self.last_month_month, int(day)).date()
        self.__render_one_day_info(self.row, click_date)

    # 下个月日期单击事件
    def __click_date_button_for_next_month(self, evt):
        day = evt.widget.cget('text')
        click_date = dt(self.next_month_year, self.next_month_month, int(day)).date()
        self.__render_one_day_info(self.row, click_date)

    def __exit_main_window(self, sys_tray=None):
        self.window.destroy()

    def __close_add_schedule_window(self):
        self.sch_window.destroy()

    def __minix_window(self):
        messagebox.showinfo(title='提示', message='窗口将最小化到右下角托盘中,右击托盘中的图标可以退出程序！')
        self.window.iconify()

    def __add_schedule_background_tasks(self):
        sch_date = self.today
        t_schedules = self.sl.get_today_schedulers(sch_date.strftime('%Y-%m-%d'))
        if t_schedules and len(t_schedules) > 0:
            for sch in t_schedules:
                tell_time = dt(self.today.year, self.today.month, self.today.day, int(sch.get('hour')),
                               int(sch.get('minute')), 0)
                # 过期的就不再添加到提醒任务中了
                if tell_time > dt.now():
                    self.bs.add_job(self.__show_msg, trigger=DateTrigger(run_date=tell_time),
                                    args=[sch.get('title'), sch.get('describ')])

        Logger.info(self.bs.get_jobs(), module='__add_schedule_background_tasks')

    def show_calendar(self):
        year = self.cmb_year.current() + Constants.BASE_YEAR
        month = self.cmb_month.current() + 1
        self.__generate_calendars(year, month)
        self.window.mainloop()


