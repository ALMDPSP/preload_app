let rolloutBaseData=null,rolloutBaseRequest=0,rolloutBasePage=1,rolloutBaseTimer;
function hideRolloutBase(){if($('rolloutBasePage'))$('rolloutBasePage').classList.add('hidden');$('rolloutBaseNav')?.classList.remove('active')}
async function showRolloutBase(){
 if(typeof hideOperations==='function')hideOperations();['cutoverWorkspace','branchesPage','reportsPage','dashboardPage','usersPage'].forEach(id=>$(id).classList.add('hidden'));$('rolloutBasePage').classList.remove('hidden');document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('active',b.id==='rolloutBaseNav'));await refreshRolloutBase();
}
async function refreshRolloutBase(page=1){
 if(!Number.isInteger(page))page=1;const sequence=++rolloutBaseRequest;$('rolloutBaseMessage').textContent='Carregando a base cadastrada…';
 const params=new URLSearchParams({q:$('rolloutBaseSearch').value,regional:$('rolloutBaseRegional').value,gr:$('rolloutBaseGr').value,uf:$('rolloutBaseUf').value,page});
 try{const data=await api('/api/rollout-base?'+params);if(sequence!==rolloutBaseRequest)return;rolloutBaseData=data;rolloutBasePage=data.page;
 for(const [id,key,label] of [['rolloutBaseRegional','regionals','Todas as regionais'],['rolloutBaseGr','grs','Todos os GRs'],['rolloutBaseUf','ufs','Todas as UFs']]){const value=$(id).value;$(id).innerHTML='<option value="">'+label+'</option>'+data[key].map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('');$(id).value=value}
 $('rolloutBaseMessage').textContent='GR e regional são por filial; versão e implantação são por PDV. Os indicadores do dashboard consideram apenas filiais ativas e abertas no escopo.';
 $('rolloutBaseTable').innerHTML=data.rows.length?`<div class="report-table-wrap"><table class="branch-table"><thead><tr><th>Filial</th><th>GR / Regional</th><th>PDVs previstos</th><th>Implantados</th><th>Escopo</th><th>Ação</th></tr></thead><tbody>${data.rows.map(r=>`<tr><td><b>${esc(r.code)}</b><span>${esc(r.name)} · ${esc(r.uf)}</span></td><td>${esc(r.gr||'GR não informado')}<span>${esc(r.regional||'Regional não informada')}</span></td><td>${r.expected}</td><td><b>${r.deployed} / ${r.expected}</b><span>${r.percent}%</span></td><td>${r.in_scope?'Ativa no rollout':r.opening_soon?'A inaugurar':!r.active?'Inativa':'Cadastro a revisar'}</td><td><button data-rollout-edit="${esc(r.id)}">${READONLY?'Consultar':'Abrir cadastro'}</button> <button data-base-cutover="${esc(r.id)}">Cutover da filial →</button></td></tr>`).join('')}</tbody></table></div><div class="branch-pagination"><span>${data.total} filial(is) · Página ${data.page} de ${data.pages}</span><div class="actions"><button id="rolloutBasePrevious" ${data.page===1?'disabled':''}>Anterior</button><button id="rolloutBaseNext" ${data.page===data.pages?'disabled':''}>Próxima</button></div></div>`:'<div class="empty">Nenhuma filial neste filtro. Cadastre as lojas na aba Filiais para começar.</div>';
 if(data.rows.length){$('rolloutBasePrevious').onclick=()=>refreshRolloutBase(data.page-1);$('rolloutBaseNext').onclick=()=>refreshRolloutBase(data.page+1)}document.querySelectorAll('[data-rollout-edit]').forEach(b=>b.onclick=()=>openRolloutBase(b.dataset.rolloutEdit));document.querySelectorAll('[data-base-cutover]').forEach(b=>b.onclick=()=>openCutoverFromBase(b.dataset.baseCutover));
 }catch(e){if(sequence===rolloutBaseRequest)$('rolloutBaseMessage').textContent=e.message}
}
async function chooseRolloutBranch(){
 try{await ensureBranches()}catch(e){toast(e.message);return}
 modal(`<h2>Cadastrar informações do rollout</h2><p class="muted">Escolha uma filial já cadastrada. Cada PDV previsto terá seu próprio registro.</p><form id="chooseRolloutBranch" class="form-stack"><label for="rolloutBranchCode">Código da filial</label><input id="rolloutBranchCode" list="rolloutBranchOptions" placeholder="Digite o código da filial" required autocomplete="off"><datalist id="rolloutBranchOptions">${registeredBranches.map(b=>`<option value="${esc(b.code)}">${esc(b.name)}</option>`).join('')}</datalist><p id="rolloutBranchError" class="sync-error" role="alert"></p><button class="primary">Abrir cadastro</button></form>`);
 $('chooseRolloutBranch').onsubmit=async e=>{e.preventDefault();const b=registeredBranches.find(b=>b.code.toUpperCase()===$('rolloutBranchCode').value.trim().toUpperCase());if(!b){$('rolloutBranchError').textContent='Escolha uma filial cadastrada pelo código.';return}await openRolloutBase(b.id)};
}
async function openRolloutBase(id){
 let data;try{data=await api('/api/rollout-base/branches/'+encodeURIComponent(id))}catch(e){toast(e.message);return}
 modal(`<h2>Base de Rollout · ${esc(data.branch.code)}</h2><p class="muted">${esc(data.branch.name)} · ${esc(data.branch.uf)}</p><div class="actions base-cutover-link"><button type="button" id="baseOpenCutover">Abrir cutover da filial →</button></div><form id="rolloutBaseForm" class="form-stack"><div class="row2"><div><label for="baseGr">Gerente regional (GR)</label><input id="baseGr" maxlength="120" value="${esc(data.gr)}" placeholder="Nome do GR" ${!DECIDE?'readonly':''}></div><div><label for="baseRegional">Regional</label><input id="baseRegional" maxlength="120" value="${esc(data.regional)}" placeholder="Ex.: SP CENTRO" ${!DECIDE?'readonly':''}></div></div><p class="notice">Marcar Implantado registra a implantação declarada e não emite GO nem conclui o checklist. PDVs com Orion OK também entram como implantados. Lojas atualizadas = ao menos um PDV implantado; lojas completas continuam exigindo todos os PDVs Orion OK.</p><div class="base-pdv-forms">${data.machines.map((m,i)=>`<section class="base-pdv-form" data-base-pdv="${i}"><div class="base-pdv-heading"><h3>PDV ${esc(m.pdv)}</h3><div class="actions">${DECIDE?`<button type="button" data-renumber-pdv="${i}">Alterar número</button>`:''}<button type="button" data-open-base-pdv="${i}">Abrir cutover do PDV →</button></div></div><div class="row2"><div><label for="baseStatus${i}">Situação declarada</label><select id="baseStatus${i}" data-base="status"><option ${m.status==='Pendente'?'selected':''}>Pendente</option><option ${m.status==='Implantado'?'selected':''}>Implantado</option></select></div><div><label for="baseVersion${i}">Versão instalada</label><input id="baseVersion${i}" data-base="installed_version" maxlength="80" value="${esc(m.installed_version)}" placeholder="Ex.: Orion 1.0.0"></div><div><label for="baseDate${i}">Data de implantação (opcional)</label><input id="baseDate${i}" data-base="deployed_at" type="date" value="${esc(m.deployed_at)}"></div><div><label for="baseNotes${i}">Observações (opcional)</label><input id="baseNotes${i}" data-base="notes" maxlength="2000" value="${esc(m.notes)}"></div></div></section>`).join('')}</div><p class="muted">Use Alterar número para corrigir a identificação de um PDV com seus registros. Para adicionar equipamentos, use Ajustar PDVs na aba Filiais. Versões não preenchidas aparecem como Não informada.</p><p id="rolloutBaseError" class="sync-error" role="alert"></p>${READONLY?'':'<button class="primary" id="saveRolloutBase">Salvar cadastro do rollout</button>'}</form>`);
 $('baseOpenCutover').onclick=()=>openCutoverFromBase(id);
 document.querySelectorAll('[data-open-base-pdv]').forEach(b=>b.onclick=()=>openCutoverFromBase(id,data.machines[Number(b.dataset.openBasePdv)].pdv));
 document.querySelectorAll('[data-renumber-pdv]').forEach(b=>b.onclick=()=>renameRolloutPdv(data,data.machines[Number(b.dataset.renumberPdv)]));
 $('rolloutBaseForm').addEventListener('input',()=>{$('rolloutBaseForm').dataset.dirty='1'});
 $('rolloutBaseForm').addEventListener('change',()=>{$('rolloutBaseForm').dataset.dirty='1'});
 if(READONLY){$('rolloutBaseForm').querySelectorAll('input,select').forEach(e=>e.disabled=true);return}
 $('rolloutBaseForm').onsubmit=async e=>{e.preventDefault();$('saveRolloutBase').disabled=true;
 const machines=data.machines.map((m,i)=>{const row=document.querySelector('[data-base-pdv="'+i+'"]');return {pdv:m.pdv,version:m.version,...Object.fromEntries([...row.querySelectorAll('[data-base]')].map(e=>[e.dataset.base,e.value]))}});
 try{await api('/api/rollout-base/branches/'+encodeURIComponent(id),'PUT',{regional:$('baseRegional').value,gr:$('baseGr').value,version:data.version,plan_version:data.plan_version,machines});$('modal').close();toast('Cadastro do rollout salvo. Os indicadores serão atualizados ao abrir o dashboard.');if(!$('rolloutBasePage').classList.contains('hidden'))await refreshRolloutBase(rolloutBasePage);else if(!$('dashboardPage').classList.contains('hidden'))await refreshDashboard()}catch(err){$('rolloutBaseError').textContent=err.message;$('saveRolloutBase').disabled=false}};
}
function baseHasUnsavedChanges(){
 const form=$('rolloutBaseForm');return $('modal').open&&form?.dataset.dirty==='1';
}
async function openCutoverFromBase(id,pdv=null){
 if(baseHasUnsavedChanges()){toast('Salve o cadastro do rollout antes de abrir o cutover.');return false}
 if(!allowDiscard())return false;
 dirty=false;
 try{
  if(!await switchBranch(id))return false;
  await refreshList();
  $('modal').close();document.querySelector('[data-view="run"]').click();showBranchPdvs();
  if(pdv&&typeof openCentralPdv==='function'){await openCentralPdv(String(Number(pdv)).padStart(2,'0'));return true}
  if(pdv){
   const machine=branchProgress?.machines.find(m=>Number(m.pdv)===Number(pdv));
   if(machine?.execution){if(await loadExecution(machine.execution.id))$('context').scrollIntoView?.({behavior:'smooth',block:'start'})}
   else if(DECIDE)startBoundCutover(pdv);
   else toast('Este PDV ainda não tem cutover. Solicite a abertura ao Gestor.');
  }
  return true;
 }catch(e){toast(e.message);return false}
}
function renameRolloutPdv(data,m){
 if(typeof centralIdentityGuard==='function'&&!centralIdentityGuard())return;
 if(baseHasUnsavedChanges()){toast('Salve o cadastro do rollout antes de alterar a numeração.');return}
 if(dirty||saving){toast('Salve o checklist em edição antes de alterar a numeração.');return}
 modal(`<h2>Alterar número do PDV</h2><p>${esc(data.branch.code)} · ${esc(data.branch.name)}</p><p class="notice">O cadastro, os cutovers, o cronograma e as pendências do PDV ${esc(m.pdv)} acompanharão o novo número. Os checklists salvos e seus históricos serão preservados.</p><form id="renumberPdvForm" class="form-stack"><label for="renumberPdvValue">Novo número do PDV</label><input id="renumberPdvValue" inputmode="numeric" pattern="[0-9]{1,4}" maxlength="4" required placeholder="Ex.: 05"><p class="muted">Use um número entre 1 e 9999, ainda não utilizado nesta filial.</p><p id="renumberPdvError" class="sync-error" role="alert"></p><div class="actions"><button type="button" id="renumberPdvCancel">Voltar ao cadastro</button><button id="renumberPdvSave" class="primary">Confirmar alteração</button></div></form>`);
 $('renumberPdvCancel').onclick=()=>openRolloutBase(data.branch.id);
 $('renumberPdvForm').onsubmit=async e=>{
  e.preventDefault();$('renumberPdvSave').disabled=true;
  try{
   await api('/api/rollout-base/branches/'+encodeURIComponent(data.branch.id)+'/pdv-number','PUT',{from_pdv:m.pdv,to_pdv:$('renumberPdvValue').value.trim(),plan_version:data.plan_version,inventory_version:m.version});
   if(typeof centralData!=='undefined'&&centralData?.branch.id===data.branch.id)centralData=null;
   if(selectedBranchId===data.branch.id){clearCurrentCutover();showBranchPdvs();await refreshList()}
   await openRolloutBase(data.branch.id);toast('Numeração alterada. Os registros do PDV foram preservados.');
   if(!$('rolloutBasePage').classList.contains('hidden'))await refreshRolloutBase(rolloutBasePage);
   else if(!$('dashboardPage').classList.contains('hidden'))await refreshDashboard();
  }catch(err){if($('renumberPdvError'))$('renumberPdvError').textContent=err.message;if($('renumberPdvSave'))$('renumberPdvSave').disabled=false}
 };
}
function rolloutGroupingTable(title,rows){return `<section class="panel"><div class="eyebrow">AVANÇO DAS LOJAS</div><h2>${title}</h2><div class="rollout-group-scroll report-table-wrap"><table class="branch-table"><thead><tr><th>${title==='Avanço por GR'?'GR':'Regional'}</th><th>Previstas</th><th>Atualizadas</th><th>Avanço</th></tr></thead><tbody>${rows.map(r=>`<tr><td><b>${esc(r.name)}</b><span>${r.pdvs_deployed} / ${r.pdvs_expected} PDVs implantados</span></td><td>${r.stores_expected}</td><td>${r.stores_updated}</td><td><b>${r.percent}%</b><div class="bar"><span style="width:${r.percent}%"></span></div></td></tr>`).join('')||'<tr><td colspan="4">Sem lojas neste recorte.</td></tr>'}</tbody></table></div></section>`}
let rolloutDashboardTab='overview';
function selectRolloutDashboardTab(name,focus=false){
 if(!['overview','groups','cutover'].includes(name))return;
 rolloutDashboardTab=name;
 document.querySelectorAll('[data-rollout-tab]').forEach(button=>{
  const active=button.dataset.rolloutTab===name;
  button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1;
  if(active&&focus)button.focus();
 });
 for(const key of ['overview','groups']){const panel=$('rolloutPanel-'+key);if(panel)panel.hidden=name!==key}
 const cutover=$('cutoverDashboardSection');if(cutover){cutover.hidden=name!=='cutover';if(name==='cutover')cutover.open=true}
}
function rolloutVersionBars(versions){
 return versions.map(v=>`<div class="rollout-version-row"><div><b>${esc(v.name)}</b><span>${v.count.toLocaleString('pt-BR')} · ${v.percent}%</span></div><div class="bar"><span style="width:${v.percent}%"></span></div></div>`).join('');
}
function renderRolloutBaseDashboard(data){
 const el=$('rolloutBaseDashboard'),b=data.rollout_base;if(!b){el.innerHTML='';return}
 const number=n=>n.toLocaleString('pt-BR'),versions=[...b.versions,...(b.deployed_without_version?[{name:'Não informada',count:b.deployed_without_version,percent:b.pdvs_deployed?Math.round(b.deployed_without_version/b.pdvs_deployed*1000)/10:0}]:[])];
 const executive=data.executive||{},totals=data.totals||{},gap=Math.max(0,b.pdvs_deployed-(totals.ok||0));
 const priority=executive.critical_issues?'Prioridade: resolver '+executive.critical_issues+' ocorrência(s) crítica(s).':executive.overdue_pdvs?'Prioridade: atuar em '+executive.overdue_pdvs+' PDV(s) com prazo vencido.':gap?'Próximo foco: validar os '+gap+' PDV(s) implantados sem Orion OK.':b.pdvs_pending?'Próximo foco: avançar a implantação dos PDVs pendentes.':'Parque implantado. Acompanhe os aceites e o suporte às lojas.';
 const regions=[...b.by_regional].sort((a,z)=>z.percent-a.percent||z.stores_expected-a.stores_expected).slice(0,5);
 el.innerHTML=`<div class="rollout-view-tabs" role="tablist" aria-label="Visões do dashboard">${[['overview','Resumo do rollout'],['groups','GR e regionais'],['cutover','Validação do cutover']].map(([id,label])=>`<button type="button" id="rolloutTab-${id}" role="tab" data-rollout-tab="${id}" aria-controls="${id==='cutover'?'cutoverDashboardSection':'rolloutPanel-'+id}" aria-selected="false" tabindex="-1">${label}</button>`).join('')}</div>
 <section id="rolloutPanel-overview" role="tabpanel" aria-labelledby="rolloutTab-overview">
 <div class="rollout-summary-line"><div><span class="eyebrow">BASE DE ROLLOUT</span><h2>Do planejamento à implantação</h2><p>${number(b.stores_expected)} lojas no escopo · ${number(b.stores_updated)} com implantação iniciada</p></div><button id="openRolloutBaseDashboard" class="primary">Gerenciar base →</button></div>
 <section class="executive-command"><div><span class="eyebrow">LEITURA EXECUTIVA</span><h2>${b.pdvs_percent}% implantado · ${totals.percent||0}% validado</h2><p>${esc(priority)}</p></div><div><strong>${number(gap)}</strong><small>implantados sem Orion OK</small></div></section>
 <div class="rollout-primary-stats">${[['PDVs previstos',b.pdvs_expected,'Equipamentos planejados','planned'],['PDVs implantados',b.pdvs_deployed,b.pdvs_percent+'% do parque previsto','deployed'],['PDVs pendentes',b.pdvs_pending,'Ainda sem implantação','pending'],['Lojas atualizadas',b.stores_updated,b.stores_percent+'% das '+number(b.stores_expected)+' lojas','stores']].map(([label,n,detail,key])=>`<article class="stat rollout-kpi rollout-kpi-${key}"><small>${label}</small><strong>${number(n)}</strong><small>${detail}</small></article>`).join('')}</div>
 <div class="rollout-overview-grid">
  <section class="panel rollout-coverage"><div class="rollout-panel-heading"><div><span class="eyebrow">EXECUÇÃO</span><h2>Avanço do parque</h2></div><span class="scope-tag">PDVs implantados</span></div><div class="rollout-coverage-body"><div class="rollout-donut" style="--rollout-progress:${b.pdvs_percent}%" role="img" aria-label="${b.pdvs_percent}% dos PDVs implantados"><div><strong>${b.pdvs_percent}%</strong><small>implantado</small></div></div><div class="rollout-coverage-legend"><p><i class="deployed"></i><span>Implantados</span><b>${number(b.pdvs_deployed)}</b></p><p><i class="pending"></i><span>Pendentes</span><b>${number(b.pdvs_pending)}</b></p><small>Implantação declarada na Base ou Orion OK. Cada filial + PDV conta uma vez.</small></div></div></section>
  <section class="panel"><div class="rollout-panel-heading"><div><span class="eyebrow">VERSÕES</span><h2>Parque instalado</h2></div><span class="scope-tag">${versions.length} versão(ões)</span></div>${versions.length?rolloutVersionBars(versions.slice(0,5))+(versions.length>5?`<details class="rollout-more"><summary>Ver outras ${versions.length-5} versões</summary>${rolloutVersionBars(versions.slice(5))}</details>`:''):'<p class="rollout-empty">As versões aparecerão após o registro da implantação.</p>'}<p class="rollout-note">${number(b.deployed_without_version)} PDV(s) implantado(s) sem versão informada.</p></section>
 </div>
 <section class="panel rollout-regional-overview"><div class="rollout-panel-heading"><div><span class="eyebrow">COBERTURA</span><h2>Avanço por regional</h2></div><button id="rolloutShowGroups">Ver GR e regionais →</button></div>${regions.length?`<div class="rollout-region-cards">${regions.map(r=>`<div><b>${esc(r.name)}</b><strong>${r.percent}%</strong><div class="bar"><span style="width:${r.percent}%"></span></div><small>${number(r.stores_updated)} de ${number(r.stores_expected)} lojas atualizadas</small></div>`).join('')}</div>`:'<p class="rollout-empty">Nenhuma loja no filtro selecionado.</p>'}<p class="rollout-note">Até 5 regionais, ordenadas pelo avanço. Loja atualizada = ao menos um PDV implantado.</p></section>
 <section class="panel central-dashboard-priorities"><div class="rollout-panel-heading"><div><span class="eyebrow">PRÓXIMAS AÇÕES</span><h2>Onde atuar agora</h2></div><span class="scope-tag">${executive.attention_total||0} lojas com atenção</span></div>${executive.attention?.length?`<div class="central-priority-cards">${executive.attention.slice(0,3).map((r,i)=>`<article><span class="central-priority-rank">0${i+1}</span><h3>${esc(r.code)} · ${esc(r.name)}</h3><p>PDVs ${esc(r.pdvs.join(', '))}</p><small>${r.critical} crítica(s) · ${r.overdue} atraso(s)</small><button type="button" data-central-priority="${i}">Atender na central →</button></article>`).join('')}</div>`:'<p class="rollout-note">Nenhum alerta de cronograma, ocorrência ou bloqueio identificado. Consulte a Base para planejar as próximas implantações.</p>'}</section>
 <details class="rollout-definitions"><summary>Critérios e qualidade do cadastro <span>${number(b.stores_missing_organization)} loja(s) sem GR e/ou regional</span></summary><p>Apenas filiais ativas, abertas e sem cadastro a revisar entram no resumo. GR e regional ausentes ficam no grupo Não informado. A implantação registrada na Base não conclui o checklist nem concede aceite. Lojas completas e Orion OK estão na visão Validação do cutover.</p></details>
 </section>
 <section id="rolloutPanel-groups" role="tabpanel" aria-labelledby="rolloutTab-groups" hidden><div class="rollout-summary-line"><div><span class="eyebrow">BASE DE ROLLOUT</span><h2>Avanço por GR e regional</h2><p>Lojas atualizadas / lojas previstas, respeitando os filtros acima.</p></div></div><div class="executive-grid">${rolloutGroupingTable('Avanço por GR',b.by_gr)}${rolloutGroupingTable('Avanço por regional',b.by_regional)}</div></section>`;
 el.querySelectorAll('[data-central-priority]').forEach(button=>button.onclick=()=>{const row=executive.attention[Number(button.dataset.centralPriority)];openCentralFromDashboard(row.branch_id,row.pdvs[0])});
 $('openRolloutBaseDashboard').onclick=showRolloutBase;$('rolloutShowGroups').onclick=()=>selectRolloutDashboardTab('groups',true);
 const tabs=[...el.querySelectorAll('[data-rollout-tab]')];
 tabs.forEach((button,index)=>{
  button.onclick=()=>selectRolloutDashboardTab(button.dataset.rolloutTab);
  button.onkeydown=e=>{let next;if(e.key==='ArrowRight')next=(index+1)%tabs.length;else if(e.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;else if(e.key==='Home')next=0;else if(e.key==='End')next=tabs.length-1;else return;e.preventDefault();selectRolloutDashboardTab(tabs[next].dataset.rolloutTab,true)};
 });
 selectRolloutDashboardTab(rolloutDashboardTab);
}
function initRolloutBase(){
 const button=document.createElement('button');button.id='rolloutBaseNav';button.textContent='Base de Rollout';button.onclick=showRolloutBase;document.querySelector('.nav').append(button);
 $('rolloutBaseNew').hidden=READONLY;$('rolloutBaseNew').onclick=chooseRolloutBranch;$('rolloutBaseRefresh').onclick=()=>refreshRolloutBase(rolloutBasePage);$('rolloutBaseSearch').oninput=()=>{clearTimeout(rolloutBaseTimer);rolloutBaseTimer=setTimeout(refreshRolloutBase,300)};for(const id of ['rolloutBaseRegional','rolloutBaseGr','rolloutBaseUf'])$(id).onchange=()=>refreshRolloutBase();
}
initRolloutBase();
