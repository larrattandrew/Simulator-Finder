from flask import Flask, render_template, request
from downloader import download_pdf
from parser import extract_sim_events
from scheduler import add_end_times, group_by_device, merge_intervals, find_gaps
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SIM_OPEN = "0430"
SIM_CLOSE = "2300"

app = Flask(__name__)

SIM_ORDER = ["807", "808", "809", "810", "811", "812"]

def generate_schedule_links():
    squadrons = ["VT-7", "VT-9"]

    central = ZoneInfo("America/Chicago")

    today = datetime.now(central)
    tomorrow = today + timedelta(days=1)

    dates = [
        today.strftime("%Y-%m-%d"),
        tomorrow.strftime("%Y-%m-%d")
    ]

    schedules = {}

    for date in dates:
        schedules[date] = []
        for sq in squadrons:
            url = f"https://www.cnatra.navy.mil/scheds/TW1/SQ-{sq}/!{date}!{sq}!Frontpage.pdf"
            schedules[date].append((sq, url))

    return schedules

def fetch_schedule():
    output = []
    schedules = generate_schedule_links()

    for date, squadron_urls in schedules.items():
        day_output = {"date": date, "simulators": []}
        all_events = []

        for sq, url in squadron_urls:
            try:
                pdf_path = download_pdf(url)
                with open(pdf_path, "rb") as f:
                    if f.read(4) != b"%PDF":
                        raise ValueError("Not a valid PDF")
            except Exception:
                day_output["simulators"].append({"name": sq, "times": [], "error": "Schedule not available"})
                continue

            try:
                events = extract_sim_events(pdf_path)
                events = add_end_times(events)
                all_events.extend(events)
            except Exception:
                day_output["simulators"].append({"name": sq, "times": [], "error": "Schedule not available"})
                continue

        if not all_events:
            day_output["no_events"] = True
            output.append(day_output)
            continue

        devices = group_by_device(all_events)

        for device in SIM_ORDER:
            intervals = devices.get(device, [])
            merged = merge_intervals(intervals)
            gaps = find_gaps(merged, SIM_OPEN, SIM_CLOSE)
            if gaps:
                day_output["simulators"].append({"name": device, "times": gaps, "error": None})
            else:
                day_output["simulators"].append({"name": device, "times": [], "error": "No available time slots"})

        output.append(day_output)
    return output

@app.route("/", methods=["GET", "POST"])
def index():
    schedule = None
    if request.method == "POST":
        schedule = fetch_schedule()
    return render_template("index.html", schedule=schedule)

if __name__ == "__main__":
    app.run(debug=True)