# Contributing

## Development workflow

1. Create a focused branch from `main`.
2. Keep source changes separate from generated experiment artifacts.
3. Add or update tests when changing disagreement, buffer, co-evolution, or
   regularization behavior.
4. Run the relevant commands from the root README.
5. Open a pull request that explains the research motivation, implementation,
   validation, and any expected metric changes.

## Repository hygiene

- Use environment variables for credentials and keep `.env` local.
- Do not commit model weights, adapter archives, dependency caches, or raw
  downloaded datasets.
- Prefer descriptive `snake_case` names for new Python modules and directories.
- Avoid adding another copy of a module to an experiment bundle. Build bundles
  from the canonical source at release time.
- Record the dataset version, model identifier, random seed, and command line
  for results intended for comparison.

## Commit style

Use short, imperative commit subjects, for example:

```text
Add adaptive hard-case threshold
Fix confidence normalization
Document Agent-C calibration run
```
