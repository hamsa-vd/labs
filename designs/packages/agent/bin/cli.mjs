#!/usr/bin/env node

import { cpSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { homedir } from 'node:os';
import process from 'node:process';

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const userRoot = process.env.HAMSA_AGENT_HOME || homedir();
const command = process.argv[2];
const requested = process.argv.slice(3);
const force = requested.includes('--force');

function usage() {
  console.log(`Usage:
  hamsa-designs install [claude|codex|all] [--force]

Installs the Hamsa Designs discovery skill once in your user-level agent configuration.
Use --force to replace an existing installation during an intentional upgrade.`);
}

if (command !== 'install') {
  usage();
  process.exit(command ? 1 : 0);
}

const selection = requested.find(value => !value.startsWith('--')) || 'all';
const targets = {
  claude: resolve(userRoot, '.claude', 'skills', 'hamsa-designs'),
  codex: resolve(userRoot, '.codex', 'skills', 'hamsa-designs')
};
const names = selection === 'all' ? Object.keys(targets) : [selection];

if (names.some(name => !targets[name])) {
  console.error(`Unknown agent "${selection}". Choose claude, codex, or all.`);
  process.exit(1);
}

for (const name of names) {
  const target = targets[name];

  if (existsSync(target) && !force) {
    console.log(`Skipped ${name}: ${target} already exists.`);
    continue;
  }

  mkdirSync(target, { recursive: true });
  cpSync(resolve(packageRoot, 'SKILL.md'), resolve(target, 'SKILL.md'));
  cpSync(resolve(packageRoot, 'scripts'), resolve(target, 'scripts'), { recursive: true, force: true });
  if (name === 'codex') {
    cpSync(resolve(packageRoot, 'agents'), resolve(target, 'agents'), { recursive: true, force: true });
  }
  console.log(`${force ? 'Updated' : 'Installed'} ${name}: ${target}`);
}
