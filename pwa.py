"""Public PWA metadata and a network-only service worker."""
from flask import jsonify,send_from_directory

def register_pwa(app,root):
    @app.get('/manifest.webmanifest')
    def manifest():
        response=jsonify(id='/',name='Cutover DPSP — Linx para Orion',short_name='Cutover',lang='pt-BR',description='Checklist e acompanhamento de cutovers por filial.',start_url='/',scope='/',display='standalone',background_color='#f5f6f9',theme_color='#242735',icons=[{'src':'/static/app-icon-192.png','sizes':'192x192','type':'image/png','purpose':'any'},{'src':'/static/app-icon-512.png','sizes':'512x512','type':'image/png','purpose':'any'},{'src':'/static/app-icon-maskable.png','sizes':'512x512','type':'image/png','purpose':'maskable'}])
        response.mimetype='application/manifest+json'
        return response
    @app.get('/sw.js')
    def service_worker():
        response=send_from_directory(root/'static','sw.js',mimetype='application/javascript',max_age=0)
        response.headers['Service-Worker-Allowed']='/'
        return response
