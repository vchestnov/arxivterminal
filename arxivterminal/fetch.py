import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from arxiv import Client, HTTPError, Search, SortCriterion, SortOrder

from arxivterminal.models import ArxivPaper

PAGE_SIZE = 100
DELAY_SECONDS = 3.0
NUM_RETRIES = 3
MAX_429_ATTEMPTS = 4
BASE_429_BACKOFF_SECONDS = 15.0


@dataclass
class FetchResult:
    papers: List[ArxivPaper]
    rate_limited: bool = False
    http_error_status: Optional[int] = None


@dataclass
class ApiCheckResult:
    ok: bool
    status_code: int
    message: str
    category: str


def _build_client() -> Client:
    return Client(
        page_size=PAGE_SIZE,
        delay_seconds=DELAY_SECONDS,
        num_retries=NUM_RETRIES,
    )


def _collect_papers(
    search: Search,
    start_date: datetime,
    end_date: datetime,
    max_results: int,
) -> List[ArxivPaper]:
    papers = []

    for i, result in enumerate(_build_client().results(search)):
        if max_results > 0 and i >= max_results:
            logging.info(f"Reached max results {max_results}")
            break

        paper = ArxivPaper(
            entry_id=result.entry_id,
            updated=result.updated,
            published=result.published,
            title=result.title,
            summary=result.summary,
            authors=[a.name for a in result.authors],
            categories=result.categories,
            viewed=False,
        )
        if start_date <= paper.published <= end_date:
            papers.append(paper)
        elif paper.published < start_date:
            logging.info(f"Reached start date {start_date}")
            break

    return papers


def download_papers(
    category: str, num_days: int, max_results: int = -1
) -> List[ArxivPaper]:
    return download_papers_with_status(
        category=category, num_days=num_days, max_results=max_results
    ).papers


def download_papers_with_status(
    category: str, num_days: int, max_results: int = -1
) -> FetchResult:
    """
    Download Arxiv papers from a specified category within the last `num_days`.

    Parameters
    ----------
    category : str
        The category to download papers from, e.g., 'cs.AI' for Artificial Intelligence.
    num_days : int
        The number of days to look back for downloading papers.
    max_results : int, optional, default=-1
        The maximum number of results to return. If -1, return all results.

    Returns
    -------
    List[ArxivPaper]
        A list of ArxivPaper objects representing the downloaded papers.
    """
    current_date = datetime.now(timezone.utc).date()

    start_date = datetime.combine(current_date, datetime.min.time()).replace(
        tzinfo=timezone.utc
    ) - timedelta(days=num_days - 1)
    end_date = datetime.combine(current_date, datetime.max.time()).replace(
        tzinfo=timezone.utc
    )
    logging.info(f"Query from {start_date} to {end_date}")

    search = Search(
        query=f"cat:{category}",
        sort_by=SortCriterion.SubmittedDate,
        sort_order=SortOrder.Descending,
    )

    for attempt in range(MAX_429_ATTEMPTS):
        try:
            papers = _collect_papers(search, start_date, end_date, max_results)
            logging.info(f"Found {len(papers)} papers")
            return FetchResult(papers=papers)
        except HTTPError as exc:
            if exc.status != 429:
                logging.warning(
                    "arXiv API returned HTTP %s for category %s. "
                    "Returning no papers for this category.",
                    exc.status,
                    category,
                )
                return FetchResult(papers=[], http_error_status=exc.status)

            if attempt == MAX_429_ATTEMPTS - 1:
                logging.warning(
                    "arXiv API returned HTTP 429 for category %s after %d attempts. "
                    "Returning no papers for this category.",
                    category,
                    MAX_429_ATTEMPTS,
                )
                return FetchResult(papers=[], rate_limited=True)

            backoff_seconds = BASE_429_BACKOFF_SECONDS * (2**attempt)
            logging.warning(
                "arXiv API returned HTTP 429 for category %s. Backing off %.1f "
                "seconds before retry %d/%d.",
                category,
                backoff_seconds,
                attempt + 2,
                MAX_429_ATTEMPTS,
            )
            time.sleep(backoff_seconds)

    return FetchResult(papers=[], rate_limited=True)


def check_api(category: str, max_results: int = 1) -> ApiCheckResult:
    search = Search(
        query=f"cat:{category}",
        max_results=max_results,
        sort_by=SortCriterion.SubmittedDate,
        sort_order=SortOrder.Descending,
    )

    try:
        list(_build_client().results(search))
    except HTTPError as exc:
        if exc.status == 429:
            return ApiCheckResult(
                ok=False,
                status_code=429,
                message="RATE LIMITED",
                category=category,
            )

        return ApiCheckResult(
            ok=False,
            status_code=exc.status,
            message=f"HTTP {exc.status}",
            category=category,
        )

    return ApiCheckResult(
        ok=True,
        status_code=200,
        message="OK",
        category=category,
    )
