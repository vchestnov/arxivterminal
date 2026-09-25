import logging
from pathlib import Path

import arxiv

from arxivterminal.models import ArxivPaper

PAGE_SIZE = 10
DELAY_SECONDS = 3.0
NUM_RETRIES = 3


class PaperDownloadError(Exception):
    pass


class PaperDownloadRateLimitError(PaperDownloadError):
    pass


def _build_client():
    return arxiv.Client(
        page_size=PAGE_SIZE,
        delay_seconds=DELAY_SECONDS,
        num_retries=NUM_RETRIES,
    )


def download_paper(paper: ArxivPaper, paper_dir: str = "/home/seva/docs/downloads"):
    """
    Downloads an Arxiv paper as PDF to the specified directory.

    Parameters
    ----------
    paper: ArxivPaper
        The paper to be downloaded.
    paper_dir: str
        The path where the paper will be saved. Defaults to ~/docs/downloads
        which means the PDFs will be stored relative to the current
        directory of the script.
    """
    id = paper.entry_id.split("/")[-1]
    file_name = f"{id}.pdf"
    paper_location = Path(paper_dir) / file_name

    if paper_location.exists():
        logging.info(f"Paper is already downloaded at {str(paper_location)}")
        raise FileExistsError
    else:
        paper_location.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = next(_build_client().results(arxiv.Search(id_list=[id])))
    except arxiv.HTTPError as exc:
        if exc.status == 429:
            raise PaperDownloadRateLimitError(
                "arXiv API rate-limited paper download metadata request"
            ) from exc
        raise PaperDownloadError(f"arXiv API returned HTTP {exc.status}") from exc

    result.download_pdf(dirpath=paper_dir, filename=file_name)
    logging.info(f"Saved paper to {str(paper_location)}")
