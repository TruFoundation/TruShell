use trushell::terminal::Terminal;

#[test]
fn renders_unicode_text() {
    let mut terminal = Terminal::new(3, 8);
    terminal.write("你好");

    assert_eq!(terminal.screen(), vec!["你好".to_string(), String::new(), String::new()]);
}

#[test]
fn handles_newlines_and_cursor_motion() {
    let mut terminal = Terminal::new(3, 5);
    terminal.write("AB");
    terminal.write("\n");
    terminal.write("CD");

    assert_eq!(terminal.screen(), vec!["AB".to_string(), "CD".to_string(), String::new()]);
}
