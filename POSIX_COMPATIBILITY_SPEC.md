# POSIX compatibility spec for TruShell v3

This document captures the minimum POSIX-oriented compatibility expectations for the v3 shell experience in TruShell. The goal is to preserve familiar shell behavior for common builtins and external commands while keeping the language parser available for TruShell-specific expressions.

## Scope

The v3 shell should support:

- interactive prompt behavior with standard input and output
- basic builtins such as `cd` and `exit`
- execution of external commands through the host system PATH
- preservation of quoted arguments for external commands
- simple fallback behavior when a line is not a TruShell expression

## Acceptance criteria

### 1. `cd` without arguments

- Running `cd` changes the shell working directory to the user's home directory.
- A following `pwd` command prints that directory.

### 2. Quoted arguments for external commands

- A command such as `printf '%s %s\n' hello world` receives the arguments `hello` and `world` exactly as written.
- The shell should preserve the quoting semantics required for the external process to see the intended arguments.

### 3. Builtin exit behavior

- `exit` terminates the interactive shell cleanly.
- The shell should not hang waiting for more input after receiving `exit`.

### 4. Fallback to external commands

- If a line cannot be parsed as a TruShell expression, the shell should attempt to execute it as an external command.
- This allows ordinary POSIX-style commands to continue working in the REPL.
