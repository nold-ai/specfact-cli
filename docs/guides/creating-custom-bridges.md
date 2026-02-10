---
layout: default
title: Creating Custom Bridges
permalink: /guides/creating-custom-bridges/
---

# Creating Custom Bridges

Custom bridges let module authors expose service-specific conversion logic via the shared bridge registry.

## 1. Implement a Converter

Create a converter class with both methods:

```python
class MyServiceConverter:
    def to_bundle(self, external_data: dict) -> dict:
        return {"id": external_data.get("issue_id"), "title": external_data.get("summary")}

    def from_bundle(self, bundle_data: dict) -> dict:
        return {"issue_id": bundle_data.get("id"), "summary": bundle_data.get("title")}
```

## 2. Declare the Bridge in `module-package.yaml`

```yaml
service_bridges:
  - id: my-service
    converter_class: specfact_cli.modules.my_module.src.adapters.my_service.MyServiceConverter
    description: Optional description
```

## 3. Validate Registration

Run module lifecycle registration and inspect logs:

- valid declarations are registered
- malformed class paths are skipped with warning
- duplicate IDs are skipped deterministically

## 4. Optional Mapping Overrides

Converters can optionally load mapping override files (for example, YAML) and should fall back to defaults
when mapping files are missing or malformed.

## Migration Notes

- Modules without `service_bridges` remain valid.
- Protocol compliance summary now reflects actual runtime interface detection (full/partial/legacy).
