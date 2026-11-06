let dashboardData=null,dashboardPage=1,dashboardRequest=0,dashboardSearchTimer;
async function showDashboard(){
 ['cutoverWorkspace','branchesPage','reportsPage'].forEach(id=>$(id).classList.add('hidden'));$('dashboardPage').classList.remove('hidden');
 document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('active',b.id==='dashboardNav'));
 await refreshDashboard();
}
function dashboardQuery(){return new URLSearchParams({q:$('dashboardSearch').value.trim(),uf:$('dashboardUf').value}).toString()}
async function refreshDashboard(){
 const sequence=++dashboardRequest;$('dashboardMessage').textContent='Atualizando máquinas e filiais…';$('dashboardPdf').disabled=true;$('dashboardCsv').disabled=true;
 try{const data=await api('/api/dashboard?'+dashboardQuery());if(sequence!==dashboardRequest)return;dashboardData=data;dashboardPage=1;
 const uf=$('dashboardUf').value;$('dashboardUf').innerHTML='<option value="">Todas as UFs</option>'+data.ufs.map(u=>`<option>${esc(u)}</option>`).join('');$('dashboardUf').value=uf;
 $('dashboardMessage').textContent='Dados salvos · '+new Date(data.generated_at).toLocaleString('pt-BR')+' · Uma máquina por filial + número de PDV. O preenchimento ainda não salvo não entra na contagem.';
 renderDashboard();$('dashboardPdf').disabled=false;$('dashboardCsv').disabled=false;
 }catch(e){if(sequence!==dashboardRequest)return;dashboardData=null;$('dashboardMessage').textContent=e.message;$('dashboardCards').innerHTML='';$('dashboardStores').innerHTML='';$('dashboardEvolution').innerHTML='';$('dashboardProgress').innerHTML='';$('dashboardExceptions').hidden=true;}
}
function renderDashboard(){
 if(!dashboardData)return;const d=dashboardData,t=d.totals;
 $('dashboardCards').innerHTML=[['PDVs previstos',t.expected,'Meta das lojas ativas'],['Virados e Orion OK',t.ok,t.percent+'% do parque previsto'],['PDVs pendentes',t.pending,'Inclui os ainda não iniciados'],['Lojas completas',t.stores_ok,t.stores+' lojas no escopo']].map(([label,n,detail])=>`<div class="stat"><small>${label}</small><strong>${n}</strong><small>${detail}</small></div>`).join('');
 $('dashboardProgress').innerHTML=`<div class="dashboard-progress-label"><b>${t.percent}% concluído</b><span>${t.ok} de ${t.expected} PDVs</span></div><div class="bar"><span style="width:${t.percent}%"></span></div><p class="muted">${t.stores_pending} loja(s) com pendências. Fora do escopo: ${d.excluded.inactive} inativa(s), ${d.excluded.opening_soon} a inaugurar e ${d.excluded.needs_review} vínculo(s) a revisar.</p>`;
 $('dashboardEvolution').innerHTML=dashboardChart(d.evolution,t.ok)+`<p class="muted dashboard-small">A curva considera as datas de aprovação dos PDVs que estão OK hoje; não representa fotografias históricas do parque.${d.date_references?' '+d.date_references+' PDV(s) sem histórico de aprovação usam a última gravação como referência.':''}</p>`;
 const pages=Math.max(1,Math.ceil(d.stores.length/25));dashboardPage=Math.max(1,Math.min(pages,dashboardPage));const stores=d.stores.slice((dashboardPage-1)*25,dashboardPage*25);
 $('dashboardStores').innerHTML=stores.length?`<div class="report-table-wrap"><table class="branch-table"><thead><tr><th>Loja</th><th>Evolução</th><th>Números dos PDVs</th><th>Ações</th></tr></thead><tbody>${stores.map(s=>`<tr><td><b>${esc(s.code)}</b><span>${esc(s.name)}</span><span>${esc([s.city,s.uf].filter(Boolean).join(' / '))}</span></td><td><strong>${s.ok} / ${s.expected} OK</strong><span>${s.pending} pendente(s)</span><div class="bar"><span style="width:${s.percent}%"></span></div></td><td><div class="pdv-chips">${s.machines.map(m=>`<span class="pdv-chip ${m.ok?'ok':'pending'}" title="${esc(m.status)}">PDV ${esc(m.pdv)} · ${m.ok?'OK':'Pendente'}</span>`).join('')}</div></td><td><div class="actions"><button data-dashboard-store="${esc(s.id)}">Ver PDVs</button>${DECIDE?`<button data-dashboard-plan="${esc(s.id)}">Ajustar PDVs</button>`:''}</div></td></tr>`).join('')}</tbody></table></div><div class="branch-pagination"><span>${d.stores.length} loja(s) · Página ${dashboardPage} de ${pages}</span><div class="actions"><button id="dashboardPrevious" ${dashboardPage===1?'disabled':''}>Anterior</button><button id="dashboardNext" ${dashboardPage===pages?'disabled':''}>Próxima</button></div></div>`:'<div class="empty">Nenhuma filial ativa neste recorte. Cadastre ou ative as lojas para iniciar o acompanhamento.</div>';
 if(stores.length){$('dashboardPrevious').onclick=()=>{dashboardPage--;renderDashboard()};$('dashboardNext').onclick=()=>{dashboardPage++;renderDashboard()}}
 document.querySelectorAll('[data-dashboard-store]').forEach(b=>b.onclick=()=>dashboardStore(b.dataset.dashboardStore));document.querySelectorAll('[data-dashboard-plan]').forEach(b=>b.onclick=()=>dashboardPlan(b.dataset.dashboardPlan));
 $('dashboardExceptions').innerHTML=d.exceptions.length?`<h3>Numeração para revisar · ${d.exceptions.length}</h3><p>Estes registros não entram na meta nem nos PDVs OK até a numeração corresponder ao plano da loja.</p><ul>${d.exceptions.slice(0,100).map(e=>`<li>${esc(e.code)} · PDV ${esc(e.pdv||'não informado')}: ${esc(e.reason)}</li>`).join('')}</ul>${d.exceptions.length>100?'<p>Os demais registros aparecem no relatório executivo.</p>':''}`:'';$('dashboardExceptions').hidden=!d.exceptions.length;
}
function dashboardChart(series,total){
 if(!series.length)return '<div class="empty">Ainda não há PDVs Orion OK no recorte.</div>';
 const x=i=>45+(660*i/Math.max(1,series.length-1)),y=n=>170-140*n/Math.max(1,total),points=series.map((p,i)=>x(i)+','+y(p.cumulative_ok)).join(' ');
 return `<svg class="dashboard-chart" viewBox="0 0 750 210" role="img" aria-label="Evolução dos PDVs atualmente Orion OK"><title>PDVs Orion OK acumulados por data de aprovação</title><line x1="45" y1="170" x2="705" y2="170" stroke="#c9d9cf"/><line x1="45" y1="25" x2="45" y2="170" stroke="#c9d9cf"/><text x="12" y="175">0</text><text x="12" y="35">${total}</text><polyline points="${points}" fill="none" stroke="#087e67" stroke-width="3"/>${series.map((p,i)=>`<circle cx="${x(i)}" cy="${y(p.cumulative_ok)}" r="${series.length<35?4:2}" fill="#087e67"><title>${esc(p.day)}: ${p.daily_ok} no dia · ${p.cumulative_ok} acumulados</title></circle>`).join('')}<text x="45" y="198">${esc(series[0].day)}</text><text x="705" y="198" text-anchor="end">${esc(series[series.length-1].day)}</text></svg>`;
}
function dashboardStore(id){
 const s=dashboardData.stores.find(s=>s.id===id);if(!s)return;
 modal(`<h2>${esc(s.code)} · ${esc(s.name)}</h2><p>${s.ok} de ${s.expected} PDVs Orion OK · ${s.pending} pendente(s)</p><div class="report-table-wrap"><table class="branch-table"><thead><tr><th>PDV</th><th>Situação atual</th><th>Processos</th><th>Execução</th></tr></thead><tbody>${s.machines.map(m=>`<tr><td><b>${esc(m.pdv)}</b></td><td>${esc(m.status)}${m.rejection_reason?'<br>'+esc(m.rejection_reason):''}</td><td>${m.completed} / 11</td><td>${m.cutover_id?`<button data-dashboard-open="${esc(m.cutover_id)}">Abrir</button>`:'Não iniciada'}</td></tr>`).join('')}</tbody></table></div>`);
 document.querySelectorAll('[data-dashboard-open]').forEach(b=>b.onclick=async()=>{if(!await switchBranch(id))return;await loadExecution(b.dataset.dashboardOpen);$('modal').close();document.querySelector('[data-view="run"]').click()});
}
function dashboardPlan(id){
 const s=dashboardData.stores.find(s=>s.id===id);if(!s||!DECIDE)return;
 modal(`<h2>PDVs previstos · ${esc(s.code)}</h2><p>O padrão é 4 PDVs por loja. Ajuste a lista para corresponder aos números reais dos equipamentos.</p><form id="pdvPlanForm" class="form-stack"><div class="row2"><div><label for="pdvPlanCount">Quantidade</label><input id="pdvPlanCount" type="number" min="1" max="50" value="${s.expected}"></div><div><label>&nbsp;</label><button type="button" id="generatePdvNumbers">Gerar de 01 até a quantidade</button></div></div><label for="pdvPlanNumbers">Números dos PDVs (separados por vírgula)</label><input id="pdvPlanNumbers" value="${esc(s.pdvs.join(', '))}" required><p class="muted">Exemplo: 01, 02, 03, 04. Se a loja usa outra numeração, informe os números reais. Alterar a lista muda a meta; os cutovers existentes permanecem.</p><p id="pdvPlanError" role="alert" class="sync-error"></p><button class="primary" id="savePdvPlan">Salvar PDVs previstos</button></form>`);
 $('generatePdvNumbers').onclick=()=>{const n=Number($('pdvPlanCount').value);if(!Number.isInteger(n)||n<1||n>50){$('pdvPlanError').textContent='Use uma quantidade entre 1 e 50.';return}$('pdvPlanNumbers').value=Array.from({length:n},(_,i)=>String(i+1).padStart(2,'0')).join(', ')};
 $('pdvPlanForm').onsubmit=async e=>{e.preventDefault();$('savePdvPlan').disabled=true;try{await api('/api/branches/'+id+'/pdv-plan','PUT',{pdvs:$('pdvPlanNumbers').value.split(/[,;]+/).map(s=>s.trim()).filter(Boolean),version:s.plan_version});$('modal').close();await refreshDashboard();toast('Plano de PDVs atualizado.')}catch(err){$('pdvPlanError').textContent=err.message;$('savePdvPlan').disabled=false}};
}
async function executiveDownload(){
 if(!dashboardData)return;const button=$('dashboardPdf');button.disabled=true;
 try{const response=await fetch('/api/dashboard/executive.pdf?'+new URLSearchParams(dashboardData.filters),{credentials:'same-origin'});if(!response.ok){const data=await response.json();throw Error(data.error||'Falha ao gerar relatório.')}
 const url=URL.createObjectURL(await response.blob()),a=document.createElement('a');a.href=url;a.download='Relatorio_Executivo_PDV_Orion.pdf';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }catch(e){toast(e.message)}finally{button.disabled=false}
}
function dashboardCsv(){
 if(!dashboardData)return;const rows=[['Filial','Loja','PDV','Situação','Orion OK','Atualizado em'],...dashboardData.machines.map(m=>[m.code,m.name,m.pdv,m.status,m.ok?'Sim':'Não',m.updated_at||''])];
 const cell=value=>{let text=String(value??'');if(/^\s*[=+@-]/.test(text))text="'"+text;return '"'+text.replace(/"/g,'""')+'"'};
 const url=URL.createObjectURL(new Blob(['\ufeff'+rows.map(r=>r.map(cell).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='Evolucao_PDV_Orion.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function initDashboard(){
 const nav=document.createElement('button');nav.id='dashboardNav';nav.textContent='▥ Dashboard';nav.onclick=showDashboard;document.querySelector('.nav').prepend(nav);
 $('dashboardSearch').oninput=()=>{clearTimeout(dashboardSearchTimer);dashboardSearchTimer=setTimeout(refreshDashboard,300)};$('dashboardUf').onchange=refreshDashboard;$('refreshDashboard').onclick=refreshDashboard;$('dashboardPdf').onclick=executiveDownload;$('dashboardCsv').onclick=dashboardCsv;
 showDashboard();
}
initDashboard();
