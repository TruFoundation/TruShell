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
    if let Some((cmd, args, stdin, stdout, stderr)) = collect_command_and_redirections(ast) {
        execute_command(&cmd, &args, stdin, stdout, stderr)
    } else if let parser::ASTNode::Pipeline { stages } = ast {
        execute_pipeline(stages)
    } else {
        None
    }
}

fn collect_command_and_redirections(
    ast: &parser::ASTNode,
) -> Option<(String, Vec<String>, Option<Stdio>, Option<Stdio>, Option<Stdio>)> {
    let mut stdin = None;
    let mut stdout = None;
    let mut stderr = None;
    let mut current = ast;

    loop {
        match current {
            parser::ASTNode::Command { name, args } => {
                let args: Vec<String> = args.iter().map(render_arg).collect();
                return Some((name.clone(), args, stdin, stdout, stderr));
            }
            parser::ASTNode::Redirect { source, fd, mode, target, merge_stderr } => {
                let (redirect_stdin, redirect_stdout, redirect_stderr) =
                    build_redirect_stdio(fd, mode, target, *merge_stderr).ok()?;
                if redirect_stdin.is_some() {
                    stdin = redirect_stdin;
                }
                if redirect_stdout.is_some() {
                    stdout = redirect_stdout;
                }
                if redirect_stderr.is_some() {
                    stderr = redirect_stderr;
                }
                current = source;
            }
            _ => return None,
        }
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
    let mut previous_pipe_reader: Option<Stdio> = None;

    for (index, stage) in stages.iter().enumerate() {
        let (cmd, args, stdin, stdout, stderr) = match collect_command_and_redirections(stage) {
            Some(values) => values,
            None => {
                eprintln!("trushell: pipeline stage is not executable");
                return None;
            }
        };

        let mut command = Command::new(&cmd);
        command.args(&args);

        if let Some(stdin) = stdin {
            command.stdin(stdin);
        } else if let Some(pipe_reader) = previous_pipe_reader.take() {
            command.stdin(pipe_reader);
        } else {
            command.stdin(Stdio::inherit());
        }

        let is_last_stage = index == stages.len() - 1;
        if let Some(stdout) = stdout {
            command.stdout(stdout);
        } else if is_last_stage {
            command.stdout(Stdio::inherit());
        } else {
            command.stdout(Stdio::piped());
        }

        command.stderr(stderr.unwrap_or_else(|| Stdio::inherit()));

        match command.spawn() {
            Ok(mut child) => {
                previous_pipe_reader = child.stdout.take().map(Stdio::from);
                children.push(child);
            }
            Err(err) => {
                eprintln!("trushell: command failed to start '{}': {}", cmd, err);
                return None;
            }
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

#[cfg(test)]
mod tests {
    use super::*;
    use std::env;
    use std::fs::{read_to_string, remove_file};
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn unique_temp_file(prefix: &str) -> PathBuf {
        let ts = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
        let mut path = env::temp_dir();
        path.push(format!("trushell_test_{}_{}.txt", prefix, ts));
        path
    }

    #[test]
    fn execute_command_with_output_redirect() {
        let path = unique_temp_file("redirect");
        let ast = parser::ASTNode::Redirect {
            source: Box::new(parser::ASTNode::Command {
                name: "echo".into(),
                args: vec![parser::ASTNode::Literal(parser::Literal::String("test".into()))],
            }),
            fd: 1,
            mode: parser::RedirectMode::Truncate,
            target: parser::RedirectTarget::File(path.to_string_lossy().into_owned()),
            merge_stderr: false,
        };

        let status = execute_ast(&ast).expect("command failed");
        assert!(status.success());

        let contents = read_to_string(&path).expect("failed to read output file");
        assert_eq!(contents, "test\n");
        remove_file(&path).ok();
    }

    #[test]
    fn execute_pipeline_with_redirected_last_stage() {
        let path = unique_temp_file("pipeline");

        let stage1 = parser::ASTNode::Command {
            name: "echo".into(),
            args: vec![parser::ASTNode::Literal(parser::Literal::String("hello".into()))],
        };

        let stage2 = parser::ASTNode::Redirect {
            source: Box::new(parser::ASTNode::Command {
                name: "cat".into(),
                args: vec![],
            }),
            fd: 1,
            mode: parser::RedirectMode::Truncate,
            target: parser::RedirectTarget::File(path.to_string_lossy().into_owned()),
            merge_stderr: false,
        };

        let pipeline = parser::ASTNode::Pipeline {
            stages: vec![Box::new(stage1), Box::new(stage2)],
        };

        let status = execute_ast(&pipeline).expect("pipeline failed");
        assert!(status.success());

        let contents = read_to_string(&path).expect("failed to read pipeline output file");
        assert_eq!(contents, "hello\n");
        remove_file(&path).ok();
    }
}
