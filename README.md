# TruShell — A Productivity Shell for Task Tracking and Time Management

**TruShell** is an interactive shell environment designed to integrate task tracking and time management tools seamlessly with traditional terminal commands. Built in Rust with a custom expression parser, TruShell extends the Unix philosophy by providing a unified interface where productivity features and system commands coexist naturally.

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Building](#installation--building)
4. [Usage](#usage)
5. [Language Features](#language-features)
6. [Module Reference](#module-reference)
7. [Parsing System](#parsing-system)
8. [Command Execution](#command-execution)
9. [Examples](#examples)
10. [Development](#development)

---

## OVERVIEW

TruShell is not a replacement shell but rather a **productivity layer** that bridges the gap between system administration and personal task management. It runs as an interactive REPL (Read-Eval-Print Loop) that:

- Accepts and executes ordinary shell commands (`ls`, `cd`, `grep`, etc.)
- Parses and interprets custom expressions for task and time operations
- Maintains compatibility with existing Unix tools through fallback command execution
- Provides a consistent interface for both system-level and productivity-level operations

### Key Features

- **Hybrid Parsing**: Intelligently distinguishes between shell commands and custom expressions
- **Expression Evaluation**: Supports arithmetic, comparisons, variables, and pipelines
- **Pipeline Support**: Chain operations together using the pipe operator (`|`)
- **Task Integration**: Foundation for task tracking and time management (future expansion)
- **Graceful Fallback**: Executes as system commands if parsing fails

---

## ARCHITECTURE

TruShell follows a modular, layered architecture typical of interpreted languages:

```
┌─────────────────────────────────────────┐
│         Interactive REPL (main.rs)      │
│  • User Input Loop                      │
│  • Command/Expression Routing           │
│  • Fallback Execution                   │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────────┐
│  Lexer      │  │   Parser        │
│  (Tokenize) │  │   (AST Build)   │
└─────────────┘  └─────────────────┘
       │                │
       └───────┬────────┘
               │
        ┌──────▼──────────┐
        │   AST Nodes     │
        │  (Expressions)  │
        └─────────────────┘
               │
        ┌──────▼──────────────────┐
        │  Command Execution      │
        │  • System Calls         │
        │  • Process Management   │
        └─────────────────────────┘
```

### Design Philosophy

1. **Separation of Concerns**: Lexing, parsing, and execution are distinct phases
2. **Error Resilience**: Parse failures trigger fallback to system command execution
3. **Minimal Dependencies**: Uses only `crossterm` for terminal handling
4. **Extensibility**: AST-based design allows easy addition of new expression types

---

## INSTALLATION & BUILDING

### Prerequisites

- **Rust 1.70+** (MSRV: Edition 2021)
- **Cargo** (Rust's package manager)

### Building from Source

```bash
git clone https://github.com/TruFoundation/TruShell.git
cd TruShell
cargo build --release
```

The compiled binary will be located at `target/release/trushell`.

### Running

```bash
./target/release/trushell
```

Or directly via Cargo:

```bash
cargo run
```

---

## USAGE

### Interactive Session

Upon startup, TruShell displays a welcome message and enters a prompt loop:

```
Welcome to TruShell Native Engine
trushell ❯ 
```

### Exit Commands

- **`exit`**: Gracefully shut down the shell
- **`Ctrl+D`** (EOF): Safely terminate the shell

### Basic Operations

#### System Commands

Execute any command available in your PATH:

```
trushell ❯ ls -la
trushell ❯ pwd
trushell ❯ echo "Hello, World!"
```

#### Directory Navigation

```
trushell ❯ cd /tmp
trushell ❯ cd ~
```

The `cd` command is handled specially to modify TruShell's working directory (not spawned as a subprocess).

#### Variable Assignment

Define variables using `let`:

```
trushell ❯ let x = 42
trushell ❯ let name = "Alice"
trushell ❯ let flag = true
```

#### Expressions

Perform arithmetic and logical operations:

```
trushell ❯ let result = 10 + 5
trushell ❯ let product = 3 * 7
trushell ❯ let ratio = 100 / 4
```

#### Comparisons

```
trushell ❯ let is_big = 42 > 10
trushell ❯ let is_equal = 5 == 5
trushell ❯ let not_empty = "text" != ""
```

#### Pipelines

Chain operations together using `|`:

```
trushell ❯ ls() | filter { $it.size > 1mb }
```

---

## LANGUAGE FEATURES

### Token Types

TruShell's lexer recognizes the following token categories:

| Token Class | Examples | Purpose |
|-------------|----------|---------|
| **Keywords** | `let`, `true`, `false` | Language control structures |
| **Identifiers** | `x`, `$var`, `_private` | Variable and function names |
| **Numbers** | `42`, `3mb`, `100kb` | Numeric literals with optional units |
| **Strings** | `"hello"` | Quoted string literals |
| **Flags** | `-la`, `--verbose`, `--help` | Command-line flags (preserved) |
| **Operators** | `+`, `-`, `*`, `/`, `>`, `<`, `==`, `!=` | Binary operations |
| **Delimiters** | `()`, `{}`, `[]`, `.`, `,`, `;` | Structure and grouping |
| **Pipes** | `\|` | Pipeline sequencing |

### Data Types

TruShell supports the following literal types:

```rust
pub enum Literal {
    Number { value: i64, unit: Option<String> },  // 42, 1mb, 500ms
    String(String),                                // "text"
    Boolean(bool),                                 // true, false
}
```

### Binary Operators

| Operator | Type | Precedence | Example |
|----------|------|------------|---------|
| `+` | Addition | Term | `5 + 3` |
| `-` | Subtraction | Term | `10 - 4` |
| `*` | Multiplication | Factor | `3 * 4` |
| `/` | Division | Factor | `12 / 3` |
| `>` | Greater Than | Comparison | `5 > 3` |
| `<` | Less Than | Comparison | `2 < 5` |
| `>=` | Greater or Equal | Comparison | `5 >= 5` |
| `<=` | Less or Equal | Comparison | `3 <= 5` |
| `==` | Equals | Comparison | `5 == 5` |
| `!=` | Not Equals | Comparison | `3 != 5` |

### Operator Precedence

TruShell follows standard mathematical precedence, evaluated in this order (lowest to highest):

1. **Comparison Operators** (`>`, `<`, `>=`, `<=`, `==`, `!=`)
2. **Term Operators** (`+`, `-`)
3. **Factor Operators** (`*`, `/`)
4. **Primary** (Literals, Identifiers, Parentheses, Blocks)

### Variables

Variables are declared with `let` and referenced with `$`:

```
trushell ❯ let count = 10
trushell ❯ let doubled = $count * 2
```

Variables starting with `$` are treated as **Variable tokens** and can be accessed in expressions.

### Blocks

Code blocks are enclosed in `{}` and contain semicolon-separated statements:

```
trushell ❯ let data = { let x = 5; let y = 10; $x + $y }
```

---

## MODULE REFERENCE

### `main.rs` — Interactive REPL & Command Execution

**Purpose**: Orchestrates the shell's interactive loop and manages command execution.

#### Main Components

##### `fn main()`
- Initializes the shell with a welcome message
- Enters an infinite loop reading user input
- Routes input to the appropriate handler (exit, cd, parse, or fallback)

**Key Invariants**:
- Reads lines until EOF (`Ctrl+D`) or explicit `exit` command
- Maintains current working directory for the shell process
- Handles all I/O errors gracefully with user-friendly messages

##### `fn execute_system_command(cmd: &str, args: &[&str])`
- Spawns a new process for the given command
- Inherits stdin, stdout, stderr for seamless integration
- Reports execution errors with descriptive messages

**Execution Flow**:
```
Command::new(cmd)
  └─ .args(args)
     └─ .stdin(Stdio::inherit())
        └─ .stdout(Stdio::inherit())
           └─ .stderr(Stdio::inherit())
              └─ .spawn()
                 └─ .wait()
```

##### `fn probable_cli_from_ast(ast: &parser::ASTNode) -> Option<(String, Vec<String>)>`
- **Heuristic Detection**: Attempts to interpret parsed AST as a CLI invocation
- **Use Case**: Handles cases where `ls -la` is parsed as `ls - la` (subtraction)
- **Strategy**: 
  1. Traverses the AST looking for a chain of subtraction operations
  2. Extracts the leftmost node as the command name
  3. Collects remaining identifiers/strings as arguments
  4. Returns `Some((cmd, args))` if the pattern matches, otherwise `None`

**Example Transformation**:
```
Input:  "ls -la"
Parse:  BinaryOp { left: Identifier("ls"), op: Subtract, right: Literal(String("-la")) }
Extract: ("ls", ["-la"])
Execute: ls -la
```

---

### `parser.rs` — Lexing & Parsing Engine

**Purpose**: Converts raw user input into an Abstract Syntax Tree (AST) for interpretation.

#### Token Definitions

```rust
pub enum Token {
    Let,                    // Variable declaration
    Flag(String),          // CLI flags (-la, --help)
    Identifier(String),    // Variable/function names
    Number(String),        // Numeric literals
    StringLiteral(String), // Quoted strings
    Boolean(bool),         // true/false
    Equals,                // = assignment
    Pipe,                  // | pipeline
    LParen, RParen,        // ( )
    LBrace, RBrace,        // { }
    Dot,                   // . property access
    Comma,                 // , separator
    Semicolon,             // ; statement terminator
    GreaterThan,           // >
    LessThan,              // <
    GreaterThanOrEqual,    // >=
    LessThanOrEqual,       // <=
    EqualsEquals,          // ==
    BangEquals,            // !=
    Plus,                  // +
    Minus,                 // -
    Star,                  // *
    Slash,                 // /
}
```

#### AST Node Types

```rust
pub enum ASTNode {
    Let { name: String, value: Box<ASTNode> },
    Pipeline { stages: Vec<Box<ASTNode>> },
    Command { name: String, args: Vec<ASTNode> },
    Block { body: Vec<ASTNode> },
    BinaryOp { left: Box<ASTNode>, op: BinaryOperator, right: Box<ASTNode> },
    Variable(String),
    Literal(Literal),
    PropertyAccess { target: Box<ASTNode>, property: String },
    Identifier(String),
}
```

#### Lexer (`struct Lexer`)

**Responsibility**: Converts a string into a sequence of tokens.

##### Tokenization Rules

1. **Whitespace**: Skipped entirely
2. **Identifiers**: Start with `a-z`, `A-Z`, `_`, or `$`; continue with alphanumerics or `_`
3. **Keywords**: `let`, `true`, `false` → special tokens
4. **Numbers**: Digits optionally followed by a unit string (e.g., `5`, `100ms`, `1mb`)
5. **Strings**: Double-quoted; no escape sequences currently supported
6. **Flags**: `-` followed by letters/hyphens (e.g., `-la`, `--help`)
7. **Operators**: Single and multi-character (`==`, `!=`, `>=`, `<=`)

##### Special Flag Handling

The lexer recognizes CLI flags intelligently:
```rust
if let Some(second) = peek_two_chars_ahead {
    if second.is_alphabetic() || second == '-' {
        // Lex as a flag (e.g., -la, --verbose)
        self.lex_flag()
    } else {
        // Lex as minus operator (e.g., 5 - 3)
        Token::Minus
    }
}
```

**Effect**: `ls-la` is lexed as a command followed by a flag, not as subtraction.

#### Parser (`struct Parser`)

**Responsibility**: Converts tokens into an AST using recursive descent parsing.

##### Parsing Precedence (Lowest to Highest)

```
parse_statement
  ├─ if let: parse_let_statement
  └─ else: parse_pipeline

parse_pipeline
  └─ parse_expression (with | separator)

parse_expression
  └─ parse_comparison

parse_comparison (>/</>=/<=,==,!=)
  └─ parse_term

parse_term (+,-)
  └─ parse_factor

parse_factor (*,/)
  └─ parse_primary

parse_primary (literals, identifiers, parens, blocks)
  └─ parse_identifier_expression (handles ., (, {})
```

##### Let Statement Parsing

```rust
let x = 5
├─ Token::Let
├─ expect identifier → "x"
├─ expect =
└─ parse_expression → Literal(Number(5))

Result: ASTNode::Let {
    name: "x",
    value: Box::new(Literal(Number(5)))
}
```

##### Pipeline Parsing

```rust
ls() | filter { $it.size > 1mb }
├─ parse_expression → Command { name: "ls", args: [] }
├─ Token::Pipe
├─ parse_expression → Command { name: "filter", args: [Block {...}] }
└─ Token::Pipe (none)

Result: ASTNode::Pipeline {
    stages: [Command{...}, Command{...}]
}
```

##### Number Literal Parsing

Numbers can include units (e.g., `5mb`, `100ms`):

```rust
pub fn parse_number_literal(raw: &str) -> Result<Literal, ParseError> {
    let digits: String = raw.chars().take_while(|ch| ch.is_ascii_digit()).collect();
    let unit: String = raw.chars().skip_while(|ch| ch.is_ascii_digit()).collect();
    
    Ok(Literal::Number {
        value: digits.parse::<i64>()?,
        unit: if unit.is_empty() { None } else { Some(unit) },
    })
}
```

**Examples**:
- `5` → `Number { value: 5, unit: None }`
- `1mb` → `Number { value: 1, unit: Some("mb") }`
- `100ms` → `Number { value: 100, unit: Some("ms") }`

---

## PARSING SYSTEM

### Input Flow

```
User Input String
    ↓
[Lexer::tokenize()]
    ↓
Token Vector
    ↓
[Parser::parse_statement()]
    ↓
ASTNode (Abstract Syntax Tree)
    ↓
[main.rs execution logic]
    ↓
Output/Side Effects
```

### Example: Parsing `let x = 5 + 3`

**Input**: `"let x = 5 + 3"`

**Step 1: Tokenization**
```
[Let, Identifier("x"), Equals, Number("5"), Plus, Number("3")]
```

**Step 2: Parsing (Recursive Descent)**
```
parse_statement
  └─ parse_let_statement
     ├─ expect Let → ✓
     ├─ expect_identifier → "x"
     ├─ expect Equals → ✓
     └─ parse_expression (for "5 + 3")
        └─ parse_comparison
           └─ parse_term
              ├─ parse_factor → Literal(5)
              ├─ detect Plus
              ├─ parse_factor → Literal(3)
              └─ combine: BinaryOp { left: 5, op: Add, right: 3 }
```

**Step 3: AST Result**
```rust
ASTNode::Let {
    name: "x",
    value: Box::new(
        ASTNode::BinaryOp {
            left: Box::new(Literal(Number { value: 5, unit: None })),
            op: Add,
            right: Box::new(Literal(Number { value: 3, unit: None }))
        }
    )
}
```

### Error Handling

The parser provides descriptive error messages:

```rust
pub struct ParseError {
    pub message: String,
}
```

**Common Errors**:
- `"Expected identifier, found ..."`
- `"Unexpected token in expression"`
- `"Unterminated string literal"`
- `"Unexpected character: '...'"` (from lexer)

---

## COMMAND EXECUTION

### Execution Flow in `main()`

```
loop {
    1. Read user input
    2. Trim whitespace
    3. Check for special commands:
       ├─ "exit" → break loop
       └─ "cd ..." → change directory
    4. Attempt to parse:
       ├─ Success → check if it's a probable CLI command
       │   ├─ Yes → execute as system command
       │   └─ No → print AST (debug mode)
       └─ Failure → fallback to system command execution
    5. Display output
}
```

### Special Command Handling

#### `exit`
Terminates the shell gracefully:
```rust
if trimmed_input == "exit" {
    println!("Goodbye!");
    break;
}
```

#### `cd` (Change Directory)
Handled specially without spawning a subprocess:
```rust
if trimmed_input.starts_with("cd") {
    let parts: Vec<&str> = trimmed_input.split_whitespace().collect();
    let new_dir = parts.get(1).copied().unwrap_or(".");
    if let Err(e) = std::env::set_current_dir(new_dir) {
        eprintln!("trushell: cd: {}: {}", new_dir, e);
    }
    continue;
}
```

### Fallback Execution

When parsing fails or the AST doesn't match a known pattern, TruShell falls back to executing the input as a system command:

```rust
Err(err) => {
    eprintln!("Parse error: {}", err);
    let parts: Vec<&str> = trimmed_input.split_whitespace().collect();
    let command = parts[0];
    let args = &parts[1..];
    execute_system_command(command, args);
}
```

**Result**: Most Unix commands work transparently even if parsing fails.

### Process Management

Commands are executed with inherited I/O streams:

```rust
Command::new(cmd)
    .args(args)
    .stdin(Stdio::inherit())      // User input reaches subprocess
    .stdout(Stdio::inherit())     // Subprocess output visible
    .stderr(Stdio::inherit())     // Errors displayed directly
    .spawn()
    .wait()
```

---

## EXAMPLES

### Basic Arithmetic

```bash
trushell ❯ let x = 10
Parsed AST: Let { name: "x", value: ... }

trushell ❯ let y = $x * 2
Parsed AST: Let { name: "y", value: ... }

trushell ❯ let z = 100 / 5
Parsed AST: Let { name: "z", value: ... }
```

### Variable Usage

```bash
trushell ❯ let name = "Alice"
trushell ❯ let greeting = "Hello, " + $name
Parsed AST: Let { name: "greeting", value: ... }
```

### Comparisons

```bash
trushell ❯ let is_adult = 25 > 18
Parsed AST: Let { name: "is_adult", value: 
    BinaryOp { 
        left: 25, 
        op: GreaterThan, 
        right: 18 
    } 
}

trushell ❯ let in_range = 50 >= 10
```

### System Commands

```bash
trushell ❯ ls -la
total 48
drwxr-xr-x  5 user  group   160 Jul  5 12:34 .
drwxr-xr-x 10 user  group   320 Jul  4 18:22 ..
-rw-r--r--  1 user  group  1234 Jul  05 12:30 README.md
...

trushell ❯ pwd
/home/user/projects/TruShell

trushell ❯ echo "Building..."
Building...
```

### Directory Navigation

```bash
trushell ❯ cd /tmp
trushell ❯ pwd
/tmp
trushell ❯ cd -
trushell ❯ pwd
/home/user/projects/TruShell
```

### Pipelines (Future Use)

```bash
trushell ❯ ls() | filter { $it.size > 1mb }
Parsed AST: Pipeline { 
    stages: [
        Command { name: "ls", args: [] },
        Command { name: "filter", args: [Block { ... }] }
    ]
}
```

---

## DEVELOPMENT

### Project Structure

```
TruShell/
├── Cargo.toml          # Rust project manifest
├── Cargo.lock          # Dependency lock file
├── src/
│   ├── main.rs         # REPL and command execution (4.3 KB)
│   └── parser.rs       # Lexer and parser (19.0 KB)
├── target/             # Compiled binaries (excluded from repo)
├── README.md           # This file
└── LICENSE.md          # Project license
```

### Dependencies

- **crossterm** (v0.27): Terminal manipulation and event handling
- **Standard Library**: All core functionality uses `std`

### Building & Testing

```bash
# Build in debug mode
cargo build

# Build optimized release binary
cargo build --release

# Run tests
cargo test

# Run with output
cargo run -- --verbose
```

### Test Coverage

The parser module includes unit tests:

```rust
#[test]
fn tokenize_basic_lets_and_pipeline() { ... }

#[test]
fn parse_let_statement() { ... }

#[test]
fn parse_pipeline_with_function_block() { ... }
```

Run tests with:
```bash
cargo test
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit changes with clear messages
4. Add tests for new functionality
5. Push to your fork
6. Submit a pull request

### Future Enhancements

- **Task Management API**: Commands to create, list, and complete tasks
- **Time Tracking**: `time start`, `time stop`, `time log` commands
- **Persistence**: SQLite backend for task/time storage
- **Configuration**: `.trushellrc` configuration file support
- **Scripting**: Multi-line scripts and batching
- **Shell Integration**: `.bashrc`/`.zshrc` integration for seamless use
- **Custom Functions**: User-defined functions with parameters
- **History & Completion**: Command history and tab completion

---

## SEE ALSO

- **Linux Shell Documentation**: `man bash`, `man sh`
- **Rust Book**: https://doc.rust-lang.org/book/
- **Crossterm Docs**: https://docs.rs/crossterm/
- **Unix Philosophy**: https://en.wikipedia.org/wiki/Unix_philosophy

---

## LICENSE

TruShell is released under the terms specified in `LICENSE.md`. See that file for full details.

---

**TruFoundation** — Empowering productivity through open-source tooling.

*Last Updated: July 5, 2026*
