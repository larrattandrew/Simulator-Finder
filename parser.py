import pdfplumber
import re


def extract_sim_events(pdf_path):

    events = []

    with pdfplumber.open(pdf_path) as pdf:

        text = ""

        for page in pdf.pages:
            text += page.extract_text() + "\n"

    pattern = re.compile(r"\b(\d{4})\s+(\d{4})\s+(\d{3})\b")

    matches = pattern.findall(text)

    for match in matches:

        brief = match[0]
        sched_to = match[1]
        device = match[2]

        events.append({
            "device": device,
            "start": sched_to
        })

    return events