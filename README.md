# GARLEB Desk

Morning trade intelligence for a mid-size pasta trader. Built for GARLEB (Dubai / Beirut, Garofalo / Ebro) as a public-data desk they can show before anyone approves a licensed feed.

**Run it here:** API `:8011` · UI `:5171` · path `~/Norfront/demos/garleb-trade-intel` (symlink to this repo).

```bash
make setup
make refresh    # pulls live public sources into backend/data/snapshot
make dev        # uvicorn :8011 + vite :5171
make test
```

## What it is

A ranked **Morning Brief** (why it matters / what to do), a grounded **Ask the Desk**, and views for markets, prices, freight, policy and sources. The moat is not a chatbot. It is the **intel layer**:

- Scattered government and agency sources (WFP retail, Saudi GASTAT monthly, TİM Turkish exports, RASFF, FDA, Resmî Gazete, Lebanon PPA, TR/AR/IT press) fused with Comext, Comtrade, PortWatch, CCFI, Federal Register and sanctions lists.
- A reconciled **share nowcast** per market.
- Trader-specific indicators: landed-cost ladder, lane stress, shelf vs CIF, Turkish price pressure, quality and tender radar.
- History we keep (weekly freight, daily ports, tenders, alerts). The longer it runs, the deeper the book.

TradeInt, Drewry and GARLEB's own files are **slots**. The NDA says they approve providers first. There is **no synthetic shipment data** and **no GARLEB data**.

## Hard lines

- No real GARLEB files, books or counterparties.
- Outbound HTTP only to listed public endpoints, with generic queries.
- `APPROVED_PROVIDERS` is empty. The Ask engine is deterministic. An OpenAI-compatible / Ollama client exists but will not fire until they approve a name.

## Stack

Python 3.12, FastAPI, DuckDB/Parquet, React + Vite + Tailwind. Snapshot is committed so the demo works offline.

## Sources (live in this build)

| Source | What we take |
| --- | --- |
| Eurostat Comext | Italy monthly pasta / semolina / tomato exports |
| UN Comtrade public preview | Annual + monthly + mirrors for non-reporters |
| EU agri-food | Weekly durum (Foggia, Bologna, …) |
| FRED / IMF | Wheat |
| FAO | Food Price Index |
| ECB + open.er-api | FX |
| IMF PortWatch | Daily Hormuz, Suez, Jebel Ali, Jeddah, Beirut, Mombasa, … |
| Shanghai Shipping Exchange | CCFI / SCFI weekly |
| Federal Register | Italy pasta AD/CVD + OFAC notices |
| OFAC / UN / UK OFSI | Screening names |
| WFP via HDX | Retail pasta & tomato, Lebanon / Syria / Somalia / Kenya / Yemen |
| GASTAT via DataSaudi | Monthly Saudi chapter-19 by partner |
| TİM | Monthly Turkish cereals-sector exports by country (Sep 2026) |
| RASFF Window | Pasta / semolina / tomato alerts |
| openFDA | US food recalls |
| Resmî Gazete | Wheat / pasta / inward-processing / asset-freeze headlines |
| Lebanon PPA | Public tenders |
| Google News RSS | EN / TR / IT / AR packs |

Slots (not connected): US Census (free key), ePing, Comtrade Plus, USDA GAIN, AIS, UNGM, KAP, Kenya Gazette PDFs, SCA circulars, geo-blocked Levant/Gulf/Kenya portals (regional relay), TradeInt, Drewry.

## Profiles

`backend/profiles/garleb.yaml` is a demo profile from the public brief only. `nairobi.yaml` and `gulf.yaml` show the resale story.

## Ask

Plain language. Intents: who / trend / price / freight / policy / sanctions / shelf / news / what-to-do. Answers carry tables, sources and follow-ups.
