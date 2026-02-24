Public verification keys for bundled module signatures.

Default key path expected by SpecFact CLI runtime:

- Repo source: `resources/keys/module-signing-public.pem`
- Installed package: `resources/keys/module-signing-public.pem`

Runtime resolution order:

1. Explicit public key argument (internal call path)
2. `SPECFACT_MODULE_PUBLIC_KEY_PEM` environment variable
3. Bundled key file (source path first, then installed package path)

Do not store private signing keys in this repository.
