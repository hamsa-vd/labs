Renders a Phosphor glyph at a tokenised size and weight — use this instead of a raw `<i class="ph …">` tag anywhere an icon is needed.

```jsx
<Icon name="rocket-launch" size={16} />
<Icon name="house" weight="fill" size={20} />        {/* selected tab */}
<Icon name="trash" size={16} label="Delete project" /> {/* icon carries meaning */}
```

Weights: `regular` default everywhere · `fill` for selected states only · `bold` at 12–14px where hairlines drop out. Icons inherit `currentColor`; pass `color` only when the label beside it is accented too.
