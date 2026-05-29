#!/usr/bin/env node
const { spawn } = require('child_process');

const args = process.argv.slice(2);
const cmd = 'trushell';

const child = spawn(cmd, args, { stdio: 'inherit' });

child.on('exit', function(code, signal) {
  if (signal) process.kill(process.pid, signal);
  process.exit(code);
});

child.on('error', function(err) {
  console.error('Failed to launch TruShell CLI:', err);
  process.exit(1);
});
