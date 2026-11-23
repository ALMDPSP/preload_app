async function dashboardCompletedStores(){
 if(!dashboardData)return;
 modal('<h2>Lojas totalmente viradas</h2><p>Somente filiais com todos os PDVs previstos Orion OK.</p><label for="completedStoreSearch">Pesquisar loja</label><input id="completedStoreSearch" type="search" placeholder="Código ou nome da filial"><div id="completedStoreResults" aria-live="polite"></div>');
 const input=$('completedStoreSearch'),host=$('completedStoreResults');
 let revision=0,timer;
 async function load(page=1){
  const current=++revision;
  host.setAttribute('aria-busy','true');
  host.innerHTML='<p role="status">Carregando lojas…</p>';
  try{
   const params=new URLSearchParams({...dashboardData.filters,store_q:input.value,page});
   const result=await api('/api/dashboard/completed-stores?'+params);
   if(current!==revision||!$('modal').open||$('completedStoreResults')!==host)return;
   host.innerHTML=`<p>${result.total.toLocaleString('pt-BR')} loja(s) totalmente virada(s) · Página ${result.page} de ${result.pages}</p><div class="report-table-wrap"><table class="branch-table"><thead><tr><th>Filial</th><th>PDVs Orion OK</th><th>Ação</th></tr></thead><tbody>${result.rows.map((row,i)=>`<tr><td><b>${esc(row.code)}</b><span>${esc(row.name)}</span></td><td>${row.ok} / ${row.expected}</td><td><button type="button" data-completed-store="${i}">Abrir filial</button></td></tr>`).join('')||'<tr><td colspan="3">Nenhuma loja totalmente virada neste filtro.</td></tr>'}</tbody></table></div><div class="actions"><button type="button" id="completedStorePrevious" ${result.page<=1?'disabled':''}>Anterior</button><button type="button" id="completedStoreNext" ${result.page>=result.pages?'disabled':''}>Próxima</button></div>`;
   $('completedStorePrevious').onclick=()=>load(result.page-1);
   $('completedStoreNext').onclick=()=>load(result.page+1);
   host.querySelectorAll('[data-completed-store]').forEach(button=>button.onclick=()=>openCentralFromDashboard(result.rows[Number(button.dataset.completedStore)].id));
  }catch(err){
   if(current===revision&&$('completedStoreResults')===host)host.innerHTML='<p role="alert">'+esc(err.message)+'</p>';
  }finally{if(current===revision)host.setAttribute('aria-busy','false')}
 }
 input.oninput=()=>{clearTimeout(timer);revision++;host.innerHTML='<p role="status">Pesquisando lojas…</p>';timer=setTimeout(()=>load(),300)};
 input.focus();await load();
}
