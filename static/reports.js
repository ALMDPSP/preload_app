let reportRows=[],reportPage=1,reportLoadSequence=0;
const reportLabels=['Concluído','Pendente','Em andamento','Bloqueado','Aguardando aceite','Rejeitado','Sem cutover'];
const reportNormalize=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');
function filteredReports(){const q=reportNormalize($('reportSearch').value.trim()),status=$('reportStatus').value,uf=$('reportUf').value;return reportRows.filter(r=>(!status||r.status===status)&&(!uf||r.uf===uf)&&reportNormalize([r.code,r.name,r.city,r.uf,r.pdv,r.title].join(' ')).includes(q))}
async function showReports(){
 if(typeof hideOperations==='function')hideOperations();
 $('usersPage').classList.add('hidden');$('usersNav')?.classList.remove('active');
 $('dashboardPage').classList.add('hidden');$('dashboardNav')?.classList.remove('active');
 $('cutoverWorkspace').classList.add('hidden');$('branchesPage').classList.add('hidden');$('reportsPage').classList.remove('hidden');
 document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('active',b.id==='reportsNav'));
 await refreshReports();
}
async function refreshReports(){
 const sequence=++reportLoadSequence;reportRows=[];$('reportTotals').textContent='';$('reportMessage').textContent='Carregando relatórios…';$('exportReport').disabled=true;$('reportCards').innerHTML='';$('reportTable').innerHTML='';
 try{const data=await api('/api/reports/cutovers');if(sequence!==reportLoadSequence)return;reportRows=data.rows;reportPage=1;
 const previous=$('reportUf').value;$('reportUf').innerHTML='<option value="">Todas as UFs</option>'+[...new Set(reportRows.map(r=>r.uf).filter(Boolean))].sort().map(uf=>`<option value="${esc(uf)}">${esc(uf)}</option>`).join('');$('reportUf').value=previous;if(!$('reportUf').value)$('reportUf').value='';
 $('reportMessage').textContent='Dados salvos no banco · Atualizado em '+new Date(data.generated_at).toLocaleString('pt-BR')+'. Alterações ainda não salvas no checklist não entram no relatório.';$('exportReport').disabled=false;renderReports();
 }catch(e){if(sequence!==reportLoadSequence)return;reportRows=[];$('reportMessage').textContent=e.message;}
}
function renderReports(){
 const rows=filteredReports(),cutovers=rows.filter(r=>r.cutover_id),pending=['Pendente','Em andamento','Bloqueado','Aguardando aceite'];
 const cards=[['Concluídos',cutovers.filter(r=>r.status==='Concluído').length],['Com pendências',cutovers.filter(r=>pending.includes(r.status)).length],['Rejeitados',cutovers.filter(r=>r.status==='Rejeitado').length],['Filiais sem cutover',rows.filter(r=>!r.cutover_id).length]];
 $('reportCards').innerHTML=cards.map(([label,n])=>`<div class="stat"><small>${label}</small><strong>${n}</strong></div>`).join('');
 $('reportTotals').textContent=new Set(rows.map(r=>r.branch_id)).size+' filial(is) · '+cutovers.length+' cutover(s) · '+cutovers.reduce((n,r)=>n+r.completed,0)+' processos concluídos · '+cutovers.reduce((n,r)=>n+r.pending,0)+' não concluídos. Totais conforme os filtros; execuções rejeitadas entram na contagem de processos.';
 const pages=Math.max(1,Math.ceil(rows.length/50));reportPage=Math.max(1,Math.min(pages,reportPage));const shown=rows.slice((reportPage-1)*50,reportPage*50);
 $('reportTable').innerHTML=rows.length?`<div class="report-table-wrap"><table class="branch-table"><thead><tr><th>Filial / PDV</th><th>Situação</th><th>Processos</th><th>Última atualização</th><th>Ações</th></tr></thead><tbody>${shown.map(r=>`<tr><td><b>${esc(r.code)} · ${esc(r.name)}</b><span>${esc([r.city,r.uf].filter(Boolean).join(' / '))}${r.pdv?' · PDV '+esc(r.pdv):''}${r.opening_soon?' · A inaugurar':''}${!r.active?' · Inativa':''}</span></td><td><span class="badge ${r.status==='Concluído'?'done':r.status==='Rejeitado'||r.status==='Bloqueado'?'blocked':''}">${esc(r.status)}</span></td><td>${r.total?`${r.completed} de ${r.total} concluídos<br><small>${r.pending} não concluídos${r.blocked?' · '+r.blocked+' bloqueado(s)':''}</small>`:'Não iniciados'}</td><td>${r.updated_at?esc(new Date(r.updated_at).toLocaleString('pt-BR')):'—'}</td><td><div class="actions">${r.cutover_id?`<button data-report-detail="${esc(r.cutover_id)}">Ver pendências</button><button data-report-open="${esc(r.cutover_id)}">Abrir cutover</button>`:`<button data-report-branch="${esc(r.branch_id)}">Abrir filial</button>`}</div></td></tr>`).join('')}</tbody></table></div><div class="branch-pagination"><span>Página ${reportPage} de ${pages}</span><div class="actions"><button id="previousReport" ${reportPage===1?'disabled':''}>Anterior</button><button id="nextReport" ${reportPage===pages?'disabled':''}>Próxima</button></div></div>`:'<div class="empty">Nenhum registro encontrado. Confira os filtros ou cadastre as filiais.</div>';
 if(rows.length){$('previousReport').onclick=()=>{reportPage--;renderReports()};$('nextReport').onclick=()=>{reportPage++;renderReports()}}
 document.querySelectorAll('[data-report-detail]').forEach(b=>b.onclick=()=>reportDetail(b.dataset.reportDetail));
 document.querySelectorAll('[data-report-open]').forEach(b=>b.onclick=()=>openReportCutover(b.dataset.reportOpen));
 document.querySelectorAll('[data-report-branch]').forEach(b=>b.onclick=()=>openReportBranch(b.dataset.reportBranch));
}
async function reportDetail(id){
 try{const r=await api('/api/cutovers/'+encodeURIComponent(id));const tasks=r.state.tasks;
 modal(`<h2>${esc(r.state.meta.branch)}</h2><p class="muted">Versão salva ${r.version}. Concluído exige todos os processos e os dois aceites GO com responsável e data.</p>${r.rejection?`<p class="notice">Rejeitado: ${esc(r.rejection.reason)}</p>`:''}<div class="report-table-wrap"><table class="branch-table"><thead><tr><th>Processo</th><th>Situação</th><th>Observações</th></tr></thead><tbody>${ALL.map(t=>{const task=tasks[t.id]||{};return `<tr><td>${esc(t.title)}</td><td>${esc(task.status||'Pendente')}</td><td>${esc(task.notes||'—')}</td></tr>`}).join('')}</tbody></table></div><p>GO retirada: ${esc(r.state.decisions.linx.value||'Pendente')} · GO operação: ${esc(r.state.decisions.orion.value||'Pendente')}</p>`);
 }catch(e){toast(e.message)}
}
async function openReportBranch(id){if(!await switchBranch(id))return;document.querySelector('[data-view="run"]').click()}
async function openReportCutover(id){const row=reportRows.find(r=>r.cutover_id===id);if(!row)return;if(!await switchBranch(row.branch_id))return;await loadExecution(id);document.querySelector('[data-view="run"]').click()}
function exportReport(){
 const cell=value=>{let text=String(value??'');if(/^[\s]*[=+@\-]/.test(text))text="'"+text;return '"'+text.replace(/"/g,'""')+'"'};
 const rows=[['Filial','Nome','Cidade','UF','PDV','Situação','Concluídos','Não concluídos','Bloqueados','Atualizado em'],...filteredReports().map(r=>[r.code,r.name,r.city,r.uf,r.pdv,r.status,r.completed,r.pending,r.blocked,r.updated_at?new Date(r.updated_at).toLocaleString('pt-BR'):''])];
 const blob=new Blob(['\ufeff'+rows.map(r=>r.map(cell).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Relatorio_Cutovers.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function downloadRolloutExecutivePdf(sourceButton=null){
 const button=sourceButton?.tagName==='BUTTON'?sourceButton:$('executiveRolloutPdf');if(button.disabled)return;
 const label=button.textContent;button.disabled=true;button.textContent='Gerando PDF executivo…';
 try{
  const response=await fetch('/api/reports/rollout-executive.pdf',{credentials:'same-origin',headers:{Accept:'application/pdf'}});
  if(!response.ok){let message='Não foi possível gerar o PDF executivo. Tente novamente.';try{const data=await response.json();message=data.error||message}catch{}throw Error(message)}
  if(!(response.headers.get('Content-Type')||'').includes('application/pdf'))throw Error('Sessão expirada. Entre novamente para baixar o relatório.');
  const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');
  link.href=url;link.download='Executivo_Rollout_PDV_Orion.pdf';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  toast('PDF executivo gerado. Confira os downloads do navegador.');
 }catch(error){toast(error.message)}finally{button.disabled=false;button.textContent=label}
}
function initReports(){
 const nav=document.createElement('button');nav.id='reportsNav';nav.textContent='▤ Relatórios';nav.onclick=showReports;document.querySelector('.nav').append(nav);
 $('reportStatus').innerHTML='<option value="">Todas as situações</option>'+reportLabels.map(s=>`<option>${s}</option>`).join('');
 ['reportSearch','reportStatus','reportUf'].forEach(id=>$(id).addEventListener(id==='reportSearch'?'input':'change',()=>{reportPage=1;renderReports()}));
 $('refreshReports').onclick=refreshReports;$('exportReport').onclick=exportReport;$('executiveRolloutPdf').onclick=downloadRolloutExecutivePdf;
}
initReports();
