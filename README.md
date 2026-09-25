# Arxiv Terminal
![Tests](https://github.com/jbencina/arxivterminal/actions/workflows/main.yaml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/arxivterminal)](https://pypi.org/project/arxivterminal)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/arxivterminal)](https://pypi.org/project/arxivterminal)

Arxiv Terminal is a command-line interface (CLI) tool for fetching, searching, and displaying papers from the [arXiv](https://arxiv.org/) preprint repository. The tool allows you to fetch papers from specified categories, search the fetched papers, and display their statistics.

## Features

- Fetch paper abstracts from specified categories and save them in a local sqllite database.
- Show fetched papers and interatively open for more detailed abstracts
- Search fetched papers based on a query
- Download papers locally as PDF

![Demo](https://raw.githubusercontent.com/jbencina/arxivterminal/main/static/demo.gif)

## Contributors
A special call out to ChatGPT (v4) which helped write and modify various code and documentation in this repository.

## Installation

```bash
pip install arxivterminal
```

For local builds, you should have Poetry installed: [User Guide](https://python-poetry.org/docs/#installation). After
installation you may clone and build this repo:
```bash
poetry install
poetry shell
arxiv <command>

# Build the wheels
poetry build
```

## Usage

The CLI is invoked using the `arxiv` command, followed by one of the available commands:

- `arxiv fetch [--num-days] [--categories]`: Fetch papers from the specified categories and store them in the database.
- `arxiv delete_all`: Delete all papers from the database.
- `arxiv show [--days-ago]`: Show papers fetched from the specified number of days ago.
- `arxiv stats`: Show statistics of the papers stored in the database.
- `arxiv search <query>`: Search papers in the database based on a query.
- `arxiv check-api [--category] [--max-results]`: Probe arXiv API and report rate-limit status.

### Examples

Fetch papers from the "cs.AI" and "cs.CL" categories from the last 7 days:

```bash
arxiv fetch --num-days 7 --categories cs.AI,cs.CL
```

Delete all papers from database:

```bash
arxiv delete_all
```

Show papers fetched in the last 7 days

```bash
arxiv show --days-ago 7

# On this screen the user can select a paper for more
# details by typing a line number. Additional options
# allow for searching & downloading
```

Display statistics of the papers stored in the database:

```bash
arxiv stats
```

Show papers containing the phrase "deep learning":

```bash
arxiv search "deep learning"
```

Check whether arXiv is rate-limiting your current network/category:

```bash
arxiv check-api --category math.AG
```
