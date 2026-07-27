#!/usr/bin/env node
// Structural validation for the plugin — stdlib only, run in CI and locally.
// Checks manifests parse, referenced paths exist, and every skill has
// well-formed frontmatter whose name matches its directory.

import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const errors = [];

function readJson(rel) {
  try {
    return JSON.parse(readFileSync(join(root, rel), "utf-8"));
  } catch (e) {
    errors.push(`${rel}: ${e.message}`);
    return null;
  }
}

// --- manifests ---
const plugin = readJson(".claude-plugin/plugin.json");
const marketplace = readJson(".claude-plugin/marketplace.json");
const mcp = readJson(".mcp.json");
const pkg = readJson("package.json");

if (plugin) {
  for (const field of ["name", "version", "description"]) {
    if (!plugin[field]) errors.push(`plugin.json: missing "${field}"`);
  }
  if (plugin.mcpServers && !existsSync(join(root, plugin.mcpServers))) {
    errors.push(`plugin.json: mcpServers path "${plugin.mcpServers}" does not exist`);
  }
}

if (marketplace?.plugins) {
  for (const p of marketplace.plugins) {
    if (!existsSync(join(root, p.source))) {
      errors.push(`marketplace.json: plugin source "${p.source}" does not exist`);
    }
  }
}

if (mcp?.mcpServers) {
  for (const [name, server] of Object.entries(mcp.mcpServers)) {
    if (!server.command && !server.url) {
      errors.push(`.mcp.json: server "${name}" has neither command nor url`);
    }
  }
}

if (plugin && pkg && plugin.version !== pkg.version) {
  errors.push(`version mismatch: plugin.json ${plugin.version} vs package.json ${pkg.version}`);
}

const lock = readJson("package-lock.json");
if (lock && pkg) {
  if (lock.name !== pkg.name || lock.version !== pkg.version) {
    errors.push(`package-lock.json out of sync: ${lock.name}@${lock.version} vs package.json ${pkg.name}@${pkg.version} — run npm install`);
  }
}

// --- server version in source matches manifests ---
if (pkg) {
  const src = readFileSync(join(root, "src/index.ts"), "utf-8");
  const m = src.match(/version:\s*"([^"]+)"/);
  if (m && m[1] !== pkg.version) {
    errors.push(`version mismatch: src/index.ts ${m[1]} vs package.json ${pkg.version}`);
  }
}

// --- skills ---
const skillsDir = join(root, "skills");
for (const dir of readdirSync(skillsDir, { withFileTypes: true })) {
  if (!dir.isDirectory()) continue;
  const skillMd = join(skillsDir, dir.name, "SKILL.md");
  if (!existsSync(skillMd)) {
    errors.push(`skills/${dir.name}: missing SKILL.md`);
    continue;
  }
  const content = readFileSync(skillMd, "utf-8");
  const fm = content.match(/^---\n([\s\S]*?)\n---/);
  if (!fm) {
    errors.push(`skills/${dir.name}/SKILL.md: missing frontmatter`);
    continue;
  }
  const name = fm[1].match(/^name:\s*(\S+)/m)?.[1];
  const desc = fm[1].match(/^description:\s*(.+)/m)?.[1];
  if (name !== dir.name) {
    errors.push(`skills/${dir.name}/SKILL.md: frontmatter name "${name}" != directory name`);
  }
  if (!desc || desc.trim().length < 20) {
    errors.push(`skills/${dir.name}/SKILL.md: description missing or too short`);
  }
}

// --- required files ---
for (const f of ["dist/index.js", "commands/agentcore.md", "LICENSE", "README.md"]) {
  if (!existsSync(join(root, f))) errors.push(`missing required file: ${f}`);
}

if (errors.length) {
  console.error(`✗ ${errors.length} validation error(s):`);
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}
console.log("✓ plugin structure valid");
