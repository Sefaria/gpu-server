# Sefaria GPU Server

A Flask-based server that serves ML models for Named Entity Recognition (NER) and reference part extraction for Sefaria clients. Supports both Hebrew and English text, with GPU acceleration via CUDA.

## Models

The server loads and serves four models, configured via `MODEL_PATHS`:

| Type | Language | Architecture | Purpose |
|------|----------|--------------|---------|
| `named_entity` | `he` | `huggingface` | Detects citations/sources in Hebrew text |
| `named_entity` | `en` | `spacy` | Detects named entities in English text |
| `ref_part` | `he` | `spacy` | Breaks Hebrew citations into constituent parts |
| `ref_part` | `en` | `spacy` | Breaks English citations into constituent parts |

## API Endpoints

**`POST /recognize-entities`** — single text

```json
{"text": "...", "lang": "en"}
```

**`POST /bulk-recognize-entities`** — batch processing

```json
{"texts": ["...", "..."], "lang": "he"}
```

Add `?with_span_text=1` to include the original span text in entity results.

## Setup

### Requirements

```bash
cd app
pip install -r requirements.txt
```

For GPU support (CUDA 12.x), install additional packages:

```bash
pip install cupy-cuda12x "spacy[cuda122]~=3.7.0" gunicorn
```

### Local Configuration

The server selects its config file via the `APP_CONFIG` environment variable. For local development, create `app/local_config.py` (git-ignored) with a `MODEL_PATHS` list pointing to your local model directories:

```python
MODEL_PATHS = [
    {
        'arch': 'huggingface',  # 'huggingface' or 'spacy'
        'lang': 'he',           # 'he' or 'en'
        'path': '/path/to/he_ner_model',
        'type': 'named_entity'  # 'named_entity' or 'ref_part'
    },
    {
        'arch': 'spacy',
        'lang': 'en',
        'path': '/path/to/en_ner_model',
        'type': 'named_entity'
    },
    {
        'arch': 'spacy',
        'lang': 'he',
        'path': '/path/to/subref_he',
        'type': 'ref_part'
    },
    {
        'arch': 'spacy',
        'lang': 'en',
        'path': '/path/to/subref_en',
        'type': 'ref_part'
    },
]
```

Each entry in `MODEL_PATHS` requires:
- **`arch`**: Model architecture — `'huggingface'` or `'spacy'`
- **`lang`**: Language code — `'he'` (Hebrew) or `'en'` (English)
- **`path`**: Absolute path to the model directory, or a `gs://` GCS URI (downloaded automatically at startup)
- **`type`**: Task type — `'named_entity'` or `'ref_part'`

## Running the Server

### Local development

```bash
cd app
APP_CONFIG=local_config.py python app.py
```

The Flask dev server starts on `http://localhost:5000`.

### Docker

```bash
cd app
docker build -t sefaria-gpu-server .
docker run -p 8000:8000 sefaria-gpu-server
```

The container runs Gunicorn on port 8000 with a single worker (required for shared GPU memory).

### Kubernetes / Helm

The `chart/` directory contains a Helm chart. Environment-specific `HelmRelease` manifests live in `deploy/dev/` and `deploy/prod/`. Model paths and resource limits are configured in `chart/values.yaml`.

In production, `MODEL_PATHS` entries use `gs://` URIs; the server downloads and extracts each model from GCS at startup using workload identity for authentication.
