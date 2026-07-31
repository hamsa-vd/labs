Transient confirmation, bottom-right, on glass.

```jsx
<ToastRegion>
  <Toast tone="success" title="Deployment promoted to production" onDismiss={close} />
  <Toast tone="danger" title="Build failed at step 3" description="Check the install log." action={<Button variant="link">View logs</Button>} />
</ToastRegion>
```

Never celebratory, never emoji. Errors say what happened, then what to do.
