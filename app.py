# app.py
from flask import Flask, render_template, request
from downloader import download_pdf
from parser import extract_sim_events
from scheduler import add_end_times, group_by_device, merge_intervals, find_gaps
from datetime import datetime, timedelta

SIM_OPEN = "0430"
SIM_CLOSE = "2300"

app = Flask(__name__)

# Generate schedule URLs for VT-7 and VT-9
def generate_schedule_links():
    squadrons = ["VT-7", "VT-9"]
    today = datetime.today()
    tomorrow = today + timedelta(days=1)
    dates = [today.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d")]

    schedules = {}
    for date in dates:
        schedules[date] = []
        for sq in squadrons:
            url = f"https://www.cnatra.navy.mil/scheds/TW1/SQ-{sq}/!{date}!{sq}!Frontpage.pdf"
            schedules[date].append((sq, url))  # Keep track of squadron
    return schedules

# Fetch and parse schedules
def fetch_schedule():
    output = []  # stores all lines for the webpage
    schedules = generate_schedule_links()

    for date, squadron_urls in schedules.items():
        output.append(f"=== Simulator Availability for {date} ===\n")
        all_events = []

        for sq, url in squadron_urls:
            try:
                pdf_path = download_pdf(url)

                # Check if the file is a valid PDF
                with open(pdf_path, "rb") as f:
                    if f.read(4) != b"%PDF":
                        raise ValueError("Not a valid PDF")

            except Exception:
                output.append(f"Schedule not available: {sq}\n")
                continue

            try:
                events = extract_sim_events(pdf_path)
                events = add_end_times(events)
                all_events.extend(events)
            except Exception:
                output.append(f"Schedule not available: {sq}\n")
                continue

        if not all_events:
            output.append("No valid events available for this date.\n")
            continue

        devices = group_by_device(all_events)

        for device, intervals in devices.items():
            merged = merge_intervals(intervals)
            gaps = find_gaps(merged, SIM_OPEN, SIM_CLOSE)
            output.append(f"Simulator {device} available:\n")
            if gaps:
                for g in gaps:
                    output.append(f"{g[0].strftime('%H:%M')} - {g[1].strftime('%H:%M')}\n")
            else:
                output.append("No available time slots.\n")

    return output

# Flask route
@app.route("/", methods=["GET", "POST"])
def index():
    schedule = []
    if request.method == "POST":
        schedule = fetch_schedule()
    return render_template("index.html", schedule=schedule)

if __name__ == "__main__":
    app.run(debug=True)