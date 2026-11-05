(()=>{
 let installPrompt=null;
 const button=document.getElementById('installApp');
 if(!button)return;
 const standalone=()=>window.matchMedia?.('(display-mode: standalone)').matches||window.navigator.standalone;
 const refresh=()=>button.hidden=!!standalone();refresh();
 window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();installPrompt=e;refresh()});
 window.addEventListener('appinstalled',()=>{installPrompt=null;button.hidden=true});
 button.onclick=async()=>{
  if(installPrompt){const prompt=installPrompt;installPrompt=null;try{await prompt.prompt();await prompt.userChoice}catch(e){showHelp()}return}
  showHelp();
 };
 function showHelp(){
  let dialog=document.getElementById('appInstallHelp');
  if(!dialog){dialog=document.createElement('dialog');dialog.id='appInstallHelp';dialog.style.cssText='max-width:520px;width:90%;border:1px solid #cddbd8;border-radius:14px;padding:24px;color:#18363b;font:15px system-ui;line-height:1.6';dialog.innerHTML='<h2>Instalar Cutover</h2><p>Abra o site no navegador do aparelho para instalar com um ícone na tela.</p><p><b>Android e computador:</b> use Chrome ou Edge. Procure Instalar aplicativo no menu do navegador ou o ícone de instalação na barra de endereço.</p><p><b>iPhone/iPad:</b> abra no Safari, toque em Compartilhar e escolha Adicionar à Tela de Início. Confirme em Adicionar.</p><p>O acesso continua com sua conta e Authenticator. É necessária conexão com a internet.</p><button type="button" style="padding:12px;border:1px solid #cddbd8;border-radius:8px;background:#087e67;color:white;cursor:pointer">Entendi</button>';document.body.append(dialog);dialog.querySelector('button').onclick=()=>dialog.close()}
  dialog.showModal();
 }
 if('serviceWorker' in navigator&&window.isSecureContext)navigator.serviceWorker.register('/sw.js',{scope:'/'}).catch(()=>{});
})();
