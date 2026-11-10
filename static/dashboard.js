let dashboardData=null,dashboardPage=1,dashboardRequest=0,dashboardSearchTimer;
async function showDashboard(){
 if(typeof hideOperations==='function')hideOperations();
 $('usersPage').classList.add('hidden');$('usersNav')?.classList.remove('active');
 ['cutoverWorkspace','branchesPage','reportsPage'].forEach(id=>$(id).classList.add('hidden'));$('dashboardPage').classList.remove('hidden');
 document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('active',b.id==='dashboardNav'));
 await refreshDashboard();
}
function dashboardQuery(){const args=new URLSearchParams({q:$('dashboardSearch').value.trim(),uf:$('dashboardUf').value});if($('dashboardFrom')?.value)args.set('from',$('dashboardFrom').value);if($('dashboardTo')?.value)args.set('to',$('dashboardTo').value);return args.toString()}
async function refreshDashboard(page=1){
 if(!Number.isInteger(page)||page<1)page=1;
 const sequence=++dashboardRequest;if(!dashboardData)$('dashboardCards').innerHTML=Array.from({length:4},()=>'<div class="skeleton-line"></div>').join('');$('dashboardMessage').textContent='Atualizando indicadores do rollout…';$('dashboardPdf').disabled=true;$('dashboardCsv').disabled=true;
 try{const data=await api('/api/dashboard?'+dashboardQuery()+'&compact=1&page='+page);if(sequence!==dashboardRequest)return;dashboardData=data;dashboardPage=data.pagination?.page||1;
 const uf=$('dashboardUf').value;$('dashboardUf').innerHTML='<option value="">Todas as UFs</option>'+data.ufs.map(u=>`<option>${esc(u)}</option>`).join('');$('dashboardUf').value=uf;
 $('dashboardMessage').textContent='Dados salvos · '+new Date(data.generated_at).toLocaleString('pt-BR')+' · Uma máquina por filial + número de PDV. O preenchimento ainda não salvo não entra na contagem.';
 renderDashboard();if(typeof renderRolloutBaseDashboard==='function')renderRolloutBaseDashboard(data);if(typeof drawManagementDashboard==='function')drawManagementDashboard(data.management);if(typeof refreshDashboardOperations==='function')refreshDashboardOperations(data.operations||null);$('dashboardPdf').disabled=false;$('dashboardCsv').disabled=false;
 }catch(e){if(sequence!==dashboardRequest)return;dashboardData=null;$('executiveDashboard').innerHTML='';$('rolloutBaseDashboard').innerHTML='';$('dashboardAttention').innerHTML='';$('dashboardMessage').textContent=e.message;$('dashboardCards').innerHTML='';$('dashboardStores').innerHTML='';$('dashboardEvolution').innerHTML='';document.querySelectorAll('[data-dashboard-focus]').forEach(b=>b.onclick=()=>dashboardMachines(b.dataset.dashboardFocus));
 $('dashboardProgress').innerHTML='';$('dashboardExceptions').hidden=true;}
}
function renderDashboard(){
 if(!dashboardData)return;const d=dashboardData,t=d.totals;
 $('dashboardCards').innerHTML=[['PDVs previstos',t.expected,'Meta das lojas ativas'],['Virados e Orion OK',t.ok,t.percent+'% do parque previsto'],['PDVs pendentes',t.pending,'Inclui os ainda não iniciados'],['Lojas completas',t.stores_ok,t.stores+' lojas no escopo']].map(([label,n,detail])=>`<button class="stat action-stat" data-dashboard-focus="${label}"><small>${label}</small><strong>${n}</strong><small>${detail} · Ver lista →</small></button>`).join('');
 document.querySelectorAll('[data-dashboard-focus]').forEach(b=>b.onclick=()=>dashboardMachines(b.dataset.dashboardFocus));
 $('dashboardProgress').innerHTML=`<div class="dashboard-progress-label"><b>${t.percent}% concluído</b><span>${t.ok} de ${t.expected} PDVs</span></div><div class="bar"><span style="width:${t.percent}%"></span></div><p class="muted">${t.stores_pending} loja(s) com pendências. Fora do escopo: ${d.excluded.inactive} inativa(s), ${d.excluded.opening_soon} a inaugurar e ${d.excluded.needs_review} vínculo(s) a revisar.</p>`;
 $('dashboardEvolution').innerHTML=dashboardChart(d.evolution,t.ok)+`<p class="muted dashboard-small">A curva considera as datas de aprovação dos PDVs que estão OK hoje; não representa fotografias históricas do parque.${d.date_references?' '+d.date_references+' PDV(s) sem histórico de aprovação usam a última gravação como referência.':''}</p>`;
 const pages=d.pagination?.pages||Math.max(1,Math.ceil(d.stores.length/25));dashboardPage=Math.max(1,Math.min(pages,dashboardPage));const stores=d.compact?d.stores:d.stores.slice((dashboardPage-1)*25,dashboardPage*25);
 $('dashboardStores').innerHTML=stores.length?`<div class="report-table-wrap"><table class="branch-table"><thead><tr><th>Loja</th><th>Evolução</th><th>Números dos PDVs</th><th>Ações</th></tr></thead><tbody>${stores.map(s=>`<tr><td><b>${esc(s.code)}</b><span>${esc(s.name)}</span><span>${esc([s.city,s.uf].filter(Boolean).join(' / '))}</span></td><td><strong>${s.ok} / ${s.expected} OK</strong><span>${s.pending} pendente(s)</span><div class="bar"><span style="width:${s.percent}%"></span></div></td><td><div class="pdv-chips">${s.machines.map(m=>`<span class="pdv-chip ${m.ok?'ok':'pending'}" title="${esc(m.status)}">PDV ${esc(m.pdv)} · ${m.ok?'OK':'Pendente'}</span>`).join('')}</div></td><td><div class="actions"><button data-dashboard-store="${esc(s.id)}">Ver PDVs</button>${DECIDE?`<button data-dashboard-plan="${esc(s.id)}">Ajustar PDVs</button>`:''}</div></td></tr>`).join('')}</tbody></table></div><div class="branch-pagination"><span>${d.totals.stores} loja(s) · Página ${dashboardPage} de ${pages}</span><div class="actions"><button id="dashboardPrevious" ${dashboardPage===1?'disabled':''}>Anterior</button><button id="dashboardNext" ${dashboardPage===pages?'disabled':''}>Próxima</button></div></div>`:'<div class="empty">Nenhuma filial ativa neste recorte. Cadastre ou ative as lojas para iniciar o acompanhamento.</div>';
 if(stores.length){$('dashboardPrevious').onclick=()=>d.compact?refreshDashboard(dashboardPage-1):(dashboardPage--,renderDashboard());$('dashboardNext').onclick=()=>d.compact?refreshDashboard(dashboardPage+1):(dashboardPage++,renderDashboard())}
 document.querySelectorAll('[data-dashboard-store]').forEach(b=>b.onclick=()=>dashboardStore(b.dataset.dashboardStore));document.querySelectorAll('[data-dashboard-plan]').forEach(b=>b.onclick=()=>dashboardPlan(b.dataset.dashboardPlan));
 if(typeof renderExecutiveDashboard==='function')renderExecutiveDashboard(d);
 $('dashboardExceptions').innerHTML=d.exceptions.length?`<h3>Numeração para revisar · ${d.totals.exceptions}</h3><p>Estes registros não entram na meta nem nos PDVs OK até a numeração corresponder ao plano da loja.</p><ul>${d.exceptions.slice(0,100).map(e=>`<li>${esc(e.code)} · PDV ${esc(e.pdv||'não informado')}: ${esc(e.reason)}</li>`).join('')}</ul>${d.totals.exceptions>100?'<p>Use a busca de loja para refinar essa lista.</p>':''}`:'';$('dashboardExceptions').hidden=!d.exceptions.length;
}
function dashboardChart(series,total){
 if(!series.length)return '<div class="empty">Ainda não há PDVs Orion OK no recorte.</div>';
 const x=i=>45+(660*i/Math.max(1,series.length-1)),y=n=>170-140*n/Math.max(1,total),points=series.map((p,i)=>x(i)+','+y(p.cumulative_ok)).join(' ');
 return `<svg class="dashboard-chart" viewBox="0 0 750 210" role="img" aria-label="Evolução dos PDVs atualmente Orion OK"><title>PDVs Orion OK acumulados por data de aprovação</title><line x1="45" y1="170" x2="705" y2="170" stroke="#c9d9cf"/><line x1="45" y1="25" x2="45" y2="170" stroke="#c9d9cf"/><text x="12" y="175">0</text><text x="12" y="35">${total}</text><polyline points="${points}" fill="none" stroke="#31527b" stroke-width="3"/>${series.map((p,i)=>`<circle cx="${x(i)}" cy="${y(p.cumulative_ok)}" r="${series.length<35?4:2}" fill="#31527b"><title>${esc(p.day)}: ${p.daily_ok} no dia · ${p.cumulative_ok} acumulados</title></circle>`).join('')}<text x="45" y="198">${esc(series[0].day)}</text><text x="705" y="198" text-anchor="end">${esc(series[series.length-1].day)}</text></svg>`;
}
async function dashboardStore(id){
 let s=dashboardData.stores.find(s=>s.id===id);if(!s&&dashboardData.compact){try{s=await api('/api/dashboard/store/'+encodeURIComponent(id))}catch(e){toast(e.message);return}}if(!s)return;
 modal(`<h2>${esc(s.code)} · ${esc(s.name)}</h2><p>${s.ok} de ${s.expected} PDVs Orion OK · ${s.pending} pendente(s)</p><div class="report-table-wrap"><table class="branch-table"><thead><tr><th>PDV</th><th>Situação atual</th><th>Processos</th><th>Execução</th></tr></thead><tbody>${s.machines.map(m=>`<tr><td><b>${esc(m.pdv)}</b></td><td>${esc(m.status)}${m.rejection_reason?'<br>'+esc(m.rejection_reason):''}</td><td>${m.completed} / 11</td><td>${m.cutover_id?`<button data-dashboard-open="${esc(m.cutover_id)}">Abrir</button>`:'Não iniciada'}</td></tr>`).join('')}</tbody></table></div>`);
 document.querySelectorAll('[data-dashboard-open]').forEach(b=>b.onclick=async()=>{if(!await switchBranch(id))return;await loadExecution(b.dataset.dashboardOpen);$('modal').close();document.querySelector('[data-view="run"]').click()});
}
async function dashboardPlan(id){return editBranchPdvPlan(id)}
async function editBranchPdvPlan(id){
 if(!DECIDE||!id)return;
 let s;try{s=await api('/api/branches/'+encodeURIComponent(id)+'/pdv-plan')}catch(e){toast(e.message);return}
 modal(`<h2>PDVs previstos · ${esc(s.code)}</h2><p>${esc(s.name)}</p><p>A loja pode ter mais de 4 PDVs. Adicione os equipamentos e salve para atualizar a meta no dashboard e nos relatórios.</p><form id="pdvPlanForm" class="form-stack"><div class="pdv-plan-toolbar"><strong id="pdvPlanTotal">${s.pdvs.length} PDVs previstos</strong><button type="button" id="appendPdvNumber">+ Adicionar próximo PDV</button></div><div class="row2"><div><label for="pdvPlanCount">Quantidade desejada</label><input id="pdvPlanCount" type="number" min="1" max="50" value="${s.pdvs.length}"></div><div><label>&nbsp;</label><button type="button" id="generatePdvNumbers">Aumentar até essa quantidade</button></div></div><label for="pdvPlanNumbers">Números reais dos PDVs (separados por vírgula)</label><input id="pdvPlanNumbers" value="${esc(s.pdvs.join(', '))}" required><p class="muted">Os botões acrescentam números sem remover os existentes. Para reduzir ou usar outra numeração, edite a lista. Os cutovers e checklists anteriores permanecem.</p><p id="pdvPlanError" role="alert" class="sync-error"></p><button class="primary" id="savePdvPlan">Salvar PDVs previstos</button></form>`);
 const values=()=>$('pdvPlanNumbers').value.split(/[,;]+/).map(v=>v.trim()).filter(Boolean);
 const display=list=>{$('pdvPlanNumbers').value=list.join(', ');$('pdvPlanTotal').textContent=list.length+' PDVs previstos';$('pdvPlanCount').value=list.length;$('pdvPlanError').textContent=''};
 function extend(target){
  const list=values();if(!Number.isInteger(target)||target<list.length||target>50){$('pdvPlanError').textContent='Informe uma quantidade maior ou igual à lista atual, até 50. Para reduzir, edite os números manualmente.';return}
  const numbers=list.map(v=>/^\d+$/.test(v)?Number(v):NaN);
  if(numbers.some(n=>!Number.isInteger(n)||n<1||n>9999)||new Set(numbers).size!==numbers.length){$('pdvPlanError').textContent='Confira a lista: use números únicos de 1 a 9999.';return}
  let next=Math.max(0,...numbers)+1;
  while(list.length<target){if(next>9999){next=1;while(numbers.includes(next))next++}list.push(String(next).padStart(2,'0'));numbers.push(next);next++}
  display(list);
 }
 $('appendPdvNumber').onclick=()=>extend(values().length+1);$('generatePdvNumbers').onclick=()=>extend(Number($('pdvPlanCount').value));$('pdvPlanNumbers').oninput=()=>{$('pdvPlanTotal').textContent=values().length+' PDVs previstos'};
 $('pdvPlanForm').onsubmit=async e=>{e.preventDefault();$('savePdvPlan').disabled=true;try{await api('/api/branches/'+id+'/pdv-plan','PUT',{pdvs:values(),version:s.plan_version});$('modal').close();if(!$('dashboardPage').classList.contains('hidden'))await refreshDashboard();toast('PDVs previstos atualizados. A loja já pode ter cutovers para os novos números.')}catch(err){$('pdvPlanError').textContent=err.message;$('savePdvPlan').disabled=false}};
}
async function executiveDownload(){
 if(!dashboardData)return;const button=$('dashboardPdf');button.disabled=true;
 try{const response=await fetch('/api/dashboard/executive.pdf?'+new URLSearchParams(dashboardData.filters),{credentials:'same-origin'});if(!response.ok){const data=await response.json();throw Error(data.error||'Falha ao gerar relatório.')}
 const url=URL.createObjectURL(await response.blob()),a=document.createElement('a');a.href=url;a.download='Relatorio_Executivo_PDV_Orion.pdf';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }catch(e){toast(e.message)}finally{button.disabled=false}
}
async function dashboardCsv(){
 if(!dashboardData)return;let exportData=dashboardData;try{if(exportData.compact)exportData=await api('/api/dashboard?'+dashboardQuery())}catch(e){toast(e.message);return}const rows=[['Filial','Loja','PDV','Situação','Orion OK','Atualizado em'],...exportData.machines.map(m=>[m.code,m.name,m.pdv,m.status,m.ok?'Sim':'Não',m.updated_at||''])];
 const cell=value=>{let text=String(value??'');if(/^\s*[=+@-]/.test(text))text="'"+text;return '"'+text.replace(/"/g,'""')+'"'};
 const url=URL.createObjectURL(new Blob(['\ufeff'+rows.map(r=>r.map(cell).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='Evolucao_PDV_Orion.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function initDashboard(){
 const nav=document.createElement('button');nav.id='dashboardNav';nav.textContent='▥ Dashboard';nav.onclick=showDashboard;document.querySelector('.nav').prepend(nav);
 $('dashboardSearch').oninput=()=>{clearTimeout(dashboardSearchTimer);dashboardSearchTimer=setTimeout(refreshDashboard,300)};$('dashboardUf').onchange=refreshDashboard;$('refreshDashboard').onclick=refreshDashboard;$('dashboardPdf').onclick=executiveDownload;$('dashboardCsv').onclick=dashboardCsv;
 showDashboard();
}
initDashboard();
async function dashboardMachines(focus,page=1){
 if(!dashboardData)return;
 if(dashboardData.compact){
  const status={'Virados e Orion OK':'ok','PDVs pendentes':'pending','Lojas completas':'stores_ok','PDVs previstos':'all'}[focus]||focus;
  modal('<h2>'+esc(focus)+'</h2><p>Carregando PDVs…</p>');
  try{const result=await api('/api/dashboard/machines?'+dashboardQuery()+'&status='+encodeURIComponent(status)+'&page='+page);if(!$('modal').open)return;renderMachinePage(focus,result);return}catch(e){$('modalBody').textContent=e.message;return}
 }
 const complete=new Set(dashboardData.stores.filter(s=>s.pending===0).map(s=>s.id));
 const machines=dashboardData.machines.filter(m=>focus==='Virados e Orion OK'?m.ok:focus==='PDVs pendentes'?!m.ok:focus==='Lojas completas'?complete.has(m.branch_id):true),pages=Math.max(1,Math.ceil(machines.length/40)),rows=machines.slice((page-1)*40,page*40);
 renderMachinePage(focus,{rows,page,pages,total:machines.length});
}
function renderMachinePage(focus,{rows,page,pages,total}){
 modal(`<h2>${esc(focus)}</h2><p>${total} PDV(s) no recorte atual · Página ${page} de ${pages}</p><div class="report-table-wrap"><table class="branch-table"><thead><tr><th>Filial / PDV</th><th>Situação</th><th>Ação</th></tr></thead><tbody>${rows.map((m,i)=>`<tr><td><b>${esc(m.code)} · PDV ${esc(m.pdv)}</b><span>${esc(m.name)}</span></td><td>${esc(m.status)}</td><td><button data-machine-index="${i}">Ver loja / execução</button></td></tr>`).join('')||'<tr><td colspan="3">Nenhum PDV neste filtro.</td></tr>'}</tbody></table></div><div class="actions"><button id="machinePrevious" ${page<=1?'disabled':''}>Anterior</button><button id="machineNext" ${page>=pages?'disabled':''}>Próxima</button></div>`);
 $('machinePrevious').onclick=()=>dashboardMachines(focus,page-1);$('machineNext').onclick=()=>dashboardMachines(focus,page+1);
 document.querySelectorAll('[data-machine-index]').forEach(b=>b.onclick=async()=>{const m=rows[Number(b.dataset.machineIndex)];if(!await switchBranch(m.branch_id))return;if(m.cutover_id)await loadExecution(m.cutover_id);$('modal').close();document.querySelector('[data-view="run"]').click();});
}
