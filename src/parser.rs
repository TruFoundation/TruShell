use std::fmt;
use std::iter::Peekable;
use std::str::Chars;

#[derive(Debug, Clone, PartialEq)]
pub enum Token {
    Let,
    Flag(String),
    Identifier(String),
    Number(String),
    StringLiteral(String),
    Boolean(bool),
    Equals,
    Pipe,
    LParen,
    RParen,
    LBrace,
    RBrace,
    Dot,
    Comma,
    Semicolon,
    GreaterThan,
    LessThan,
    GreaterThanOrEqual,
    LessThanOrEqual,
    EqualsEquals,
    BangEquals,
    Plus,
    Minus,
    Star,
    Slash,
}

#[derive(Debug, Clone, PartialEq)]
pub enum Literal {
    Number { value: i64, unit: Option<String> },
    String(String),
    Boolean(bool),
}

#[derive(Debug, Clone, PartialEq)]
pub enum BinaryOperator {
    GreaterThan,
    LessThan,
    GreaterThanOrEqual,
    LessThanOrEqual,
    Equals,
    NotEquals,
    Add,
    Subtract,
    Multiply,
    Divide,
}

#[derive(Debug, Clone, PartialEq)]
pub enum ASTNode {
    Let {
        name: String,
        value: Box<ASTNode>,
    },
    Pipeline {
        stages: Vec<Box<ASTNode>>,
    },
    Command {
        name: String,
        args: Vec<ASTNode>,
    },
    Block {
        body: Vec<ASTNode>,
    },
    BinaryOp {
        left: Box<ASTNode>,
        op: BinaryOperator,
        right: Box<ASTNode>,
    },
    Variable(String),
    Literal(Literal),
    PropertyAccess {
        target: Box<ASTNode>,
        property: String,
    },
    Identifier(String),
}

#[derive(Debug, Clone, PartialEq)]
pub struct ParseError {
    pub message: String,
}

impl ParseError {
    pub fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
        }
    }
}

impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Parse Error: {}", self.message)
    }
}

impl std::error::Error for ParseError {}

pub fn tokenize_line(input: &str) -> Result<Vec<Token>, ParseError> {
    Lexer::new(input).tokenize()
}

pub fn parse_line(input: &str) -> Result<ASTNode, ParseError> {
    let tokens = tokenize_line(input)?;
    let mut parser = Parser::new(tokens);
    let node = parser.parse_statement()?;

    if parser.peek().is_some() {
        Err(ParseError::new("Unexpected input after end of statement"))
    } else {
        Ok(node)
    }
}

struct Lexer<'a> {
    chars: Peekable<Chars<'a>>,
}

impl<'a> Lexer<'a> {
    fn new(input: &'a str) -> Self {
        Self {
            chars: input.chars().peekable(),
        }
    }

    fn tokenize(mut self) -> Result<Vec<Token>, ParseError> {
        let mut tokens = Vec::new();

        while let Some(&ch) = self.chars.peek() {
            match ch {
                ch if ch.is_whitespace() => {
                    self.chars.next();
                }
                'a'..='z' | 'A'..='Z' | '_' | '$' => {
                    tokens.push(self.lex_identifier_or_keyword()?);
                }
                '0'..='9' => {
                    tokens.push(self.lex_number()?);
                }
                '"' => {
                    tokens.push(self.lex_string()?);
                }
                '=' => {
                    self.chars.next();
                    if matches!(self.chars.peek(), Some('=')) {
                        self.chars.next();
                        tokens.push(Token::EqualsEquals);
                    } else {
                        tokens.push(Token::Equals);
                    }
                }
                '|' => {
                    self.chars.next();
                    tokens.push(Token::Pipe);
                }
                '(' => {
                    self.chars.next();
                    tokens.push(Token::LParen);
                }
                ')' => {
                    self.chars.next();
                    tokens.push(Token::RParen);
                }
                '{' => {
                    self.chars.next();
                    tokens.push(Token::LBrace);
                }
                '}' => {
                    self.chars.next();
                    tokens.push(Token::RBrace);
                }
                '.' => {
                    self.chars.next();
                    tokens.push(Token::Dot);
                }
                ',' => {
                    self.chars.next();
                    tokens.push(Token::Comma);
                }
                ';' => {
                    self.chars.next();
                    tokens.push(Token::Semicolon);
                }
                '>' => {
                    self.chars.next();
                    if matches!(self.chars.peek(), Some('=')) {
                        self.chars.next();
                        tokens.push(Token::GreaterThanOrEqual);
                    } else {
                        tokens.push(Token::GreaterThan);
                    }
                }
                '<' => {
                    self.chars.next();
                    if matches!(self.chars.peek(), Some('=')) {
                        self.chars.next();
                        tokens.push(Token::LessThanOrEqual);
                    } else {
                        tokens.push(Token::LessThan);
                    }
                }
                '!' => {
                    self.chars.next();
                    if matches!(self.chars.peek(), Some('=')) {
                        self.chars.next();
                        tokens.push(Token::BangEquals);
                    } else {
                        return Err(ParseError::new("Unexpected '!' without '='"));
                    }
                }
                '+' => {
                    self.chars.next();
                    tokens.push(Token::Plus);
                }
                '-' => {
                    // Could be a flag like `-la` or `--help`. If the hyphen is followed
                    // by a letter or another hyphen, lex the whole word as a Flag token.
                    if let Some(second) = {
                        // clone iterator to peek two chars ahead safely
                        let mut it = self.chars.clone();
                        it.next(); // current '-'
                        it.peek().cloned()
                    } {
                        if second.is_alphabetic() || second == '-' {
                            tokens.push(self.lex_flag()?);
                        } else {
                            self.chars.next();
                            tokens.push(Token::Minus);
                        }
                    } else {
                        self.chars.next();
                        tokens.push(Token::Minus);
                    }
                }
                '*' => {
                    self.chars.next();
                    tokens.push(Token::Star);
                }
                '/' => {
                    self.chars.next();
                    tokens.push(Token::Slash);
                }
                other => {
                    return Err(ParseError::new(format!("Unexpected character: '{}'", other)));
                }
            }
        }

        Ok(tokens)
    }

    fn lex_identifier_or_keyword(&mut self) -> Result<Token, ParseError> {
        let mut text = String::new();

        while let Some(&ch) = self.chars.peek() {
            if ch.is_alphanumeric() || ch == '_' || ch == '$' {
                text.push(ch);
                self.chars.next();
            } else {
                break;
            }
        }

        let token = match text.as_str() {
            "let" => Token::Let,
            "true" => Token::Boolean(true),
            "false" => Token::Boolean(false),
            _ => Token::Identifier(text),
        };

        Ok(token)
    }

    fn lex_flag(&mut self) -> Result<Token, ParseError> {
        let mut text = String::new();
        // consume the leading '-'
        if let Some(ch) = self.chars.next() {
            if ch != '-' {
                // should not happen
            }
            text.push('-');
        }

        // capture optional second '-'
        if let Some(&next) = self.chars.peek() {
            if next == '-' {
                text.push('-');
                self.chars.next();
            }
        }

        while let Some(&ch) = self.chars.peek() {
            if ch.is_alphanumeric() || ch == '-' || ch == '_' {
                text.push(ch);
                self.chars.next();
            } else {
                break;
            }
        }

        Ok(Token::Flag(text))
    }

    fn lex_number(&mut self) -> Result<Token, ParseError> {
        let mut text = String::new();

        while let Some(&ch) = self.chars.peek() {
            if ch.is_ascii_digit() {
                text.push(ch);
                self.chars.next();
            } else {
                break;
            }
        }

        while let Some(&ch) = self.chars.peek() {
            if ch.is_ascii_alphabetic() {
                text.push(ch);
                self.chars.next();
            } else {
                break;
            }
        }

        if text.is_empty() {
            return Err(ParseError::new("Expected number literal"));
        }

        Ok(Token::Number(text))
    }

    fn lex_string(&mut self) -> Result<Token, ParseError> {
        self.chars.next();
        let mut value = String::new();

        while let Some(ch) = self.chars.next() {
            match ch {
                '"' => return Ok(Token::StringLiteral(value)),
                other => value.push(other),
            }
        }

        Err(ParseError::new("Unterminated string literal"))
    }
}

struct Parser {
    tokens: Vec<Token>,
    position: usize,
}

impl Parser {
    fn new(tokens: Vec<Token>) -> Self {
        Self { tokens, position: 0 }
    }

    fn peek(&self) -> Option<&Token> {
        self.tokens.get(self.position)
    }

    fn next(&mut self) -> Option<&Token> {
        let token = self.tokens.get(self.position);
        if token.is_some() {
            self.position += 1;
        }
        token
    }

    fn expect_identifier(&mut self) -> Result<String, ParseError> {
        match self.next() {
            Some(Token::Identifier(name)) => Ok(name.clone()),
            Some(other) => Err(ParseError::new(format!("Expected identifier, found {:?}", other))),
            None => Err(ParseError::new("Expected identifier, found end of input")),
        }
    }

    fn expect_token(&mut self, expected: Token) -> Result<(), ParseError>
    where
        Token: PartialEq,
    {
        match self.next() {
            Some(token) if *token == expected => Ok(()),
            Some(other) => Err(ParseError::new(format!("Expected {:?}, found {:?}", expected, other))),
            None => Err(ParseError::new(format!("Expected {:?}, found end of input", expected))),
        }
    }

    fn parse_statement(&mut self) -> Result<ASTNode, ParseError> {
        if matches!(self.peek(), Some(Token::Let)) {
            self.parse_let_statement()
        } else {
            self.parse_pipeline()
        }
    }

    fn parse_let_statement(&mut self) -> Result<ASTNode, ParseError> {
        self.next();
        let name = self.expect_identifier()?;
        self.expect_token(Token::Equals)?;
        let value = self.parse_expression()?;
        Ok(ASTNode::Let {
            name,
            value: Box::new(value),
        })
    }

    fn parse_pipeline(&mut self) -> Result<ASTNode, ParseError> {
        let mut stages = vec![Box::new(self.parse_expression()?)];

        while matches!(self.peek(), Some(Token::Pipe)) {
            self.next();
            stages.push(Box::new(self.parse_expression()?));
        }

        if stages.len() == 1 {
            Ok(*stages.remove(0))
        } else {
            Ok(ASTNode::Pipeline { stages })
        }
    }

    fn parse_expression(&mut self) -> Result<ASTNode, ParseError> {
        self.parse_comparison()
    }

    fn parse_comparison(&mut self) -> Result<ASTNode, ParseError> {
        let mut left = self.parse_term()?;

        while let Some(op) = self.peek_comparison_operator() {
            self.next();
            let right = self.parse_term()?;
            left = ASTNode::BinaryOp {
                left: Box::new(left),
                op,
                right: Box::new(right),
            };
        }

        Ok(left)
    }

    fn peek_comparison_operator(&self) -> Option<BinaryOperator> {
        match self.peek() {
            Some(Token::GreaterThan) => Some(BinaryOperator::GreaterThan),
            Some(Token::LessThan) => Some(BinaryOperator::LessThan),
            Some(Token::GreaterThanOrEqual) => Some(BinaryOperator::GreaterThanOrEqual),
            Some(Token::LessThanOrEqual) => Some(BinaryOperator::LessThanOrEqual),
            Some(Token::EqualsEquals) => Some(BinaryOperator::Equals),
            Some(Token::BangEquals) => Some(BinaryOperator::NotEquals),
            _ => None,
        }
    }

    fn parse_term(&mut self) -> Result<ASTNode, ParseError> {
        let mut node = self.parse_factor()?;

        while let Some(op) = self.peek_term_operator() {
            self.next();
            let right = self.parse_factor()?;
            node = ASTNode::BinaryOp {
                left: Box::new(node),
                op,
                right: Box::new(right),
            };
        }

        Ok(node)
    }

    fn peek_term_operator(&self) -> Option<BinaryOperator> {
        match self.peek() {
            Some(Token::Plus) => Some(BinaryOperator::Add),
            Some(Token::Minus) => Some(BinaryOperator::Subtract),
            _ => None,
        }
    }

    fn parse_factor(&mut self) -> Result<ASTNode, ParseError> {
        let mut node = self.parse_primary()?;

        while let Some(op) = self.peek_factor_operator() {
            self.next();
            let right = self.parse_primary()?;
            node = ASTNode::BinaryOp {
                left: Box::new(node),
                op,
                right: Box::new(right),
            };
        }

        Ok(node)
    }

    fn peek_factor_operator(&self) -> Option<BinaryOperator> {
        match self.peek() {
            Some(Token::Star) => Some(BinaryOperator::Multiply),
            Some(Token::Slash) => Some(BinaryOperator::Divide),
            _ => None,
        }
    }

    fn parse_primary(&mut self) -> Result<ASTNode, ParseError> {
        let token = self.next().cloned();

        match token {
            Some(Token::Identifier(name)) => self.parse_identifier_expression(name),
            Some(Token::Number(number)) => Ok(ASTNode::Literal(self.parse_number_literal(&number)?)),
            Some(Token::StringLiteral(text)) => Ok(ASTNode::Literal(Literal::String(text))),
            Some(Token::Flag(flag)) => Ok(ASTNode::Literal(Literal::String(flag))),
            Some(Token::Boolean(b)) => Ok(ASTNode::Literal(Literal::Boolean(b))),
            Some(Token::LParen) => {
                let expression = self.parse_expression()?;
                self.expect_token(Token::RParen)?;
                Ok(expression)
            }
            Some(Token::LBrace) => self.parse_block(),
            Some(other) => Err(ParseError::new(format!("Unexpected token {:?} in expression", other))),
            None => Err(ParseError::new("Unexpected end of input")),
        }
    }

    fn parse_identifier_expression(&mut self, name: String) -> Result<ASTNode, ParseError> {
        let mut expression = if name.starts_with('$') {
            ASTNode::Variable(name.clone())
        } else {
            ASTNode::Identifier(name.clone())
        };

        loop {
            match self.peek() {
                Some(Token::LParen) => {
                    expression = self.parse_call(name.clone())?;
                }
                Some(Token::LBrace) => {
                    let block = self.parse_block()?;
                    expression = ASTNode::Command {
                        name: name.clone(),
                        args: vec![block],
                    };
                }
                Some(Token::Dot) => {
                    self.next();
                    let property = self.expect_identifier()?;
                    expression = ASTNode::PropertyAccess {
                        target: Box::new(expression),
                        property,
                    };
                }
                _ => break,
            }
        }

        Ok(expression)
    }

    fn parse_call(&mut self, name: String) -> Result<ASTNode, ParseError> {
        self.expect_token(Token::LParen)?;
        let mut args = Vec::new();

        while !matches!(self.peek(), Some(Token::RParen)) {
            args.push(self.parse_expression()?);
            if matches!(self.peek(), Some(Token::Comma)) {
                self.next();
            } else {
                break;
            }
        }

        self.expect_token(Token::RParen)?;

        Ok(ASTNode::Command { name, args })
    }

    fn parse_block(&mut self) -> Result<ASTNode, ParseError> {
        let mut body = Vec::new();
        self.expect_token(Token::LBrace)?;

        while !matches!(self.peek(), Some(Token::RBrace)) {
            body.push(self.parse_expression()?);
            if matches!(self.peek(), Some(Token::Semicolon)) {
                self.next();
            } else {
                break;
            }
        }

        self.expect_token(Token::RBrace)?;

        Ok(ASTNode::Block { body })
    }

    fn parse_number_literal(&self, raw: &str) -> Result<Literal, ParseError> {
        let digits: String = raw.chars().take_while(|ch| ch.is_ascii_digit()).collect();
        let unit: String = raw.chars().skip_while(|ch| ch.is_ascii_digit()).collect();

        if digits.is_empty() {
            return Err(ParseError::new("Numeric literal must start with a digit"));
        }

        let value = digits.parse::<i64>().map_err(|_| ParseError::new("Failed to parse numeric literal"))?;
        let unit = if unit.is_empty() { None } else { Some(unit) };

        Ok(Literal::Number { value, unit })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tokenize_basic_lets_and_pipeline() {
        let tokens = tokenize_line("let x = 5").unwrap();
        assert_eq!(tokens, vec![Token::Let, Token::Identifier("x".into()), Token::Equals, Token::Number("5".into())]);

        let pipeline = tokenize_line("ls() | filter { $it.size > 1mb }").unwrap();
        assert!(pipeline.contains(&Token::Pipe));
    }

    #[test]
    fn parse_let_statement() {
        let ast = parse_line("let x = 5").unwrap();
        assert_eq!(
            ast,
            ASTNode::Let {
                name: "x".into(),
                value: Box::new(ASTNode::Literal(Literal::Number { value: 5, unit: None })),
            }
        );
    }

    #[test]
    fn parse_pipeline_with_function_block() {
        let ast = parse_line("ls() | filter { $it.size > 1mb }").unwrap();

        assert!(matches!(ast, ASTNode::Pipeline { .. }));
    }
}
