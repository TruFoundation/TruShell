use unicode_width::UnicodeWidthChar;

#[derive(Debug, Clone, PartialEq)]
pub struct Terminal {
    width: usize,
    height: usize,
    rows: Vec<String>,
    cursor_row: usize,
    cursor_col: usize,
}

impl Terminal {
    pub fn new(height: usize, width: usize) -> Self {
        Self {
            width: width.max(1),
            height: height.max(1),
            rows: vec![String::new(); height.max(1)],
            cursor_row: 0,
            cursor_col: 0,
        }
    }

    pub fn write(&mut self, input: &str) {
        let mut chars = input.chars().peekable();
        while let Some(ch) = chars.next() {
            if ch == '\u{1b}' {
                self.handle_escape(&mut chars);
            } else {
                self.write_char(ch);
            }
        }
    }

    pub fn screen(&self) -> Vec<String> {
        self.rows.clone()
    }

    pub fn cursor_position(&self) -> (usize, usize) {
        (self.cursor_row, self.cursor_col)
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

    fn handle_escape(&mut self, chars: &mut std::iter::Peekable<std::str::Chars<'_>>) {
        match chars.next() {
            Some('[') => {
                let mut params = String::new();
                let mut final_byte = None;

                while let Some(ch) = chars.next() {
                    if ch.is_ascii_digit() || ch == ';' {
                        params.push(ch);
                    } else {
                        final_byte = Some(ch);
                        break;
                    }
                }

                if let Some(final_byte) = final_byte {
                    self.handle_csi(&params, final_byte);
                }
            }
            Some('(') => {
                let _ = chars.next();
            }
            Some(_) | None => {}
        }
    }

    fn handle_csi(&mut self, params: &str, final_byte: char) {
        match final_byte {
            'J' => {
                let mode = params.trim();
                if mode == "2" {
                    self.clear_screen();
                } else {
                    self.clear_to_end();
                }
            }
            'K' => self.clear_line(),
            'H' | 'f' => {
                let (row, col) = parse_cursor_location(params);
                self.cursor_row = row.min(self.height.saturating_sub(1));
                self.cursor_col = col.min(self.width.saturating_sub(1));
            }
            'A' => {
                let amount = params.parse::<usize>().unwrap_or(1);
                self.cursor_row = self.cursor_row.saturating_sub(amount);
            }
            'B' => {
                let amount = params.parse::<usize>().unwrap_or(1);
                self.cursor_row = (self.cursor_row + amount).min(self.height.saturating_sub(1));
            }
            'C' => {
                let amount = params.parse::<usize>().unwrap_or(1);
                self.cursor_col = (self.cursor_col + amount).min(self.width.saturating_sub(1));
            }
            'D' => {
                let amount = params.parse::<usize>().unwrap_or(1);
                self.cursor_col = self.cursor_col.saturating_sub(amount);
            }
            'm' => {}
            _ => {}
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
}

fn parse_cursor_location(params: &str) -> (usize, usize) {
    let mut values = params.split(';').filter(|s| !s.is_empty());
    let row = values.next().unwrap_or("1").parse::<usize>().unwrap_or(1).saturating_sub(1);
    let col = values.next().unwrap_or("1").parse::<usize>().unwrap_or(1).saturating_sub(1);
    (row, col)
}
