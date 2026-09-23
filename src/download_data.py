"""Download the public UCI Online Retail workbook without committing it."""

from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile


DATASET_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
RAW_DIR = Path("data/raw")
ZIP_PATH = RAW_DIR / "online-retail.zip"
WORKBOOK_PATH = RAW_DIR / "Online Retail.xlsx"


def download_source(force: bool = False) -> Path:
    """Download and extract the official UCI workbook to the ignored raw-data folder."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if WORKBOOK_PATH.exists() and not force:
        return WORKBOOK_PATH

    request = Request(DATASET_URL, headers={"User-Agent": "ecommerce-sales-analytics/1.0"})
    with urlopen(request, timeout=60) as response, ZIP_PATH.open("wb") as output:
        output.write(response.read())

    with ZipFile(ZIP_PATH) as archive:
        member = next((name for name in archive.namelist() if name.endswith("Online Retail.xlsx")), None)
        if member is None:
            raise ValueError("The UCI archive did not contain Online Retail.xlsx")
        with archive.open(member) as source, WORKBOOK_PATH.open("wb") as output:
            output.write(source.read())
    return WORKBOOK_PATH


if __name__ == "__main__":
    print(download_source())
