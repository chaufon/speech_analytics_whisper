# Speech Analytics Whisper

Speech Analytics Whisper transcribes agent–customer conversations with OpenAI's Whisper, separates 
who said what through speaker diarization, scores each call against configurable business rules
("typifications"). Quality teams manage campaigns, launch batch processing, and export results 
from a web UI, while the heavy ML work runs out-of-band on GPU/CPU worker fleets.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.5-37814A?logo=celery&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-psycopg3-4169E1?logo=postgresql&logoColor=white)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.2-005571?logo=elasticsearch&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-broker%2Fcache-DC382D?logo=redis&logoColor=white)
![Whisper](https://img.shields.io/badge/faster--whisper-1.2-FF6F00)
![pyannote](https://img.shields.io/badge/pyannote--audio-4.0-5C2D91)
![CUDA](https://img.shields.io/badge/CUDA-GPU%20accelerated-76B900?logo=nvidia&logoColor=white)

---

## Key Features

- **Whisper transcription** with custom hotword/word-list biasing to improve accuracy on
  domain-specific vocabulary (brands, product names, jargon).
- **Speaker diarization** (`pyannote-audio`) producing per-segment speaker labels, so each
  utterance is attributed to a speaker on the call.
- **Typification engine** — a configurable rule layer that matches transcripts against
  fuzzy fixed phrases (with adjustable `[n]` slop), producing a
  match / no-match / error result per rule per call.
- **Multi-tenant campaigns** with role-based access control and scoped data isolation.
- **Dual processing backends** — run inference locally on a GPU/CPU worker fleet, or hand
  off to AWS Transcribe, selectable by configuration.
- **Excel export** of analysis results for reporting and downstream BI.
- **Audit trail** — every change to core records is tracked and reversible via
  `django-pghistory`.

---

## Architecture

The system is split into a **web application** (Django, server-rendered) and a **worker
fleet** (Celery) so that long-running, resource-intensive ML never blocks request/response
cycles. The two roles are deployed and scaled independently.

![Deployment topology: an Nginx + Django web tier with Redis, PostgreSQL, Elasticsearch and a Celery "default" worker on the Speech Analytics server, connected over the local network to a GPU server running the "local_ai" Celery worker and GPU card](docs/media/full_topology.png)

**Engineering highlights**

- **GPU/CPU queue separation with fallback** — transcription is routed to a CUDA queue
  when a GPU is available and degrades gracefully to a CPU queue, configured via
  `LOCALAI_CUDA_QUEUE` / `LOCALAI_CPU_QUEUE`.
- **Pause / resume control** — in-flight batch processes can be paused and resumed through
  a Redis-backed control channel, without losing progress.
- **Per-run resource metrics** — each job records peak VRAM / RAM / CPU usage and duration,
  giving visibility into model cost and capacity planning.
- **Pluggable inference** — local Whisper + pyannote and AWS Transcribe sit behind the same
  processing flow, switchable by configuration.
- **Immutable change history** — `django-pghistory` captures a reversible audit log of
  changes to agents, word lists, typifications, processes, and audio records.

### Django apps

| App             | Responsibility                                                            |
| --------------- | ------------------------------------------------------------------------- |
| `apps.users`    | Authentication, multi-tenant campaigns, roles & permissions               |
| `apps.common`   | Shared configuration (singleton `Config`), constants, utilities           |
| `apps.analytics`| Core domain: processes, audios, segments, typifications, results, search  |
| `apps.localai`  | Celery tasks and runners for local Whisper transcription + diarization     |

---

## Demo

https://github.com/user-attachments/assets/46bf4021-19e6-41e7-aab3-01aaa707d076

▶ A short screencast walking through campaign setup, audio upload, transcription with
speaker diarization, and typification results.

---

## Repository layout

```
speech_analytics_whisper/
├── apps/
│   ├── users/          # auth, campaigns, roles, permissions
│   ├── common/         # config, constants, shared utilities
│   ├── analytics/      # processes, audios, segments, typifications, results
│   └── localai/        # Celery tasks + ML runners (Whisper, pyannote)
├── config/
│   ├── settings/       # base / dev / prod
│   ├── celery.py       # Celery application
│   ├── urls.py         # URL routing
│   └── wsgi.py         # WSGI entry point
├── templates/          # Django HTML templates (Bootstrap 5)
├── static/             # CSS / JS
├── requirements/       # dependencies split by role: common / speech / localai
├── docs/               # MkDocs (Material) documentation
└── manage.py
```

---

## Getting started

> See the [deployment overview](docs/deployment.md) for the production architecture and per-server setup.

### Prerequisites

- Python **3.13**
- PostgreSQL, Redis, and Elasticsearch 8.x
- A Hugging Face token (to download the pyannote diarization model)
- *Optional:* an NVIDIA GPU with CUDA for accelerated transcription

### Setup

The project is deployed in two roles. Install the web app and worker dependencies from
their respective requirement sets:

```bash
# Web application
pip install -r requirements/speech/dev.txt

# Local-AI worker (GPU/CPU transcription)
pip install -r requirements/localai/dev.txt
```

Create an environment file from one of the provided templates (`.env` is git-ignored):

```bash
cp .env.example.dev .env                 # web app
cp .env.localai.example.dev .env         # local-AI worker
```

Initialize the database and download the diarization model:

```bash
python manage.py migrate
python manage.py download_pyannote
```

### Run

```bash
# Web app
python manage.py runserver

# Default Celery worker
celery -A config worker --loglevel=info

# Celery worker (GPU and CPU queues, configured via env)
celery -A config worker -Q local_cuda,local_cpu --loglevel=info

# Flower monitoring dashboard
celery -A config flower
```

The app is then available at `http://localhost:8000/` (Django admin at `/admin/`).

### Configuration

Configuration is environment-driven; see the `.env.example.*` templates for the full set.
The most relevant variables:

| Variable                                   | Purpose                                |
| ------------------------------------------ | -------------------------------------- |
| `DJANGO_SETTINGS_MODULE`                   | `config.settings.dev` / `.prod`        |
| `DB_*`                                     | PostgreSQL connection                  |
| `REDIS_URL` / `CELERY_BROKER_URL`          | Redis broker & cache                   |
| `ELASTICSEARCH_HOSTS`                      | Elasticsearch endpoint                 |
| `LOCALAI_CUDA_QUEUE` / `LOCALAI_CPU_QUEUE` | Celery queue routing for transcription |
| `HF_TOKEN`                                 | Hugging Face token for model downloads |
| `AWS_*`                                    | Optional AWS Transcribe / S3 backend   |

---

## Documentation

Project documentation is built with MkDocs (Material) under [`docs/`](docs) — see
[`mkdocs.yml`](mkdocs.yml). It covers the user guide (roles & permissions, scopes), the
developer guide (data models), and per-platform deployment guides. To serve it locally:

```bash
mkdocs serve
```

---

## Testing

Tests live under `apps/*/tests/`, with sample audio fixtures for the transcription pipeline.

```bash
python manage.py test
```
