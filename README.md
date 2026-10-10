# TruShell

A shell, written in Rust. It is alpha. It is not finished, it is not a
bash replacement, and you should not trust it with anything you can't
afford to lose.

We're building it because we think a shell can be safer by default than
the ones we all use, and the only way to find out whether that's true is
to write one and see. This is what exists so far, what doesn't, and what
we're still arguing with ourselves about.

Feedback is very welcome, especially the unflattering kind.


## Where it came from

TruShell did not start as a shell in the strict sense. It began as a
Python program, a "productivity shell" with todos, jokes, world clocks
and a CSV viewer. Version 2 threw the engine out and rewrote it in
Rust. In July and August 2026 we ran a sprint (v3) to turn it into what
it is trying to be now: a Linux- and POSIX-compatible shell with a
terminal core and sandboxed WASM extensions.

That history is why there are odd leftovers lying around: task-management
ideas in the old roadmap, a few repository topics, possibly some old
package pages. We know. They're on the cleanup list.


## Status, plainly

- Alpha. Things break, and behaviour changes between commits without notice.
- Don't set it as your login shell.
- Don't run scripts you don't trust under it and assume it protects you.
  WASM plugins run inside a capability sandbox. The commands you type
  do not. They go out with your full privileges, same as in any other
  shell.
- Nobody outside the project has done a security review. We have already
  had one shell-injection bug in the fallback path (see below) and we
  assume there are more.
- We haven't measured performance. Rust rules out a class of memory
  bugs. It does not make a design safe or fast, and we won't claim
  either until we have numbers or a review.
- Linux is the platform we build and test on. The PTY layer is Linux-only
  as far as we know. macOS may work, may not. Windows: no.


## What works today

As far as we know. This list is only as good as our testing, and the
v3 sprint moved a lot of code quickly.

- An interactive prompt that runs ordinary Unix commands (`ls`, `cat`,
  `grep`, ...) through your PATH.
- Pipes and redirects, including `&>`.
- Job control and signal handling (merged in v3, so young).
- Variables (`let name = "Alice"`, used as `$name`), integer arithmetic,
  comparisons, and `{ ... }` blocks that return their last value.
- Numbers with units: `1mb`, `500ms`.
- A PTY abstraction with a Linux backend, and a terminal emulator core
  (VT sequences, Unicode). Both are new and neither has had much abuse.
- A WASM plugin host with a capability model. A plugin ships a JSON
  manifest declaring what it needs, and a plugin that imports a host
  function it didn't declare fails to load. Example plugins live in
  `examples/plugins/`.
- A dotfile importer and a compatibility linter.
- A POSIX compatibility spec with acceptance tests. Read the spec before
  you get excited: it covers a small, specific set of behaviours, not
  "POSIX" as a whole.
- Linux packages (.deb/.rpm) and release binaries built by CI.

<!-- VERIFY each bullet against main before publishing. Several come from
     the v3 sprint checklist and release notes, not from us running the
     code. Delete anything that doesn't hold up. -->


## What doesn't work yet

- The docs don't describe `if`, `for`, `while` or functions, or how
  variable scope works. If they exist, the docs are wrong. If they
  don't, that's the biggest gap between us and a shell you can write
  scripts in.
- Our goal is that scripts written for `/bin/sh` run, with a fallback
  when they don't. We are nowhere near "run any sh script". The
  compatibility spec is a start, not a finish, and bash-only features
  are a separate, larger problem.
- The commands you run are not sandboxed. Only plugins are.
- Tab completion and history: the README used to list history as both a
  feature and a roadmap item. We need to find out which is true.
- Not everything on this list has been checked against the code.

<!-- VERIFY: several of these come from missing documentation, not from
     reading the source. Confirm each one, then fix the wording. -->


## Something we know is wrong

If a line doesn't parse as a TruShell expression, we hand it to the
system as an external command. It sounds friendly and it's a bad idea: a
typo in a TruShell line can turn into a PATH lookup, what a line means
depends on what happens to be installed on the machine, and this is
exactly the kind of path where injection bugs live. It has bitten us once
already. We plan to remove the fallback, or at least make it explicit
(see TS-005 in [`trushell-issues.md`](trushell-issues.md)). It will
break some things when we do. That's fine, this is alpha.

<!-- VERIFY: "bitten us once already" and the mention in "Status, plainly"
     refer to a shell-injection fix in the fallback path, PR #55, which I
     found credited on an outside contributor's public profile. Confirm
     the PR before keeping the claim. -->

The full list of known problems, ugly parts and missing pieces is in
[`trushell-issues.md`](trushell-issues.md). We keep it up to date on
purpose. If you find something that isn't on it, that's a bug in the
list.


## Try it

You need current stable Rust (edition 2021). The minimum supported version
has not been verified yet; see TS-004.

    git clone https://github.com/TruFoundation/TruShell.git
    cd TruShell
    cargo build --release
    ./target/release/trushell

Or, while hacking:

    cargo run

A session looks like this:

    trushell> let name = "Alice"
    trushell> let age = 30
    trushell> let next_year = $age + 1
    trushell> echo "Hello, $name! Next year you'll be $next_year."
    trushell> cat server.log | grep "ERROR" > errors.txt
    trushell> let sum = { let a = 5; let b = 10; $a + $b }

Tests:

    cargo test

Release binaries and Linux packages come out of CI. See the Releases
page and `packaging/` for what is actually published. Treat them as
lightly tested.

Please run `cargo fmt` and `cargo clippy` before sending anything.


## Where we're heading

The goals we set for, in our own words at the time:

1. Scripts that work with `/bin/sh` should work here too, with a fallback
   when they don't.
2. Processes handled correctly: job control, signals, pipelines.
3. A small, fast core. Optional features load only when needed.
4. Safe by default: extensions run in a sandbox that limits what they
   can do.

Ideas we'd like to try after that. None of these are built, and some may
turn out worse than they sound:

- Extending the permission model from plugins to the commands you run,
  with a way to preview destructive actions and a record of who ran what.
- Data with types: lists and records through a pipeline instead of
  guessing at columns in text.
- A plain JSON interface for automated agents, which today scrape
  terminals built for humans.
- Running old bash scripts inside a sandbox so nobody has to rewrite
  them to try this.


## Not doing

- Bug-for-bug bash compatibility. We want to run sh scripts and
  eventually bash ones (through a bridge), not become bash.
- A task manager or time tracker inside the shell. It's a Python-era
  idea and we lean towards moving it out of core (TS-003).
- Windows support, for now.


## Help wanted

There's plenty to do, and most of it is not glamorous.

- Read [`trushell-issues.md`](trushell-issues.md), pick something, and
  say so in the issue so two people don't do the same work.
- Try it, break it, and tell us how. A minimal reproducer with the
  commit you built from and your OS is worth more than a long essay.
- Tell us what you think of the design. What would stop you from ever
  using a shell like this? That's very useful to know.
- Review code. Very few people outside the project have looked at it,
  and it would help.

Bigger design questions (the permission model, the language semantics)
get discussed before they get written. Please don't send a 2000-line
patch for something we haven't talked about. It isn't a rule made to
annoy you. It's so we don't waste your weekend.

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`NEW_CONTRIBUTOR_CHECKLIST.md`](NEW_CONTRIBUTOR_CHECKLIST.md) first.
Be decent to each other ([`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)).


## Project

- Bugs and questions: open an issue, or start a discussion.
- Security problems: don't file a public issue. See
  [`SECURITY.md`](SECURITY.md).
- How the project is run: [`GOVERNANCE.md`](GOVERNANCE.md)
- License: see [`LICENSE.md`](LICENSE.md)
- Maintained by TruFoundation.

It's alpha. It will eat your homework. Back it up.
