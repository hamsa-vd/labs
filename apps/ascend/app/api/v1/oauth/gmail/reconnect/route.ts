import { NextRequest, NextResponse } from 'next/server';
import { currentUser } from '@/auth/access';

export async function POST(request: NextRequest) {
  if (!(await currentUser())) return Response.json({ error: 'forbidden' }, { status: 403 });
  return NextResponse.redirect(new URL('/api/v1/oauth/gmail/start', request.nextUrl.origin), 303);
}
