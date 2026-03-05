import requests
from pathlib import Path


def download_pdf(url, folder="pdfs"):

    Path(folder).mkdir(exist_ok=True)

    filename = url.split("/")[-1]
    filepath = Path(folder) / filename

    r = requests.get(url)

    with open(filepath, "wb") as f:
        f.write(r.content)

    return filepath