Product sidebar navigation, 264px column. Active row gets `--bg-selected` plus accent text and a Phosphor `fill` icon — there are no left-border accent stripes in arey.

```jsx
<SidebarNav value={page} onChange={setPage} groups={[
  { items: [{ value: 'overview', label: 'Overview', icon: 'squares-four' }] },
  { label: 'Project', items: [
    { value: 'deployments', label: 'Deployments', icon: 'rocket-launch', count: 24 },
    { value: 'logs', label: 'Logs', icon: 'terminal-window' },
  ] },
]} />
```
