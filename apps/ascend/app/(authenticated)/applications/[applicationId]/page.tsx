/**
 * Application detail. The prototype styles every board card and table row as
 * clickable but never defines the destination; this is it. Owns the full event
 * history, manual status override, merge and unmerge, and "this was never an
 * application". See architecture §11.5.1, and ui_kits/console DeploymentDetail
 * in @hamsa-designs/arey for the layout precedent.
 */
export default async function ApplicationDetailPage({
  params,
}: Readonly<{ params: Promise<{ applicationId: string }> }>) {
  await params;
  return null;
}
