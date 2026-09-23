# TruShell: known issues and open work

Last updated: 2026-09-19
Maintainers: TruFoundation

This file lists what we know is broken, missing, or badly designed in
TruShell, roughly in the order we intend to deal with it. It is a working
document. Entries get closed, reworded, or deleted as the code changes.
If something here is wrong, send a patch.

TruShell is alpha. Do not use it as your login shell yet, and do not run
anything you care about under it without a backup.


## How to read an entry

Each entry has an ID, a one-line summary, and a metadata line:

    Kind:      bug | design | missing | doc | infra
    Severity:  blocker | high | medium | low
    Status:    open | in progress | needs design | unconfirmed

"unconfirmed" means the problem is inferred from the README or the specs
and nobody has reproduced it against the code yet. If you can reproduce
it (or show it is not real), say so in the issue and we will fix the
entry. The ID (TS-nnn) is only a label for this file. Each one will get
a real issue number.

Severity is about what happens to a user, not how hard the fix is:

    blocker   we do not tag a release until this is dealt with
    high      needed before 1.0; can cause data loss or wrong behaviour
    medium    real annoyance, workaround exists
    low       polish


## Reporting a bug

Open an issue. Please include:

  - the commit you built from (`git rev-parse HEAD`)
  - OS and kernel version (`uname -a`), and the terminal you use
  - the exact input, the output you got, and the output you expected
  - whether it still happens with no config file

A minimal reproducer beats a long description. If it crashes, run with
`RUST_BACKTRACE=1` and paste the backtrace.

Security problems: do not file a public issue. See the Security tab on
the repository for how to contact us privately.


## Where this is going

The goal, in three lines:

  1. A shell that is safe by default: permissions are explicit,
     destructive actions can be previewed, and there is an audit trail.
  2. A language with real data types, so pipelines stop being a game of
     guessing column positions.
  3. A way to keep running the existing pile of sh and bash scripts
     without rewriting them.

Order of work: get the core semantics right (M1), then the security
model (M2), then structured data and agent mode (M3), then the bash
bridge (M4). Docs and release plumbing run alongside (M5). A feature that
does not help one of those three goals is probably a plugin.


## What v3 already did

The v3 sprint (July 8 to August 9, 2026) closed out this checklist, per
the sprint discussion and the v3 release notes: POSIX spec and
acceptance tests; parser and executor for pipelines and redirects; job
control and signal handling; a PTY abstraction with a Linux backend; a
terminal emulator core; a WASM host with a capability model and example
plugins; a dotfile importer and compatibility linter; a CI acceptance
harness and Linux packages.

Merged is not the same as audited. Many entries below are about
checking, hardening and documenting what the sprint landed, not
starting from scratch. Entries marked "unconfirmed" are still inferred
from documents and haven't been reproduced against the code.


## Index

    M0 housekeeping
      TS-004  ci: we have not audited what CI actually checks

    M1 core shell
      TS-005  parser: a failed parse runs the line as an external command
      TS-006  parser: command-mode quoting and expansion rules unwritten
      TS-007  lang: no control flow
      TS-008  lang: no functions, scoping undefined
      TS-009  exec: no error model
      TS-010  exec: pipeline status, SIGPIPE, stderr ordering
      TS-011  exec: job control merged in v3, needs auditing
      TS-012  exec: signals, zombies, terminal state on exit
      TS-013  expand: globbing, tilde, env, command substitution
      TS-014  builtins: only cd and exit are specified
      TS-015  repl: history and completion status unclear
      TS-016  config: run modes and rc file loading
      TS-017  test: conformance suite, differential tests, fuzzing

    M2 security model
      TS-018  sec: plugin capability model undocumented; extending it needs an RFC
      TS-019  sec: capabilities are not enforced on child processes
      TS-020  sec: --allow / --deny and script permission headers
      TS-021  plugin: capabilities too coarse, API not versioned
      TS-022  sec: plan / dry-run mode
      TS-023  sec: paste and pipe-to-shell protection
      TS-024  audit: no record of who ran what
      TS-025  sec: secrets leak into history, logs and children

    M3 structured data and agent mode
      TS-026  lang: only int, string and units; no list or record
      TS-027  pipeline: values between commands are bytes only
      TS-028  cmd: no machine-readable command descriptions
      TS-029  agent: no non-interactive protocol
      TS-030  errors: free-text messages, no stable codes

    M4 compatibility
      TS-031  compat: no way to run sh/bash scripts safely
      TS-032  compat: linter and dotfile importer exist; scope unclear

    M5 release and docs
      TS-033  release: releases exist; packaging and signing unverified
      TS-034  docs: no man page, no language reference


===========================================================================
M0: housekeeping
===========================================================================

### TS-004  ci: we have not audited what CI actually checks

Kind: infra   Severity: medium   Status: in progress

There is a .github directory and the README says "ensure CI passes", but
we have not written down what it covers. The v3 sprint added a Linux
package-build workflow and an acceptance test script, so it isn't empty;
the question is whether fmt, clippy and the tests run on every PR. A
shell behaves differently per OS (process groups, terminals, signals), so
a Linux-only run is not enough. The README also states Rust 1.70 as the
minimum; nothing we know of tests that.

What we found on closer look, and it's worse than "unaudited":

  - `.github/workflows/ci-packaging.yml` is plain text with a `.yml`
    name. It has never run as a GitHub Actions workflow. See TS-036.
  - `.github/workflows/triage.yml` is a real workflow and is fine. It
    labels PRs; it does not build or test anything.
  - Cargo.toml has an unterminated string
    (`portable-pty = "0.10`), so no `cargo` command has ever worked
    against this manifest as committed. See TS-035. This has to be
    fixed before any of the below can run at all.
  - It's a single package, not a workspace. Use plain `cargo test` /
    `cargo clippy --all-targets`, not `--workspace`.
  - The real tests are `tests/dotfiles.rs`, `tests/posix_compatibility.rs`,
    `tests/terminal_emulator.rs`, `tests/wasm_plugin.rs`. `cargo test`
    picks these up on its own.
  - The acceptance script is `packaging/acceptance_test.sh`, not
    `tests/acceptance.sh`. It checks `trushell -c 'echo ...'` against a
    binary on PATH. Nothing runs it automatically; a workflow has to
    build the binary, put it on PATH, and call it.
  - `rust-version` isn't set in Cargo.toml. 1.70 in the README has never
    actually been tested, since the manifest didn't parse.

Status of the fix: a new `.github/workflows/ci.yml` runs `cargo fmt
--check`, `cargo clippy --all-targets -D warnings` and `cargo test` on
Linux and macOS, a separate MSRV job that reads `rust-version` from
Cargo.toml, an acceptance job that builds the binary and runs
`packaging/acceptance_test.sh`, plus `cargo audit` and `cargo deny`.
`.github/workflows/ci-packaging.yml` has been rewritten as real YAML
(TS-036). `rust-toolchain.toml` and `deny.toml` were added.
`rust-version` still needs to be set by hand once someone determines the
real MSRV (see CARGO_TOML_PATCH.md); nobody has been able to build this
manifest yet to check.

Still to do:

  - fix Cargo.toml's unterminated string first (TS-035), or nothing else
    in this list can even be attempted
  - determine the real MSRV (`cargo +1.70.0 build`, or older/newer until
    one works) and set `rust-version` in Cargo.toml to match
  - fill in `[package.metadata.deb]` in Cargo.toml so `cargo deb` (used
    by the packaging workflow) produces a real package
  - confirm `packaging/build_rpm.sh`'s actual output path and fix the
    artifact-upload step in ci-packaging.yml to match
  - run `cargo deny check` for real once the manifest parses, and correct
    deny.toml's license allow-list against what it actually reports
  - require the `CI ok` status check in Settings → Branches → main

Done when: fmt, clippy, test (Linux + macOS), the MSRV build, the
packaging acceptance smoke test, audit and deny all run on every PR
against a manifest that actually parses, are required by branch
protection, and Cargo.toml's rust-version matches a Rust version someone
has actually built successfully. Windows is out of scope for now, and
the README says so.



===========================================================================
M1: core shell
===========================================================================

### TS-005  parser: a failed parse runs the line as an external command

Kind: design   Severity: blocker   Status: open

Documented behaviour: if a line does not parse as a TruShell expression,
the shell tries to run it as an external command. This is wrong for two
reasons.

A syntax error turns into a PATH lookup. `let x = 1 +` ends up as
"command not found: let", which sends the user looking in the wrong
place. Worse, what a line means now depends on what happens to be in
$PATH. Two machines, same script, different behaviour. We would not
accept that from anyone else's shell.

This path has already produced one security bug: a shell injection in
the OS fallback, fixed earlier (PR #55). One fix doesn't make the design
safe.

<!-- VERIFY: PR #55 is credited to an outside contributor's public
     profile. Confirm the PR and the wording before publishing. -->

Fix: decide the mode from the first token. Reserved words (`let`, `if`,
`for`, `while`, `fn`, `match`, `return`, ...) start language mode.
Anything else is a command. A syntax error is an error and never falls
through. Provide an explicit escape for commands that collide with a
keyword (`^name` or `command name`; not decided).

Done when: no code path retries a failed parse as a command, and a test
shows the same input parses identically with an empty PATH.

This breaks alpha behaviour. It goes in the changelog.


### TS-006  parser: command-mode quoting and expansion rules unwritten

Kind: missing   Severity: blocker   Status: open

All we promise today is that quoted arguments reach external commands
intact. We need the full rules: single and double quotes, backslash
escapes, comments, line continuation, here-documents (do we want them?),
and how `$var` behaves inside quotes.

One decision we want to make on purpose: no implicit word splitting. A
variable containing `a b` expands to one argument. Lists expand to many
(TS-026). That removes the biggest class of bug ShellCheck exists to
catch, and it will surprise people coming from bash. Document it loudly.

Open question: here-documents. Implement `<<EOF`, or say no and offer
something else? We do not have a settled answer.

Done when: rules are in docs/design/command-mode.md before the
implementation PR, and tests cover empty strings, embedded newlines,
and non-UTF-8 bytes in arguments.


### TS-007  lang: no control flow

Kind: missing   Severity: blocker   Status: unconfirmed

The documented language has variables, arithmetic, comparisons and
`{ }` blocks that return a value. We found no mention of conditionals or
loops. Without them nothing longer than a one-liner can be written.

Proposed shape, braces and no `fi`/`done`:

    if $x > 3 { echo big } else { echo small }
    for f in *.log { gzip $f }
    while $i < 10 { let i = $i + 1 }
    match $status { 0 => echo ok, _ => echo failed }

Conditions must be booleans. No truthiness of strings, and no implicit
"exit status 0 means true". Branching on a command's result gets its own
explicit form. Non-boolean condition is a type error.

Done when: grammar is in docs/design/grammar.md, and tests cover
nesting and `break`/`continue` in nested loops.


### TS-008  lang: no functions, scoping undefined

Kind: missing   Severity: blocker   Status: unconfirmed

No way to define reusable code, and no written rule for what `let` does
inside a block. Shadowing? Mutation? Accidental global state is
guaranteed if we leave this open.

Proposal: lexical scoping, blocks open a scope, `let` shadows.
Assignment to an existing variable uses a different form than
declaration (`set x = 5`), so a typo cannot create a new variable.
Functions take named parameters with optional defaults and return their
last expression. Environment variables are separate: `export NAME = v`,
read as `$env.NAME`. Using an undefined variable is an error.

We are deliberately not adding dynamic scoping for compatibility.
Scripts that need it go through TS-031.

Done when: shadowing, outer mutation, recursion, wrong argument count and
undefined variable all have tests, and the error names the variable and
the line.


### TS-009  exec: no error model

Kind: design   Severity: blocker   Status: open

Nothing in the docs says what happens when a command fails. Bash keeps
going by default, which is behind a large share of real-world script
disasters (`cd $dir; rm -rf *`). `set -e` helps a little and has enough
odd edge cases that people stopped trusting it.

Proposal: in non-interactive mode a failing command stops the script
unless its status is consumed (by `if`, `match`, `try`, or `?`). In
interactive mode nothing exits; the last status is `$status`.
Exit codes as users expect from sh: 2 for shell errors, 126 for found
but not executable, 127 for not found, 128+N for death by signal N.

Open question: `try/catch` or a postfix `?`. Pick one, not both.

Done when: docs/design/errors.md exists, and `false; echo unreachable`
prints nothing when run as a script.


### TS-010  exec: pipeline status, SIGPIPE, stderr ordering

Kind: bug   Severity: high   Status: unconfirmed

Pipelines are documented, but not what they mean. Three things we expect
to be wrong until proven otherwise:

  - Status. In bash `false | true` succeeds unless pipefail is set. We
    want a pipeline to fail if any stage fails, by default, with the
    per-stage list in `$pipestatus`.
  - SIGPIPE. The Rust runtime sets SIGPIPE to ignored at startup, and
    ignored signals stay ignored across exec. Children then see EPIPE
    errors where they should quietly die (`yes | head -1`). It has to be
    reset to default in the child before exec.
  - stderr. `&>` is documented. `2>&1` must dup2 onto the same file
    descriptor so output interleaves correctly, not merge two pipes
    later.

Also: never read one stage's output to completion before starting the
next. That is how you get a deadlock on a full 64 KiB pipe buffer.

Done when: `yes | head -1` exits cleanly with no message, and a 3-stage
pipeline moving more than 64 KiB does not hang.


### TS-011  exec: job control merged in v3, needs auditing

Kind: verify   Severity: high   Status: open, unconfirmed

Job control and signal handling were merged in v3 (PR #89). Good. Now we
need to know whether it holds up. Without correct process groups and
terminal ownership, Ctrl-C kills the shell along with the child, Ctrl-Z
does nothing useful, and `&` misbehaves. Nobody has tested this under a
real PTY on more than one terminal yet.

What it should do: one process group per pipeline (`setpgid`), foreground group owns
the terminal (`tcsetpgrp`), shell takes it back after. `jobs`, `fg`,
`bg`, `wait`, trailing `&`. The shell ignores SIGINT, SIGTSTP, SIGTTIN
and SIGTTOU for itself and restores default in children. Only when stdin
is a TTY and the shell is interactive.

Test this under a PTY. Testing job control with plain pipes hides every
interesting bug. Manual checklist goes in tests/manual/jobcontrol.md.


### TS-012  exec: signals, zombies, terminal state on exit

Kind: verify   Severity: high   Status: open, unconfirmed

Signal handling landed with job control in v3 (PR #89); this entry is
the checklist for auditing it. A shell that does not reap children leaves zombies. One that mishandles
signals leaves the terminal in raw mode or hangs on exit. The spec
promises `exit` will not hang waiting for input; that is the easy part.

What we want: SIGCHLD reaps and updates job state. SIGINT at the prompt
clears the line and redraws. SIGHUP and SIGTERM go to running jobs, then
we exit (whether jobs survive SIGHUP, like bash `huponexit`, is a
decision to make and document). Terminal settings are restored on every
exit path, including a panic. A panic prints its report and exits 70
instead of dying mid-line.

Prefer signal-hook or a self-pipe over doing work in a handler.

Done when: after 1000 short commands `ps` shows no defunct children, and
a forced panic in a builtin leaves the terminal usable.


### TS-013  expand: globbing, tilde, env, command substitution

Kind: missing   Severity: high   Status: open

Nothing documents what `*.log`, `~`, `$HOME` or `$(cmd)` do. People will
type all of them in the first five minutes.

Proposal: `~` and `~user` expand at the start of a word. A glob returns a
list, sorted bytewise (not by locale), with no splitting of file names on
spaces. Dotfiles only match a pattern that starts with a dot. `**` is
recursive and does not follow symlink loops. Environment is `$env.NAME`;
plain `$NAME` is a shell variable (TS-008). Command substitution output
is a string with trailing newlines trimmed.

Open question: a glob that matches nothing. sh passes the literal
pattern, which has caused a lot of pain. We lean towards making it an
error (`rm *.tmp` should not run `rm` with a literal `*.tmp`), with an
opt-out. Not decided.

Leading-dash file names (`-rf`) are the classic trap. Tests need files
with spaces, newlines, and leading dashes in their names.


### TS-014  builtins: only cd and exit are specified

Kind: missing   Severity: high   Status: open

Some things must be builtins because a child process cannot do them.
Our minimum list: `cd pwd exit export unset source exec type alias
unalias jobs fg bg wait kill umask history echo true false`, plus
`test`/`[` if the language does not cover it.

Each needs a documented contract: arguments, status, output. Some
details to settle: `cd -` and `$OLDPWD`, `pwd` logical vs physical
(default logical), `echo` with no option parsing beyond `--`, and
`type` telling keyword, function, builtin, alias and file apart.

The list stays closed. A new builtin needs a reason a plugin or an
external tool cannot do the job.

Done when: each builtin has a section in docs/reference/builtins.md,
`--help`, and a success and a failure test.


### TS-015  repl: history and completion status unclear

Kind: doc   Severity: medium   Status: unconfirmed

The README lists "interactive REPL with history" under features and
"command history and tab completion" under the roadmap. Both cannot be
true. Whichever it is, a shell without decent history and completion
does not get used daily, which means nobody dogfoods it.

Plan: pick an established line-editor crate (reedline or rustyline;
write down why in the PR). History goes in
$XDG_STATE_HOME/trushell/history with timestamp, cwd, exit status and
duration; lines starting with a space are not stored. Completion for
commands, paths and variables, with a hook for plugins and command
schemas (TS-028). Multi-line input for unfinished blocks.

Do not read the whole history file at startup. Concurrent shells must not
corrupt it. Target: startup under 50 ms with a 100k-line history.


### TS-016  config: run modes and rc file loading

Kind: missing   Severity: medium   Status: open

The roadmap names `~/.trushellrc` and `.bashrc`/`.zshrc` helpers. It does
not say when any config is read, or how to run a script or a one-liner.
That blocks CI, shebang use, and being a login shell.

Proposal:

    interactive login      reads config   job control   prompt
    interactive non-login  reads config   job control   prompt
    trushell -c 'cmd'      no config      no            no
    trushell script.tru    no config      no            no

Non-interactive runs never read user config. That one rule makes scripts
reproducible. Config path is $XDG_CONFIG_HOME/trushell/config.tru with
~/.trushellrc as fallback. Add `--no-config` and `--config FILE`.
`#!/usr/bin/env trushell` must work, script arguments in `$args`. An
error in the config file is reported and the shell still starts.

Also needs a documented recipe for /etc/shells and `chsh`, and for
falling back to bash when things go wrong.


### TS-017  test: conformance suite, differential tests, fuzzing

Kind: infra   Severity: high   Status: open

A shell has too many corner cases to think of by hand. tests/ exists,
but we have not written down a strategy.

Three layers:

  1. Golden tests: tests/conformance/*.tru with .out, .err and .status
     next to each. One behaviour per file. Runs on every PR.
  2. Differential tests: run the same snippet through dash and
     TruShell for the parts that are supposed to match sh (quoting,
     redirections, pipelines). Deliberate differences go on an
     allow-list, each with a reason. Skip cleanly when dash is absent.
  3. Fuzzing: cargo-fuzz on the lexer and parser. Must never panic or
     hang, and print-then-reparse must be stable. Nightly job, ten
     minutes.

Every fixed bug adds a regression test. That goes in CONTRIBUTING.


===========================================================================
M2: security model
===========================================================================

### TS-018  sec: plugin capability model undocumented; extending it needs an RFC

Kind: design   Severity: blocker   Status: needs design

The v3 sprint shipped a WASM plugin host with a capability model
(today the documented capabilities are `logging` and `environment-get`).
We haven't written down how that model is designed or what it promises.
Nothing else in the shell has capabilities: a script or command launched
from TruShell can do anything the user can. If "safe by default" is
going to mean something, the model gets written down and reviewed first,
or the enforcement gets written twice.

The RFC (docs/design/capabilities.md) has to cover:

  - Threat model: user vs a malicious or buggy script, user vs an agent
    that has been prompt-injected, system vs a compromised plugin. And
    an explicit list of what we do NOT protect against (root, kernel
    bugs, side channels).
  - Vocabulary, first cut: fs.read:<path> fs.write:<path>
    fs.exec:<path> net.connect:<host:port> net.none env.read:<name>
    proc.spawn:<cmd> tty
  - Defaults: deny in sandboxed mode, allow in plain interactive mode
    so daily use does not break.
  - Children can be narrowed, never widened, without a new user decision.
  - Paths: canonicalise, resolve symlinks, be honest about TOCTOU.

Prior art we should read and cite: Landlock, OpenBSD pledge/unveil, Deno
permissions, WASI capabilities.

Done when: RFC merged after at least one outside review thread is
resolved, and the vocabulary is versioned.


### TS-019  sec: capabilities are not enforced on child processes

Kind: missing   Severity: high   Status: needs design

A capability checked only inside the shell is advisory. A permitted
`sh -c 'curl ...'` walks straight around it. Real enforcement has to be
in the kernel.

Linux first: Landlock rulesets applied in the child before exec
(filesystem rules need 5.13+; TCP connect/bind rules need a newer ABI,
detect at runtime and say what is actually enforced). seccomp-bpf for a
short deny-list. `no_new_privs` on every sandboxed child. Close every
descriptor that was not explicitly passed (CLOEXEC everywhere,
`close_range`), because descriptors opened before the sandbox stay
valid.

If the kernel cannot do what was asked: refuse in strict mode, warn in
permissive mode. Never quietly run unsandboxed after the user asked for a
sandbox. macOS is best effort via Seatbelt (deprecated, still works) and
the docs will say so.

Done when: `trushell --allow fs.read:. --deny net -c 'curl example.com'`
fails and names the missing capability, and `trushell --check-sandbox`
prints what this kernel can enforce.


### TS-020  sec: --allow / --deny and script permission headers

Kind: missing   Severity: high   Status: open

Reviewing what a script may do should take seconds, not a read of the
whole file.

    trushell --allow fs.read:./src --allow fs.write:./build --deny net build.tru

and in the script itself:

    #!/usr/bin/env trushell
    #! allow fs.read:./src
    #! allow fs.write:./build
    #! deny net

Flags can narrow what the header asks for, never widen it. A header that
asks for more than the caller granted prompts, or fails when
non-interactive. `trushell --explain script.tru` prints the effective
permissions without running anything; its output must be stable, since
people will diff it in code review. Permission denial exits with 77
(EX_NOPERM).

Header lines are plain comments to every other shell. We are not adding
syntax another shell would try to execute.


### TS-021  plugin: capabilities too coarse, API not versioned

Kind: design   Severity: high   Status: open

The plugin host is the most promising part of the tree. Today a plugin
can have `logging` or `environment-get`, and the manifest carries an
`api_version` with no written compatibility policy. Nothing like "read
only this one variable" exists, so plugins cannot do anything useful yet.

Fix: use the same permission language as TS-018 for plugins (same names,
same scoping). Add host functions behind capabilities: scoped fs, net and
spawn, and `value.emit` for structured output (TS-027). Fuel/time and
memory limits per call. Publish the manifest as a JSON Schema and reject
unknown fields. Additive change bumps minor, breaking bumps major, the
host supports current and previous major. A plugin importing an
undeclared host function must fail to instantiate (documented already;
keep it and test it).

Every host function is attack surface and gets a security review.
Denied calls go to the audit log (TS-024).


### TS-022  sec: plan / dry-run mode

Kind: missing   Severity: high   Status: open

Nothing tells the user what a command is about to do before it does it.
`rm -rf $dir/` with an empty `$dir` is only visible afterwards.

Proposal: `trushell --plan script.tru` and an interactive `plan { ... }`
block. Mutating builtins (`cp mv rm`, redirections, `export`, `cd`)
report their effect without doing it ("would remove 4312 files under
./build"). External commands are opaque; the shell cannot know what they
do, so it says "would run: cmd args, with capabilities ..." and marks
them opaque. A command schema (TS-028) may declare a `--dry-run` flag
that we pass along. `--confirm-over N` asks before one operation touches
more than N files.

A plan is a prediction, not a guarantee, and the output says so. A plan
that says "ok" for something it cannot see is worse than no plan.

Done when: plan mode makes zero writes (checked against a read-only
filesystem or by mtimes) and every mutating builtin has a plan or is
marked opaque.


### TS-023  sec: paste and pipe-to-shell protection

Kind: missing   Severity: medium   Status: open

Pasted commands are an everyday attack path: `curl ... | bash` from a
README, look-alike Unicode in hostnames, escape sequences hidden in the
pasted text. Terminals show all of it without complaint.

Fix: bracketed paste, so pasted text lands in the buffer and never runs
until Enter. Before execution, scan the buffer for network fetch piped to
an interpreter, non-ASCII in hostnames, control characters and ANSI
escapes, and invisible Unicode (zero-width, bidi overrides). On a
finding, show it with code points and ask again. Modes: warn, block,
off. Off for non-interactive runs. All checks are local.

This is a guard for the person at the keyboard. It is not a security
boundary and the docs will say so. No false positives on plain ASCII like
`grep foo | wc -l`.


### TS-024  audit: no record of who ran what

Kind: missing   Severity: medium   Status: open

With a person, some scripts and an automated agent all working under one
account, nobody can answer "who ran this, when, with what permissions,
and what happened?" The SQLite store on the roadmap fits here.

Proposal: append-only log in $XDG_STATE_HOME/trushell/audit.db (WAL
mode, mode 0600). Per command: time, duration, cwd, expanded argv,
status, effective capabilities, session and parent session, actor.
Actor is `human`, `script:<path>`, `agent:<name>` or `plugin:<name>`;
agents identify themselves via TRUSHELL_ACTOR, we do not try to guess.
Denied requests are logged with the reason. `trushell audit
list|show|export --json`. Short default retention. Can be turned off
completely. A hash chain over rows catches casual tampering; it does not
stop someone who can rewrite the file, and we will say so.

Done when: schema is versioned with a migration test, eight concurrent
writers do not corrupt it, and logging adds under 1 ms to the median
command.


### TS-025  sec: secrets leak into history, logs and children

Kind: bug   Severity: high   Status: unconfirmed

Passwords, tokens and API keys typed on a command line or exported into
the environment end up in history files and logs. Every shell has this
problem. We should not repeat it.

Proposal: a `secret` value type that prints as `<secret>` and is never
written to history, audit log or plan output. Redaction patterns for
common token formats (AWS keys, JWTs, bearer tokens, ghp_...) plus
user-supplied ones. Variables matching `*_TOKEN`, `*_SECRET`,
`*_PASSWORD`, `*_KEY` are marked secret when read from the environment.
Sandboxed children get a minimal environment (PATH, HOME, LANG, TERM)
plus whatever `env.read:` allows. Lines starting with a space stay out of
history.

Pattern-based redaction always misses something. The typed `secret` is
the dependable path and the one the docs should push.


===========================================================================
M3: structured data and agent mode
===========================================================================

### TS-026  lang: only int, string and units; no list or record

Kind: missing   Severity: high   Status: open

The language has integers, strings and unit numbers like `1mb` and
`500ms`. Without lists and records, structured pipelines (TS-027) and
no-splitting argument passing (TS-006) have nothing to carry.

    let xs = [1, 2, 3]
    let user = { name: "alice", uid: 1000 }
    let p = /var/log/syslog        # a path, not a string
    let limit = 10mb               # 1kb is 1000 bytes, 1kib is 1024
    let t = 2s + 500ms

Types: bool, int, float, string, path, size, duration, list, record,
secret, null. Arithmetic only where it means something (`size + size`
yes, `size + duration` no). No implicit string-to-number coercion.
Lists expand to several arguments in command mode; records are an error
unless converted explicitly.

Units are already a distinctive feature. Keep them, and make sure `1mb`
can never quietly turn into a plain integer.

Done when: docs/reference/types.md has the rule table and every
operator/type pair has a test, error cases included.


### TS-027  pipeline: values between commands are bytes only

Kind: missing   Severity: high   Status: open

Between external tools a pipeline carries bytes, so pulling out a field
means `awk`, `cut`, or a regex against output made for humans.

Proposal: between shell-native stages (builtins, functions, plugins)
values travel typed. At the boundary with an external command they are
serialised: lines for a list of strings, JSON for everything else,
overridable with `to json`, `to lines`, `to csv`. In the other direction
`from json`, `from csv`, `from lines`, `from toml`. Built-in stages:
`where select sort-by group-by take`. On a terminal, structured output
renders as a table; to a pipe or file it is JSON.

    curl -s https://example.test/api | from json | where status == "failed" | select id name

We never parse external output silently. Conversion is always explicit,
so a plain `ls | grep foo` keeps working as anyone expects. A gigabyte of
bytes moving between two external commands is not touched or buffered by
the shell.


### TS-028  cmd: no machine-readable command descriptions

Kind: missing   Severity: low   Status: needs design

Flags are discoverable only through man pages. Completion scripts are
written by hand, per shell, per tool. New users cannot find options, and
agents guess flags and get them wrong.

Idea: a small schema file (TOML or JSON) per command: subcommands, flags
with types and defaults, positionals, whether the command is destructive,
optional dry-run flag. Looked up under $XDG_DATA_HOME/trushell/schemas/
and a system directory. Used for completion (TS-015), `help`, optional
argument validation, plan hints (TS-022) and agent tool descriptions
(TS-029). Ship schemas for a few common tools (git, ls, cp, mv, rm, tar,
curl) kept apart from the core so they can update independently.

Keep the format small. The more it models, the less likely the people who
maintain other tools are to ever adopt it.


### TS-029  agent: no non-interactive protocol

Kind: missing   Severity: high   Status: open

Automated agents currently drive a shell through a pseudo-terminal,
scrape prompts and screen output, and use whichever shell they were
started under (in practice bash or zsh, whatever the user runs
interactively). It is slow, ambiguous, and hard to secure.

Proposal: `trushell --agent` speaks JSON lines on stdin/stdout. No
prompt, no colour, no TTY assumptions. Request:
`{"id":1,"cmd":"ls -la","cwd":"...","timeout_ms":5000}`. Events:
`started`, `stdout`, `stderr`, `exited` (status, duration), `denied`
(with the missing capability). Sandboxed by default with permissions
given at start. Every command logged with actor `agent:<name>`.
Session state can persist or reset per request, and the request says
which. Output size limits with a truncation marker. Timeout and
cancellation kill the whole process group. `"plan": true` supported.

The protocol is not tied to one vendor. Anything that reads and writes
JSON lines should be able to use it. We want a reference client in
examples/agent-client/ that fits in about 100 lines.


### TS-030  errors: free-text messages, no stable codes

Kind: design   Severity: medium   Status: open

Scripts, tests and agents that need to react to one specific failure have
to match on strings, and those change whenever we reword something.

Fix: one central error type. Every shell-generated error has a stable
code (`TS0101`), a short message, a source span, optional help. Codes
are listed in docs/reference/errors.md and never reused.
`--error-format=human|json`. Human format looks like a compiler
diagnostic: message, the source line, a caret under the span. Colour off
when stderr is not a TTY or NO_COLOR is set. Exit statuses stay as in
TS-009. Errors from external commands are not rewritten; we report the
status and point at the captured stderr.

Add codes as the language grows. Retrofitting them after a hundred
message strings exist is miserable.


===========================================================================
M4: compatibility
===========================================================================

### TS-031  compat: no way to run sh/bash scripts safely

Kind: missing   Severity: high   Status: open

The world's install scripts, Dockerfiles, CI steps and README snippets
are sh or bash. A shell that cannot run them stays a curiosity. We are
not going to reimplement bash (TS-001), and doing so would import its
problems.

The v3 goal was that scripts written for /bin/sh work here, with a
fallback when they don't. The compatibility spec covers four behaviours
(see TS-002), so we're a long way from that, and bash-only features are
a separate and larger problem.

Instead: `trushell compat sh script.sh` and `trushell compat bash
script.sh` run the script with the system interpreter, wrapped in the
sandbox from TS-019. We do not parse it. When TruShell is asked to run a
file whose shebang names sh or bash, it does the same and prints the
effective capabilities first. `trushell compat bash` also opens a
sandboxed subshell for a one-off paste from some documentation.
Missing-capability failures get translated into readable hints.

The guarantee is narrow and the docs will state it: the sandbox limits
what the script can touch. It does not make the script correct.

Done when: a known bash script (arrays, `[[ ]]`, process substitution)
runs unchanged, a second run shows it cannot read outside its allowed
paths, and exit status and signals pass through untouched.


### TS-032  compat: linter and dotfile importer exist; scope unclear

Kind: doc   Severity: low   Status: open, unconfirmed

The v3 sprint added a dotfile importer and a compatibility linter, but
we haven't documented what either checks. People with existing scripts
want to know how much would change before they decide anything, so step
one is writing down what exists and where the gaps are.

What we'd like the tools to cover:

`trushell lint file.tru` checks TruShell code: unused variables,
shadowing, unreachable code, unchecked command failures, deprecated
syntax. `trushell lint --from-bash file.sh` reports which constructs have
a direct equivalent, which need a rewrite, and which should stay under
`compat`. It is advisory. It does not translate; a real translator has a
long tail of edge cases and is a much larger project. Rules are named and
can be silenced with a comment. Exits non-zero on findings unless
`--exit-zero`.


===========================================================================
M5: release and docs
===========================================================================

### TS-033  release: releases exist; packaging and signing unverified

Kind: infra   Severity: medium   Status: open, unconfirmed

There are tagged releases (v1.0, v1.3, v2 and v3 among them). v3 added a
CI workflow for Linux package building, an RPM build script and
packaging notes. What we don't know is whether the packages install
cleanly on a fresh box, whether releases are signed or checksummed, and
how much of the process is still manual. A shell has to be easy to drop
into a container or onto a server, or it will not be tried.

Plan: SemVer tags built by CI, with release notes (the existing tags
are v1.0, v1.3, v2, v3, which aren't SemVer). Static binaries
for x86_64 and aarch64 musl, and macOS. SHA-256 checksums and detached
signatures (minisign or cosign; pick one and document verification).
SBOM with each release. Pin the toolchain in rust-toolchain.toml.
.deb, .rpm, Homebrew and AUR packages; finish each one or delete it, and
put the status in packaging/README. The binary only goes into
/etc/shells when the user asks.

Our install docs will not tell anyone to `curl | sh` without also
showing the verified alternative. Recommending pipe-to-shell installs in
a project about safer shells would be embarrassing.

Done when: a tag produces every artifact with no manual step, the binary
runs in an alpine and a scratch container, and somebody who did not write
the verification instructions has followed them.


### TS-034  docs: no man page, no language reference

Kind: doc   Severity: medium   Status: open

Everything lives in one README. There is no trushell(1), no language
reference, and no guidance for people moving from bash.

Layout under docs/: guide/ (install, first steps, moving from bash, the
permission model, agents), reference/ (grammar, types, builtins, error
codes, capabilities, config, plugin manifest), design/ (the RFCs the
entries above refer to). man/trushell.1 and man/trushell-lang.7
generated from the reference and installed by packages. CI builds the
docs, checks links, and runs the examples so they cannot go stale.

Write a "Differences from bash" page early: every deliberate
incompatibility, with the reason (no word splitting, fail-fast by
default, undefined variables are errors, ...). It will be the most-read
page we have. A PR that changes user-visible behaviour updates the docs
in the same PR; that goes in the PR template.


===========================================================================
Things we are not going to do
===========================================================================

  - Bug-for-bug bash compatibility. Use `compat` (TS-031).
  - Windows support, for now.
  - A GUI or an editor. The terminal emulator core added in v3 is a
    separate question we haven't settled.
  - Task management or time tracking in core (TS-003).


## Working on these

Pick an entry, say so in its issue so two people do not do the same work,
and open the PR against main. Design-heavy entries (marked "needs
design") want the RFC discussed first; please do not send a 2000-line
patch for TS-018. Every PR should pass `cargo fmt`, `cargo clippy` and
`cargo test`, and add a test for whatever it fixes.

When you fix something listed here, delete the entry (or move it to the
changelog) in the same PR.
