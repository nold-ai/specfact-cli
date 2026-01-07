# Sidecar Templates Directory Structure

## Overview

The sidecar templates are organized into common and framework-specific modules to support multiple frameworks (Django, FastAPI, DRF, etc.).

## Directory Structure

```bash
sidecar/
├── __init__.py                    # Root package marker
├── common/                        # Common modules used by all frameworks
│   ├── __init__.py
│   ├── populate_contracts.py     # Orchestrates contract population
│   ├── generate_harness.py       # Generates CrossHair harness files
│   ├── adapters.py               # Framework adapters (Django, FastAPI, etc.)
│   ├── crosshair_plugin.py       # CrossHair plugin
│   ├── run_sidecar.sh            # Main sidecar execution script
│   ├── sidecar-init.sh           # Sidecar initialization script
│   ├── requirements.txt          # Python dependencies
│   ├── README.md                 # Documentation
│   ├── bindings.yaml.example     # Example bindings file
│   └── harness_contracts.py.example  # Example harness file (shows generated structure)
├── frameworks/
│   ├── django/                   # Django-specific modules
│   │   ├── __init__.py
│   │   ├── django_url_extractor.py      # Extracts Django URL patterns
│   │   ├── django_form_extractor.py     # Extracts Django form schemas
│   │   └── crosshair_django_wrapper.py  # Django-aware CrossHair wrapper
│   ├── fastapi/                  # FastAPI-specific modules
│   │   ├── __init__.py
│   │   └── fastapi_route_extractor.py   # Extracts FastAPI routes and Pydantic models
│   └── drf/                      # Django REST Framework-specific modules
│       ├── __init__.py
│       └── drf_serializer_extractor.py  # Extracts DRF serializer schemas

```

## Import Patterns

### From Common Modules

Common modules import framework-specific modules using:

```python
from frameworks.django.django_url_extractor import extract_django_urls
from frameworks.fastapi.fastapi_route_extractor import extract_fastapi_routes
from frameworks.drf.drf_serializer_extractor import extract_serializer_schema
```

### From Framework Modules

Framework modules are self-contained and don't import from other frameworks.

## Adding New Framework Support

To add support for a new framework:

1. Create a new directory under `frameworks/` (e.g., `frameworks/flask/`)
2. Add framework-specific extractors (e.g., `flask_route_extractor.py`)
3. Update `common/populate_contracts.py` to import and use the new extractor
4. Update `common/adapters.py` to add framework-specific adapter if needed
5. Update `common/run_sidecar.sh` to detect and handle the new framework

## File Organization Principles

- **Common modules**: Shared logic used by all frameworks
- **Framework modules**: Framework-specific extraction and adapter logic
- **Separation of concerns**: Each framework module is independent
- **Extensibility**: Easy to add new frameworks without modifying existing code
