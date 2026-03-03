# Import Dependency Analysis

Full unique list of `from specfact_cli.* import` in specfact-cli-modules (from `rg -e "from specfact_cli.* import" -o -IN --trim packages | sort | uniq`).

## Categories

- **CORE** — Must stay in specfact-cli; bundles depend on `specfact-cli` package APIs.
- **MIGRATE** — Used primarily by migrated bundles; move to specfact-cli-modules bundle/shared packages before migration-03 source-prune work.
- **SHARED** — Used by both core and bundles or cross-bundle; keep in core for now with explicit contract until shared extraction is planned.

## Verification

- Import count from current modules repo scan: **91**
- Note: prior references to 85 imports are outdated; this file is normalized to the current 91-entry set.

## Categorized import list

| Import | Category | Target bundle (if MIGRATE) | Notes |
|--------|----------|----------------------------|-------|
| `from specfact_cli import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.adapters.registry import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.agents.analyze_agent import` | MIGRATE | specfact-project | Agent orchestration used by import/project flows; source exists under src/specfact_cli/agents/. |
| `from specfact_cli.agents.registry import` | MIGRATE | specfact-project | Agent orchestration used by import/project flows; source exists under src/specfact_cli/agents/. |
| `from specfact_cli.analyzers.ambiguity_scanner import` | MIGRATE | specfact-codebase | Codebase/spec analysis subsystem; source exists under src/specfact_cli/<subsystem>/. |
| `from specfact_cli.analyzers.code_analyzer import` | MIGRATE | specfact-codebase | Codebase/spec analysis subsystem; source exists under src/specfact_cli/<subsystem>/. |
| `from specfact_cli.analyzers.graph_analyzer import` | MIGRATE | specfact-codebase | Codebase/spec analysis subsystem; source exists under src/specfact_cli/<subsystem>/. |
| `from specfact_cli.analyzers.relationship_mapper import` | MIGRATE | specfact-codebase | Codebase/spec analysis subsystem; source exists under src/specfact_cli/<subsystem>/. |
| `from specfact_cli.backlog.adapters.base import` | MIGRATE | specfact-backlog | Bundle-specific backlog subsystem; source exists under src/specfact_cli/backlog/. |
| `from specfact_cli.backlog.ai_refiner import` | MIGRATE | specfact-backlog | Bundle-specific backlog subsystem; source exists under src/specfact_cli/backlog/. |
| `from specfact_cli.backlog.filters import` | MIGRATE | specfact-backlog | Bundle-specific backlog subsystem; source exists under src/specfact_cli/backlog/. |
| `from specfact_cli.backlog.mappers.ado_mapper import` | MIGRATE | specfact-backlog | Bundle-specific backlog subsystem; source exists under src/specfact_cli/backlog/. |
| `from specfact_cli.backlog.mappers.github_mapper import` | MIGRATE | specfact-backlog | Bundle-specific backlog subsystem; source exists under src/specfact_cli/backlog/. |
| `from specfact_cli.backlog.mappers.template_config import` | MIGRATE | specfact-backlog | Bundle-specific backlog subsystem; source exists under src/specfact_cli/backlog/. |
| `from specfact_cli.backlog.template_detector import` | MIGRATE | specfact-backlog | Bundle-specific backlog subsystem; source exists under src/specfact_cli/backlog/. |
| `from specfact_cli.cli import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.common import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.comparators.plan_comparator import` | MIGRATE | specfact-codebase | Codebase/spec analysis subsystem; source exists under src/specfact_cli/<subsystem>/. |
| `from specfact_cli.contracts.module_interface import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.enrichers.constitution_enricher import` | MIGRATE | specfact-project/specfact-spec(shared) | Project/spec generation pipeline; source exists under src/specfact_cli/<subsystem>/. Move before migration-03 prune. |
| `from specfact_cli.enrichers.plan_enricher import` | MIGRATE | specfact-project/specfact-spec(shared) | Project/spec generation pipeline; source exists under src/specfact_cli/<subsystem>/. Move before migration-03 prune. |
| `from specfact_cli.generators.contract_generator import` | MIGRATE | specfact-project/specfact-spec(shared) | Project/spec generation pipeline; source exists under src/specfact_cli/<subsystem>/. Move before migration-03 prune. |
| `from specfact_cli.generators.openapi_extractor import` | MIGRATE | specfact-project/specfact-spec(shared) | Project/spec generation pipeline; source exists under src/specfact_cli/<subsystem>/. Move before migration-03 prune. |
| `from specfact_cli.generators.persona_exporter import` | MIGRATE | specfact-project/specfact-spec(shared) | Project/spec generation pipeline; source exists under src/specfact_cli/<subsystem>/. Move before migration-03 prune. |
| `from specfact_cli.generators.plan_generator import` | MIGRATE | specfact-project/specfact-spec(shared) | Project/spec generation pipeline; source exists under src/specfact_cli/<subsystem>/. Move before migration-03 prune. |
| `from specfact_cli.generators.report_generator import` | MIGRATE | specfact-project/specfact-spec(shared) | Project/spec generation pipeline; source exists under src/specfact_cli/<subsystem>/. Move before migration-03 prune. |
| `from specfact_cli.generators.test_to_openapi import` | MIGRATE | specfact-project/specfact-spec(shared) | Project/spec generation pipeline; source exists under src/specfact_cli/<subsystem>/. Move before migration-03 prune. |
| `from specfact_cli.importers.speckit_converter import` | MIGRATE | specfact-project/specfact-spec(shared) | Project/spec generation pipeline; source exists under src/specfact_cli/<subsystem>/. Move before migration-03 prune. |
| `from specfact_cli.integrations.specmatic import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.merge.resolver import` | MIGRATE | specfact-project/specfact-spec(shared) | Project/spec generation pipeline; source exists under src/specfact_cli/<subsystem>/. Move before migration-03 prune. |
| `from specfact_cli.migrations.plan_migrator import` | MIGRATE | specfact-project/specfact-spec(shared) | Project/spec generation pipeline; source exists under src/specfact_cli/<subsystem>/. Move before migration-03 prune. |
| `from specfact_cli.models.backlog_item import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.bridge import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.contract import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.deviation import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.dor_config import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.enforcement import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.persona_template import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.plan import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.project import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.protocol import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.quality import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.sdd import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.models.validation import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.modes import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.modules import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.parsers.persona_importer import` | MIGRATE | specfact-codebase | Codebase/spec analysis subsystem; source exists under src/specfact_cli/<subsystem>/. |
| `from specfact_cli.registry.registry import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.runtime import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.sync.bridge_probe import` | MIGRATE | specfact-project | Sync orchestration currently used by project/codebase bundles; source exists under src/specfact_cli/sync/. |
| `from specfact_cli.sync.bridge_sync import` | MIGRATE | specfact-project | Sync orchestration currently used by project/codebase bundles; source exists under src/specfact_cli/sync/. |
| `from specfact_cli.sync.bridge_watch import` | MIGRATE | specfact-project | Sync orchestration currently used by project/codebase bundles; source exists under src/specfact_cli/sync/. |
| `from specfact_cli.sync.change_detector import` | MIGRATE | specfact-project | Sync orchestration currently used by project/codebase bundles; source exists under src/specfact_cli/sync/. |
| `from specfact_cli.sync.code_to_spec import` | MIGRATE | specfact-project | Sync orchestration currently used by project/codebase bundles; source exists under src/specfact_cli/sync/. |
| `from specfact_cli.sync.drift_detector import` | MIGRATE | specfact-project | Sync orchestration currently used by project/codebase bundles; source exists under src/specfact_cli/sync/. |
| `from specfact_cli.sync.repository_sync import` | MIGRATE | specfact-project | Sync orchestration currently used by project/codebase bundles; source exists under src/specfact_cli/sync/. |
| `from specfact_cli.sync.spec_to_code import` | MIGRATE | specfact-project | Sync orchestration currently used by project/codebase bundles; source exists under src/specfact_cli/sync/. |
| `from specfact_cli.sync.spec_to_tests import` | MIGRATE | specfact-project | Sync orchestration currently used by project/codebase bundles; source exists under src/specfact_cli/sync/. |
| `from specfact_cli.sync.watcher import` | MIGRATE | specfact-project | Sync orchestration currently used by project/codebase bundles; source exists under src/specfact_cli/sync/. |
| `from specfact_cli.telemetry import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |
| `from specfact_cli.templates.registry import` | MIGRATE | specfact-backlog | Backlog template registry; source exists under src/specfact_cli/templates/. |
| `from specfact_cli.utils import` | CORE |  | Infrastructure utilities used by core and bundles; keep in core API surface. |
| `from specfact_cli.utils.acceptance_criteria import` | MIGRATE | specfact-project | Project/import-specific utility; source exists under src/specfact_cli/utils/. |
| `from specfact_cli.utils.auth_tokens import` | MIGRATE | specfact-project | Project/import-specific utility; source exists under src/specfact_cli/utils/. |
| `from specfact_cli.utils.bundle_converters import` | SHARED |  | Used across multiple bundles; treat as shared contract until dedicated shared package is created. |
| `from specfact_cli.utils.bundle_loader import` | SHARED |  | Used across multiple bundles; treat as shared contract until dedicated shared package is created. |
| `from specfact_cli.utils.enrichment_context import` | MIGRATE | specfact-project | Project/import-specific utility; source exists under src/specfact_cli/utils/. |
| `from specfact_cli.utils.enrichment_parser import` | MIGRATE | specfact-project | Project/import-specific utility; source exists under src/specfact_cli/utils/. |
| `from specfact_cli.utils.env_manager import` | CORE |  | Infrastructure utilities used by core and bundles; keep in core API surface. |
| `from specfact_cli.utils.feature_keys import` | MIGRATE | specfact-project | Project/import-specific utility; source exists under src/specfact_cli/utils/. |
| `from specfact_cli.utils.git import` | CORE |  | Infrastructure utilities used by core and bundles; keep in core API surface. |
| `from specfact_cli.utils.ide_setup import` | CORE |  | Infrastructure utilities used by core and bundles; keep in core API surface. |
| `from specfact_cli.utils.incremental_check import` | MIGRATE | specfact-project | Project/import-specific utility; source exists under src/specfact_cli/utils/. |
| `from specfact_cli.utils.optional_deps import` | CORE |  | Infrastructure utilities used by core and bundles; keep in core API surface. |
| `from specfact_cli.utils.performance import` | CORE |  | Infrastructure utilities used by core and bundles; keep in core API surface. |
| `from specfact_cli.utils.persona_ownership import` | MIGRATE | specfact-project | Project/import-specific utility; source exists under src/specfact_cli/utils/. |
| `from specfact_cli.utils.progress import` | SHARED |  | Used across multiple bundles; treat as shared contract until dedicated shared package is created. |
| `from specfact_cli.utils.sdd_discovery import` | SHARED |  | Used across multiple bundles; treat as shared contract until dedicated shared package is created. |
| `from specfact_cli.utils.source_scanner import` | MIGRATE | specfact-project | Project/import-specific utility; source exists under src/specfact_cli/utils/. |
| `from specfact_cli.utils.structure import` | CORE |  | Infrastructure utilities used by core and bundles; keep in core API surface. |
| `from specfact_cli.utils.structured_io import` | CORE |  | Infrastructure utilities used by core and bundles; keep in core API surface. |
| `from specfact_cli.utils.terminal import` | CORE |  | Infrastructure utilities used by core and bundles; keep in core API surface. |
| `from specfact_cli.utils.yaml_utils import` | MIGRATE | specfact-project | Project/import-specific utility; source exists under src/specfact_cli/utils/. |
| `from specfact_cli.validators.contract_validator import` | SHARED |  | Validation contracts shared across bundles/core; keep in core until split package exists. |
| `from specfact_cli.validators.repro_checker import` | MIGRATE | specfact-codebase | Codebase/spec analysis subsystem; source exists under src/specfact_cli/<subsystem>/. |
| `from specfact_cli.validators.schema import` | SHARED |  | Validation contracts shared across bundles/core; keep in core until split package exists. |
| `from specfact_cli.validators.sidecar.crosshair_summary import` | MIGRATE | specfact-codebase | Codebase/spec analysis subsystem; source exists under src/specfact_cli/<subsystem>/. |
| `from specfact_cli.validators.sidecar.models import` | MIGRATE | specfact-codebase | Codebase/spec analysis subsystem; source exists under src/specfact_cli/<subsystem>/. |
| `from specfact_cli.validators.sidecar.orchestrator import` | MIGRATE | specfact-codebase | Codebase/spec analysis subsystem; source exists under src/specfact_cli/<subsystem>/. |
| `from specfact_cli.validators.sidecar.unannotated_detector import` | MIGRATE | specfact-codebase | Codebase/spec analysis subsystem; source exists under src/specfact_cli/<subsystem>/. |
| `from specfact_cli.versioning import` | CORE |  | Core runtime/interface/model contract expected to stay in specfact-cli. |

## Bundle mapping (for Target bundle)

- **specfact-project**: project, plan, import_cmd, sync, migrate
- **specfact-backlog**: backlog, policy_engine
- **specfact-codebase**: analyze, drift, validate, repro
- **specfact-spec**: contract, spec, sdd, generate
- **specfact-govern**: enforce, patch_mode

## Gate notes for 17.8.0

- 17.8.0.1: completed against current repo state (91 unique imports).
- 17.8.0.2: all listed imports categorized with target + notes.
- 17.8.0.3: every MIGRATE assignment references source currently present in specfact-cli (src/specfact_cli/<subsystem>/); migration-03 must not prune these before migration-05 section 19.2.
- 17.8.0.4: SHARED entries are explicitly marked to remain in core until shared-package extraction is scheduled.
