Two-to-four option switch on an inset track; the selected segment lifts onto a card-coloured chip. The most iOS-flavoured control in arey.

```jsx
<SegmentedControl value={mode} onChange={setMode} options={['Light', 'Dark', 'System']} />
<SegmentedControl inline value={view} onChange={setView} options={[
  { value: 'grid', icon: 'squares-four', label: 'Grid' },
  { value: 'list', icon: 'rows', label: 'List' },
]} />
```

Selected items switch their icon to Phosphor `fill`.
