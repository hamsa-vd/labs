Single-line text control — 36px, 12px radius, hairline border with a soft inset shadow.

```jsx
<Input placeholder="arey-web" />
<Input icon="magnifying-glass" placeholder="Search projects" suffix={<Kbd keys="cmd+k" />} />
<Input mono defaultValue="sk_live_9f2a…" />
<Input invalid defaultValue="bad name" />
```

Wrap in `<Field>` for a label and helper text. Focus replaces the hover border with the accent ring.
