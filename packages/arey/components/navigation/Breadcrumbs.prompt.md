Ancestry trail in the top bar. Separator is a 12px Phosphor caret, never a "/" glyph.

```jsx
<Breadcrumbs items={[
  { label: 'riya', href: '#' },
  { label: 'arey-web', href: '#' },
  { label: 'Deployments' },
]} />
```

The last item is current, coloured `--text-primary`, and not a link.
