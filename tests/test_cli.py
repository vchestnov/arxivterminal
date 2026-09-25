from click.testing import CliRunner

from arxivterminal.cli import check_api_command, fetch
from arxivterminal.fetch import ApiCheckResult, FetchResult


def test_fetch_prints_rate_limit_note(monkeypatch):
    monkeypatch.setattr(
        "arxivterminal.cli.download_papers_with_status",
        lambda _category, num_days: FetchResult(papers=[], rate_limited=True),
    )

    class DummyDb:
        def __init__(self, _path):
            self.saved = []

        def save_papers(self, papers):
            self.saved.append(papers)

    monkeypatch.setattr("arxivterminal.cli.ArxivDatabase", DummyDb)

    result = CliRunner().invoke(fetch, ["--num-days", "2", "--categories", "math.AG"])

    assert result.exit_code == 0
    assert (
        "Skipped math.AG: arXiv API rate-limited requests for this category."
        in result.output
    )


def test_fetch_skips_http_406(monkeypatch):
    monkeypatch.setattr(
        "arxivterminal.cli.download_papers_with_status",
        lambda _category, num_days: FetchResult(papers=[], http_error_status=406),
    )

    class DummyDb:
        def __init__(self, _path):
            self.saved = []

        def save_papers(self, papers):
            self.saved.append(papers)

    monkeypatch.setattr("arxivterminal.cli.ArxivDatabase", DummyDb)

    result = CliRunner().invoke(fetch, ["--num-days", "2", "--categories", "math.AG"])

    assert result.exit_code == 0
    assert "Skipped math.AG: arXiv API returned HTTP 406." in result.output


def test_check_api_reports_ok(monkeypatch):
    monkeypatch.setattr(
        "arxivterminal.cli.check_api",
        lambda category, max_results: ApiCheckResult(
            ok=True,
            status_code=200,
            message="OK",
            category=category,
        ),
    )

    result = CliRunner().invoke(check_api_command, ["--category", "math.AG"])

    assert result.exit_code == 0
    assert "OK: arXiv API responded for math.AG (status 200)." in result.output


def test_check_api_reports_rate_limited(monkeypatch):
    monkeypatch.setattr(
        "arxivterminal.cli.check_api",
        lambda category, max_results: ApiCheckResult(
            ok=False,
            status_code=429,
            message="RATE LIMITED",
            category=category,
        ),
    )

    result = CliRunner().invoke(check_api_command, ["--category", "math.AG"])

    assert result.exit_code == 2
    assert (
        "RATE LIMITED: arXiv API rejected math.AG (status 429). "
        "Try later or another network."
    ) in result.output
