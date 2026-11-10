The list primitive behind settings rows, iOS grouped lists, and result lists.

```jsx
<List inset>
  <ListRow icon="bell" title="Notifications" chevron onClick={open} />
  <ListRow icon="moon" title="Appearance" value="System" chevron onClick={open} />
  <ListRow icon="key" title="API key" value="sk_live_9f2a" mono trailing={<IconButton icon="copy" label="Copy" size="sm" />} />
</List>
```

`inset` for mobile and settings; plain `<List>` inside an existing Card.
