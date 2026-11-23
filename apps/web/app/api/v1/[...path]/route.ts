import { NextRequest } from 'next/server';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
async function proxy(request: NextRequest) {
  const origin = process.env.AMVS_ORIGIN;
  const backend = process.env.AMVS_API_URL;
  if (!origin || !backend)
    return Response.json(
      { message: 'Hãy khởi chạy bằng scripts/start.ps1.' },
      { status: 503 },
    );
  if (
    request.headers.get('host') !== new URL(origin).host ||
    (request.headers.get('origin') &&
      request.headers.get('origin') !== origin) ||
    request.headers.get('sec-fetch-site') === 'cross-site'
  )
    return Response.json(
      { message: 'Nguồn truy cập không được phép.' },
      { status: 403 },
    );
  const path = request.nextUrl.pathname;
  if (!/^\/api\/v1\/[a-zA-Z0-9/_-]+$/.test(path))
    return new Response(null, { status: 400 });
  const headers = new Headers();
  for (const name of ['authorization', 'content-type', 'range', 'cookie']) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  headers.set('origin', origin);
  const init: RequestInit & { duplex?: string } = {
    method: request.method,
    headers,
    redirect: 'manual',
    cache: 'no-store',
    signal: request.signal,
  };
  if (!['GET', 'HEAD'].includes(request.method)) {
    init.body = request.body;
    init.duplex = 'half';
  }
  try {
    const response = await fetch(new URL(path, backend), init);
    const out = new Headers();
    for (const name of [
      'content-type',
      'content-length',
      'content-range',
      'accept-ranges',
      'content-disposition',
      'set-cookie',
    ]) {
      const value = response.headers.get(name);
      if (value) out.set(name, value);
    }
    out.set('cache-control', 'no-store');
    out.set('x-content-type-options', 'nosniff');
    return new Response(response.body, {
      status: response.status,
      headers: out,
    });
  } catch {
    return Response.json(
      { message: 'Không kết nối được dịch vụ local.' },
      { status: 502 },
    );
  }
}
export {
  proxy as GET,
  proxy as POST,
  proxy as PATCH,
  proxy as DELETE,
  proxy as HEAD,
};
