# Release Notes

This directory contains human-readable release notes used by the GitHub Release
workflow.

When a release changes operator or user behavior, add a Markdown file named after
the release tag:

```text
docs/releases/notes/<release_tag>.md
```

The release packaging script automatically includes the matching file in the
generated `release-summary.md`.

## Published Notes

- [v0.2.2-internal.1](v0.2.2-internal.1.md): internal dogfood API smoke
  evidence and API version metadata alignment.
- [v0.2.1-internal.1](v0.2.1-internal.1.md): packaged contract resources and
  release consumer smoke verification.
- [v0.2.0-internal.1](v0.2.0-internal.1.md): formal GitHub Release mechanism and
  internal release package publication.
