/* Online app: no caching of sessions, APIs, checklists or reports. */
self.addEventListener('install',event=>event.waitUntil(self.skipWaiting()));
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
self.addEventListener('fetch',event=>{
 if(event.request.method!=='GET'||event.request.mode!=='navigate'||new URL(event.request.url).origin!==self.location.origin)return;
 event.respondWith(fetch(event.request).catch(()=>new Response('<!doctype html><html lang="pt-BR"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cutover — Sem conexão</title><body style="font:17px system-ui;background:#f3f7f5;color:#18363b;padding:40px;max-width:560px;margin:auto"><h1>Conecte-se para continuar</h1><p>O Cutover precisa de internet para entrar, carregar os registros e salvar o checklist.</p><p>Confira a conexão e abra o aplicativo novamente.</p><a href="/">Tentar novamente</a></body></html>',{status:503,headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'}})));
});
