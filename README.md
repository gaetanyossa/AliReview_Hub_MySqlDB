```markdown
# AliReview Hub – Universal Review Scraper & WordPress Importer

<img src="img/img.png" alt="Streamlit dashboard preview" width="700"/>

---

## Overview

**AliReview Hub** is a modular toolset to:

- Scrape product reviews from AliExpress (more platforms coming soon)
- Clean, anonymize, or rename review authors
- Inject reviews directly into a WordPress database
- All from a user-friendly [Streamlit](https://streamlit.io/) interface — no CLI required

Each operation is handled by a Python script automatically detected and exposed in the UI.

---

## Project Structure

```

ALIREVIEW\_HUB/
├── img/
│   └── img.png
├── scripts/
│   ├── extract\_reviews.py
│   ├── insert\_reviews.py
│   ├── modify\_reviews.py
│   ├── rename\_authors.py
│   └── replace\_word.py
├── streamlit\_app.py
├── requirements.txt
└── README.md

````

---

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
````

### 2. Launch the app

```bash
streamlit run streamlit_app.py
```

### 3. Add your own scripts

Any Python file added to the `scripts/` folder is automatically loaded into the dashboard with its arguments mapped to interactive form fields.

---

## Key Features

| Module               | Purpose                                                             |
| -------------------- | ------------------------------------------------------------------- |
| `extract_reviews.py` | Scrape reviews from AliExpress to CSV                               |
| `insert_reviews.py`  | Import CSV reviews into WordPress (`wp_comments`, `wp_commentmeta`) |
| `modify_reviews.py`  | Rename authors for low-rated reviews (e.g. < 4★)                    |
| `rename_authors.py`  | Replace generic names like “AliExpress Shopper”                     |
| `replace_word.py`    | Replace words in reviews (e.g. "aliexpress" → "YourBrand")          |

Each script uses `argparse` with a `cli()` function. Streamlit automatically converts arguments into form inputs.

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

<img src="img/img.png" width="720"/>

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
Ensure each new script provides a `cli(parser)` interface for automatic integration.

---

## License

MIT – free to use and modify.

```
```
