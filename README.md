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

You need **[uv](https://docs.astral.sh/uv/)** (it installs Python for you), **Git**, and either **VS Code** or
**JupyterLab**. Do each step once.

### 1. Install the tools

<details>
<summary><b>Windows 10/11</b></summary>

1. **uv** (manages Python and the lab's packages) — in PowerShell:
   `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   (or `winget install astral-sh.uv`). You do **not** need to install Python separately.
2. **Git**: <https://git-scm.com/download/win> (accept the defaults) or `winget install Git.Git`.
3. **VS Code**: <https://code.visualstudio.com/>, then install the **Python** and **Jupyter** extensions
   from the Extensions panel (Ctrl+Shift+X).
4. Close and reopen PowerShell, then check: `uv --version` and `git --version`.
</details>

<details>
<summary><b>macOS</b></summary>

1. Open **Terminal** and run `xcode-select --install` (gives you Git and developer tools).
2. **uv** (manages Python and the lab's packages):
   `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`).
   You do **not** need to install Python separately.
3. **VS Code**: <https://code.visualstudio.com/>, then install the **Python** and **Jupyter** extensions (⌘⇧X).
4. Close and reopen Terminal, then check: `uv --version` and `git --version`.
</details>

### 2. Get the lab

```bash
git clone https://github.com/jnorthey-mtu/mtu-fin4600-lab2-apis.git
cd mtu-fin4600-lab2-apis
```

### 3. Install Python and the packages (one command)

Same on Windows and macOS, run inside the `mtu-fin4600-lab2-apis` folder:
```bash
uv sync
```
This reads `pyproject.toml`, downloads the right Python (pinned in `.python-version`) if you don't have it,
creates a `.venv` folder, and installs the exact package versions recorded in `uv.lock`.
No activation is needed — prefix commands with `uv run` (e.g. `uv run jupyter lab`).

Optional extras: `uv sync --extra yfinance` adds the `yfinance` library for comparison.

**Got an updated copy of the lab?** After `git pull`, run `uv sync` again to pick up any package changes.

### 4. Run the lab — pick **one** of these two ways

Both use the same `.venv` that `uv sync` created, so you can switch between them at any time.

#### Option A — Inside VS Code

1. Open VS Code → *File → Open Folder…* → choose the `mtu-fin4600-lab2-apis` folder.
   If asked *“Do you trust the authors?”*, click **Yes**.
2. In the Explorer panel (left), click **`lab2_apis.ipynb`**. It opens as a notebook.
3. Click **Select Kernel** (top right) → **Python Environments** → **`.venv`**
   (it shows `.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS).
   *Don't see `.venv`?* Run `uv sync` in the VS Code terminal (*Terminal → New Terminal*), then
   *Ctrl+Shift+P* (⌘⇧P on macOS) → **Developer: Reload Window** and try again.
4. Run cells with **Shift+Enter**, or **Run All** in the toolbar. Start with the *Setup* cell.
5. If something gets stuck, click **Restart** in the notebook toolbar, then run the cells again from the top.

VS Code remembers the kernel for this notebook, so next time just open the folder and the notebook.

#### Option B — JupyterLab in your web browser

1. Open a terminal **in the lab folder**:
   * Windows: PowerShell, then `cd` to the folder (e.g. `cd $HOME\mtu-fin4600-lab2-apis`).
   * macOS: Terminal, then `cd ~/mtu-fin4600-lab2-apis`.
   * Or, in VS Code: *Terminal → New Terminal* (it already starts in the lab folder).
2. Start JupyterLab:
   ```bash
   uv run jupyter lab
   ```
   Your browser opens at `http://localhost:8888/lab`. If it doesn't, copy the
   `http://localhost:8888/lab?token=…` link printed in the terminal into your browser.
3. Double-click **`lab2_apis.ipynb`** in the file browser on the left. The kernel is already the
   lab's `.venv`, so you don't need to choose one.
4. Run cells with **Shift+Enter**, or use *Run → Run All Cells*. To restart: *Kernel → Restart Kernel…*.
5. **To stop:** save your work (*Ctrl+S* / ⌘S), close the browser tab, then press **Ctrl+C** in the
   terminal (press it twice if asked). Leave the terminal open while you work, because closing it stops JupyterLab.

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
| Sliders don't appear | Front-end lacks widget support | Run `uv sync`, restart the kernel; or use the static cells |
| `ModuleNotFoundError` | Wrong kernel or packages not installed | Select the `.venv` kernel; re-run `uv sync`, then restart the kernel |
| `uv` not found | Terminal opened before uv was installed | Close and reopen the terminal (or VS Code) |

## Repository layout
```
lab2_apis.ipynb        ← the lab (start here)
curl_cheatsheet.md     ← command-line reference for macOS & Windows
helpers/http.py        ← polite fetch(): caching, retries, back-off
helpers/market.py      ← Yahoo chart endpoint → pandas; synthetic fallback
helpers/encodings.py   ← JSON / XML / Protobuf / Avro / MessagePack / CBOR encoders
pyproject.toml         ← dependencies (managed by uv)
uv.lock                ← exact pinned versions — commit it, don't edit by hand
.python-version  .env.example  .gitignore
```

## Terms of use
Yahoo Finance has no official public API; the lab calls the endpoint Yahoo's own web pages use, for
educational purposes only. Respect each provider's terms, rate limits, and attribution requirements
(CoinGecko's free tier requires attribution). Nothing here is investment advice.
