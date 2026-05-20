from __future__ import annotations

import zipfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup


DETAILS_URL = "https://korpus.dsl.dk/resources/details/freq-lemmas.html"
DEFAULT_ZIP_URL = "https://korpus.dsl.dk/download/lemma-10k.zip"


def discover_download_url(details_url: str = DETAILS_URL) -> str:
    """Return the ZIP URL from the DSL details/licence pages, with a stable fallback."""
    try:
        response = requests.get(details_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.endswith(".zip"):
                return href
    except requests.RequestException:
        pass
    return DEFAULT_ZIP_URL


def download_and_extract(data_dir: Path) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    zip_url = discover_download_url()
    zip_path = data_dir / "lemma-frequency-source.zip"

    response = requests.get(zip_url, timeout=60)
    response.raise_for_status()
    zip_path.write_bytes(response.content)

    with zipfile.ZipFile(zip_path) as archive:
        txt_names = [name for name in archive.namelist() if name.lower().endswith(".txt")]
        if not txt_names:
            raise RuntimeError("No .txt frequency list found in downloaded ZIP.")
        source_name = txt_names[0]
        source_path = data_dir / Path(source_name).name
        source_path.write_bytes(archive.read(source_name))

    return source_path
