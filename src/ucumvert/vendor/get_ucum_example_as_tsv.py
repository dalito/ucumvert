import shutil
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

import openpyxl

SOURCE_FILE_URL = "https://github.com/ucum-org/ucum/raw/main/common-units/TableOfExampleUcumCodesForElectronicMessaging.xlsx"


def download_file(outdir: Path, url: str = SOURCE_FILE_URL) -> Path:
    """
    Download xlsx file from url to outdir and return filepath
    """
    filepath = outdir / Path(urlparse(url).path).name
    with urlopen(url) as response, filepath.open("wb") as out_file:  # noqa: S310
        shutil.copyfileobj(response, out_file)
    return filepath


def extract_examples_as_tsv(filepath: Path) -> None:
    """
    Extract first 4 columns of sheet "Example UCUM ..." as TSV file
    """
    wb = openpyxl.load_workbook(filepath)
    ws = next(ws for ws in wb.worksheets if ws.title.startswith("Example UCUM"))

    tsv = []
    for row in ws.iter_rows(min_row=2, max_col=4, max_row=ws.max_row):
        tsv.append(  # noqa: PERF401
            [
                (str(cell.value).replace("\n", "") if cell.value is not None else "")
                for cell in row
            ]
        )

    with Path(filepath.parent / "ucum_examples.tsv").open("w") as f:
        for row in tsv:
            f.write("\t".join(row) + "\n")


if __name__ == "__main__":
    outdir = Path(__file__).resolve().parent
    filepath = download_file(outdir)
    extract_examples_as_tsv(filepath)
