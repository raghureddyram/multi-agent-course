# Product Evaluation — Live Translate

- **Student:** Raghu Reddy
- **Date:** 2026-07-15
- **Video demo:** _PENDING — record 60–90s screen capture (page → live translate → cache-hit badges)_
- **LLM provider / model:** Anthropic · `claude-sonnet-4-6`
- **Backend target:** deployed gateway `https://rr-livetranslate-gw.fly.dev` (AI service private on Fly `.internal`); benchmark run against local `http://localhost:8787` for stable numbers

## Verdict

> This is shippable. The strongest part is the caching layer: identical input never
> hits the LLM twice, a cache hit returns in **0 ms** vs **~1.2–2.6 s** on a miss
> (~337× on the benchmark), and the SQLite tier survives restarts and deploys (it
> lives on a Fly volume). Translation quality is genuinely Mexican (es-MX register —
> "Agregar al carrito", "Los más vendidos en herramientas eléctricas"), translation-only,
> with numbers, prices, brands and SKU codes preserved verbatim. Service separation is
> clean: the browser only ever touches the public Node gateway; the Python AI service is
> private and holds the API key. The weakest part is first-pass latency on large pages —
> the AI service translates each chunk of a batch **sequentially**, so a content-heavy
> retail page's first (all-miss) translation is slow; the concurrency fix is the top
> recommendation below. Notably, error handling is **fail-loud**: during setup a real
> `anthropic`/`httpx` dependency mismatch made every LLM call throw, and the service
> correctly surfaced it as a 5xx error and logged it — it never served untranslated
> English as if it had succeeded.

**Rubric score (from `eval/report.json`):** 70 / 70 auto (+ 30 manual, grader) — all five automated dimensions full marks.

## 1. Performance & cost (from `benchmark/bench.py`, cold-cache run)

| Metric | Result | SLA | Pass? |
|---|---|---|---|
| Cache hit p95 | 7.0 ms | ≤ 60 ms | ✅ |
| Cache miss p95 | 2436 ms | ≤ 3500 ms | ✅ |
| Cache hit rate | 77.5 % | ≥ 60 % | ✅ |
| Throughput | 1363 req/s | ≥ 20 | ✅ |
| Error rate | 0.0 % | ≤ 1 % | ✅ |
| Cost per miss | $0.00017 | — | — |
| Monthly savings from cache | $65.81 | — | — |

`python benchmark/bench.py` exits `0` — every SLA met. Cost model at 500,000
translations/mo: **$84.92 without cache → $19.11 with cache** (placeholder prices in
`sla.json` = current published Sonnet rates $3/$15 per MTok).

## 2. Live-website test

- **Site tested:** `https://www.homedepot.com` (strict-CSP retail site the student does not control)
- **Translated whole page?** Yes — page text flipped to Mexican Spanish via the Chrome extension (student-confirmed manual run); on-camera capture pending the video. Sample pairs below are captured **directly from the deployed product's API**, so they are exact production output.
- **Coverage gaps:** Dynamically-loaded content (lazy-loaded sections, content injected after the translate click) can remain in English — the widget translates the text nodes present at translate time. Real finding on a live SPA-style retail site, not a backend defect.
- **Cache on re-translate:** Same string twice against the **deployed** gateway → 1245 ms (miss) then **0 ms** (`cached: true`). Deployed `/stats` after the session: **1289 requests, 77.9 % hit rate, 285 cached entries.** In the widget, the badges row shows the per-run cache-hit count and total ms.
- **Resilience:** The extension works on strict-CSP Home Depot (its content script injects the widget and it proxies over HTTPS) — console-snippet injection would be CSP-blocked, which is exactly why the extension is the required path. No layout breakage; no console errors against the deployed gateway.
- **Screenshots:** to be attached with the video submission.

### Sample translations (from the deployed product)

| Original (EN) | Translation (es-MX) | Numbers/prices/codes kept? | OK? |
|---|---|---|---|
| Add to cart | Agregar al carrito | — | ✅ |
| Free 2-day shipping on orders over $45 | Envío gratis en 2 días en pedidos mayores de $45 | $45 ✅ | ✅ |
| Best Sellers in Power Tools | Los más vendidos en herramientas eléctricas | — | ✅ |
| DeWalt 20V MAX Cordless Drill — model DCD771C2 | DeWalt 20V MAX Taladro Inalámbrico — modelo DCD771C2 | DeWalt / 20V MAX / DCD771C2 ✅ | ✅ |
| Only 3 left in stock | Solo quedan 3 en existencia | 3 ✅ | ✅ |
| Save $150.00 today | Ahorra $150.00 hoy | $150.00 ✅ | ✅ |
| Proceed to secure checkout | Ir al pago seguro | — | ✅ |

## 3. Dimension scorecard

| Dimension | Pass / Partial / Fail | Evidence |
|---|---|---|
| Translation accuracy | Pass | All 7 sampled pairs are correct, fluent, translation-only (no preamble/quotes) |
| Mexican-Spanish register (es-MX) | Pass | "carrito", "existencia", "Ir al pago", "herramientas eléctricas" — Mexican, not Castilian |
| Numbers / prices / codes preserved | Pass | `$45`, `$150.00`, `DCD771C2`, `20V MAX`, `DeWalt` all verbatim |
| Page coverage | Partial | Static DOM text translated; dynamically-loaded content can remain English |
| Cache effectiveness | Pass | 0 ms hit vs ~1.2–2.6 s miss; 77.9 % deployed hit rate; SQLite survives restart |
| Latency vs SLA | Pass | All five SLAs green; `bench.py` exits 0 |
| Error handling (no silent English) | Pass | Fail-loud by design; caught a real `anthropic`/`httpx` bug as a 5xx, never served English |
| Resilience on a real site | Pass | Extension works on strict-CSP homedepot.com over the public HTTPS gateway |
| UX polish | Partial | Clean widget/badges/status; first-pass on large pages is slow (sequential batch) |

## 4. Top fixes before shipping

1. **Parallelize batch translation** — `translate_batch` currently `await`s each chunk in
   series; running a batch's misses concurrently (`asyncio.gather`, bounded by a semaphore)
   would cut first-pass latency on large pages dramatically. This is the single biggest UX win.
2. **Handle dynamic content** — add a MutationObserver (or a re-translate affordance) so
   lazy-loaded sections on SPA/retail sites get translated too, closing the coverage gap.
3. **Gateway hardening before public exposure** — add per-IP rate limiting (`429` + friendly
   widget message) and a cache TTL / `POST /clear-cache`. (AI service is already private via
   Fly `.internal`, and the API key is a Fly secret — good.)

---

### Verification appendix (all self-checked, not asserted)

- **Contract:** `/translate`, `/translate/batch`, `/health`, `/stats` all match the required shapes; provided `widget/`, `extension/`, `benchmark/` unmodified (git clean).
- **Cache:** identical `(text, target)` never calls the LLM twice; `cached:true` only from cache; two tiers (memory + SQLite); SQLite persists across a process restart (verified by restarting with a cold memory tier and still getting a hit).
- **Tracing:** one request ID (`X-Request-Id` reused or generated at the gateway, forwarded to the AI service) is greppable end-to-end across `gateway.log` + `ai-service.log`.
- **Deploy:** both services on Fly.io (region `sjc`); public gateway `/health` → `{"status":"ok", aiService:{...ok}}`; AI service private (no public IP); API key stored via `flyctl secrets`, never in the image.
- **Hygiene:** `.env`, `node_modules/`, `.venv/`, `*.db`, `*.log` git-ignored and uncommitted.
