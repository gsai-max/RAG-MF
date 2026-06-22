# Project Context: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview
The goal of this project is to build a lightweight, facts-only FAQ assistant for mutual fund schemes, utilizing **Groww** as the reference product context. The assistant will answer objective, verifiable queries about mutual funds by retrieving information exclusively from ICICI Prudential Mutual Fund scheme pages on Groww.

The system must strictly avoid providing investment advice, opinions, recommendations, or performance comparisons. Every response must include a single, clear source link from the corpus (or educational links for refusals) and adhere to strict constraints around brevity, accuracy, and compliance.

---

## Objectives
- **Factual Q&A**: Design and implement a lightweight Retrieval-Augmented Generation (RAG)-based assistant that answers factual queries about mutual fund schemes.
- **Curated Corpus**: Utilize an active corpus of ICICI Prudential Mutual Fund scheme pages.
- **Source-Backed Responses**: Provide concise, source-backed responses with citation links (supporting multiple citation links when multiple funds are selected) and a last-updated footer.

---

## Target Users
1. **Retail Investors**: Individuals looking to compare mutual fund schemes based on factual metrics.
2. **Internal Teams (Customer Support / Content)**: Staff handling repetitive, factual customer queries about mutual fund details and processes.

---

## Scope of Work

### 1. Corpus Definition
The assistant is scoped to the **110 ICICI Prudential Mutual Fund scheme pages on Groww** listed in [icici_funds_list.md](file:///c:/Nextleap%20Projects%20Git/RAGMF/docs/icici_funds_list.md). The crawler will target and parse all the scheme detail pages listed in that index.
*(Note: Because of URL aliasing/duplication on Groww, these 110 URLs consolidate into **104 unique schemes** inside the database index.)*

### 2. FAQ Assistant Requirements
The assistant must answer objective and verifiable queries. The chatbot must store and reply to the following data:
- **Core fund identity**: Scheme name, AMC (fund house), scheme code/ISIN, Category (equity/debt/hybrid), sub-category (large cap, mid cap, liquid, etc.), Plan type (Direct/Regular), option (Growth/IDCW), Benchmark index, Fund manager name(s) & tenure, Inception/launch date.
- **Performance & pricing**: NAV (current + historical time series), Returns: 1M, 3M, 6M, 1Y, 3Y, 5Y, since inception (absolute & CAGR), Rolling returns, Benchmark comparison returns.
- **Cost**: Expense ratio (Direct vs Regular), Exit load & exit load period, Entry load.
- **Risk metrics**: Standard deviation, Sharpe ratio, Sortino ratio, Beta, Alpha, Riskometer level (Low/Moderate/High/Very High).
- **Portfolio composition**: AUM (fund size) — historical too, since it changes monthly, Top holdings (stock/bond name, % allocation), Sector allocation %, Market cap split (large/mid/small for equity funds), Credit rating breakup (for debt funds), Average maturity, modified duration, YTM (for debt funds), Portfolio turnover ratio.
- **Other operational data**: Minimum investment (lumpsum/SIP), SIP dates available, Lock-in period (for ELSS etc.), Taxation rules applicable, Fund objective/investment strategy.

#### Response Format Constraints
- **Length**: Maximum of 3 sentences per response.
- **Citation**: Clickable citation link(s) pointing to the relevant Groww scheme page(s) (supporting multiple source links if multiple funds are selected).
- **Footer**: Every response must include the footer:
  `Last updated from sources: <date>` (using the page fetch/parse date)

### 3. Refusal & Out-of-Scope Handling
The assistant must politely refuse any query that is advisory, subjective, or speculative.
- **Examples of Refusals**:
  - *"Should I invest in this fund?"*
  - *"Which fund is better?"*
  - *"What returns will I get?"*
- **Refusal Response Checklist**:
  - Must be polite and clearly worded.
  - Must reinforce the facts-only limitation.
  - Must provide a relevant educational link:
    - [AMFI — Mutual Funds](https://www.amfiindia.com/)
    - [SEBI — Investor Education](https://investor.sebi.gov.in/)

### 4. User Interface (Minimal)
A simple, clean UI that includes:
- A welcome message
- Three clickable example questions:
  1. *What is the expense ratio of ICICI Prudential Large Cap Fund?*
  2. *What is the exit load on ICICI Prudential Commodities Fund?*
  3. *Who manages ICICI Prudential Technology Direct Plan-Growth?*
- A visible disclaimer snippet:
  > **Facts-only. No investment advice.**

---

## Key Constraints

### Data & Sources
- Use **only** the ICICI Prudential Mutual Fund scheme pages on Groww as the source corpus.
- Do **not** use external search engines or third-party blogs.

### Privacy & Security
To ensure regulatory compliance and user security, the system must **never** collect, store, or process:
- Permanent Account Number (PAN) or Aadhaar numbers
- Account/Portfolio numbers
- One-Time Passwords (OTPs)
- Personally Identifiable Information (PII) such as email addresses or phone numbers
- The application must remain completely stateless with no persistence of user chat history.

### Content Restrictions
- **No investment advice** or opinions.
- **No subjective performance comparisons** or speculative return projections. Factual historical returns (1M, 3M, 6M, 1Y, 3Y, 5Y, since inception), NAV, and rolling returns from the corpus are allowed.
- For speculative or subjective comparison queries, refuse or refer the user to the scheme page URL.

### Transparency
- Responses must be short, factual, and verifiable.
- A valid source link and last updated date are mandatory for every response.

---

## Expected Deliverables
1. **README Document** containing:
   - Setup and installation instructions.
   - The selected schemes included in the corpus.
   - An architectural overview detailing the RAG approach.
   - Known limitations.
2. **Disclaimer Snippet** visible on the UI:
   - `“Facts-only. No investment advice.”`
3. **Interactive React Dashboard**:
   - Single-page application built inside `frontend/` using Vite, React, TypeScript, and Tailwind CSS.
   - Responsive modal selection list mapping all active schemes, supporting multi-fund filtering by passing selected fund slugs to the backend to constrain retrieval precisely.
4. **Daily Ingestion Scheduler**:
   - Deployed as a GitHub Actions workflow ([daily-scheduler.yml](file:///c:/Nextleap%20Projects%20Git/RAGMF/.github/workflows/daily-scheduler.yml)). It runs automatically on pushes to the `main` branch or daily at 9:15 AM IST (03:45 UTC).
   - Features performance caching (for Hugging Face models and page raw/processed dumps) and speed-oriented crawl mode (`--fast` delay of `0.1s - 0.3s`) to execute runs in minutes.
   - Uploads the persistent vector database indices directory as a downloadable ZIP workflow artifact (`RAG-MF-index-database`).

---

## Success Criteria
- **Accurate Retrieval**: Correctly fetches factual mutual fund information.
- **Strict Compliance**: Zero occurrences of advisory or opinionated responses.
- **Source Integrity**: Reliable inclusion of a single valid source citation link in every response.
- **Robust Refusal**: Handles out-of-scope queries gracefully and educationally.
- **Premium Responsive UI**: Renders a visually stunning Groww-inspired interface optimized for both desktop viewports and mobile screens, offering real-time fund search filtering and query scoping context integrations.

