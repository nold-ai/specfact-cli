# Import Dependency Analysis

Full unique list of `from specfact_cli.* import` in specfact-cli-modules (from `rg -e "from specfact_cli.* import" -o -IN --trim | sort | uniq`). Categorize each as **CORE**, **MIGRATE**, or **SHARED** per Section 19 tasks.

## Categories

- **CORE** — Must stay in specfact-cli; bundles depend on `specfact-cli` as a pip package. Allowed in bundle code.
- **MIGRATE** — Used only by bundle code; move to appropriate bundle or shared package in specfact-cli-modules.
- **SHARED** — Used by both core and bundles; decide: extract to shared pkg, or keep in core with clear contract.

## Import list (to categorize)

| Import | Category | Target bundle (if MIGRATE) | Notes |
|--------|----------|----------------------------|-------|
| `from specfact_cli.adapters.registry import` | | | |
| `from specfact_cli.agents.analyze_agent import` | | | |
| `from specfact_cli.agents.registry import` | | | |
| `from specfact_cli.analyzers.ambiguity_scanner import` | | | |
| `from specfact_cli.analyzers.code_analyzer import` | | | |
| `from specfact_cli.analyzers.graph_analyzer import` | | | |
| `from specfact_cli.analyzers.relationship_mapper import` | | | |
| `from specfact_cli.backlog.adapters.base import` | | | |
| `from specfact_cli.backlog.ai_refiner import` | | | |
| `from specfact_cli.backlog.filters import` | | | |
| `from specfact_cli.backlog.mappers.ado_mapper import` | | | |
| `from specfact_cli.backlog.mappers.github_mapper import` | | | |
| `from specfact_cli.backlog.mappers.template_config import` | | | |
| `from specfact_cli.backlog.template_detector import` | | | |
| `from specfact_cli.cli import` | | | |
| `from specfact_cli.common import` | | | |
| `from specfact_cli.comparators.plan_comparator import` | | | |
| `from specfact_cli.contracts.module_interface import` | | | |
| `from specfact_cli.enrichers.constitution_enricher import` | | | |
| `from specfact_cli.enrichers.plan_enricher import` | | | |
| `from specfact_cli.generators.contract_generator import` | | | |
| `from specfact_cli.generators.openapi_extractor import` | | | |
| `from specfact_cli.generators.persona_exporter import` | | | |
| `from specfact_cli.generators.plan_generator import` | | | |
| `from specfact_cli.generators.report_generator import` | | | |
| `from specfact_cli.generators.test_to_openapi import` | | | |
| `from specfact_cli import` | | | |
| `from specfact_cli.importers.speckit_converter import` | | | |
| `from specfact_cli.integrations.specmatic import` | | | |
| `from specfact_cli.merge.resolver import` | | | |
| `from specfact_cli.migrations.plan_migrator import` | | | |
| `from specfact_cli.models.backlog_item import` | | | |
| `from specfact_cli.models.bridge import` | | | |
| `from specfact_cli.models.contract import` | | | |
| `from specfact_cli.models.deviation import` | | | |
| `from specfact_cli.models.dor_config import` | | | |
| `from specfact_cli.models.enforcement import` | | | |
| `from specfact_cli.models.persona_template import` | | | |
| `from specfact_cli.models.plan import` | | | |
| `from specfact_cli.models.project import` | | | |
| `from specfact_cli.models.protocol import` | | | |
| `from specfact_cli.models.quality import` | | | |
| `from specfact_cli.models.sdd import` | | | |
| `from specfact_cli.models.validation import` | | | |
| `from specfact_cli.modes import` | | | |
| `from specfact_cli.modules import` | | | |
| `from specfact_cli.parsers.persona_importer import` | | | |
| `from specfact_cli.registry.registry import` | | | |
| `from specfact_cli.runtime import` | | | |
| `from specfact_cli.sync.bridge_probe import` | | | |
| `from specfact_cli.sync.bridge_sync import` | | | |
| `from specfact_cli.sync.bridge_watch import` | | | |
| `from specfact_cli.sync.change_detector import` | | | |
| `from specfact_cli.sync.code_to_spec import` | | | |
| `from specfact_cli.sync.drift_detector import` | | | |
| `from specfact_cli.sync.repository_sync import` | | | |
| `from specfact_cli.sync.spec_to_code import` | | | |
| `from specfact_cli.sync.spec_to_tests import` | | | |
| `from specfact_cli.sync.watcher import` | | | |
| `from specfact_cli.telemetry import` | | | |
| `from specfact_cli.templates.registry import` | | | |
| `from specfact_cli.utils.acceptance_criteria import` | | | |
| `from specfact_cli.utils.auth_tokens import` | | | |
| `from specfact_cli.utils.bundle_converters import` | | | |
| `from specfact_cli.utils.bundle_loader import` | | | |
| `from specfact_cli.utils.enrichment_context import` | | | |
| `from specfact_cli.utils.enrichment_parser import` | | | |
| `from specfact_cli.utils.env_manager import` | | | |
| `from specfact_cli.utils.feature_keys import` | | | |
| `from specfact_cli.utils.git import` | | | |
| `from specfact_cli.utils.ide_setup import` | | | |
| `from specfact_cli.utils import` | | | |
| `from specfact_cli.utils.incremental_check import` | | | |
| `from specfact_cli.utils.optional_deps import` | | | |
| `from specfact_cli.utils.performance import` | | | |
| `from specfact_cli.utils.persona_ownership import` | | | |
| `from specfact_cli.utils.progress import` | | | |
| `from specfact_cli.utils.sdd_discovery import` | | | |
| `from specfact_cli.utils.source_scanner import` | | | |
| `from specfact_cli.utils.structured_io import` | | | |
| `from specfact_cli.utils.structure import` | | | |
| `from specfact_cli.utils.terminal import` | | | |
| `from specfact_cli.utils.yaml_utils import` | | | |
| `from specfact_cli.validators.contract_validator import` | | | |
| `from specfact_cli.validators.repro_checker import` | | | |
| `from specfact_cli.validators.schema import` | | | |
| `from specfact_cli.validators.sidecar.crosshair_summary import` | | | |
| `from specfact_cli.validators.sidecar.models import` | | | |
| `from specfact_cli.validators.sidecar.orchestrator import` | | | |
| `from specfact_cli.validators.sidecar.unannotated_detector import` | | | |
| `from specfact_cli.versioning import` | | | |

## Bundle mapping (for Target bundle)

- **specfact-project**: project, plan, import_cmd, sync, migrate
- **specfact-backlog**: backlog, policy_engine
- **specfact-codebase**: analyze, drift, validate, repro
- **specfact-spec**: contract, spec, sdd, generate
- **specfact-govern**: enforce, patch_mode

## Suggested initial categorization (to be verified)

| Subsystem | Likely category | Rationale |
|-----------|-----------------|-----------|
| `common`, `cli`, `contracts`, `modes`, `runtime`, `telemetry`, `versioning`, `registry` | CORE | Core infra; bundles depend on specfact-cli |
| `models.*` | CORE or SHARED | Pydantic models; widely used; may stay in core |
| `analyzers.*`, `sync.*` (drift, code_to_spec, etc.) | MIGRATE → codebase/project | Used by analyze, drift, sync, migrate |
| `backlog.*` | MIGRATE → backlog | Used only by backlog bundle |
| `comparators`, `enrichers`, `generators` | MIGRATE → spec/project | Used by plan, generate, spec |
| `importers`, `migrations`, `parsers` | MIGRATE → project | Used by import_cmd, migrate, backlog |
| `validators.*` | MIGRATE or SHARED | Contract/repro used by codebase/spec |
| `adapters`, `agents` | MIGRATE or SHARED | Backlog/codebase integration |
| `utils.*` | Per-item | Many are generic; some bundle-specific |

Update this table as categorization is refined during task 19.1.
