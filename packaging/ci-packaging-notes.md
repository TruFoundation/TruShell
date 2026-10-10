# Packaging notes

This repository contains GitHub Actions workflows and helper scripts for
building Linux packages and running packaging acceptance tests.

## What was added

- `.github/workflows/ci.yml`: correctness checks including formatting,
  Clippy, tests, MSRV validation, audit, and dependency checks.
- `.github/workflows/ci-packaging.yml`: workflow for building `.deb` and
  `.rpm` packages and testing the packaged binaries.
- `packaging/build_rpm.sh`: helper script that uses `fpm` to create an RPM
  from the release binary.
- `packaging/acceptance_test.sh`: smoke-test script that expects `trushell`
  to be available in `PATH`.

## Rust toolchain

CI builds with stable Rust. `rust-toolchain.toml` pins local and CI
builds to `stable`; it overrides whatever toolchain a workflow step
installs, so it must name a toolchain that can build the crate.

`rust-version` in `Cargo.toml` (the MSRV) has not been verified yet. Run
the "MSRV find" workflow from the Actions tab and set `rust-version` to
what it reports. The `msrv` job in `ci.yml` then builds with exactly that
version on every PR.

## Debian package

Install `cargo-deb`:

```sh
cargo install cargo-deb --locked
```

Build the Debian package:

```sh
cargo deb
```

The package is written to `target/debian/*.deb` and installs the binary
at `/usr/bin/trushell` (see `[package.metadata.deb]` in `Cargo.toml`).

## RPM package

Install `fpm` and the RPM build tools.

Build the release binary first:

```sh
cargo build --release
```

Build the RPM by passing the release binary as the first argument:

```sh
./packaging/build_rpm.sh target/release/trushell
```

The RPM is written to `target/rpm/trushell_<version>_x86_64.rpm` and
installs the binary at `/usr/local/bin/trushell`.

The script expects the following usage:

```text
./packaging/build_rpm.sh <path-to-release-binary> [out-dir]
```

## Acceptance testing

The acceptance script checks that:

1. `trushell` is available on `PATH`.
2. `trushell --version` prints a version number.
3. `trushell -c 'echo packaging-smoke'` prints `packaging-smoke`.

It checks output, not just exit status: a `trushell` that ignores its
arguments drops into the REPL, reads EOF and exits 0. Neither `--version`
nor `-c` is implemented yet (TS-016), so this check fails until they are.

When running locally against the release binary:

```sh
cargo build --release
PATH="$PWD/target/release:$PATH" ./packaging/acceptance_test.sh
```

The packaging workflow runs the acceptance test twice:

- Once after installing the Debian package.
- Once after extracting the RPM package into a temporary directory.
