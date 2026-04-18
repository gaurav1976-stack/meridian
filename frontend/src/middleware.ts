// Next.js edge middleware — HTTP Basic Auth front door.
//
// When BASIC_AUTH_USER and BASIC_AUTH_PASSWORD are both set in the frontend
// service's environment, every request to this Next.js app is gated behind
// HTTP Basic Auth with those credentials. When either is missing the
// middleware is a no-op (dev / local default).
//
// Paired with backend/app/core/basic_auth.py so the backend enforces the
// same shared secret — see frontend/src/lib/api/client.ts for the SSR
// Authorization-header pass-through.
//
// Meridian Airport PMO suite
// (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
// Proprietary software — unauthorised copying, distribution, modification or
// use is prohibited.

import { NextRequest, NextResponse } from "next/server";

const USER = process.env.BASIC_AUTH_USER ?? "";
const PW = process.env.BASIC_AUTH_PASSWORD ?? "";

const REALM = 'Basic realm="Meridian"';

function unauthorized(): NextResponse {
  return new NextResponse("Authentication required.", {
    status: 401,
    headers: {
      "WWW-Authenticate": REALM,
      "Content-Type": "text/plain",
    },
  });
}

function credentialsMatch(header: string | null): boolean {
  if (!header) return false;
  if (!header.toLowerCase().startsWith("basic ")) return false;
  let decoded: string;
  try {
    decoded = atob(header.slice(6).trim());
  } catch {
    return false;
  }
  const idx = decoded.indexOf(":");
  if (idx < 0) return false;
  const user = decoded.slice(0, idx);
  const pw = decoded.slice(idx + 1);
  return user === USER && pw === PW;
}

export function middleware(req: NextRequest) {
  // No-op mode when either secret is blank — essential so local dev works.
  if (!USER || !PW) {
    return NextResponse.next();
  }

  const auth = req.headers.get("authorization");
  if (credentialsMatch(auth)) {
    return NextResponse.next();
  }
  return unauthorized();
}

// Match everything except static/internals and the Next.js image optimiser.
// Health path isn't gated here because the frontend has none — Render uses
// the backend's /health endpoint for liveness probes.
export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|assets/).*)",
  ],
};
