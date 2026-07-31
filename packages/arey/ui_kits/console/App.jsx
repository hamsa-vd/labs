const { ToastRegion, Toast, Button, IconButton, EmptyState, Card } = window.AreyDesignSystem_1909f9;

function Placeholder({ page }) {
  return (
    <Page>
      <PageHead eyebrow="arey-web" title={page[0].toUpperCase() + page.slice(1)} />
      <Card variant="flat" padded={false}>
        <EmptyState
          icon="crosshair"
          title="Not part of this kit"
          description="This screen was not defined in the source material, so it is intentionally left blank rather than invented."
        />
      </Card>
    </Page>
  );
}

function App() {
  const [page, setPage] = React.useState('overview');
  const [detail, setDetail] = React.useState(null);
  const [toast, setToast] = React.useState(true);

  const crumbs = [{ label: 'riya', href: '#' }, { label: 'arey-web', href: '#' }, { label: detail ? detail.sha : page[0].toUpperCase() + page.slice(1) }];

  let body;
  if (detail) body = <DeploymentDetail d={detail} onBack={() => setDetail(null)} />;
  else if (page === 'overview') body = <Overview onOpenProject={() => setPage('deployments')} />;
  else if (page === 'deployments') body = <Deployments onSelect={setDetail} />;
  else if (page === 'settings') body = <Settings />;
  else body = <Placeholder page={page} />;

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-canvas)' }}>
      <Sidebar page={page} setPage={(p) => { setDetail(null); setPage(p); }} />
      <main style={{ flex: 1, minWidth: 0 }}>
        <TopBar crumbs={crumbs} actions={<Button size="sm" variant="secondary" iconLeft="terminal-window">CLI</Button>} />
        {body}
      </main>
      {toast && (
        <ToastRegion>
          <Toast tone="success" title="Deployment promoted to production" description="arey-web · a3f91c8" onDismiss={() => setToast(false)} />
        </ToastRegion>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
