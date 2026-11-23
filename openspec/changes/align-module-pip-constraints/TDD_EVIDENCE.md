# Module resolver constraint evidence

## Failing evidence

On 22 November 2026, the published #524 workflow selects modules fixture `046d366c190af7a188d6f48953a96edb65e766db` and pins Typer to 0.27.0 from the paired core lock. The fixture tree is `c5b44db3477d1c9ea8dae1dceab2af276d265353`. With the #797 candidate graph and the unchanged workflow constraints, direct and Hatch passed locally. Pip-editable then resolved Typer 0.29.2 with pip-compile. Its existing pip constraint rejected that result with `ResolutionImpossible`.

Before changing the resolver, `python -m pytest tests/unit/registry/test_dependency_resolver.py::test_pip_compile_honors_pip_install_constraints` failed because neither configured constraint file reached pip-compile.

## Passing evidence

The updated resolver supplies the caller’s ordered `PIP_CONSTRAINT` files to
`pip-compile`. All 16 focused resolver tests passed. The same six discovery
launchers passed locally with modules fixture `046d366c190af7a188d6f48953a96edb65e766db`
and the paired core Typer pin. The hosted modules check will use the signed
paired core branch and the same fixture.
