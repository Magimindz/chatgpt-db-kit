# ChatGPT Database Kit

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SQLite](https://img.shields.io/badge/sqlite-3-lightgrey.svg)](https://www.sqlite.org/index.html)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A lightweight toolkit for building and searching a local ChatGPT conversation database.  
Easily transform exported ChatGPT JSON into a searchable SQLite database with full-text search (FTS).

## ✨ Features
- 📦 Build a searchable **SQLite database** from ChatGPT export data.  
- 🔍 Query the database with custom Python scripts.  
- 📊 Extendable for **analysis** and **visualization** workflows.  
- ⚡ Includes optional **full-text search** (FTS5) for faster queries. 

## ⚙️ Requirements
- Python **3.8+**
- SQLite3 (bundled with Python)

## 🚀 Installation

Clone the repository:

```bash
git clone git@github.com:Magimindz/chatgpt-db-kit.git
cd chatgpt-db-kit
```

## Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate   # On Windows PowerShell
```

## Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Build the database:

```bash
python build_chatgpt_db.py "C:\path\to\conversations.json" --out chatgpt.db
```

Search the database:

```bash
python search_chatgpt_db.py "your query"
```

## Maintenance

If you see:

```
sqlite3.OperationalError: no such table: messages_fts
```

Rebuild the full-text search (FTS) index:

```bash
python rebuild_fts.py
```