const PROJECTS = [
  { name: 'arey-web', framework: 'Next.js', branch: 'main', status: 'ready', time: '3 m ago', dur: '48 s', sha: 'a3f91c8', author: 'Riya Menon' },
  { name: 'arey-docs', framework: 'Astro', branch: 'main', status: 'building', time: '6 m ago', dur: '—', sha: '7c02be1', author: 'Dev Kapoor' },
  { name: 'arey-api', framework: 'Node', branch: 'main', status: 'ready', time: '1 h ago', dur: '1 m 12 s', sha: 'f18d4aa', author: 'Sam Ito' },
  { name: 'arey-mobile', framework: 'Expo', branch: 'release/4.2', status: 'failed', time: '2 h ago', dur: '22 s', sha: '9b7e330', author: 'Lea Fischer' },
  { name: 'arey-design', framework: 'Vite', branch: 'main', status: 'ready', time: '5 h ago', dur: '31 s', sha: '2d5c917', author: 'Riya Menon' },
  { name: 'arey-status', framework: 'Static', branch: 'main', status: 'queued', time: '5 h ago', dur: '—', sha: '55a1f0d', author: 'Nils Berg' },
];

const DEPLOYMENTS = [
  { env: 'Production', status: 'ready', sha: 'a3f91c8', msg: 'Tighten card shadow on dark surfaces', branch: 'main', author: 'Riya Menon', dur: '48 s', time: '3 m ago' },
  { env: 'Preview', status: 'building', sha: '7c02be1', msg: 'Add usage meter to overview', branch: 'feat/usage', author: 'Dev Kapoor', dur: '—', time: '6 m ago' },
  { env: 'Preview', status: 'ready', sha: 'f18d4aa', msg: 'Move eyebrow labels to mono', branch: 'feat/type', author: 'Sam Ito', dur: '1 m 12 s', time: '1 h ago' },
  { env: 'Preview', status: 'failed', sha: '9b7e330', msg: 'Bump build image to node-20', branch: 'chore/node', author: 'Lea Fischer', dur: '22 s', time: '2 h ago' },
  { env: 'Production', status: 'ready', sha: '2d5c917', msg: 'Ship segmented control', branch: 'main', author: 'Riya Menon', dur: '31 s', time: '5 h ago' },
  { env: 'Preview', status: 'ready', sha: '55a1f0d', msg: 'Docs: deployment lifecycle', branch: 'docs/lifecycle', author: 'Nils Berg', dur: '39 s', time: '8 h ago' },
  { env: 'Preview', status: 'ready', sha: 'c41b8e2', msg: 'Fix focus ring offset in Safari', branch: 'fix/focus', author: 'Dev Kapoor', dur: '44 s', time: '1 d ago' },
];

const STATUS = {
  ready: { tone: 'success', label: 'Ready' },
  building: { tone: 'warning', label: 'Building' },
  failed: { tone: 'danger', label: 'Failed' },
  queued: { tone: 'neutral', label: 'Queued' },
};

const MEMBERS = [
  { name: 'Riya Menon', email: 'riya@arey.dev', role: 'Owner' },
  { name: 'Dev Kapoor', email: 'dev@arey.dev', role: 'Member' },
  { name: 'Sam Ito', email: 'sam@arey.dev', role: 'Member' },
  { name: 'Lea Fischer', email: 'lea@arey.dev', role: 'Viewer' },
];

Object.assign(window, { PROJECTS, DEPLOYMENTS, STATUS, MEMBERS });
