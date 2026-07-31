Icon-only control for toolbars, table rows, and dismiss affordances.

```jsx
<IconButton icon="dots-three" label="More actions" />
<IconButton icon="x" label="Close" size="sm" />
<IconButton icon="sun" label="Toggle theme" variant="bordered" />
<IconButton icon="star" label="Star" weight="fill" aria-pressed={true} />
```

`aria-pressed="true"` gives the selected accent wash. Never ship one without `label`.
