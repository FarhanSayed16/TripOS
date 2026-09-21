# TripOS — AI Spec (Farhan-owned)

### Internal contract for the AI Copilot — built entirely by Farhan

**Status:** FINAL ownership — **Farhan builds AI**. Sahil/Nilesh only supply travel/payment API access elsewhere; they do **not** build this service.  

**Former name:** `tripos-sahil-ai-handoff.md` (repurposed; do not hand to Sahil as a build track).

**When:** Product integration in **V2 / Master Plan Phase 35**. Can prototype against mock offers earlier if Farhan has bandwidth — must not delay V1.

---

## 1. Decision (locked)

| Question | Answer |
|---|---|
| Who builds AI? | **Farhan only** |
| Custom model training required for V2? | **No** |
| What is V2 AI? | LLM orchestration: parse intent + format draft |
| Who fetches TBO/TripJack/hotels? | **Farhan Inventory adapters only** — AI never calls suppliers |
| Sahil/Nilesh role related to AI? | **None** (unless later helping with an LLM account admin — optional) |

---

## 2. Architecture

### Sprint R decision (FIX-P35-02) — **Option B for V2**

**Accepted 2026-09-19:** AI stays a **monolith module** inside `apps/api` (`app/api/ai.py`, `app/services/ai_copilot.py`) for V2.

| Plan (original) | V2 reality |
|---|---|
| Separate `apps/ai` service + `/ai/v1/...` | Deferred — `apps/ai/.gitkeep` placeholder only |
| Gateway auth between API ↔ AI | Not needed while in-process |
| Deploy story | Same Render API service; gate with `AI_COPILOT_ENABLED` + `OPENAI_API_KEY` |

Extracting `apps/ai` remains a **V3 option** if latency/isolation requires it. Do not claim Phase 35 “separate service” exit.

---

Keep booking/money code clean: AI never invents prices or availability.

```text
[Agent NL text]
      │
      ▼
Farhan main API  /api/v1/ai/parse-intent ──► structured params
      │
      ▼
Farhan Inventory.search (REAL adapters)
      │
      ▼
Farhan main API  /api/v1/ai/search-and-draft ──► draft (offer IDs subset only)
      │
      ▼
Agent reviews → Quote → wa.me → Pay → Book
```

---

## 3. API contract (Farhan implements both producer and consumer)

### 3.1 `POST /ai/v1/parse-intent`

**Request**
```json
{
  "text": "4 pax, Mumbai to Dubai, 5 nights December, budget 2 lakh",
  "locale": "en-IN",
  "today": "2026-09-16"
}
```

**Response**
```json
{
  "ok": true,
  "intent": {
    "origin": "BOM",
    "destination": "DXB",
    "departure_date": "2026-12-01",
    "return_date": "2026-12-06",
    "nights": 5,
    "adults": 4,
    "children": 0,
    "budget_amount": 200000,
    "budget_currency": "INR",
    "product_hints": ["flight", "hotel"],
    "raw_notes": "..."
  },
  "confidence": 0.86,
  "missing_fields": []
}
```

Rules: do not hallucinate critical dates; use `missing_fields`; never include prices.

### 3.2 `POST /ai/v1/format-quote-draft`

**Request:** intent + `offers[]` (NormalizedOffer snapshots) + optional agency brand name.  

**Response:** title, customer_message, recommended_offer_ids (must be subset of input), line_items_text, caveats.  

Rules: empty offers → say so; no invented options.

### 3.3 Auth between main API and AI service
- Shared secret `X-TripOS-AI-Key` (or internal network only on Render)

---

## 4. Farhan delivery checklist (Phase 35)

- [ ] Scaffold `apps/ai`
- [ ] LLM provider key in env
- [ ] parse-intent + tests
- [ ] format-quote-draft + “no invented price” tests
- [ ] Deploy AI service
- [ ] Main API `ai_gateway` + feature flag `AI_COPILOT_ENABLED`
- [ ] `/app/ai` UI → prefill quote builder
- [ ] Eval set of real agent phrases (collect via Nilesh’s agents — phrases only, not code)

---

## 5. Optional heavy ML (parked)

Fine-tuning / ranking models — **not required**. If ever done, still **Farhan-owned**, still behind the same HTTP contract.

---

## 6. One-liner

> Farhan owns AI end-to-end as a small LLM service that only parses language and formats real search results. Nilesh and Sahil supply travel/payment APIs for the rest of TripOS — not the AI engine.
