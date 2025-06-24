# AliReview Hub – Universal Review Scraper & WordPress Importer

![Streamlit dashboard preview](img/img.png)

---

## Overview

**AliReview Hub** is a modular toolset that allows you to:

* Scrape product reviews from AliExpress (more platforms coming soon)
* Clean, anonymize, or rename review authors
* Inject reviews directly into a WordPress database
* Operate entirely from a user-friendly [Streamlit](https://streamlit.io/) interface — no CLI required

Each operation is handled by an independent Python script, auto-detected and exposed as a form in the dashboard.

---

## Project Structure

```txt
ALIREVIEW_HUB/
├── img/                      # UI screenshots
│   └── img.png
├── scripts/                  # Auto-discovered backend tools
│   ├── extract_reviews.py
│   ├── insert_reviews.py
│   ├── modify_reviews.py
│   ├── rename_authors.py
│   └── replace_word.py
├── streamlit_app.py          # ⇨ Main dashboard
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch the app

```bash
streamlit run streamlit_app.py
```

### 3. Add your own scripts

Any Python file added to the `scripts/` folder will be auto-detected and exposed in the UI, with arguments mapped to input fields.

---

## Key Features

| Module               | Purpose                                                             |
| -------------------- | ------------------------------------------------------------------- |
| `extract_reviews.py` | Scrape reviews from AliExpress and export to CSV                    |
| `insert_reviews.py`  | Import CSV reviews into WordPress (`wp_comments`, `wp_commentmeta`) |
| `modify_reviews.py`  | Rename authors for reviews below a certain rating (e.g. < 4★)       |
| `rename_authors.py`  | Replace default names like "AliExpress Shopper"                     |
| `replace_word.py`    | Replace specific words in reviews (e.g. "aliexpress" → "YourBrand") |

Each script uses `argparse` and exposes a `cli()` function. Streamlit automatically maps arguments to form fields.

---

## WordPress / MySQL Integration

Enter your database credentials once in the sidebar. They’ll be reused across all compatible tools.

Supports:

* Any WordPress table prefix (`--prefix`)
* Custom meta keys (`--rating-key`, `--verified-key`, etc.)
* Dry-run mode to preview changes before applying

---

## Requirements

```txt
streamlit
pymysql
httpx
faker
pandas
```

Included in [`requirements.txt`](requirements.txt)

---

## UI Preview

![Streamlit dashboard preview](img/img.png)

---

## To-do / Suggestions

* [ ] Add support for Temu / Amazon
* [ ] Add cron scheduler
* [ ] Export to JSON or SQLite
* [ ] Toggle visibility for advanced parameters
* [ ] Optional login/auth for dashboard

---

## Contributions

Forks and improvements are welcome.
Make sure each new script provides a `cli(parser)` interface for automatic integration.

---

## License

MIT – free to use and modify.
