/* Operational work queue, waves, period reporting and administrator recovery. */
let managementTab='queue',managementPage=1,managementSequence=0,managementQueue=null,managementWaves=[],restoreFile=null,restorePreview=null;
function hideManagement(){if($('managementPage'))$('managementPage').classList.add('hidden');['queueNav','wavesNav','backupNav'].forEach(id=>$(id)?.classList.remove('active'))}
function activateManagement(tab){
 hideOperations();['cutoverWorkspace','branchesPage','reportsPage','dashboardPage','usersPage','operationsPage','rolloutBasePage'].forEach(id=>$(id).classList.add('hidden'));
 managementTab=tab;$('managementPage').classList.remove('hidden');document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('active',b.id===({queue:'queueNav',waves:'wavesNav',backup:'backupNav'}[tab])));
 $('managementTitle').textContent={queue:'Fila operacional',waves:'Ondas do rollout',backup:'Backup e restauração'}[tab];
 $('managementSubtitle').textContent={queue:'PDVs do dia, responsáveis, aceites e impedimentos em uma fila de trabalho.',waves:'Planeje por período e acompanhe previsto versus validado.',backup:'Proteja os dados operacionais e confira o arquivo antes de restaurar.'}[tab];
 $('managementFilters').hidden=tab!=='queue';$('managementAdd').hidden=tab!=='waves'||!DECIDE;$('managementCards').innerHTML='';$('managementContent').innerHTML='';
}
async function showManagement(tab='queue'){
 if(tab==='backup'&&ROLE!=='admin'){toast('Somente Administrador gerencia backups.');return}
 activateManagement(tab);managementPage=1;
 if(tab==='queue')await refreshManagementQueue();
 else if(tab==='waves')await refreshManagementWaves();
 else renderBackupManager();
}
async function refreshManagementQueue(page=1){
 managementPage=page;const sequence=++managementSequence;$('managementMessage').textContent='Carregando fila salva…';
 const args=new URLSearchParams({page,mode:$('queueMode').value,owner:$('queueOwner').value,wave:$('queueWave').value,q:$('queueSearch').value});
 try{
  const data=await api('/api/rollout/queue?'+args);if(sequence!==managementSequence||managementTab!=='queue')return;
  managementQueue=data;const owner=$('queueOwner').value,wave=$('queueWave').value;
  $('queueOwner').innerHTML='<option value="">Todos os responsáveis</option><option value="my">Meus PDVs / validações</option>'+data.people.filter(u=>u.role!=='viewer').map(u=>`<option value="${esc(u.id)}">${esc(u.name)}</option>`).join('');$('queueOwner').value=owner;
  $('queueWave').innerHTML='<option value="">Todas as ondas</option>'+data.waves.map(w=>`<option value="${esc(w.id)}">${esc(w.name)}</option>`).join('');$('queueWave').value=wave;
  $('managementMessage').textContent=data.total+' PDV(s) no filtro · Hoje: '+data.today.split('-').reverse().join('/')+'. Atraso exige prazo definido; PDVs sem planejamento não são tratados como atrasados.';
  $('managementCards').innerHTML=[['PDVs na fila',data.total],['Atrasados',data.metrics.overdue],['Aguardando aceite',data.metrics.approval],['Ocorrências críticas',data.metrics.critical]].map(([label,value])=>`<article class="stat"><small>${label}</small><strong>${value}</strong></article>`).join('');
  $('managementContent').innerHTML=`<div class="report-table-wrap"><table class="branch-table"><thead><tr><th>Filial / PDV</th><th>Execução</th><th>Responsáveis</th><th>Onda / prazo</th><th>Impedimentos</th><th>Ação</th></tr></thead><tbody>${data.rows.map((r,i)=>`<tr><td><b>${esc(r.code)} · PDV ${esc(r.pdv)}</b><span>${esc(r.name)}</span></td><td><span class="badge ${r.ok?'done':r.overdue?'blocked':''}">${esc(r.status)}</span></td><td>Executor: ${esc(r.executor)}<span>Validador: ${esc(r.validator)}</span></td><td>${esc(r.wave)}<span>${esc(r.planned_date?r.planned_date.split('-').reverse().join('/'):'Sem prazo')}${r.overdue?' · Atrasado':''}</span></td><td>${r.open_issues} aberta(s)${r.critical?' · '+r.critical+' crítica(s)':''}<span>${esc(r.impact||'Sem impacto informado')}</span></td><td><button data-queue-open="${i}">Atender PDV →</button></td></tr>`).join('')||'<tr><td colspan="6">Nenhum PDV neste filtro. Use Todas as execuções para consultar outros registros.</td></tr>'}</tbody></table></div><div class="branch-pagination"><span>Página ${data.page} de ${data.pages}</span><div class="actions"><button id="queuePrev" ${data.page<=1?'disabled':''}>Anterior</button><button id="queueNext" ${data.page>=data.pages?'disabled':''}>Próxima</button></div></div>`;
  $('queuePrev').onclick=()=>refreshManagementQueue(data.page-1);$('queueNext').onclick=()=>refreshManagementQueue(data.page+1);
  document.querySelectorAll('[data-queue-open]').forEach(b=>b.onclick=()=>{const r=data.rows[Number(b.dataset.queueOpen)];openCentralFromDashboard(r.branch_id,r.pdv)});
 }catch(e){if(sequence===managementSequence)$('managementMessage').textContent=e.message}
}
async function refreshManagementWaves(){
 const sequence=++managementSequence;$('managementMessage').textContent='Carregando ondas…';
 try{const data=await api('/api/rollout/waves');if(sequence!==managementSequence||managementTab!=='waves')return;managementWaves=data.rows;
  $('managementMessage').textContent='Os números usam os PDVs vinculados à onda na central. Validado exige Orion OK; a situação administrativa da onda não altera o checklist.';
  $('managementContent').innerHTML=`<div class="report-table-wrap"><table class="branch-table"><thead><tr><th>Onda / período</th><th>Previstos</th><th>Implantados</th><th>Validados</th><th>Atrasados</th><th>Justificativa</th><th>Ação</th></tr></thead><tbody>${data.rows.map((w,i)=>`<tr><td><b>${esc(w.name)}</b><span>${esc(w.start_date)} até ${esc(w.due_date)} · ${esc(w.status)}</span></td><td>${w.planned}</td><td>${w.deployed}</td><td>${w.validated} / ${w.planned}<span>${w.percent}%</span></td><td>${w.overdue}</td><td>${esc(w.delay_reason||'Não informada')}</td><td><button data-wave-queue="${i}">Ver PDVs</button>${DECIDE?`<button data-wave-edit="${i}">Editar</button><button data-wave-bind="${i}">Vincular filial</button>`:''}</td></tr>`).join('')||'<tr><td colspan="7">Nenhuma onda cadastrada. Crie uma onda e vincule os PDVs na central.</td></tr>'}</tbody></table></div>`;
  document.querySelectorAll('[data-wave-bind]').forEach(b=>b.onclick=()=>bindWaveBranch(data.rows[Number(b.dataset.waveBind)]));
  document.querySelectorAll('[data-wave-edit]').forEach(b=>b.onclick=()=>waveForm(data.rows[Number(b.dataset.waveEdit)]));
  document.querySelectorAll('[data-wave-queue]').forEach(b=>b.onclick=async()=>{const id=data.rows[Number(b.dataset.waveQueue)].id;await showManagement('queue');$('queueMode').value='all';$('queueWave').value=id;await refreshManagementQueue()});
 }catch(e){if(sequence===managementSequence)$('managementMessage').textContent=e.message}
}
function waveForm(row=null){
 if(!DECIDE)return;
 modal(`<h2>${row?'Editar onda':'Nova onda do rollout'}</h2><form id="waveForm" class="form-stack"><label for="waveName">Nome da onda</label><input id="waveName" maxlength="120" value="${esc(row?.name||'')}" required><div class="row2"><div><label for="waveStart">Início</label><input id="waveStart" type="date" value="${esc(row?.start_date||'')}" required></div><div><label for="waveDue">Prazo</label><input id="waveDue" type="date" value="${esc(row?.due_date||'')}" required></div></div><label for="waveStatus">Situação administrativa</label><select id="waveStatus">${['Planejada','Em execução','Concluída','Cancelada'].map(s=>`<option ${row?.status===s?'selected':''}>${s}</option>`).join('')}</select><label for="waveReason">Justificativa de desvio / atraso</label><textarea id="waveReason" maxlength="2000">${esc(row?.delay_reason||'')}</textarea><label for="waveNotes">Observações</label><textarea id="waveNotes" maxlength="2000">${esc(row?.notes||'')}</textarea><p class="muted">Depois de salvar, abra a filial na central e escolha esta onda nos PDVs atendidos. O progresso é calculado pelos registros salvos.</p><p id="waveError" class="sync-error" role="alert"></p><button id="waveSave" class="primary">Salvar onda</button></form>`);
 $('waveForm').onsubmit=async e=>{e.preventDefault();$('waveSave').disabled=true;try{await api('/api/rollout/waves'+(row?'/'+row.id:''),row?'PUT':'POST',{name:$('waveName').value,start_date:$('waveStart').value,due_date:$('waveDue').value,status:$('waveStatus').value,delay_reason:$('waveReason').value,notes:$('waveNotes').value,version:row?.version||0});$('modal').close();if(managementTab==='waves')await refreshManagementWaves();toast('Onda salva.')}catch(err){$('waveError').textContent=err.message;$('waveSave').disabled=false}};
}
async function bindWaveBranch(wave){
 if(!DECIDE)return;if(dirty||centralDirty){toast('Salve os rascunhos da central antes de vincular a filial.');return}
 await ensureBranches();
 modal(`<h2>Vincular filial à onda</h2><p>${esc(wave.name)}</p><form id="waveBindForm" class="form-stack"><label for="waveBranchCode">Código da filial</label><input id="waveBranchCode" list="waveBranchOptions" required placeholder="Digite o código"><datalist id="waveBranchOptions">${registeredBranches.map(b=>`<option value="${esc(b.code)}">${esc(b.name)}</option>`).join('')}</datalist><p class="notice">Vincula todos os PDVs previstos desta filial. Executor, validador e datas específicas existentes são preservados.</p><p id="waveBindError" class="sync-error" role="alert"></p><button id="waveBindSave" class="primary">Vincular todos os PDVs da filial</button></form>`);
 $('waveBindForm').onsubmit=async e=>{e.preventDefault();const branch=registeredBranches.find(b=>b.code.toUpperCase()===$('waveBranchCode').value.trim().toUpperCase());if(!branch){$('waveBindError').textContent='Escolha uma filial cadastrada.';return}
 $('waveBindSave').disabled=true;try{const ctx=await api('/api/rollout/branches/'+branch.id+'/context');const versions=Object.fromEntries(ctx.machines.map(m=>[m.pdv,(ctx.assignments||[]).find(a=>a.pdv===m.pdv)?.version||0]));
 await api('/api/rollout/waves/'+wave.id+'/assign-branch','POST',{branch_id:branch.id,plan_version:ctx.plan_version,versions});$('modal').close();if(centralData?.branch.id===branch.id)centralData=null;await refreshManagementWaves();toast('Filial vinculada à onda.')}catch(err){$('waveBindError').textContent=err.message;$('waveBindSave').disabled=false}};
}
async function downloadManagementFile(path,name,button=null){
 const label=button?.textContent;if(button){button.disabled=true;button.textContent='Preparando arquivo…'}
 try{const response=await fetch(path,{credentials:'same-origin'});if(!response.ok){const d=await response.json();throw Error(d.error||'Não foi possível gerar o arquivo.')}
 const url=URL.createObjectURL(await response.blob()),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);toast('Download solicitado. Confira os downloads do navegador.');
 }catch(e){toast(e.message)}finally{if(button){button.disabled=false;button.textContent=label}}
}
function renderBackupManager(){
 $('managementMessage').textContent='Backup operacional assinado: filiais, PDVs, cadastros, ondas, pendências, checklists e histórico. Não inclui senhas, MFA, sessões ou chaves. Contas existentes são preservadas na restauração.';
 $('managementContent').innerHTML='<div class="backup-grid"><section class="panel"><h2>Baixar backup operacional</h2><p>Guarde o arquivo em local restrito. A restauração exige a mesma SECRET_KEY e uma versão compatível do sistema.</p><button id="downloadOperationalBackup" class="primary">↓ Baixar backup .json.gz</button><button id="checkOperationalIntegrity" type="button">Conferir integridade e totais</button><div id="integrityResult" role="status"></div></section><section class="panel"><h2>Conferir e restaurar</h2><p>A restauração substitui os dados operacionais. Primeiro confira a prévia e combine uma janela sem alterações com a equipe.</p><label for="restoreUpload">Arquivo de backup</label><input type="file" id="restoreUpload" accept=".gz,.json"><button id="previewOperationalBackup">Conferir arquivo</button><div id="restoreDetails" role="status"></div></section></div>';
 $('downloadOperationalBackup').onclick=()=>downloadManagementFile('/api/admin/operational-backup','Backup_Operacional_Rollout.json.gz',$('downloadOperationalBackup'));
 $('checkOperationalIntegrity').onclick=async()=>{const button=$('checkOperationalIntegrity');button.disabled=true;try{const data=await api('/api/admin/operational-integrity');$('integrityResult').innerHTML='<h3>'+esc(data.ok?'Conferência sem erro estrutural':'Confira os erros identificados')+'</h3>'+(data.totals?'<p>'+data.totals.stores+' lojas · '+data.totals.planned+' PDVs previstos · '+data.totals.deployed+' implantados · '+data.totals.validated+' validados</p>':'')+data.issues.map(i=>'<p>'+i.count+' · '+esc(i.description)+'</p>').join('')+'<small>'+esc(data.note)+'</small>'}catch(e){$('integrityResult').textContent=e.message}finally{button.disabled=false}};
 $('restoreUpload').onchange=()=>{restorePreview=null;restoreFile=$('restoreUpload').files[0];$('restoreDetails').innerHTML=''};
 $('previewOperationalBackup').onclick=previewOperationalBackup;
}
async function restoreRequest(path,extra={}){
 const form=new FormData();form.append('file',restoreFile);for(const [k,v]of Object.entries(extra))form.append(k,v);
 const r=await fetch(path,{method:'POST',headers:{'X-CSRF-Token':csrf},body:form,credentials:'same-origin'});const data=await r.json();if(!r.ok)throw Error(data.error||'Não foi possível concluir.');return data;
}
async function previewOperationalBackup(){
 if(!restoreFile){toast('Selecione um arquivo de backup.');return}
 const button=$('previewOperationalBackup');button.disabled=true;
 try{restorePreview=await restoreRequest('/api/admin/operational-restore/preview');
 const labels={ct_branches:'Filiais',ct_branch_pdv_plan:'Planos de PDVs',ct_cutovers:'Cutovers',ct_cutover_branch:'Vínculos de filial',ct_cutover_reviews:'Rejeições',ct_audit:'Histórico de auditoria',ct_rollout_organization:'GR / regionais',ct_rollout_inventory:'Implantações',ct_rollout_waves:'Ondas',ct_pdv_assignments:'Atribuições',ct_rollout_schedule:'Cronogramas',ct_rollout_issues:'Pendências',ct_rollout_goals:'Metas',ct_rollout_snapshots:'Consolidados diários'};
 $('restoreDetails').innerHTML='<h3>Prévia da restauração</h3><p>Backup de '+esc(new Date(restorePreview.created_at).toLocaleString('pt-BR'))+'</p><div class="report-table-wrap"><table class="branch-table"><thead><tr><th>Dados</th><th>Atuais</th><th>No backup</th></tr></thead><tbody>'+Object.entries(restorePreview.counts).map(([key,value])=>'<tr><td>'+esc(labels[key]||key)+'</td><td>'+value.current+'</td><td>'+value.backup+'</td></tr>').join('')+'</tbody></table></div><p class="notice">'+esc(restorePreview.note)+(restorePreview.unlinked_assignments?' '+restorePreview.unlinked_assignments+' atribuição(ões) ficarão sem responsável.':'')+'</p><label for="restoreConfirmation">Para substituir os dados operacionais, digite RESTAURAR</label><input id="restoreConfirmation" autocomplete="off"><button id="applyOperationalRestore" class="danger">Confirmar restauração</button><p id="restoreError" class="sync-error" role="alert"></p>';
 $('applyOperationalRestore').onclick=async()=>{
  if($('restoreConfirmation').value!=='RESTAURAR'){toast('Digite RESTAURAR para confirmar.');return}
  if(dirty||centralDirty||saving||centralSaving){toast('Salve ou descarte os rascunhos da central antes de restaurar.');return}
  $('applyOperationalRestore').disabled=true;
  try{const result=await restoreRequest('/api/admin/operational-restore/apply',{token:restorePreview.token,confirmation:'RESTAURAR'});restorePreview=null;restoreFile=null;registeredBranches=[];centralData=null;centralSaved=null;selectedBranchId='';clearCurrentCutover();showBranchPdvs();toast(result.note);renderBackupManager()}catch(e){$('restoreError').textContent=e.message;$('applyOperationalRestore').disabled=false}
 };
 }catch(e){$('restoreDetails').textContent=e.message}finally{button.disabled=false}
}
function periodQuery(prefix){
 const from=$(prefix+'From')?.value,to=$(prefix+'To')?.value;
 if(!from||!to||from>to)throw Error('Escolha um período válido, com início anterior ao fim.');
 return new URLSearchParams({from,to}).toString();
}
function drawManagementDashboard(data){
 const el=$('managementDashboard');if(!el||!data)return;
 el.innerHTML=`<section class="panel management-executive"><div class="rollout-panel-heading"><div><span class="eyebrow">PREVISTO X REALIZADO</span><h2>Período: ${esc(data.from_date.split('-').reverse().join('/'))} a ${esc(data.to_date.split('-').reverse().join('/'))}</h2></div><button id="openDayQueue">Abrir fila do dia →</button></div><div class="stats">${[['Previsto no período',data.current.planned],['Previstos já validados',data.current.validated_planned],['Previstos não validados',data.current.deviation],['Validados por data',data.current.validated]].map(([label,value])=>`<div class="stat"><small>${label}</small><strong>${value}</strong></div>`).join('')}</div><p class="management-comparison">Período anterior (${esc(data.previous_from)} a ${esc(data.previous_to)}): ${data.previous.validated} validação(ões) vigente(s) por data. Variação: ${data.validated_delta>0?'+':''}${data.validated_delta} PDV(s).</p><div class="management-flags"><span>${data.overdue} PDV(s) atrasado(s)</span><span>${data.awaiting_acceptance} aguardando aceite</span><span>${data.critical} ocorrência(s) crítica(s)</span><span>${data.unassigned} sem executor atribuído</span></div><details class="rollout-definitions"><summary>Critérios do período</summary><p>${esc(data.note)} Previsto usa a data específica do PDV, o cronograma ou o prazo da onda. As datas do planejamento refletem o cadastro atual.</p></details></section>`;
 $('openDayQueue').onclick=()=>showManagement('queue');
}
async function refreshManagementPeriod(){
 const button=$('applyDashboardPeriod');button.disabled=true;
 try{const result=await api('/api/rollout/summary?'+periodQuery('dashboard'));drawManagementDashboard(result)}catch(e){toast(e.message)}finally{button.disabled=false}
}
async function refreshCentralIssues(){
 if(!selectedBranchId)return;
 const data=await api('/api/rollout/branches/'+encodeURIComponent(selectedBranchId)+'/context');
 if(centralData&&centralData.branch.id===selectedBranchId)centralData.issues=data.issues;
 renderCentralIssuePanel();
}
function renderCentralIssuePanel(){
 const host=$('centralIssuesHost');if(!host)return;
 const rows=(centralData?.issues||[]).filter(r=>Number(r.pdv)===Number(centralPdv));
 host.innerHTML=`<details class="central-record central-issues"><summary><b>Pendências do PDV ${esc(centralPdv)}</b><span>${rows.length} aberta(s)</span></summary><div class="management-issue-list">${rows.map((r,i)=>`<article><b>${esc(r.title)}</b><span>${esc(r.owner)} · ${esc(r.due_date)} · ${esc(r.priority)}</span><p>${esc(r.impact||'Impacto não informado')}</p><button type="button" data-central-issue="${i}">${READONLY?'Consultar':'Atualizar / resolver'}</button></article>`).join('')||'<p class="muted">Nenhuma pendência aberta para este PDV.</p>'}${READONLY?'':'<button id="centralNewIssue" type="button">+ Registrar impedimento</button>'}</div></details>`;
 host.querySelectorAll('[data-central-issue]').forEach(b=>b.onclick=()=>issueForm(rows[Number(b.dataset.centralIssue)]));
 if($('centralNewIssue'))$('centralNewIssue').onclick=async()=>{await issueForm();$('opBranch').value=currentBranch()?.code||'';$('opPdv').value=centralPdv};
}
function initManagement(){
 const section=document.createElement('section');section.id='managementPage';section.className='hidden';
 section.innerHTML='<div class="section-top"><div><div class="eyebrow">OPERAÇÃO E GESTÃO</div><h1 id="managementTitle"></h1><p id="managementSubtitle" class="muted"></p></div><div class="actions"><button id="managementRefresh">Atualizar</button><button id="managementAdd" class="primary">+ Nova onda</button></div></div><div id="managementFilters" class="report-filters"><div><label for="queueSearch">Filial, PDV ou responsável</label><input id="queueSearch" type="search"></div><div><label for="queueMode">Fila</label><select id="queueMode"><option value="today">Fila do dia</option><option value="all">Todas as execuções / planejamentos</option><option value="approval">Aguardando aceite</option><option value="overdue">Atrasados</option><option value="done">Orion OK</option></select></div><div><label for="queueOwner">Responsáveis</label><select id="queueOwner"><option value="">Todos os responsáveis</option><option value="my">Meus PDVs / validações</option></select></div><div><label for="queueWave">Onda</label><select id="queueWave"><option value="">Todas as ondas</option></select></div></div><p id="managementMessage" class="notice" role="status"></p><div id="managementCards" class="stats"></div><div id="managementContent" class="panel"></div>';
 document.querySelector('main').append(section);
 const oldHide=hideRolloutBase;hideRolloutBase=function(){oldHide();hideManagement()};
 const nav=document.querySelector('.nav'),icon=$('reportsNav').querySelector('svg')?.outerHTML||'';
 for(const [id,label,tab] of [['queueNav','Fila do dia','queue'],['wavesNav','Ondas de rollout','waves'],...(ROLE==='admin'?[['backupNav','Gestão de dados','backup']]:[])]){
  const button=document.createElement('button');button.id=id;button.title=label;button.innerHTML=icon+'<span class="nav-label">'+label+'</span>';button.onclick=()=>showManagement(tab);nav.append(button);
 }
 $('managementRefresh').onclick=()=>managementTab==='queue'?refreshManagementQueue(managementPage):managementTab==='waves'?refreshManagementWaves():renderBackupManager();
 $('managementAdd').onclick=()=>waveForm();
 let timer;$('queueSearch').oninput=()=>{clearTimeout(timer);timer=setTimeout(()=>refreshManagementQueue(),250)};
 for(const id of ['queueMode','queueOwner','queueWave'])$(id).onchange=()=>refreshManagementQueue();
 const parts=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'America/Sao_Paulo',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date()).map(p=>[p.type,p.value]));
 const current=parts.year+'-'+parts.month+'-'+parts.day,day=new Date(current+'T12:00:00Z');day.setUTCDate(day.getUTCDate()-(day.getUTCDay()+6)%7);const start=day.toISOString().slice(0,10),sunday=new Date(day);sunday.setUTCDate(sunday.getUTCDate()+6);const end=sunday.toISOString().slice(0,10);
 for(const prefix of ['dashboard','report']){
  $(prefix+'From').value=start;$(prefix+'To').value=end;
  const controls=$(prefix+'From').closest('.management-period'),preset=document.createElement('select');preset.id=prefix+'PeriodPreset';preset.setAttribute('aria-label','Atalhos de período');preset.innerHTML='<option value="current">Semana atual (seg. a dom.)</option><option value="previous">Semana anterior (seg. a dom.)</option><option value="custom">Período personalizado</option>';controls.prepend(preset);
  preset.onchange=()=>{if(preset.value==='custom')return;const from=new Date(start+'T12:00:00Z'),to=new Date(end+'T12:00:00Z');if(preset.value==='previous'){from.setUTCDate(from.getUTCDate()-7);to.setUTCDate(to.getUTCDate()-7)}$(prefix+'From').value=from.toISOString().slice(0,10);$(prefix+'To').value=to.toISOString().slice(0,10);if(prefix==='dashboard')refreshManagementPeriod()};
  for(const suffix of ['From','To'])$(prefix+suffix).addEventListener('input',()=>preset.value='custom');
 }
 $('applyDashboardPeriod').onclick=refreshManagementPeriod;
 $('operationalPeriodCsv').onclick=()=>{try{downloadManagementFile('/api/rollout/operations.csv?'+periodQuery('report'),'Rollout_Operacional_por_PDV.csv',$('operationalPeriodCsv'))}catch(e){toast(e.message)}};
 const oldRender=renderCentral;renderCentral=function(){oldRender();if(!$('centralFormHost'))return;if(!$('centralIssuesHost'))$('centralFormHost').insertAdjacentHTML('beforeend','<div id="centralIssuesHost"></div>');renderCentralIssuePanel()};
}
initManagement();
