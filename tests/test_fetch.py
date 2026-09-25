from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from arxiv import HTTPError

from arxivterminal import fetch


class FakeClient:
    def __init__(self, results_fn):
        self._results_fn = results_fn

    def results(self, search):
        return self._results_fn(search)


def _paper_result(days_ago: int):
    now = datetime.now(timezone.utc)
    published = now - timedelta(days=days_ago)
    return SimpleNamespace(
        entry_id=f"http://arxiv.org/abs/{days_ago}",
        updated=published,
        published=published,
        title=f"Paper {days_ago}",
        summary="summary",
        authors=[SimpleNamespace(name="Author")],
        categories=["math.AG"],
    )


def test_download_papers_handles_429_gracefully(monkeypatch):
    def fake_results(_search):
        raise HTTPError("https://export.arxiv.org/api/query", 0, 429)
        yield

    monkeypatch.setattr(fetch, "_build_client", lambda: FakeClient(fake_results))
    sleeps = []
    monkeypatch.setattr(fetch.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = fetch.download_papers_with_status("math.AG", num_days=2)

    assert result.papers == []
    assert result.rate_limited is True
    assert sleeps == [15.0, 30.0, 60.0]


def test_download_papers_handles_406_gracefully(monkeypatch):
    def fake_results(_search):
        raise HTTPError("https://export.arxiv.org/api/query", 0, 406)
        yield

    monkeypatch.setattr(fetch, "_build_client", lambda: FakeClient(fake_results))

    result = fetch.download_papers_with_status("math.AG", num_days=2)

    assert result.papers == []
    assert result.rate_limited is False
    assert result.http_error_status == 406


def test_download_papers_filters_to_requested_window(monkeypatch):
    def fake_results(_search):
        yield _paper_result(days_ago=0)
        yield _paper_result(days_ago=1)
        yield _paper_result(days_ago=3)

    monkeypatch.setattr(fetch, "_build_client", lambda: FakeClient(fake_results))

    papers = fetch.download_papers("math.AG", num_days=2)

    assert len(papers) == 2
