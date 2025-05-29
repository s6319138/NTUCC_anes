# -*- coding: utf-8 -*-
"""
Created on Thu May 29 11:42:05 2025

@author: user
"""

import streamlit as st
from datetime import datetime, timedelta
import random
from collections import defaultdict

st.set_page_config(page_title="4週自動排班 Web 版", layout="wide")
st.title("4週自動排班日曆（Web版）")

people = {
    "瑛": 1,
    "慈": 2,
    "翰": 2,
    "葉": 3,
    "石": 3,
    "涵": 3,
    "勳": 3,
    "帆": 3
}
persons = list(people.keys())

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("排班起始日（請選週一）", datetime.now())
with col2:
    holiday_str = st.text_input("國定假日（yyyy-mm-dd, 逗號分隔）", "")

def get_4weeks_dates(start_date):
    # 確保起始日是週一
    if start_date.weekday() != 0:
        start_date = start_date - timedelta(days=start_date.weekday())
    all_days = []
    current_day = start_date
    while len(all_days) < 4 * 5:
        # 只收錄週一到週五（weekday() 0=週一, 4=週五）
        if current_day.weekday() < 5:
            all_days.append(current_day)
        current_day += timedelta(days=1)
    return all_days

all_possible_dates = get_4weeks_dates(start_date)
all_possible_dates_str = [d.strftime("%Y-%m-%d") for d in all_possible_dates]

st.write("### 不可排日期（點選多選框選擇）")
exclude_date_vars = {}
cols = st.columns(4)
for idx, p in enumerate(persons):
    with cols[idx % 4]:
        exclude_date_vars[p] = st.multiselect(
            f"{p} 不可排日期",
            options=all_possible_dates_str,
            default=[],
            key=f"ex_{p}"
        )

def parse_holidays(holiday_str):
    holidays = set()
    for s in holiday_str.split(","):
        s = s.strip()
        if s:
            try:
                holidays.add(datetime.strptime(s, "%Y-%m-%d").date())
            except Exception:
                pass
    return holidays

def get_exclude_dates_rule(exclude_date_vars):
    rule = {}
    for p in persons:
        dates = [datetime.strptime(dstr, "%Y-%m-%d").date() for dstr in exclude_date_vars[p]]
        rule[p] = set(dates)
    return rule

def will_be_consecutive_three(person, day, assigned_days):
    check_days = set(assigned_days)
    check_days.add(day)
    days_list = sorted(check_days)
    idx = days_list.index(day)
    if idx >= 2:
        if (days_list[idx] - days_list[idx-2]).days == 2:
            return True
    if 0 < idx < len(days_list)-1:
        if (days_list[idx+1] - days_list[idx-1]).days == 2:
            return True
    if idx < len(days_list)-2:
        if (days_list[idx+2] - days_list[idx]).days == 2:
            return True
    return False

if st.button("自動排班"):
    holidays = parse_holidays(holiday_str)
    month_weeks = [all_possible_dates[i*5:(i+1)*5] for i in range(4)]
    exclude_dates_rule = get_exclude_dates_rule(exclude_date_vars)
    schedule = defaultdict(dict)

    cd_people = ["慈", "翰", "葉", "石", "涵", "勳", "帆"]
    cd_assign_counts = {p: {"C": 0, "D": 0, "total": 0} for p in cd_people}
    weekly_counts = {p: defaultdict(int) for p in cd_people}

    for week_idx, week in enumerate(month_weeks):
        etas_bing_days = {"慈": set(), "翰": set()}
        for day in week:
            for shift in ["A", "B", "C", "D"]:
                if shift in schedule[day]:
                    who = schedule[day][shift]
                    if who in ["慈", "翰"]:
                        etas_bing_days[who].add(day)
        for shift in ["C", "D"]:
            for day in week:
                weekday = day.strftime("%A")
                if day in holidays or all(day in exclude_dates_rule[p] for p in people):
                    continue
                available = [
                    p for p in cd_people
                    if day not in exclude_dates_rule[p]
                    and shift not in schedule[day]
                    and p not in schedule[day].values()
                    and weekly_counts[p][week_idx] < people[p]
                    and ((p != "慈") or (weekday not in ["Monday", "Wednesday"]))
                    and ((p != "翰") or (weekday not in ["Monday", "Thursday"]))
                    and ((p != "葉") or (weekday != "Wednesday"))
                    and ((p not in ["慈", "翰"]) or (len(etas_bing_days[p]) < 2))
                ]
                if not available:
                    continue
                min_shift = min(cd_assign_counts[p][shift] for p in available)
                best = [p for p in available if cd_assign_counts[p][shift] == min_shift]
                min_total = min(cd_assign_counts[p]["total"] for p in best)
                best = [p for p in best if cd_assign_counts[p]["total"] == min_total]
                random.shuffle(best)
                for person in best:
                    if shift not in schedule[day] and person not in schedule[day].values():
                        schedule[day][shift] = person
                        cd_assign_counts[person][shift] += 1
                        cd_assign_counts[person]["total"] += 1
                        weekly_counts[person][week_idx] += 1
                        if person in ["慈", "翰"]:
                            etas_bing_days[person].add(day)
                        break

    for week in month_weeks:
        weekly_assigned_counts = defaultdict(int)
        for day in week:
            weekday = day.strftime("%A")
            if day in holidays or all(day in exclude_dates_rule[p] for p in people):
                continue
            if weekday == "Thursday":
                if ("瑛" not in schedule[day].values() and
                    day not in exclude_dates_rule["瑛"] and
                    weekly_assigned_counts["瑛"] < people["瑛"]):
                    empty_shifts = [s for s in ["A", "B", "C", "D"] if s not in schedule[day]]
                    random.shuffle(empty_shifts)
                    for selected_shift in empty_shifts:
                        if "瑛" not in schedule[day].values():
                            schedule[day][selected_shift] = "瑛"
                            weekly_assigned_counts["瑛"] += 1
                            break

    for week_idx, week in enumerate(month_weeks):
        weekly_assigned_counts = defaultdict(int)
        etas_bing_days = {"慈": set(), "翰": set()}
        for day in week:
            for shift in ["A", "B", "C", "D"]:
                assigned = schedule[day].get(shift, "")
                if assigned in ["慈", "翰"]:
                    etas_bing_days[assigned].add(day)
        for day in week:
            weekday = day.strftime("%A")
            if day in holidays or all(day in exclude_dates_rule[p] for p in people):
                continue
            for shift in ["A", "B"]:
                if shift in schedule[day]:
                    continue
                exclude瑛 = lambda p: p != "瑛"
                def can_etas_bing(p):
                    if p in ["慈", "翰"]:
                        return len(etas_bing_days[p]) < 2 or day in etas_bing_days[p]
                    return True
                def extra_rule(p, weekday):
                    if p == "慈" and weekday in ["Monday", "Wednesday"]:
                        return False
                    if p == "翰" and weekday in ["Monday", "Thursday"]:
                        return False
                    if p == "葉" and weekday == "Wednesday":
                        return False
                    return True
                candidate_pool = [p for p in people
                    if day not in exclude_dates_rule[p]
                    and p not in schedule[day].values()
                    and exclude瑛(p)
                    and can_etas_bing(p)
                    and extra_rule(p, weekday)
                    and weekly_assigned_counts[p] < people[p]]
                if not candidate_pool:
                    candidate_pool = [p for p in people
                        if day not in exclude_dates_rule[p]
                        and p not in schedule[day].values()
                        and exclude瑛(p)
                        and can_etas_bing(p)
                        and extra_rule(p, weekday)]
                if not candidate_pool:
                    continue
                def sort_key(p):
                    return (
                        sum(1 for d in schedule if p in schedule[d].values()),
                        random.random()
                    )
                sorted_candidates = sorted(candidate_pool, key=sort_key)
                person = sorted_candidates[0]
                schedule[day][shift] = person
                weekly_assigned_counts[person] += 1
                if person in ["慈", "翰"]:
                    etas_bing_days[person].add(day)

    people_dates = defaultdict(list)
    for week in month_weeks:
        for day in week:
            shifts = schedule.get(day, {})
            day_people = set(shifts.values())
            for p in day_people:
                people_dates[p].append(day)
    warnings = []
    for p, days in people_dates.items():
        if p == "":
            continue
        days_sorted = sorted(days)
        count = 1
        for i in range(1, len(days_sorted)):
            if (days_sorted[i] - days_sorted[i - 1]).days == 1:
                count += 1
                if count >= 3:
                    warnings.append(
                        f"{p} 連續上班 {count} 天（{days_sorted[i - count + 1].strftime('%Y-%m-%d')}~{days_sorted[i].strftime('%Y-%m-%d')}）"
                    )
            else:
                count = 1

    if warnings:
        st.error("⚠️ " + "； ".join(warnings))
    else:
        st.success("✅ 無人連續上班三天以上")

    st.header("四週日曆班表")
    weekdays_zh = ["週一", "週二", "週三", "週四", "週五"]
    table_html = "<table style='border-collapse:collapse;width:90%;margin-bottom:16px;'>"
    table_html += (
        "<tr style='background-color:#f0f0f0;'>"
        + "".join([f"<th style='padding:8px;border:1px solid #ccc'>{wd}</th>" for wd in weekdays_zh])
        + "</tr>"
    )
    for w, week in enumerate(month_weeks):
        table_html += "<tr>"
        for day in week:
            shifts = schedule.get(day, {})
            daytxt = f"<b>{day.strftime('%m-%d')}</b>"
            if day in holidays:
                daytxt += "<br><span style='color:red'>(假日)</span>"
            for shift in ["A", "B", "C", "D"]:
                who = shifts.get(shift, "")
                if who:
                    daytxt += f"<br>{shift}: {who}"
            bgcolor = "#fdd" if day in holidays else "#fff"
            table_html += f"<td style='vertical-align:top;padding:8px;border:1px solid #ccc;background:{bgcolor};font-size:13px'>{daytxt}</td>"
        table_html += "</tr>"
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)

    st.header("每人每週上班天數統計")
    columns = ["人員"] + [f"第{i+1}週" for i in range(4)] + ["合計"]
    stats = []
    for person in people:
        days_by_week = []
        total = 0
        for week in month_weeks:
            workdays = set()
            for day in week:
                shifts = schedule.get(day, {})
                if person in shifts.values():
                    workdays.add(day)
            days_by_week.append(len(workdays))
            total += len(workdays)
        stats.append([person] + days_by_week + [total])
    st.table([columns] + stats)

    st.header("各人班別統計")
    header = ["人員", "A班", "B班", "C班", "D班", "合計"]
    stats2 = []
    stats_dict = {p: {"A":0, "B":0, "C":0, "D":0} for p in people}
    for day in schedule:
        for shift in ["A", "B", "C", "D"]:
            p = schedule[day].get(shift, "")
            if p in stats_dict:
                stats_dict[p][shift] += 1
    for person in people:
        a = stats_dict[person]["A"]
        b = stats_dict[person]["B"]
        c = stats_dict[person]["C"]
        d = stats_dict[person]["D"]
        total = a+b+c+d
        stats2.append([person, a, b, c, d, total])
    st.table([header]+stats2)
