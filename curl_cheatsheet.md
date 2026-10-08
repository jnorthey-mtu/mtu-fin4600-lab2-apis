# Lab 2 · `curl` Cheat Sheet (macOS & Windows)

All endpoints were checked against provider documentation in September 2026. Unofficial endpoints
(Yahoo) can change without notice.

## Which command do I type?

| You are in… | Use | Why |
|---|---|---|
| macOS Terminal (zsh) | `curl` | Built in |
| Windows **Command Prompt** | `curl` | Windows 10 (1803+) and 11 ship the real `curl.exe` |
| Windows **PowerShell 5.1** | `curl.exe` | In Windows PowerShell, `curl` is an *alias* for `Invoke-WebRequest` and the flags below won't work |
| Windows PowerShell 7+ | `curl` or `curl.exe` | The alias was removed in PowerShell 7 |
| Any PowerShell, JSON pre-parsed | `Invoke-RestMethod "URL"` | Returns objects you can dot into: `(irm "URL").rates.EUR` |

**Quote every URL** — `&` means "run in background" to macOS shells and "next command" to `cmd.exe`.

## Useful flags

| Flag | Meaning |
|---|---|
| `-s` | silent (no progress bar) |
| `-i` | include response status line + headers |
| `-I` | HEAD request: headers only |
| `-v` | verbose: show request *and* response headers (great for learning HTTP) |
| `-A "text"` | set the User-Agent header |
| `-H "Name: value"` | add any header |
| `-o file.json` | save body to a file |
| `-g` | turn off curl's `[]{}` "globbing" (needed for `page[size]=` style parameters) |
| `-w "%{http_code}\n"` | print just the status code |
| `--compressed` | ask for gzip and decompress automatically |

## 1 · Currency exchange — Frankfurter (keyless, ECB reference rates)
```bash
curl -s "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR,CAD,JPY"
curl -s "https://api.frankfurter.dev/v1/2008-09-15?base=USD&symbols=EUR,JPY"        # historical
curl -s "https://api.frankfurter.dev/v1/2026-01-01..?base=USD&symbols=EUR"          # time series
```
PowerShell: `(Invoke-RestMethod "https://api.frankfurter.dev/v1/latest?base=USD").rates.EUR`

## 2 · Crypto — CoinGecko (keyless, IP-rate-limited)
```bash
curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd,eur"
curl -s "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=5"
# with a free Demo key (recommended in class — the keyless pool is shared by the whole room)
curl -s -H "x-cg-demo-api-key: YOUR_KEY" "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
```

## 3 · Stocks — Yahoo Finance v8 chart (unofficial, keyless, needs a browser User-Agent)
```bash
curl -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
  "https://query1.finance.yahoo.com/v8/finance/chart/F?range=5d&interval=1d"
```
Windows `cmd.exe` / PowerShell (one line):
```
curl.exe -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" "https://query1.finance.yahoo.com/v8/finance/chart/F?range=5d&interval=1d"
```
* Without `-A` you will often get **429 Edge: Too Many Requests**.
* The old `/v7/finance/quote` endpoint now answers **401 Unauthorized** to anonymous clients.
* `range`: 1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max · `interval`: 1m 5m 15m 1h 1d 1wk 1mo

## 4 · Stocks — Alpha Vantage (free key, 25 requests/day)
```bash
curl -s "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey=demo"
curl -s "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=YOUR_KEY"
```
⚠️ Errors and rate-limit messages arrive as **HTTP 200** with an `"Information"`, `"Note"` or
`"Error Message"` field in the JSON. `outputsize=full` and adjusted series are premium features.

## 5 · Economics — FRED (St. Louis Fed)
```bash
# Keyless CSV download
curl -s "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE" -o unrate.csv
# Official JSON API (free key)
curl -s "https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key=YOUR_KEY&file_type=json&sort_order=desc&limit=5"
```

## 6 · Filings — SEC EDGAR (keyless, User-Agent with contact info REQUIRED)
```bash
curl -s -A "Your Name your_uid@mtu.edu" "https://data.sec.gov/submissions/CIK0000037996.json"
curl -s -A "Your Name your_uid@mtu.edu" "https://www.sec.gov/files/company_tickers.json"
curl -s -A "Your Name your_uid@mtu.edu" "https://data.sec.gov/api/xbrl/companyfacts/CIK0000037996.json"
```
No contact info → **403 Forbidden**. Stay under 10 requests/second.

## 7 · Government finance — U.S. Treasury Fiscal Data (keyless)
```bash
curl -s -g "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?sort=-record_date&page[size]=1"
curl -s -g "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?sort=-record_date&page[size]=5"
# Same data, different encoding:
curl -s -g "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?sort=-record_date&page[size]=1&format=xml"
```

## 8 · Watching HTTP happen
```bash
curl -v  "https://api.frankfurter.dev/v1/latest" -o /dev/null      # macOS  (Windows: -o NUL)
curl -s -o /dev/null -w "%{http_code}\n" "https://httpbin.org/status/418"
curl -I "https://api.coingecko.com/api/v3/ping"
```

## Pretty-printing JSON
* macOS: `curl -s URL | python3 -m json.tool` (or `| jq .` if you install jq with `brew install jq`)
* Windows: `curl.exe -s URL | py -m json.tool` or `Invoke-RestMethod URL | ConvertTo-Json -Depth 5`
