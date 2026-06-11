mod parser;

use std::io::{self, Write};
use std::process::{Command, Stdio};

fn main() {
    println!("Welcome to TruShell Native Engine");

    loop {
        print!("trushell ❯ ");
        if let Err(e) = io::stdout().flush() {
            eprintln!("Prompt flush error: {}", e);
            continue;
        }

        let mut input = String::new();
        match io::stdin().read_line(&mut input) {
            Ok(0) => break, // Ctrl+D to exit safely
            Ok(_) => {}
            Err(e) => {
                eprintln!("Error reading input: {}", e);
                continue;
            }
        }

        // Clean trailing newlines and whitespace completely
        let trimmed_input = input.trim();
        if trimmed_input.is_empty() {
            continue;
        }

        if trimmed_input == "exit" {
            println!("Goodbye!");
            break;
        }

        if trimmed_input.starts_with("cd") {
            let parts: Vec<&str> = trimmed_input.split_whitespace().collect();
            let new_dir = parts.get(1).copied().unwrap_or(".");
            if let Err(e) = std::env::set_current_dir(new_dir) {
                eprintln!("trushell: cd: {}: {}", new_dir, e);
            }
            continue;
        }

        match parser::parse_line(trimmed_input) {
            Ok(ast) => {
                // If the parsed AST looks like a CLI invocation that was
                // accidentally parsed as subtraction (e.g. `ls -la` -> `ls - la`),
                // fall back to executing the system command.
                if let Some((cmd, args)) = probable_cli_from_ast(&ast) {
                    let arg_refs: Vec<&str> = args.iter().map(|s| s.as_str()).collect();
                    execute_system_command(&cmd, &arg_refs);
                } else {
                    println!("Parsed AST: {:#?}", ast);
                }
            }
            Err(err) => {
                eprintln!("Parse error: {}", err);
                let parts: Vec<&str> = trimmed_input.split_whitespace().collect();
                let command = parts[0];
                let args = &parts[1..];
                execute_system_command(command, args);
            }
        }
    }
}

// Heuristic: if AST is a chain of subtraction operations where the leftmost
// node is an identifier (the command) and the rest are identifiers or
// string-like literals, treat it as a CLI invocation and extract command+args.
fn probable_cli_from_ast(ast: &parser::ASTNode) -> Option<(String, Vec<String>)> {
    use parser::{ASTNode, BinaryOperator};

    fn collect_subtract_parts(node: &ASTNode, parts: &mut Vec<ASTNode>) -> bool {
        match node {
            ASTNode::BinaryOp { left, op, right } if *op == BinaryOperator::Subtract => {
                if !collect_subtract_parts(left, parts) {
                    return false;
                }
                parts.push((**right).clone());
                true
            }
            other => {
                parts.push(other.clone());
                true
            }
        }
    }

    let mut parts: Vec<ASTNode> = Vec::new();
    if !collect_subtract_parts(ast, &mut parts) {
        return None;
    }

    if parts.is_empty() {
        return None;
    }

    // first must be an identifier (command name)
    let cmd = match &parts[0] {
        ASTNode::Identifier(name) => name.clone(),
        _ => return None,
    };

    let mut args: Vec<String> = Vec::new();
    for part in parts.into_iter().skip(1) {
        match part {
            ASTNode::Identifier(s) => args.push(s),
            ASTNode::Literal(parser::Literal::String(s)) => args.push(s),
            _ => return None,
        }
    }

    Some((cmd, args))
}

fn execute_system_command(cmd: &str, args: &[&str]) {
    // Removed 'mut' here to fix the compilation warning perfectly
    let child = Command::new(cmd)
        .args(args)
        .stdin(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .spawn();

    match child {
        Ok(mut child_proc) => {
            if let Err(e) = child_proc.wait() {
                eprintln!("Execution error: {}", e);
            }
        }
        Err(e) => {
            eprintln!("trushell: command not found '{}': {}", cmd, e);
        }
    }
}
