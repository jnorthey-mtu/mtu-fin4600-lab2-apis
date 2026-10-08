# mtu-fin4600-lab2-apis
**FIN 4600 · Financial Technology Foundations · Michigan Technological University**
**Lab 2 — Talking to Markets: Financial APIs from the URL up**

Welcome to the Husky Capital Quant Desk. In this lab you will call real financial APIs, turn their JSON into
pandas DataFrames, chart the results, and build an interactive stock screener of Michigan companies.

| Mission | Topic | APIs used |
|---|---|---|
| 1 | Anatomy of an HTTP request | Frankfurter (FX rates) |
| 2 | Status Code Safari | Frankfurter, CoinGecko, SEC, Yahoo, Alpha Vantage, httpbin |
| 3 | Crypto market pulse (treemap + movers) | CoinGecko |
| 4 | Candlestick charts straight from a URL | Yahoo Finance v8 chart |
| 5 | **The Mitten Screener** (interactive) | Yahoo Finance + FRED |
| 6 | Yield-curve recession signal | FRED |
| 7 | Company filings as data | SEC EDGAR |
| 8 | Encoding face-off: JSON vs XML vs Protobuf vs Avro | — |

---

## Setup — step by step

You need **Python 3.11 or newer**, **Git**, and either **VS Code** or **JupyterLab**. Do each step once.

### 1. Install the tools

<details>
<summary><b>Windows 10/11</b></summary>

1. **Python**: download from <https://www.python.org/downloads/>. On the first installer screen, tick
   **“Add python.exe to PATH”**, then *Install Now*. (Or in PowerShell: `winget install Python.Python.3.13`.)
2. **Git**: <https://git-scm.com/download/win> (accept the defaults) or `winget install Git.Git`.
3. **VS Code**: <https://code.visualstudio.com/>, then install the **Python** and **Jupyter** extensions
   from the Extensions panel (Ctrl+Shift+X).
4. Close and reopen PowerShell, then check: `py --version` and `git --version`.
</details>

<details>
<summary><b>macOS</b></summary>

1. Open **Terminal** and run `xcode-select --install` (gives you Git and developer tools).
2. **Python**: download from <https://www.python.org/downloads/> and run the installer
   (or `brew install python` if you use Homebrew).
3. **VS Code**: <https://code.visualstudio.com/>, then install the **Python** and **Jupyter** extensions (⌘⇧X).
4. Check: `python3 --version` and `git --version`.
</details>

### 2. Get the lab

```bash
git clone https://github.com/jnorthey-mtu/mtu-fin4600-lab2-apis.git
cd mtu-fin4600-lab2-apis
```

### 3. Create a virtual environment and install packages

**Windows (PowerShell)**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
If PowerShell says *running scripts is disabled*, run this once and try again:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**macOS (Terminal)**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```
Your prompt now starts with `(.venv)`. Activate it again every time you open a new terminal.

### 4. Open the notebook

* **VS Code:** *File → Open Folder* → `mtu-fin4600-lab2-apis`, open `lab2_apis.ipynb`, click
  **Select Kernel** (top right) → **Python Environments** → `.venv`.
* **JupyterLab:** with the venv active, run `jupyter lab` and open `lab2_apis.ipynb` in the browser tab.

### 5. (Optional) API keys
Everything works without keys. Free keys give you higher limits:
```bash
cp .env.example .env          # macOS
copy .env.example .env        # Windows
```
Edit `.env` and paste your keys. `.env` is listed in `.gitignore` — **never commit it.**

---

## Before class: try the command line
See **[curl_cheatsheet.md](curl_cheatsheet.md)** for tested `curl` commands for every API on macOS and Windows.
Windows PowerShell users: type **`curl.exe`**, not `curl`.

## Troubleshooting

| Symptom | Meaning | Fix |
|---|---|---|
| `429 Too Many Requests` | Rate limit hit — often because the whole class shares one campus IP | Wait 60 s and re-run; results are cached after the first success. For CoinGecko, add a free Demo key |
| `403 Forbidden` from SEC | No contact info in your User-Agent | Set `YOUR_NAME` / `YOUR_EMAIL` in the Setup cell |
| `401 Unauthorized` from Yahoo v7 | That endpoint is retired for anonymous use | Use the v8 `chart` endpoint (as the lab does) |
| `⚠️ … Using SYNTHETIC prices` | Yahoo refused or the network is down; the lab substituted random-walk data so you can keep going | Re-run later with `clear_cache()`; synthetic numbers are **not real prices** |
| Alpha Vantage data is missing but status is 200 | Errors arrive inside a 200 response | Read the `"Information"` / `"Note"` field |
| Sliders don't appear | Front-end lacks widget support | `pip install ipywidgets`, restart; or use the static cells |
| `ModuleNotFoundError` | Wrong kernel or packages not installed | Select the `.venv` kernel; re-run `pip install -r requirements.txt` |

## Repository layout
```
lab2_apis.ipynb        ← the lab (start here)
curl_cheatsheet.md     ← command-line reference for macOS & Windows
helpers/http.py        ← polite fetch(): caching, retries, back-off
helpers/market.py      ← Yahoo chart endpoint → pandas; synthetic fallback
helpers/encodings.py   ← JSON / XML / Protobuf / Avro / MessagePack / CBOR encoders
requirements.txt  .env.example  .gitignore
```

## Terms of use
Yahoo Finance has no official public API; the lab calls the endpoint Yahoo's own web pages use, for
educational purposes only. Respect each provider's terms, rate limits, and attribution requirements
(CoinGecko's free tier requires attribution). Nothing here is investment advice.
