# yaml and workflows: formatting and linting

This project standardizes YAML and GitHub workflow hygiene with one script and Hatch wrappers.

commands (via hatch)

- format everything: `hatch run yaml-fix-all`
- check everything: `hatch run yaml-check-all`
- format yaml (all, including workflows): `hatch run yaml-fmt`
- lint yaml (non-workflow): `hatch run yaml-lint`
- format workflows: `hatch run workflows-fmt`
- lint workflows: `hatch run workflows-lint`

what each does

- `yaml-fmt` / `workflows-fmt`
  - Uses Prettier to fix whitespace, indentation, and final newline across `*.yml` and `*.yaml` files.
- `yaml-lint`
  - Uses yamllint with repo .yamllint (workflows excluded; they are handled by actionlint).
- `workflows-lint`
  - Uses actionlint for semantic GitHub Actions validation. It tries a local actionlint, then `./bin/actionlint`, then a Docker fallback.

when to use

- before committing: `hatch run yaml-fix-all`
- in CI or before PR: `hatch run yaml-check-all`
- after editing workflows: `hatch run workflows-fmt && hatch run workflows-lint`

configuration

- `.yamllint`: line-length raised to 140, workflows ignored, trailing spaces and final newline enforced.
- `.prettierrc.json`: printWidth 100; YAML tab width 2.

requirements

- `npx` (Node.js installed) for Prettier.
- `actionlint` for workflows (install locally, download to `./bin`, or rely on Docker):

  ```bash
    curl -sSL <https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash> | bash -s -- -b ./bin
  ```
