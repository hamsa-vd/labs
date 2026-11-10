#!/usr/bin/env node

import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { createRequire } from 'node:module';
import process from 'node:process';

function findProject(start) {
  let current = resolve(start);

  while (true) {
    const packageJson = join(current, 'package.json');
    if (existsSync(packageJson)) return { root: current, packageJson };

    const parent = dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

const project = findProject(process.argv[2] || process.cwd());

if (!project) {
  console.error('No package.json found in this directory or its parents.');
  process.exit(1);
}

const packageJson = readJson(project.packageJson);
const dependencyGroups = [
  packageJson.dependencies,
  packageJson.devDependencies,
  packageJson.peerDependencies,
  packageJson.optionalDependencies
];
const dependencyNames = [...new Set(dependencyGroups.flatMap(group => Object.keys(group || {})))];
const systemNames = dependencyNames.filter(name => name.startsWith('@hamsa-designs/') && name !== '@hamsa-designs/agent');
const projectRequire = createRequire(project.packageJson);
const systems = [];
const unresolved = [];

for (const packageName of systemNames) {
  try {
    const manifestPath = projectRequire.resolve(`${packageName}/manifest`);
    const manifest = readJson(manifestPath);
    if (manifest.schemaVersion !== 1) throw new Error(`Unsupported Hamsa manifest schema: ${manifest.schemaVersion}`);
    if (manifest.package !== packageName) throw new Error(`Manifest package mismatch: ${manifest.package}`);
    const packageRoot = dirname(manifestPath);
    const resources = {};

    for (const key of ['skill', 'guidelines', 'styles', 'react', 'tokens', 'components', 'assets', 'uiKits']) {
      if (manifest[key]) resources[key] = resolve(packageRoot, manifest[key]);
    }

    systems.push({ package: packageName, manifest: manifestPath, ...manifest, resources });
  } catch (error) {
    unresolved.push({ package: packageName, error: error.message });
  }
}

const result = {
  projectRoot: project.root,
  systems,
  unresolved
};

console.log(JSON.stringify(result, null, 2));

if (systems.length === 0) {
  console.error('No installed Hamsa design system with a /manifest export was detected.');
  process.exit(2);
}
