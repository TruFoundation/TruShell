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

The project uses Rust `1.70.0` as its selected MSRV and CI toolchain.

`Cargo.toml` must contain:

```toml
[package]
rust-version = "1.70.0"
```

`rust-toolchain.toml` must contain:

```toml
[toolchain]
channel = "1.70.0"
components = ["rustfmt", "clippy"]
```

## Debian package

Install `cargo-deb`:

```sh
cargo install cargo-deb --locked
```

Build the Debian package:

```sh
cargo deb
```

The package is written to:

```text
target/debian/*.deb
```

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

The RPM is written to:

```text
target/rpm/*.rpm
```

The script expects the following usage:

```text
./packaging/build_rpm.sh <path-to-release-binary> [out-dir]
```

## Acceptance testing

The acceptance script checks that:

1. `trushell` is available on `PATH`.
2. `trushell --version` exits successfully.
3. `trushell -c 'echo packaging-smoke'` exits successfully.

When running locally against the release binary:

```sh
cargo build --release
PATH="$PWD/target/release:$PATH" ./packaging/acceptance_test.sh
```

The packaging workflow runs the acceptance test twice:

- Once after installing the Debian package.
- Once after extracting the RPM package into a temporary directory.
