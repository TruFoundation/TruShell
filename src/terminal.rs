use nu_ansi_term::{Color, Style};
use unicode_width::UnicodeWidthChar;
use vte::{Params, Parser, Perform};

pub struct Terminal {
    parser: Parser,
    buffer: TerminalBuffer,
}

struct TerminalBuffer {
    width: usize,
    height: usize,
    rows: Vec<String>,
    cursor_row: usize,
    cursor_col: usize,
    current_style: Style,
}

impl Terminal {
    pub fn new(height: usize, width: usize) -> Self {
        Self {
            parser: Parser::new(),
            buffer: TerminalBuffer::new(height, width),
        }
    }

    pub fn write(&mut self, input: &str) {
        for byte in input.bytes() {
            self.parser.advance(&mut self.buffer, byte);
        }
    }

    pub fn screen(&self) -> Vec<String> {
        self.buffer.rows.clone()
    }

    pub fn cursor_position(&self) -> (usize, usize) {
        (self.buffer.cursor_row, self.buffer.cursor_col)
    }

    pub fn prompt(&self) -> String {
        Style::new().bold().fg(Color::Cyan).paint("trushell ❯").to_string()
    }
}

impl TerminalBuffer {
    fn new(height: usize, width: usize) -> Self {
        Self {
            width: width.max(1),
            height: height.max(1),
            rows: vec![String::new(); height.max(1)],
            cursor_row: 0,
            cursor_col: 0,
            current_style: Style::new(),
        }
    }

    fn write_char(&mut self, ch: char) {
        match ch {
            '\n' => self.newline(),
            '\r' => self.cursor_col = 0,
            '\t' => self.advance_tab(),
            '\u{8}' => self.backspace(),
            _ if ch.is_control() => {}
            _ => {
                let width = ch.width().unwrap_or(1);
                if self.cursor_col + width > self.width {
                    self.newline();
                }

                if self.cursor_row >= self.height {
                    self.scroll_up();
                }

                self.rows[self.cursor_row].push(ch);
                self.cursor_col += width;
            }
        }
    }

    fn newline(&mut self) {
        self.cursor_row += 1;
        self.cursor_col = 0;
        if self.cursor_row >= self.height {
            self.scroll_up();
        }
    }

    fn backspace(&mut self) {
        if self.cursor_col > 0 {
            self.cursor_col -= 1;
            if let Some(row) = self.rows.get_mut(self.cursor_row) {
                let mut chars: Vec<char> = row.chars().collect();
                if !chars.is_empty() {
                    chars.pop();
                    *row = chars.into_iter().collect();
                }
            }
        }
    }

    fn advance_tab(&mut self) {
        let step = 4usize;
        let next_col = ((self.cursor_col / step) + 1) * step;
        self.cursor_col = next_col.min(self.width.saturating_sub(1));
    }

    fn clear_screen(&mut self) {
        self.rows.iter_mut().for_each(|row| row.clear());
        self.cursor_row = 0;
        self.cursor_col = 0;
    }

    fn clear_to_end(&mut self) {
        if let Some(row) = self.rows.get_mut(self.cursor_row) {
            row.clear();
        }
        for row in self.rows.iter_mut().skip(self.cursor_row + 1) {
            row.clear();
        }
        self.cursor_col = 0;
    }

    fn clear_line(&mut self) {
        if let Some(row) = self.rows.get_mut(self.cursor_row) {
            row.clear();
        }
        self.cursor_col = 0;
    }

    fn scroll_up(&mut self) {
        self.rows.remove(0);
        self.rows.push(String::new());
        self.cursor_row = self.height.saturating_sub(1);
    }

    fn handle_sgr(&mut self, params: &[i64]) {
        if params.is_empty() {
            self.current_style = Style::new();
            return;
        }

        for param in params {
            match *param {
                0 => self.current_style = Style::new(),
                1 => self.current_style = self.current_style.bold(),
                4 => self.current_style = self.current_style.underline(),
                31 => self.current_style = self.current_style.fg(Color::Red),
                32 => self.current_style = self.current_style.fg(Color::Green),
                33 => self.current_style = self.current_style.fg(Color::Yellow),
                34 => self.current_style = self.current_style.fg(Color::Blue),
                35 => self.current_style = self.current_style.fg(Color::Purple),
                36 => self.current_style = self.current_style.fg(Color::Cyan),
                37 => self.current_style = self.current_style.fg(Color::White),
                90..=97 => self.current_style = self.current_style.fg(Color::White),
                _ => {}
            }
        }
    }
}

impl Perform for TerminalBuffer {
    fn print(&mut self, ch: char) {
        self.write_char(ch);
    }

    fn execute(&mut self, byte: u8) {
        match byte {
            b'\n' => self.newline(),
            b'\r' => self.cursor_col = 0,
            b'\t' => self.advance_tab(),
            b'\x08' => self.backspace(),
            _ => {}
        }
    }

    fn hook(&mut self, _params: &Params, _intermediates: &[u8], _ignore: bool, _c: char) {}

    fn put(&mut self, _ch: u8) {}

    fn unhook(&mut self) {}

    fn esc_dispatch(&mut self, _intermediates: &[u8], _ignore: bool, _byte: u8) {}

    fn csi_dispatch(&mut self, params: &Params, _intermediates: &[u8], _ignore: bool, action: char) {
        let params: Vec<i64> = params
            .iter()
            .flat_map(|param| param.iter().copied().map(|value| i64::from(value)))
            .collect();

        match action {
            'J' => {
                let mode = params.first().copied().unwrap_or(0);
                if mode == 2 {
                    self.clear_screen();
                } else {
                    self.clear_to_end();
                }
            }
            'K' => self.clear_line(),
            'H' | 'f' => {
                let row = params.first().copied().unwrap_or(1).saturating_sub(1) as usize;
                let col = params.get(1).copied().unwrap_or(1).saturating_sub(1) as usize;
                self.cursor_row = row.min(self.height.saturating_sub(1));
                self.cursor_col = col.min(self.width.saturating_sub(1));
            }
            'A' => {
                let amount = params.first().copied().unwrap_or(1) as usize;
                self.cursor_row = self.cursor_row.saturating_sub(amount);
            }
            'B' => {
                let amount = params.first().copied().unwrap_or(1) as usize;
                self.cursor_row = (self.cursor_row + amount).min(self.height.saturating_sub(1));
            }
            'C' => {
                let amount = params.first().copied().unwrap_or(1) as usize;
                self.cursor_col = (self.cursor_col + amount).min(self.width.saturating_sub(1));
            }
            'D' => {
                let amount = params.first().copied().unwrap_or(1) as usize;
                self.cursor_col = self.cursor_col.saturating_sub(amount);
            }
            'm' => self.handle_sgr(&params),
            _ => {}
        }
    }

    fn osc_dispatch(&mut self, _params: &[&[u8]], _bell_terminated: bool) {}
}
