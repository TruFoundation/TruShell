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
    rows: Vec<Vec<char>>,
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
        self.buffer
            .rows
            .iter()
            .map(|row| row.iter().collect::<String>().trim_end().to_string())
            .collect()
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
        let height = height.max(1);
        let width = width.max(1);
        Self {
            width,
            height,
            rows: vec![vec![' '; width]; height],
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
                let width = 1usize;
                if self.cursor_col + width > self.width {
                    self.newline();
                }

                if self.cursor_row >= self.height {
                    self.scroll_up();
                }

                let row = &mut self.rows[self.cursor_row];
                row[self.cursor_col] = ch;
                self.cursor_col = (self.cursor_col + width).min(self.width.saturating_sub(1));
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
                row[self.cursor_col] = ' ';
            }
        }
    }

    fn advance_tab(&mut self) {
        let step = 4usize;
        let next_col = ((self.cursor_col / step) + 1) * step;
        self.cursor_col = next_col.min(self.width.saturating_sub(1));
    }

    fn clear_screen(&mut self) {
        self.rows.iter_mut().for_each(|row| {
            for cell in row.iter_mut() {
                *cell = ' ';
            }
        });
        self.cursor_row = 0;
        self.cursor_col = 0;
    }

    fn clear_to_end(&mut self) {
        if let Some(row) = self.rows.get_mut(self.cursor_row) {
            for cell in row.iter_mut().skip(self.cursor_col) {
                *cell = ' ';
            }
        }
        for row in self.rows.iter_mut().skip(self.cursor_row + 1) {
            for cell in row.iter_mut() {
                *cell = ' ';
            }
        }
    }

    fn clear_line(&mut self) {
        if let Some(row) = self.rows.get_mut(self.cursor_row) {
            for cell in row.iter_mut().skip(self.cursor_col) {
                *cell = ' ';
            }
        }
    }

    fn scroll_up(&mut self) {
        self.rows.remove(0);
        self.rows.push(vec![' '; self.width]);
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
