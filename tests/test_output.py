from datetime import datetime
from types import SimpleNamespace

import pytest

from arxivterminal.db import ArxivStats
from arxivterminal.download import PaperDownloadRateLimitError
from arxivterminal.output import print_papers, print_stats


@pytest.fixture
def test_stats():
    return [
        ArxivStats(date="2023-01-01", count=5),
        ArxivStats(date="2023-01-02", count=3),
        ArxivStats(date="2023-01-03", count=2),
    ]


def test_print_stats(capsys, test_stats):
    print_stats(test_stats)

    captured = capsys.readouterr()
    output = captured.out.splitlines()

    assert output[0] == "Date       | Count"
    assert output[1] == "-------------------"
    assert output[2] == "2023-01-01 | 5"
    assert output[3] == "2023-01-02 | 3"
    assert output[4] == "2023-01-03 | 2"
    assert output[5] == "-------------------"
    assert output[6] == "Total count: 10"


def test_print_papers_shows_download_rate_limit_note(monkeypatch, capsys):
    paper = SimpleNamespace(
        entry_id="http://arxiv.org/abs/1234.5678",
        updated=datetime.now(),
        published=datetime.now(),
        title="Test Paper",
        summary="Summary",
        authors=["Author One"],
        categories=["math.AG"],
        viewed=False,
    )

    inputs = iter(["1", "d", "q"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
    monkeypatch.setattr(
        "arxivterminal.output.download_paper",
        lambda _paper: (_ for _ in ()).throw(PaperDownloadRateLimitError("429")),
    )

    class DummyDb:
        def mark_paper_viewed(self, _paper):
            pass

    monkeypatch.setattr("arxivterminal.output.ArxivDatabase", lambda _path: DummyDb())

    with pytest.raises(Exception) as exc_info:
        print_papers([paper], show_dates=False)

    assert exc_info.type.__name__ == "ExitAppException"
    output = capsys.readouterr().out
    assert "Download skipped: arXiv API rate-limited request. Try later." in output
