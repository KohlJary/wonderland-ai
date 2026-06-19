# Partner Dashboard — FastAPI + React + SQLite

A fullstack dashboard that shows a partner's current local time, weather, and news at a glance — built end-to-end by Wonderland (Haiku-only). The most complex pilot to date: real external API integration, scheduled background polling, and a graceful-degradation cache layer.

See the full writeup: [`analyses/048-ldr-ophanic-substrate-fixes-and-failure-findings.md`](../../analyses/048-ldr-ophanic-substrate-fixes-and-failure-findings.md).

**Stack:**
- Backend: Python + FastAPI + SQLAlchemy + SQLite + APScheduler (hourly polling)
- Frontend: React + Vite + TypeScript (react-router)
- External APIs: Open-Meteo (weather), RSS (news) — fetched server-side, cached in SQLite

**Features (4 milestones):**
- **M1 — Auth & foundation:** signup / signin / sign-out with signed-cookie sessions; partner profile setup that resolves a city/country to an IANA timezone + lat/lon.
- **M2 — Time card:** the partner's current local time, rendered client-side and ticking every second (`Intl.DateTimeFormat` over the resolved timezone).
- **M3 — Weather card:** hourly-cached Open-Meteo data with a full error taxonomy (`not_yet_available` / `unavailable` / `degraded` / stale) and a stale indicator.
- **M4 — News card:** RSS headlines on the same cached + graceful-degradation pattern (first implementation pass).

---

## Quick Start

### Prerequisites
- Python 3.11+, Node 18+

### Backend
```bash
pip install -r requirements.txt
uvicorn src.backend.main:app --reload
# → http://localhost:8000/docs  (Swagger)
```

### Frontend
```bash
npm install
npm run dev
# → http://localhost:5173
```

Sign up, set a partner location (e.g. "Vienna, Austria"), and the dashboard renders the time / weather / news cards for that location.

---

## Project Layout

```
src/
  backend/
    main.py            # FastAPI app + lifespan (starts the polling scheduler)
    database.py        # SQLAlchemy models (User, PartnerProfile, WeatherCache, NewsCache)
    auth.py            # password hashing + session cookies
    geolocation.py     # city/country → IANA timezone + lat/lon
    weather_service.py # Open-Meteo client + WMO code map
    news_service.py    # RSS client
    polling_job.py     # hourly background poll → cache
    routers/           # auth / partner / dashboard / api routers
  components/          # TimeCard, WeatherCard, NewsCard, PartnerForm, ProtectedRoute
  contexts/           # AuthContext, PartnerContext
  pages/              # Signin, Signup, Dashboard, PartnerSetup
tests/                # backend tests
```

---

## Known Limitations (honest state)

This demo is preserved **as the substrate produced it**, including a real bug — the substrate-level lesson is more valuable than a hand-patched artifact (see the analysis, §V).

- **Staleness indicator is wrong.** `is_stale` and "last updated Xh ago" are computed as `now - cached_at`, but `cached_at` is frozen at row creation, so a cache that refreshes hourly reports stale after the threshold of *row life* regardless of refreshes. It measures row age, not data age. The correct key is `last_successful_fetch_at` (which does advance on each refresh). This affects both the weather and news cards — the news card copied the weather card's pattern verbatim, which is itself one of the run's findings (a certified bug propagating as a template).
- **News polling** may not be wired into the scheduler in this snapshot (the news card renders `not_yet_available` until it is) — one of the M4 follow-up tickets.
- **M5 (graceful degradation polish)** — manual-refresh buttons and cache observability — was designed but not implemented; most of its scope was already delivered by the M2/M3 card error-states.

The core app — auth, partner setup, live time, and weather/news rendering — works; the trust-precision layer (accurate staleness) is the known-broken part.
