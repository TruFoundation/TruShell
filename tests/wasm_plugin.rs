use std::path::PathBuf;

use trushell::wasm_host::WasmPlugin;

fn example_path(name: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("examples/plugins").join(name)
}

#[test]
fn can_load_and_run_logging_plugin() {
    let path = example_path("log_echo.wat");
    let mut plugin = WasmPlugin::load(&path).expect("failed to load logging plugin");
    assert_eq!(plugin.manifest().name, "log-echo");

    let output = plugin
        .run("Hello from plugin")
        .expect("plugin execution failed");

    assert_eq!(output, vec!["Hello from plugin".to_string()]);
}

#[test]
fn can_load_and_run_environment_plugin() {
    let path = example_path("env_logger.wat");
    let mut plugin = WasmPlugin::load(&path).expect("failed to load env plugin");
    assert_eq!(plugin.manifest().name, "env-logger");

    let output = plugin
        .run("Inspect environment")
        .expect("plugin execution failed");

    assert!(output.contains(&"Inspect environment".to_string()));
    let home = std::env::var("HOME").unwrap_or_default();
    if !home.is_empty() {
        assert!(output.iter().any(|line| line.contains(&home)));
    }
}
