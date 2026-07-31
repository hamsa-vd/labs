Wraps any form control with its label, helper text, and error. Use it rather than hand-rolling labels so the error pattern stays identical everywhere.

```jsx
<Field label="Project name" hint="Lowercase letters, numbers and dashes">
  <Input placeholder="arey-web" />
</Field>

<Field layout="row" label="Production branch" hint="Changes apply to the next deployment">
  <Select options={[{ value: 'main', label: 'main' }]} />
</Field>
```

arey marks *optional* fields, never required ones.
