import logging
import sys
from datetime import datetime, timedelta

import click

from arxivterminal.constants import DATABASE_PATH, LOG_PATH
from arxivterminal.db import ArxivDatabase
from arxivterminal.fetch import check_api, download_papers_with_status
from arxivterminal.output import ExitAppException, print_papers, print_stats


@click.group()
def cli():
    """
    Main CLI entry point.
    """
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, filename=LOG_PATH)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


@click.command()
@click.option("--num-days", default=7, help="Number of days to fetch papers.")
@click.option(
    "--categories",
    default="hep-th,hep-ph",
    help="Comma-separated list of categories to fetch papers.",
)
def fetch(num_days, categories):
    """
    Fetch papers from the specified categories and store them in the database.
    """
    categories = categories.split(",")
    db = ArxivDatabase(DATABASE_PATH)
    for category in categories:
        logging.info(f"Fetching papers from {category}")
        result = download_papers_with_status(category, num_days=num_days)
        if result.rate_limited:
            click.echo(
                f"Skipped {category}: arXiv API rate-limited requests for this category."
            )
            continue

        if result.http_error_status is not None:
            click.echo(
                f"Skipped {category}: arXiv API returned HTTP "
                f"{result.http_error_status}."
            )
            continue

        db.save_papers(result.papers)


@click.command()
def delete_all():
    """
    Delete all papers from the database.
    """
    db = ArxivDatabase(DATABASE_PATH)
    db.delete_papers()


@click.command()
@click.option("--days-ago", default=7, help="Number of days ago to fetch papers.")
@click.option(
    "--categories",
    default="hep-th,hep-ph",
    help="Comma-separated list of categories to show.",
)
def show(days_ago, categories):
    """
    Show papers fetched from the specified number of days ago.
    """
    # categories = categories.split(",")
    categories = [c.strip() for c in categories.split(",") if c.strip()]
    published_after = datetime.now() - timedelta(days=days_ago)
    db = ArxivDatabase(DATABASE_PATH)
    papers = db.get_papers(published_after, categories=categories)

    try:
        print_papers(papers)
    except ExitAppException:
        sys.exit(0)


@click.command()
def stats():
    """
    Show statistics of the papers stored in the database.
    """
    db = ArxivDatabase(DATABASE_PATH)
    stats = db.get_stats()
    print_stats(stats)
    print(f"Log path: {LOG_PATH}")
    print(f"Data path: {DATABASE_PATH}")


@click.command(name="check-api")
@click.option("--category", default="math.AG", help="Category to probe.")
@click.option("--max-results", default=1, help="Number of results to request.")
def check_api_command(category, max_results):
    """
    Probe arXiv API and report rate-limit status for one category.
    """
    result = check_api(category=category, max_results=max_results)
    if result.ok:
        click.echo(
            f"{result.message}: arXiv API responded for {result.category} "
            f"(status {result.status_code})."
        )
        return

    if result.status_code == 429:
        click.echo(
            f"{result.message}: arXiv API rejected {result.category} "
            f"(status {result.status_code}). Try later or another network."
        )
        sys.exit(2)

    click.echo(
        f"{result.message}: arXiv API probe failed for {result.category} "
        f"(status {result.status_code})."
    )
    sys.exit(1)


@click.command()
@click.argument("query")
@click.option(
    "-l", "--limit", default=10, help="The maximum number of results to return"
)
def search(query, limit):
    """
    Search papers in the database based on a query.
    """
    db = ArxivDatabase(DATABASE_PATH)
    search_results = db.search_papers(query)[:limit]

    try:
        print_papers(search_results, show_dates=True)
    except ExitAppException:
        sys.exit(0)


for cmd in [check_api_command, delete_all, fetch, search, show, stats]:
    cli.add_command(cmd)

if __name__ == "__main__":
    cli()
