Section switcher. The active underline is *ink*, not accent — arey reserves blue for actions.

```jsx
<Tabs value={tab} onChange={setTab} items={[
  { value: 'overview', label: 'Overview' },
  { value: 'deployments', label: 'Deployments', count: 24 },
  { value: 'settings', label: 'Settings', icon: 'gear-six' },
]} />

<Tabs variant="pill" value={range} onChange={setRange} items={['24h', '7d', '30d']} />
```
