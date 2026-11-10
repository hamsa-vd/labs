Filter chip or removable token — bordered, pill-shaped, 28px tall.

```jsx
<Tag icon="funnel" onClick={toggle} selected={active}>Production</Tag>
<Tag onRemove={() => remove('node-20')}>node-20</Tag>
```

Use Tag when the thing is interactive; use Badge when it's read-only status.
