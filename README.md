
```
████████████████████████████████████████████████████████████████████████
█                                                                      █
█  ████████╗██████╗ ██╗   ██╗███████╗██╗  ██╗███████╗██╗     ██╗       █
█  ╚══██╔══╝██╔══██╗██║   ██║██╔════╝██║  ██║██╔════╝██║     ██║       █
█     ██║   ██████╔╝██║   ██║███████╗███████║█████╗  ██║     ██║       █
█     ██║   ██╔══██╗██║   ██║╚════██║██╔══██║██╔══╝  ██║     ██║       █
█     ██║   ██║  ██║╚██████╔╝███████║██║  ██║███████╗███████╗███████╗  █
█     ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝  █
█                                                                      █
█                                                                      █    
█                      The Next-Generation Shell                       █
█                    Built in Rust for Performance                     █
█                                                                      █
████████████████████████████████████████████████████████████████████████
```

# TruShell

A general-purpose shell written in Rust. Like Bash and Zsh, but with modern syntax and task management baked in.

Status: Alpha (actively developing)

---

## QUICK START

### Installation

```bash
$ git clone https://github.com/TruFoundation/TruShell.git
$ cd TruShell
$ cargo build --release
$ ./target/release/trushell
```

Or run directly:

```bash
$ cargo run
```

### Your First Commands

```bash
Welcome to TruShell Native Engine
trushell> pwd
/home/user/projects

trushell> ls -la
total 48
drwxr-xr-x  5 user  staff   160 Jul  5 12:34 .
-rw-r--r--  1 user  staff  1234 Jul  05 12:30 README.md

trushell> let x = 42
trushell> let result = $x * 2
```

---

## WHAT IS TRUSHELL?

TruShell is a modern shell that:

- Runs standard Unix commands: ls, cat, grep, cd, etc.
- Understands expressions: arithmetic, variables, comparisons
- Chains operations: pipes, redirects, filters
- Manages tasks: integrate time tracking and task management (coming soon)
- Written in Rust: fast, safe, and reliable

Think of it as Bash meets a modern expression language. You get the power of the shell with cleaner, more intuitive syntax.

---

## FEATURES

### Interactive REPL

Just like your favorite shell, TruShell reads input, evaluates it, prints output, and loops:

```bash
trushell> echo "Hello, World!"
Hello, World!

trushell> exit
Goodbye!
```

### Variables and Expressions

```bash
# Declare variables with 'let'
trushell> let name = "Alice"
trushell> let age = 30

# Use variables with $
trushell> let next_year_age = $age + 1

# Arithmetic
trushell> let sum = 10 + 5
trushell> let product = 3 * 7
```

### Comparisons and Logic

```bash
trushell> let is_adult = $age > 18
trushell> let is_match = "hello" == "hello"
trushell> let not_empty = "text" != ""
```

### Number Units

```bash
# Numbers can have units for readability
trushell> let file_size = 1mb
trushell> let timeout = 500ms
```

### Pipes and Redirects

```bash
# Chain commands with pipes
trushell> cat data.txt | grep "error"

# Redirect output to files
trushell> echo "Hello" > greeting.txt
trushell> echo "World" >> greeting.txt

# Redirect stdin
trushell> cat < input.txt > output.txt

# Combine stdout and stderr
trushell> command &> log.txt
```

### Code Blocks

```bash
# Group statements in blocks
trushell> let data = { let x = 5; let y = 10; $x + $y }
```

---

## HOW IT WORKS

TruShell uses a classic interpreter pipeline:

```
┌─────────────────────────────────────────┐
│         User Input (REPL)               │
├─────────────────────────────────────────┤
│  Lexer: Convert text -> tokens          │
├─────────────────────────────────────────┤
│  Parser: Convert tokens -> AST          │
├─────────────────────────────────────────┤
│  Executor: Run AST or fallback to shell │
├─────────────────────────────────────────┤
│  Output / Side Effects                  │
└─────────────────────────────────────────┘
```

### Example: Parsing 'let x = 5 + 3'

Tokenize:
```
[let, x, =, 5, +, 3]
```

Parse:
```
Let {
  name: "x",
  value: BinaryOp {
    left: 5,
    op: Add,
    right: 3
  }
}
```

Execute:
```
Variable x is now 8
```

---

## COMMAND REFERENCE

### Built-in Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| let | let name = expression | Declare a variable |
| exit | exit | Leave the shell (or Ctrl+D) |
| cd | cd path | Change directory |

### Operators

Arithmetic:
- '+' Add
- '-' Subtract
- '*' Multiply
- '/' Divide

Comparison:
- '>' Greater than
- '<' Less than
- '>=' Greater or equal
- '<=' Less or equal
- '==' Equal
- '!=' Not equal

Input/Output:
- '|' Pipe output to next command
- '>' Write to file (overwrite)
- '>>' Append to file
- '<' Read from file
- '&>' Redirect stderr and stdout

---

## EXAMPLES

### Navigation

```bash
trushell> cd /tmp
trushell> pwd
/tmp

trushell> cd ~
trushell> pwd
/home/user
```

### File Operations

```bash
trushell> ls -la
trushell> cat README.md | head -20
trushell> grep "error" *.log > errors.txt
trushell> cp file.txt backup.txt
```

### Calculations

```bash
trushell> let bytes = 1024
trushell> let kilobytes = $bytes / 1024
trushell> let total = 10 + 20 + 30 + 40
```

### Conditional Logic

```bash
trushell> let threshold = 100
trushell> let value = 150
trushell> let exceeds = $value > $threshold
# exceeds is now true
```

### Complex Expressions

```bash
trushell> let x = 10
trushell> let y = 20
trushell> let z = $x + $y * 2
# z is 50 (multiplication happens first)

trushell> let result = ($x + $y) * 2
# result is 60
```

## WASM Plugin Host

TruShell can load sandboxed WASM plugins with a capability-based host model.
Plugins live in `examples/plugins` and must publish a JSON manifest next to the WASM module.

### Plugin CLI

```bash
trushell> plugin manifest examples/plugins/log_echo.wat
trushell> plugin run examples/plugins/log_echo.wat "Hello from host"
```

### Plugin manifest

A plugin manifest looks like this:

```json
{
  "name": "log-echo",
  "version": "0.1.0",
  "api_version": "1.0",
  "capabilities": ["logging"]
}
```

### Supported capabilities

- `logging` – allows plugins to call `host_log`.
- `environment-get` – allows plugins to call `host_get_env`.

### Example plugins

- `examples/plugins/log_echo.wat` – logs the input string using the host logger.
- `examples/plugins/env_logger.wat` – reads an environment variable and logs the result.

### Plugin safety model

Plugins are sandboxed in WASM. The host only exposes host functions for the declared capabilities.
A plugin with missing capabilities will fail to instantiate if it imports host functions it is not allowed to call.

---

## SYNTAX

### Tokens

TruShell recognizes the following token types:

| Token Class | Examples | Purpose |
|-------------|----------|---------|
| Keywords | let, true, false | Language control |
| Identifiers | x, $var, _private | Variable and function names |
| Numbers | 42, 3mb, 100kb | Numeric literals with optional units |
| Strings | "hello" | Quoted string literals |
| Flags | -la, --verbose, --help | Command-line flags |
| Operators | +, -, *, /, >, <, ==, != | Binary operations |
| Delimiters | (), {}, [], ., ,, ; | Structure and grouping |
| Pipes | \| | Pipeline sequencing |

### Data Types

TruShell supports the following literal types:

```
Number     - Integer values, optionally with units (42, 1mb, 500ms)
String     - Double-quoted text literals ("text")
Boolean    - true or false values
```

### Operator Precedence

Operators are evaluated in this order (lowest to highest):

1. Comparison Operators (>, <, >=, <=, ==, !=)
2. Term Operators (+, -)
3. Factor Operators (*, /)
4. Primary (Literals, Identifiers, Parentheses, Blocks)

### Variables

Variables are declared with 'let' and referenced with '$':

```bash
trushell> let count = 10
trushell> let doubled = $count * 2
```

---

## ARCHITECTURE

### Project Structure

```
TruShell/
├── src/
│   ├── main.rs         - REPL and command execution
│   └── parser.rs       - Lexer and parser
├── Cargo.toml          - Project manifest
├── Cargo.lock          - Dependency lock file
└── README.md           - This file
```

### Parsing Flow

```
User Input String
    ↓
Lexer::tokenize()
    ↓
Token Vector
    ↓
Parser::parse_statement()
    ↓
ASTNode (Abstract Syntax Tree)
    ↓
Execution logic
    ↓
Output/Side Effects
```

### Design Philosophy

1. Separation of Concerns: Lexing, parsing, and execution are distinct phases
2. Error Resilience: Parse failures trigger fallback to system command execution
3. Minimal Dependencies: Uses only crossterm for terminal handling
4. Extensibility: AST-based design allows easy addition of new expression types

---

## EXECUTION MODEL

### Command Routing

When you enter a command, TruShell:

1. Reads the input line
2. Checks for special commands (exit, cd)
3. Attempts to parse it
4. If parse succeeds, checks if it's a recognized pattern
5. If not recognized, falls back to executing as a system command

### Special Commands

exit - Terminates the shell gracefully

cd path - Changes the current directory (handled specially, not as a subprocess)

### Fallback Execution

If parsing fails, TruShell executes the input as a system command. This means most Unix commands work transparently:

```bash
trushell> grep pattern file.txt
trushell> find . -name "*.rs"
trushell> ps aux | less
```

### Pipes and Redirects

TruShell supports shell-style redirection:

- 'cmd > file' writes stdout to a file
- 'cmd >> file' appends stdout to a file
- 'cmd < file' reads stdin from a file
- 'cmd &> file' redirects stderr to the same target file
- 'cmd | other > file' pipes data into a redirected final stage

This integration keeps parsed AST behavior aligned with traditional shell semantics.

---

## DEVELOPMENT

### Requirements

- Rust 1.70 or later (Edition 2021)
- Cargo (comes with Rust)

### Building

Debug build:
```bash
$ cargo build
```

Release build (optimized):
```bash
$ cargo build --release
```

Run tests:
```bash
$ cargo test
```

Run with debugging:
```bash
$ RUST_BACKTRACE=1 cargo run
```

### Code Guidelines

- Use 'cargo fmt' for formatting
- Run 'cargo clippy' to catch common mistakes
- Add unit tests for new features
- Update docs if behavior changes

### Contributing

We welcome contributions! Here's how to help:

1. Fork the repo
2. Create a feature branch: git checkout -b feature/awesome-feature
3. Make your changes and write tests
4. Commit with clear messages: git commit -m "Add awesome feature"
5. Push: git push origin feature/awesome-feature
6. Open a Pull Request and describe what you did

---

## ROADMAP

We are actively developing TruShell. Planned features:

- Task Management: task create, task list, task complete
- Time Tracking: time start, time stop, time log
- Persistence: SQLite backend for tasks
- Configuration: .trushellrc config file
- Custom Functions: Define and reuse scripts
- History and Completion: Arrow keys for recall, tab completion
- Shell Integration: Load in .bashrc / .zshrc

---

## SUPPORT

Got questions? Ideas? Bug reports?

- Open an Issue on GitHub
- Start a Discussion if you want to chat
- Check existing issues for answers

---

## LICENSE

TruShell is released under the terms in LICENSE.md.

See LICENSE.md for full details.

---

Made with care by TruFoundation

Empowering productivity through open-source tooling.
