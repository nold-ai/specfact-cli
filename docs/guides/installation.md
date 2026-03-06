---
layout: default
title: Installation
nav_order: 5
permalink: /guides/installation/
---

# Installation

SpecFact CLI installation is now a two-step flow:

1. Install the CLI (`pip install -U specfact-cli` or `uvx specfact-cli@latest`).
2. Select workflow bundles on first run:

```bash
specfact init --profile solo-developer
# or
specfact init --install all
```

For complete platform options and CI/CD examples, see:

- [Getting Started Installation](../getting-started/installation.md)
- [Marketplace Bundles](marketplace.md)
- [Migration Guide](migration-guide.md)
