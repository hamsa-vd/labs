Modal sheet — 20px radius, rises 8px with a scale from .98, scrim at 28 %.

```jsx
<Dialog
  open={open}
  onClose={close}
  title="Delete project"
  description="This removes all deployments and cannot be undone."
  footer={<><Button onClick={close}>Cancel</Button><Button variant="danger">Delete</Button></>}
>
  <Field label="Type the project name to confirm"><Input placeholder="arey-web" /></Field>
</Dialog>
```

Destructive dialogs require typing the name. Cancel sits left of the primary action.
