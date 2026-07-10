mod parser;

use std::fs::OpenOptions;
use std::io::{self, Write};
use std::process::{Child, Command, ExitStatus, Stdio};

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
                if let Some(status) = execute_ast(&ast) {
                    if !status.success() {
                        eprintln!("trushell: command failed with status {}", status);
                    }
                } else if let Some((cmd, args)) = probable_cli_from_ast(&ast) {
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

fn execute_ast(ast: &parser::ASTNode) -> Option<ExitStatus> {
    match ast {
        parser::ASTNode::Command { name, args } => {
            let args: Vec<String> = args.iter().map(render_arg).collect();
            execute_command(name, &args, None, None, None)
        }
        parser::ASTNode::Redirect { source, fd, mode, target, merge_stderr } => {
            let (stdin, stdout, stderr) = build_redirect_stdio(fd, mode, target, *merge_stderr).ok()?;
            match &**source {
                parser::ASTNode::Command { name, args } => {
                    let args: Vec<String> = args.iter().map(render_arg).collect();
                    execute_command(name, &args, stdin, stdout, stderr)
                }
                parser::ASTNode::Redirect { .. } => execute_ast(source),
                _ => None,
            }
        }
        parser::ASTNode::Pipeline { stages } => execute_pipeline(stages),
        _ => None,
    }
}

fn execute_command(
    cmd: &str,
    args: &[String],
    stdin: Option<Stdio>,
    stdout: Option<Stdio>,
    stderr: Option<Stdio>,
) -> Option<ExitStatus> {
    let mut command = Command::new(cmd);
    command.args(args);

    if let Some(stdin) = stdin {
        command.stdin(stdin);
    }
    if let Some(stdout) = stdout {
        command.stdout(stdout);
    }
    if let Some(stderr) = stderr {
        command.stderr(stderr);
    }

    match command.spawn() {
        Ok(mut child) => child.wait().ok(),
        Err(err) => {
            eprintln!("trushell: command not found '{}': {}", cmd, err);
            None
        }
    }
}

fn execute_pipeline(stages: &[Box<parser::ASTNode>]) -> Option<ExitStatus> {
    let mut children: Vec<Child> = Vec::new();
    let mut previous_stdout = None;

    for stage in stages.iter() {
        if let parser::ASTNode::Command { name, args } = &**stage {
            let args: Vec<String> = args.iter().map(render_arg).collect();
            let mut command = Command::new(name);
            command.args(&args);

            if let Some(stdout) = previous_stdout.take() {
                command.stdin(stdout);
            } else {
                command.stdin(Stdio::inherit());
            }

            if stage != stages.last().unwrap() {
                command.stdout(Stdio::piped());
            } else {
                command.stdout(Stdio::inherit());
            }

            command.stderr(Stdio::inherit());

            match command.spawn() {
                Ok(mut child) => {
                    previous_stdout = child.stdout.take().map(Stdio::from);
                    children.push(child);
                }
                Err(err) => {
                    eprintln!("trushell: command failed to start '{}': {}", name, err);
                    return None;
                }
            }
        } else {
            eprintln!("trushell: pipeline stage is not a command");
            return None;
        }
    }

    let mut last_status = None;
    for mut child in children {
        if let Ok(status) = child.wait() {
            last_status = Some(status);
        }
    }

    last_status
}

fn build_redirect_stdio(
    fd: &u8,
    mode: &parser::RedirectMode,
    target: &parser::RedirectTarget,
    merge_stderr: bool,
) -> io::Result<(Option<Stdio>, Option<Stdio>, Option<Stdio>)> {
    let file = match target {
        parser::RedirectTarget::File(path) => match mode {
            parser::RedirectMode::Truncate => OpenOptions::new().write(true).create(true).truncate(true).open(path),
            parser::RedirectMode::Append => OpenOptions::new().write(true).create(true).append(true).open(path),
        },
    }?;

    let stdin = if *fd == 0 { Some(Stdio::from(file.try_clone()?)) } else { None };
    let stdout = if *fd == 1 { Some(Stdio::from(file.try_clone()?)) } else { None };
    let stderr = if *fd == 2 || merge_stderr { Some(Stdio::from(file)) } else { None };
    Ok((stdin, stdout, stderr))
}

fn render_arg(arg: &parser::ASTNode) -> String {
    match arg {
        parser::ASTNode::Literal(parser::Literal::String(text)) => text.clone(),
        parser::ASTNode::Literal(parser::Literal::Number { value, unit }) => {
            value.to_string() + unit.as_deref().unwrap_or("")
        }
        parser::ASTNode::Identifier(name) => name.clone(),
        _ => format!("{:#?}", arg),
    }
}
