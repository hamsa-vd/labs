'use client';
import { Button } from '@labs/design/arey';
import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

export function ApplicationActions({ id }: { id:string }) {
  const [loading,setLoading]=useState(false);const router=useRouter();
  async function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();setLoading(true);const form=new FormData(event.currentTarget);await fetch(`/api/v1/applications/${id}`,{method:'PATCH',headers:{'content-type':'application/json'},body:JSON.stringify({action:'status',status:form.get('status'),occurredAt:new Date().toISOString()})});setLoading(false);router.refresh();}
  return <form className="ascend-inline-form" onSubmit={submit}><label className="ascend-label">Update status<select name="status"><option value="acknowledged">Acknowledged</option><option value="assessment">Assessment</option><option value="interview_invite">Interview</option><option value="offer">Offer</option><option value="rejected">Rejected</option><option value="withdrawn">Withdrawn</option></select></label><Button type="submit" loading={loading}>Add event</Button></form>;
}
