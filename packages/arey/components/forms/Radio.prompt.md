Single choice with all options visible. Above four options, use Select.

```jsx
<RadioGroup
  name="visibility"
  value={v}
  onChange={setV}
  options={[
    { value: 'private', label: 'Private', description: 'Only members can view deployments' },
    { value: 'public', label: 'Public', description: 'Anyone with the link can view' },
  ]}
/>
```
