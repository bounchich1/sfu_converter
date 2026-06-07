#!/usr/bin/env node
// sfu-converter agent installer.
//
// One Node script owns the install logic. POSIX and PowerShell shims only check
// Node and forward arguments here.

'use strict';

const childProcess = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const REPO = 'bounchich1/sfu_converter';
const PLUGIN_ID = 'sfu-converter';
const EXPECTED_SKILLS = [
  'sfu-common',
  'sfu-coursework',
  'sfu-practice',
  'sfu-report-lab',
  'sfu-research',
  'sfu-small-works',
  'sfu-vkr',
];

const PROVIDERS = [
  { id: 'claude', label: 'Claude Code', command: 'claude', mechanism: 'claude plugin install' },
  { id: 'codex', label: 'Codex CLI', command: 'codex', mechanism: 'npx skills add -a codex' },
];

const IS_WIN = process.platform === 'win32';

function parseArgs(argv) {
  const opts = {
    dryRun: false,
    force: false,
    listOnly: false,
    noColor: false,
    help: false,
    only: [],
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case '--':
        break;
      case '--dry-run':
        opts.dryRun = true;
        break;
      case '--force':
        opts.force = true;
        break;
      case '--list':
        opts.listOnly = true;
        break;
      case '--no-color':
        opts.noColor = true;
        break;
      case '-h':
      case '--help':
        opts.help = true;
        break;
      case '--only': {
        const value = argv[++i];
        if (!value || value.startsWith('--')) die('error: --only requires claude or codex');
        opts.only.push(value.toLowerCase());
        break;
      }
      default:
        die(`error: unknown flag: ${arg}\nrun 'sfu-converter-agent-install --help' for usage`);
    }
  }

  const known = new Set(PROVIDERS.map((provider) => provider.id));
  for (const id of opts.only) {
    if (!known.has(id)) {
      die(`error: unknown agent: ${id}\nrun 'sfu-converter-agent-install --list' for valid ids`);
    }
  }

  return opts;
}

function die(message) {
  process.stderr.write(message + '\n');
  process.exit(2);
}

function makeChalk(noColor) {
  const useColor = !noColor && process.stdout.isTTY && !process.env.NO_COLOR;
  const wrap = (code) => (text) => (useColor ? `\x1b[${code}m${text}\x1b[0m` : text);
  return {
    dim: wrap('2'),
    green: wrap('32'),
    red: wrap('31'),
  };
}

function shellQuote(value) {
  const text = String(value);
  if (IS_WIN) return `"${text.replace(/"/g, '\\"')}"`;
  return `'${text.replace(/'/g, "'\\''")}'`;
}

function spawnXplat(command, args, opts) {
  if (!IS_WIN) return childProcess.spawnSync(command, args, opts || {});

  // npm, npx, claude, and codex are commonly .cmd shims on Windows. Running
  // through the shell avoids ENOENT from direct spawnSync.
  const line = [command, ...args].map(shellQuote).join(' ');
  return childProcess.spawnSync(line, [], { shell: true, ...(opts || {}) });
}

function runSpawn(command, args, dryRun) {
  const printable = `${command} ${args.join(' ')}`;
  if (dryRun) {
    process.stdout.write(`  would run: ${printable}\n`);
    return { status: 0 };
  }

  process.stdout.write(`  $ ${printable}\n`);
  return spawnXplat(command, args, { stdio: 'inherit' });
}

function captureSpawn(command, args) {
  try {
    return spawnXplat(command, args, { encoding: 'utf-8' });
  } catch (_) {
    return { status: 1, stdout: '', stderr: '' };
  }
}

function hasCommand(command) {
  const probe = IS_WIN ? ['where', [command]] : ['command', ['-v', command]];
  const result = IS_WIN
    ? childProcess.spawnSync(probe[0], probe[1], { encoding: 'utf-8', shell: true })
    : childProcess.spawnSync(probe[0], probe[1], { encoding: 'utf-8' });
  return result.status === 0;
}

function repoRoot() {
  return path.resolve(__dirname, '..');
}

function validateBundledPlugin(root) {
  const errors = [];
  const pluginJson = path.join(root, 'plugins', PLUGIN_ID, '.claude-plugin', 'plugin.json');
  const marketplaceJson = path.join(root, '.claude-plugin', 'marketplace.json');
  const referencesDir = path.join(root, 'plugins', PLUGIN_ID, 'references');
  const skillsDir = path.join(root, 'plugins', PLUGIN_ID, 'skills');

  if (!fs.existsSync(pluginJson)) errors.push(`missing ${path.relative(root, pluginJson)}`);
  if (!fs.existsSync(marketplaceJson)) errors.push(`missing ${path.relative(root, marketplaceJson)}`);
  if (!fs.existsSync(referencesDir)) errors.push(`missing ${path.relative(root, referencesDir)}`);
  if (!fs.existsSync(skillsDir)) errors.push(`missing ${path.relative(root, skillsDir)}`);

  for (const skill of EXPECTED_SKILLS) {
    const skillPath = path.join(skillsDir, skill, 'SKILL.md');
    if (!fs.existsSync(skillPath)) {
      errors.push(`missing ${path.relative(root, skillPath)}`);
      continue;
    }

    const body = fs.readFileSync(skillPath, 'utf-8');
    if (!body.startsWith('---\n')) {
      errors.push(`${path.relative(root, skillPath)} is missing frontmatter`);
      continue;
    }

    const frontmatter = body.split('---', 3)[1] || '';
    if (!new RegExp(`(^|\\n)name:\\s*${escapeRegExp(skill)}\\s*(\\n|$)`).test(frontmatter)) {
      errors.push(`${path.relative(root, skillPath)} frontmatter must name ${skill}`);
    }
    if (!/(^|\n)description:\s*/.test(frontmatter)) {
      errors.push(`${path.relative(root, skillPath)} frontmatter is missing description`);
    }
  }

  if (errors.length > 0) {
    die('sfu-converter installer packaging is incomplete:\n' + errors.map((error) => `  - ${error}`).join('\n'));
  }
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function installClaude(ctx) {
  ctx.results.detected += 1;
  ctx.say('Claude Code');
  validateBundledPlugin(ctx.root);

  if (!ctx.opts.dryRun && !hasCommand('claude')) {
    ctx.results.failed.push(['claude', 'claude command not found']);
    return;
  }

  if (!ctx.opts.force && !ctx.opts.dryRun) {
    const listed = captureSpawn('claude', ['plugin', 'list']);
    if (listed.status === 0 && (listed.stdout || '').includes(PLUGIN_ID)) {
      ctx.results.skipped.push(['claude', 'plugin already installed']);
      return;
    }
  }

  const add = runSpawn('claude', ['plugin', 'marketplace', 'add', REPO], ctx.opts.dryRun);
  const install = runSpawn('claude', ['plugin', 'install', `${PLUGIN_ID}@${PLUGIN_ID}`], ctx.opts.dryRun);
  if ((add.status || 0) === 0 && (install.status || 0) === 0) {
    ctx.results.installed.push('claude');
  } else {
    ctx.results.failed.push(['claude', 'claude plugin install failed']);
  }
}

function installCodex(ctx) {
  ctx.results.detected += 1;
  ctx.say('Codex CLI');
  validateBundledPlugin(ctx.root);

  if (!ctx.opts.dryRun && !hasCommand('npx')) {
    ctx.results.failed.push(['codex', 'npx command not found; install Node.js >=18']);
    return;
  }

  const result = runSpawn('npx', ['-y', 'skills', 'add', REPO, '-a', 'codex', '--yes', '--all'], ctx.opts.dryRun);
  if ((result.status || 0) === 0) {
    ctx.results.installed.push('codex');
  } else {
    ctx.results.failed.push(['codex', 'npx skills add -a codex failed']);
  }
}

function printList() {
  process.stdout.write('sfu-converter installer provider matrix\n\n');
  process.stdout.write('  ID      AGENT        INSTALL MECHANISM\n');
  process.stdout.write('  --      -----        -----------------\n');
  for (const provider of PROVIDERS) {
    process.stdout.write(`  ${provider.id.padEnd(7)} ${provider.label.padEnd(12)} ${provider.mechanism}\n`);
  }
}

function printHelp() {
  process.stdout.write(`sfu-converter agent installer.

USAGE
  npx -y github:${REPO} -- [flags]
  node bin/install.js [flags]
  bash install.sh [flags]
  pwsh install.ps1 [flags]

FLAGS
  --dry-run          Print commands without writing anything.
  --force            Re-run even when Claude reports the plugin installed.
  --only <agent>     Install only for claude or codex. Repeatable.
  --list             Print supported agents and exit.
  --no-color         Disable ANSI colors.
  -h, --help         Show this help.

EXAMPLES
  npx -y github:${REPO} -- --only claude
  npx -y github:${REPO} -- --only codex
`);
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    printHelp();
    return 0;
  }
  if (opts.listOnly) {
    printList();
    return 0;
  }

  const chalk = makeChalk(opts.noColor);
  const ctx = {
    opts,
    root: repoRoot(),
    say: (message) => process.stdout.write(`${message}\n`),
    note: (message) => process.stdout.write(chalk.dim(message) + '\n'),
    ok: (message) => process.stdout.write(chalk.green(message) + '\n'),
    warn: (message) => process.stderr.write(chalk.red(message) + '\n'),
    results: { installed: [], skipped: [], failed: [], detected: 0 },
  };

  const selected = opts.only.length > 0
    ? PROVIDERS.filter((provider) => opts.only.includes(provider.id))
    : PROVIDERS.filter((provider) => hasCommand(provider.command));

  if (selected.length === 0) {
    ctx.warn('No supported agent detected. Re-run with --only claude or --only codex.');
    return 1;
  }

  for (const provider of selected) {
    if (provider.id === 'claude') installClaude(ctx);
    if (provider.id === 'codex') installCodex(ctx);
  }

  process.stdout.write('\n');
  if (ctx.results.installed.length > 0) {
    ctx.ok('installed: ' + ctx.results.installed.join(', '));
  }
  if (ctx.results.skipped.length > 0) {
    ctx.note('skipped: ' + ctx.results.skipped.map(([id, reason]) => `${id} (${reason})`).join(', '));
  }
  if (ctx.results.failed.length > 0) {
    ctx.warn('failed: ' + ctx.results.failed.map(([id, reason]) => `${id} (${reason})`).join(', '));
    return 1;
  }

  return 0;
}

main()
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    process.stderr.write((error && error.stack) || String(error));
    process.stderr.write('\n');
    process.exitCode = 1;
  });
