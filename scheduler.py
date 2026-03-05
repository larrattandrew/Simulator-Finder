from datetime import datetime, timedelta
from collections import defaultdict


def add_end_times(events):

    for e in events:

        start = datetime.strptime(e["start"], "%H%M")

        e["start_dt"] = start
        e["end_dt"] = start + timedelta(minutes=90)

    return events


def group_by_device(events):

    devices = defaultdict(list)

    for e in events:
        devices[e["device"]].append((e["start_dt"], e["end_dt"]))

    return devices


def merge_intervals(intervals):

    intervals.sort()

    merged = []

    for start, end in intervals:

        if not merged or start > merged[-1][1]:

            merged.append([start, end])

        else:

            merged[-1][1] = max(merged[-1][1], end)

    return merged


def find_gaps(intervals, start_day="0430", end_day="2300"):

    day_start = datetime.strptime(start_day, "%H%M")
    day_end = datetime.strptime(end_day, "%H%M")

    gaps = []

    current = day_start

    for start, end in intervals:

        if start > current:
            gaps.append((current, start))

        current = max(current, end)

    if current < day_end:
        gaps.append((current, day_end))

    return gaps