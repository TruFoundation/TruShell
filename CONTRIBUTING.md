# Contributing to TruShell

Thanks for looking. This is a small project and every bit of help counts,
including bug reports and reading code. You don't need to be a shell
expert. Being careful helps more than being clever.

<!-- NOTE FOR MAINTAINERS: this is a draft written without seeing the
     current CONTRIBUTING.md. Diff it against the old one and keep
     anything the old one requires that this one doesn't mention
     (sign-off, license terms, coding rules). -->


## Start here

1. Read the README, especially "Status, plainly". It's short.
2. Skim [`trushell-issues.md`](trushell-issues.md). It's our list of
   known problems. Something on it is probably a good first patch.
3. Build it and break it before you change it.

    git clone https://github.com/TruFoundation/TruShell.git
    cd TruShell
    cargo build
    cargo test

You need current stable Rust (edition 2021). The minimum supported version
has not been verified yet; see TS-004.


## Picking something to work on

- Say what you're doing before you do it. Comment on the issue, or in
  the sprint discussion if there is one, with what you're taking and
  roughly when you expect a PR. Something like: "Claiming: job control
  tests, PR in two weeks, @yourhandle".
- If you're new, say "mentor me" and one of us will pair with you on a
  first PR.
- Claims go stale. If you've gone quiet for a few weeks, someone else
  may pick it up. No hard feelings, life happens.
- Bigger changes, such as the permission model, language semantics, or
  anything that changes what an existing input means, need discussion
  first. Open an issue, describe the problem and what you'd like to do,
  and wait for a reply before writing 2000 lines. It saves you a
  weekend.


## What a good patch looks like

- One logical change per PR. If you find an unrelated bug on the way,
  fix it separately.
- Explain why, not just what. The diff shows what changed. Only you can
  say why it needed to change.
- Add a test. If you fix a bug, the test should fail without your fix.
  If you add a feature, test the odd cases too: empty input, quotes,
  spaces in names, non-UTF-8 bytes.
- Don't reformat code you aren't otherwise changing. It buries the real
  change.
- Run these before you push, and keep the tree warning-free:

      cargo fmt
      cargo clippy --all-targets
      cargo test

- Update the docs in the same PR if you change behaviour a user can see.
  If you fixed something listed in `trushell-issues.md`, remove the entry.
- Keep it portable. Linux is what we test on, but don't assume it
  where you don't have to.


## Commit messages

Start with the part of the tree you touched, then a short summary:

    parser: reject unterminated quotes with a line number
    exec: reset SIGPIPE to default in child processes

If the reason isn't obvious, say it in the body, wrapped at about 72
columns. Mention the issue number. We aren't strict about this. A clear
message beats a perfectly formatted vague one.


## Review

Somebody will read your PR and probably ask questions or ask for
changes. That's normal, and it's about the patch, not about you. We do
the same to each other.

Reviews from people who aren't maintainers are welcome and useful.
"I read this and here's what I didn't understand" is a real
contribution.

We may say no. Usually that's because the change doesn't fit the goals
in the README, in which case we'll try to point you to a better place for
it, often a plugin.


## Reporting bugs

Open an issue. Please include:

- the commit you built from (`git rev-parse HEAD`)
- your OS and kernel (`uname -a`) and the terminal you use
- the exact input, the output you got, and the output you expected
- whether it still happens with no config file

Run with `RUST_BACKTRACE=1` if it crashes and paste the backtrace.

Security bugs don't go in public issues. See [`SECURITY.md`](SECURITY.md).


## Other ways to help

- Try TruShell as your everyday prompt for a few hours (not as your
  login shell) and tell us what annoyed you.
- Write test cases: odd scripts, odd file names, odd terminals.
- Improve the docs, or point out where they're wrong. They probably are.
- Review other people's PRs.


## Behaviour

Be decent. See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
