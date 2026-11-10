The standard surface — 16px radius, hairline border *and* soft shadow together.

```jsx
<Card title="Usage" description="Current billing period" action={<IconButton icon="dots-three" label="Options" />}>
  <div style={{ font: 'var(--type-display)' }}>412 GB</div>
</Card>

<Card variant="inset" padded={false}><ProjectTable /></Card>
<Card variant="glass">Floating popover content</Card>
```

`variant="glass"` is only for layers that float over other content. Set `padded={false}` when the child owns its own padding (tables, images).
