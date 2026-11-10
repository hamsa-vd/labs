The action control — one `primary` per view, `secondary` for everything else, `ghost` inside toolbars and table rows.

```jsx
<Button variant="primary" iconLeft="rocket-launch">Create project</Button>
<Button>Cancel</Button>
<Button variant="ghost" size="sm" iconRight="arrow-up-right">View logs</Button>
<Button variant="danger" loading>Deleting</Button>
```

Labels are sentence case and verb-first ("Rotate key", not "Key Rotation"). `inverse` is the black-on-white / white-on-black CTA used on marketing surfaces. `link` collapses the box entirely for inline actions. Press gives `scale(.97)`; focus replaces hover with the accent ring.
