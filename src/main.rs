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

        // Split input cleanly into tokens
        let parts: Vec<&str> = trimmed_input.split_whitespace().collect();
        let command = parts[0];
        let args = &parts[1..];

        // Route commands
        match command {
            "exit" => {
                println!("Goodbye!");
                break;
            }
            "cd" => {
                // If user just types 'cd', default to home or current directory safely
                let new_dir = args.first().copied().unwrap_or(".");
                if let Err(e) = std::env::set_current_dir(new_dir) {
                    eprintln!("trushell: cd: {}: {}", new_dir, e);
                }
            }
            external_cmd => {
                execute_system_command(external_cmd, args);
            }
        }
    }
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
