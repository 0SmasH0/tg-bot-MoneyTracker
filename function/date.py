import datetime as dt
import math


def day_week_year():
    data = {'День': [], "Месяц": [], "Год": []}


    day_today = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    day_of_week_now = dt.datetime.now()
    year_today = dt.datetime.now().replace(month=1,day=1,hour=0, minute=0, second=0, microsecond=0)



    data["День"].extend([day_today, day_today + dt.timedelta(days=1)
                          ])

    # start_week = dt.date.today() - dt.timedelta(days=day_of_week_now.weekday())
    # start_date_of_week = dt.datetime(start_week.year,start_week.month,start_week.day,0,0,0 )
    #
    # data['Месяц'].extend([start_date_of_week, start_date_of_week + dt.timedelta(days=7)])

    start_month = dt.datetime(year=dt.datetime.now().year, month=dt.datetime.now().month, day=1,hour=0, minute=0, second=0, microsecond=0)
    next_month = dt.datetime(year=dt.datetime.now().year, month=dt.datetime.now().month + 1, day=1, hour=0, minute=0,
                              second=0, microsecond=0)

    data['Месяц'].extend([start_month, next_month])

    data["Год"].extend([year_today, dt.datetime(year=dt.datetime.now().year + 1, month=1,day=1,hour=0, minute=0, second=0, microsecond=0)])

    print(data)
    return data


def week(flag: str):
    day_of_week_now = dt.datetime.now()

    match flag:

        case 'pie':
            start_week = dt.date.today() - dt.timedelta(days=day_of_week_now.weekday())
            start_date_of_week = dt.datetime(start_week.year,start_week.month,start_week.day,0,0,0 )

            return start_date_of_week, day_of_week_now

        case 'bar':
            days = []
            for w in range(day_of_week_now.weekday() + 1):
                start_time = day_of_week_now - dt.timedelta(days=w,hours=day_of_week_now.hour,
                                                            minutes=day_of_week_now.minute,
                                                            seconds=day_of_week_now.second,
                                                            microseconds=day_of_week_now.microsecond)

                days.append((start_time,start_time + dt.timedelta(days=1)))
            print(11111111111111,days)
            return days


def month(flag: str):
    day_of_month_now = dt.datetime.now()
    start_date_of_month = dt.datetime(day_of_month_now.year,day_of_month_now.month,1,0,0,0 )

    match flag:

        case 'pie':
            return start_date_of_month, day_of_month_now

        case 'bar':
            num_day = start_date_of_month.weekday()

            start_week = start_date_of_month - dt.timedelta(days=num_day)
            dif = day_of_month_now - start_week
            if dif.seconds > 0 or dif.microseconds > 0:
                days = dif.days + 1
            else:
                days = dif.days

            count_week = math.ceil(days / 7)

            weeks = []
            for i in range(count_week):
                weeks.append((start_week + dt.timedelta(days=7 * i), start_week + dt.timedelta(days=7 * (i+1))))

            return weeks

def year(flag: str):
    day_of_year_now = dt.datetime.now()

    match flag:

        case 'pie':
            start_date_of_year = dt.datetime(day_of_year_now.year,1,1,0,0,0 )

            return start_date_of_year, day_of_year_now

        case 'bar':
            month = []
            for m in range(1,day_of_year_now.month + 1):
                if m == 12:
                    month.append((dt.datetime(day_of_year_now.year, m, 1, 0, 0, 0),
                                  dt.datetime(day_of_year_now.year, m, 31, 24, 0, 0)))
                else:
                    month.append((dt.datetime(day_of_year_now.year, m, 1, 0,0,0),
                                  dt.datetime(day_of_year_now.year, m+1, 1, 0,0,0)))

            return month


def custom_time(first_date: dict, second_date: dict):
    start_date = dt.date(first_date['year'], first_date['month'], first_date['day'])
    end_date = dt.date(second_date['year'], second_date['month'], second_date['day'])

    return start_date, end_date
