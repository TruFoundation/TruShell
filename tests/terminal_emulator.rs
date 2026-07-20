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

#[test]
fn overwrites_existing_cells_and_preserves_gaps() {
    let mut terminal = Terminal::new(3, 5);
    terminal.write("A");
    terminal.write("\r");
    terminal.write("B");

    assert_eq!(terminal.screen(), vec!["B".to_string(), String::new(), String::new()]);

    let mut terminal = Terminal::new(3, 5);
    terminal.write("AB");
    terminal.write("\x1b[4C");
    terminal.write("C");

    assert_eq!(terminal.screen(), vec!["AB  C".to_string(), String::new(), String::new()]);
}

#[test]
fn clear_line_and_clear_to_end_preserve_cursor_position() {
    let mut terminal = Terminal::new(3, 5);
    terminal.write("ABC");
    terminal.write("\x1b[2D");
    terminal.write("\x1b[K");

    assert_eq!(terminal.screen(), vec!["A".to_string(), String::new(), String::new()]);
    assert_eq!(terminal.cursor_position(), (0, 1));

    let mut terminal = Terminal::new(3, 5);
    terminal.write("AB");
    terminal.write("\n");
    terminal.write("CD");
    terminal.write("\x1b[2;1H");
    terminal.write("\x1b[J");

    assert_eq!(terminal.screen(), vec!["AB".to_string(), "".to_string(), String::new()]);
    assert_eq!(terminal.cursor_position(), (1, 0));
}
