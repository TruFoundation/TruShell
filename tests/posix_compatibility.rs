use std::io::Write;
use std::process::{Command, Stdio};

fn run_shell(input: &str) -> std::process::Output {
    let mut child = Command::new(env!("CARGO"))
        .arg("run")
        .arg("--quiet")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("failed to spawn trushell");

    if let Some(stdin) = child.stdin.as_mut() {
        stdin
            .write_all(input.as_bytes())
            .expect("failed to write shell input");
    }

    child.wait_with_output().expect("failed to read shell output")
}

#[test]
fn cd_without_arguments_uses_the_home_directory() {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/root".to_string());
    let output = run_shell("cd\npwd\nexit\n");
    let stdout = String::from_utf8_lossy(&output.stdout);

    assert!(
        output.status.success(),
        "shell exited with {:?}: {}",
        output.status,
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(
        stdout.contains(&home),
        "expected pwd output to contain home directory {home}, got: {stdout}"
    );
}

#[test]
fn quoted_arguments_are_preserved_for_external_commands() {
    let output = run_shell("printf '%s %s\\n' hello world\nexit\n");
    let stdout = String::from_utf8_lossy(&output.stdout);

    assert!(
        output.status.success(),
        "shell exited with {:?}: {}",
        output.status,
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(
        stdout.contains("hello world"),
        "expected printf output to include the quoted arguments, got: {stdout}"
    );
}
