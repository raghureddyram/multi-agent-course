# Submission Report — Assignment 1 — Live Translate

- **Student:** Raghu Reddy
- **Video demo:** PENDING — record 60–90s demo
- **Backend target:** `http://localhost:8787`
- **Auto-graded score:** **70 / 70**  ·  manual portion: 30 pts (grader)

## Rubric

| Criterion | Type | Points | Result |
|---|---|---|---|
| Widget lights up (contract works end to end) | auto | 15/15 | translate + batch return valid shapes |
| Caching correctness (two-tier, provable, persistent) | auto | 20/20 | 2nd cached=True, faster=True, sqlite_persisted=True |
| Performance & SLA gate | auto | 15/15 | bench SLA gate PASS |
| Logging & observability | auto | 10/10 | stats_hit_rate=True, health_reports_ai=True, ai_log_file=True, trace_correlated=True |
| Service separation & correct status codes | auto | 10/10 | 400_on_bad_input=True, gateway_nests_ai_health=True |
| LLM & prompt quality (natural Mexican Spanish) | manual | —/20 | **grader** — see evidence + video |
| Deploy & docs | manual | —/10 | **grader** — see evidence + video |

## Evidence

- Sample translation (`Good morning, welcome!`): **¡Buenos días, bienvenido!**
- Cache latency: first `1419 ms` → second `0 ms`
- Trace correlation (one request across both logs): ✅ yes
- Benchmark: hit p95 `7 ms`, miss p95 `2436 ms`, hit rate `78%`, throughput `1363 rps`, SLA **PASS**
- Cost: `$0.000170`/miss; monthly savings from cache `$65.81`
- Deploy: `https://rr-livetranslate-gw.fly.dev/health` → ✅ ok

<details><summary>Benchmark output</summary>

```
    cost per MISS (avg)         $0.000170
    @ 500,000/mo, no cache      $84.92
    @ 500,000/mo, cached        $19.11
    monthly savings from cache  $65.81
── SLA GATE ────────────────────────────────────────
    PASS  cache_hit_p95_ms         7.0 <= 60
    PASS  cache_miss_p95_ms        2436.1 <= 3500
    PASS  min_cache_hit_rate_pct   77.5 >= 60
    PASS  max_error_rate_pct       0.0 <= 1.0
    PASS  min_throughput_rps       1362.6 >= 20

✅ ALL SLAs MET

Wrote /Users/raghureddy/multi-agent-course/FDE/Assignment_1_Live_Translate/eval/_bench.json
```
</details>
