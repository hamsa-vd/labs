'use client';
import { Button, Checkbox, Table, TableCell, TableHead, TableRow } from '@labs/design/arey';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import type { ApplicationListItem } from '@/application/tracker-service';
import { StatusBadge } from './status-badge';

export function ApplicationsTable({ applications }: { applications: ApplicationListItem[] }) {
  const [selected,setSelected]=useState<string[]>([]);const router=useRouter();
  function toggle(id:string){setSelected((current)=>current.includes(id)?current.filter((value)=>value!==id):[...current,id]);}
  async function merge(){if(selected.length!==2)return;await fetch('/api/v1/applications/merge',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({sourceId:selected[1],targetId:selected[0]})});setSelected([]);router.refresh();}
  return <><div className="ascend-actions" style={{ margin:'var(--space-4)'}}><Button iconLeft="git-merge" disabled={selected.length!==2} onClick={merge}>Merge selected</Button><span className="ascend-meta">Select exactly two applications</span></div><Table><thead><TableRow><TableHead>Merge</TableHead><TableHead>Company</TableHead><TableHead>Role</TableHead><TableHead>Status</TableHead><TableHead>Source</TableHead><TableHead align="right">Events</TableHead></TableRow></thead><tbody>{applications.map((application)=><TableRow key={application.id}><TableCell><Checkbox checked={selected.includes(application.id)} onChange={()=>toggle(application.id)} aria-label={`Select ${application.company}`}/></TableCell><TableCell><Link href={`/applications/${application.id}`} style={{fontWeight:600,color:'var(--text-primary)'}}>{application.company}</Link></TableCell><TableCell>{application.role??'Role unknown'}</TableCell><TableCell><StatusBadge status={application.status}/></TableCell><TableCell mono>{application.source??application.origin}</TableCell><TableCell mono align="right">{application.eventCount}</TableCell></TableRow>)}</tbody></Table></>;
}
