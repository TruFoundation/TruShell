# Packaging notes

This is the original content of `.github/workflows/ci-packaging.yml`,
moved here because it was plain text, not YAML — GitHub Actions has
never been able to run it as a workflow, despite the `.yml` name and
the `.github/workflows/` path. The real, working workflow is now at
`.github/workflows/ci-packaging.yml` (rewritten) and this file holds
the human-readable notes that used to live inline in the broken one.

---

This branch adds a CI workflow and helper scripts to produce Linux
packages (.deb and .rpm) and run basic acceptance tests.

## What was added

- `.github/workflows/ci-packaging.yml`: GitHub Actions workflow that
  builds the project, runs tests, produces .deb/.rpm packages, uploads
  them as artifacts, and performs simple acceptance tests.
- `packaging/build_rpm.sh`: small helper script that uses `fpm` to
  create an RPM from the release binary.
- `packaging/acceptance_test.sh`: a tiny smoke-test script (expects
  `trushell` in PATH).

## What you should check / customize

- Cargo.toml package metadata: `cargo-deb` derives package metadata
  from `Cargo.toml` under `[package.metadata.deb]`. Add fields like
  `maintainer`, `description`, `assets`, etc., to produce richer
  DEB/RPM metadata.
- Binary name: scripts assume the built binary is
  `target/release/trushell`. If your binary name differs, update the
  workflow and `build_rpm.sh` call accordingly.
- fpm dependencies: building RPM uses `fpm`; CI installs it via gem. If
  you prefer `cargo-rpm` or another tool, adjust `packaging/build_rpm.sh`
  and the workflow.

## How to use locally

- Install cargo-deb: `cargo install cargo-deb`
- Build .deb: `cargo deb`
- Build .rpm: `./packaging/build_rpm.sh` (requires `fpm`)
