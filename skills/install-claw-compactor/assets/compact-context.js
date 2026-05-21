#!/usr/bin/env node

const { spawnSync } = require('node:child_process');
const path = require('node:path');

const script = path.join(__dirname, 'compact-context.py');
const args = [script, ...process.argv.slice(2)];
const candidates = process.platform === 'win32'
  ? ['python', 'py']
  : ['python3', 'python'];

for (const candidate of candidates) {
  const commandArgs = candidate === 'py' ? ['-3', ...args] : args;
  const result = spawnSync(candidate, commandArgs, {
    stdio: 'inherit',
    windowsHide: true,
  });

  if (result.error && result.error.code === 'ENOENT') {
    continue;
  }

  process.exit(result.status ?? 0);
}

const providerIndex = process.argv.indexOf('--provider');
const provider = providerIndex >= 0 ? process.argv[providerIndex + 1] : '';

if (provider === 'codex') {
  process.stdout.write('{"continue":true,"systemMessage":""}\n');
} else if (provider === 'copilot') {
  process.stdout.write('{"permissionDecision":"allow"}\n');
}

process.exit(0);
