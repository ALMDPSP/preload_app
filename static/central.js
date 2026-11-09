/* Central workspace: saved base and checklist share a screen, never an implicit write. */
let centralData=null,centralSaved=null,centralPdv='',centralDirty=false,centralSaving=false,centralLoading=null,centralSequence=0;
const centralClone=v=>JSON.parse(JSON.stringify(v));
function centralMachine(){return centralData?.machines.find(m=>m.pdv===centralPdv)}
function centralPending(){return centralDirty||centralSaving}
function centralSyncBadge(){
 const badge=$('centralSaveState');if(badge){badge.textContent=centralSaving?'Salvando cadastro…':centralDirty?'Cadastro não salvo':'Cadastro salvo';badge.classList.toggle('unsaved',centralDirty)}
}
function centralIdentityGuard(){
 if(saving||centralSaving||executionLoading){toast('Aguarde a operação em andamento terminar.');return false}
 if(dirty||centralDirty){toast('Salve o cadastro e o checklist em edição antes de alterar a identificação do PDV.');return false}
 return true;
}
async function loadCentralBase(force=false){
 const id=selectedBranchId;if(!id){centralData=null;centralSaved=null;centralPdv='';renderCentral();return}
 if(centralDirty||centralSaving)return;
 if(!force&&centralData?.branch.id===id){renderCentral();return}
 if(centralLoading?.id===id)return centralLoading.promise;
 const sequence=++centralSequence;
 $('centralFormHost').innerHTML='<p class="muted">Carregando cadastro da filial…</p>';
 const promise=(async()=>{
  try{const data=await api('/api/rollout-base/branches/'+encodeURIComponent(id));
   if(sequence!==centralSequence||selectedBranchId!==id)return;
   centralData=centralClone(data);centralSaved=centralClone(data);
   if(!data.machines.some(m=>m.pdv===centralPdv))centralPdv=data.machines[0]?.pdv||'';
   renderCentral();
  }catch(e){if(selectedBranchId===id){$('centralFormHost').innerHTML='<p class="sync-error">'+esc(e.message)+'</p><button id="centralRetry">Tentar novamente</button>';$('centralRetry').onclick=()=>loadCentralBase(true)}}
  finally{if(centralLoading?.promise===promise)centralLoading=null}
 })();centralLoading={id,promise};return promise;
}
function renderCentral(){
 const host=$('centralFormHost');if(!host)return;
 const branch=currentBranch(),data=centralData;
 $('centralWorkspace').hidden=!branch;
 if(!branch){host.innerHTML='';return}
 $('centralBranchLabel').textContent=branch.code+' · '+branch.name;
 $('centralEditBranch').hidden=!DECIDE;$('centralAddPdv').hidden=!DECIDE;
 if(!data||data.branch.id!==selectedBranchId){host.innerHTML='<p class="muted">Selecione um PDV para carregar o cadastro.</p>';return}
 if(cutoverEditing&&state.meta.branch_id===selectedBranchId&&data.machines.some(m=>Number(m.pdv)===Number(state.meta.pdv)))centralPdv=data.machines.find(m=>Number(m.pdv)===Number(state.meta.pdv)).pdv;
 const m=centralMachine(),latest=branchProgress?.machines.find(m=>m.pdv===centralPdv)?.execution;
 const execution=cutoverEditing&&Number(state.meta.pdv)===Number(centralPdv)?branchProgress?.executions.find(r=>r.id===currentId)||latest:latest;
 if(!m){host.innerHTML='<div class="notice"><b>PDV '+esc(centralPdv)+' fora da lista prevista</b><p>O checklist continua disponível abaixo. Para cadastrar a implantação ou alterar o número, inclua este PDV no plano da filial pelo botão Adicionar PDV.</p></div>';highlightCentralPdv();return}
 const disabled=READONLY||centralSaving?'disabled':'';
 const recordOpen=$('centralRecord')?.open;
 host.innerHTML=`<details class="central-record" id="centralRecord" ${centralDirty||recordOpen?'open':''}><summary><div><b>Cadastro da filial e do PDV ${esc(centralPdv)}</b><span>${esc(data.regional||'Regional não informada')} · ${esc(data.gr||'GR não informado')}</span></div><span id="centralSaveState"></span></summary><form id="centralBaseForm"><div class="central-fields"><div><label for="centralGr">GR</label><input id="centralGr" data-central-org="gr" maxlength="120" value="${esc(data.gr)}" ${!DECIDE?'readonly':''} ${disabled}></div><div><label for="centralRegional">Regional</label><input id="centralRegional" data-central-org="regional" maxlength="120" value="${esc(data.regional)}" ${!DECIDE?'readonly':''} ${disabled}></div><div><label for="centralStatus">Implantação declarada</label><select id="centralStatus" data-central-machine="status" ${disabled}><option ${m?.status==='Pendente'?'selected':''}>Pendente</option><option ${m?.status==='Implantado'?'selected':''}>Implantado</option></select></div><div><label for="centralVersion">Versão instalada</label><input id="centralVersion" data-central-machine="installed_version" maxlength="80" value="${esc(m?.installed_version)}" ${disabled}></div><div><label for="centralDate">Data da implantação</label><input id="centralDate" data-central-machine="deployed_at" type="date" value="${esc(m?.deployed_at)}" ${disabled}></div><div><label for="centralNotes">Observações do cadastro (opcional)</label><input id="centralNotes" data-central-machine="notes" maxlength="2000" value="${esc(m?.notes)}" ${disabled}></div></div><div class="central-record-footer"><small>Implantação declarada não concede GO. Este botão salva o cadastro; o checklist tem seu próprio botão.</small>${!READONLY?'<button type="submit" class="primary" id="centralSaveBase">Salvar cadastro</button>':''}<button type="button" id="centralReloadBase">Recarregar cadastro</button></div><p id="centralBaseError" class="sync-error" role="alert"></p></form></details>
 <div class="central-pdv-heading"><div><span class="eyebrow">PDV SELECIONADO</span><h2>PDV ${esc(centralPdv)} <span class="badge">${esc(execution?.status||'Não iniciado')}</span></h2></div><div class="actions">${DECIDE?'<button id="centralRenameToggle" type="button">Editar número do PDV</button>':''}${execution?'<button id="centralGoLinx" type="button">GO da retirada</button><button id="centralGoOrion" type="button">Aceite Orion</button>':''}</div></div>
 <div id="centralRenameBox" class="central-rename" hidden><label for="centralNewNumber">Novo número do PDV ${esc(centralPdv)}</label><div class="actions"><input id="centralNewNumber" inputmode="numeric" maxlength="4" placeholder="Ex.: 05"><button id="centralRenameConfirm" class="primary" type="button">Confirmar número</button><button id="centralRenameCancel" type="button">Cancelar</button></div><p class="muted">Usar um número livre de 1 a 9999. Os registros e o histórico acompanham a alteração.</p><p id="centralRenameError" class="sync-error" role="alert"></p></div>
 ${!execution?`<div class="central-start"><div><b>Este PDV ainda não tem checklist.</b><p>${DECIDE?'Inicie a execução para marcar os processos e registrar os aceites nesta tela.':'Solicite a abertura da execução ao Administrador ou Gestor.'}</p></div>${DECIDE?`<button id="centralStartPdv" type="button" class="primary" ${!branch.active||branch.needs_review?'disabled':''}>Iniciar PDV ${esc(centralPdv)}</button>`:''}</div>`:!cutoverEditing?'<button id="centralResumePdv" class="primary" type="button">Abrir checklist deste PDV</button>':''}`;
 document.querySelectorAll('[data-central-org],[data-central-machine]').forEach(input=>{
  const update=()=>{if(READONLY)return;if(input.dataset.centralOrg)data[input.dataset.centralOrg]=input.value;else if(m)m[input.dataset.centralMachine]=input.value;centralDirty=true;centralSyncBadge()};
  input.addEventListener('input',update);input.addEventListener('change',update);
 });
 if($('centralBaseForm'))$('centralBaseForm').onsubmit=saveCentralBase;
 $('centralReloadBase').onclick=async()=>{if(centralSaving)return;if(centralDirty&&!confirm('Descartar as alterações do cadastro e recarregar? O checklist em edição será mantido.'))return;centralDirty=false;centralData=null;await loadCentralBase(true)};
 if($('centralSaveBase'))$('centralSaveBase').disabled=centralSaving;
 if($('centralStartPdv'))$('centralStartPdv').onclick=startCentralPdv;
 if($('centralResumePdv'))$('centralResumePdv').onclick=()=>openCentralPdv(centralPdv);
 if($('centralGoLinx'))$('centralGoLinx').onclick=()=>centralGoDecision('linx');
 if($('centralGoOrion'))$('centralGoOrion').onclick=()=>centralGoDecision('orion');
 if($('centralRenameToggle'))$('centralRenameToggle').onclick=()=>{$('centralRenameBox').hidden=false;$('centralNewNumber').focus()};
 $('centralRenameCancel').onclick=()=>{$('centralRenameBox').hidden=true};
 $('centralRenameConfirm').onclick=renameCentralPdv;
 centralSyncBadge();highlightCentralPdv();
}
function highlightCentralPdv(){
 document.querySelectorAll('#branchProgress [data-resume-pdv]').forEach(button=>{
  const m=branchProgress?.machines[Number(button.dataset.resumePdv)];if(!m)return;
  button.disabled=false;button.textContent='Selecionar PDV '+m.pdv;button.setAttribute('aria-pressed',String(m.pdv===centralPdv));
  button.closest('article').classList.toggle('pdv-selected',m.pdv===centralPdv);
  button.onclick=()=>openCentralPdv(m.pdv);
 });
}
async function saveCentralBase(event){
 event?.preventDefault();if(READONLY||centralSaving||!centralData)return;
 const data=centralData,m=centralMachine(),id=selectedBranchId;if(!m)return;
 centralSaving=true;centralSyncBadge();$('centralSaveBase').disabled=true;$('centralBaseForm').querySelectorAll('input,select').forEach(e=>e.disabled=true);
 try{
  await api('/api/rollout-base/branches/'+encodeURIComponent(id),'PUT',{regional:data.regional,gr:data.gr,version:data.version,plan_version:data.plan_version,machines:[m]});
  centralDirty=false;centralSaving=false;centralData=null;
  await loadCentralBase(true);toast('Cadastro salvo. O checklist continua sendo salvo pelo botão Salvar checklist.');
 }catch(e){$('centralBaseError').textContent=e.message;centralSaving=false;centralSyncBadge();$('centralSaveBase').disabled=false;$('centralBaseForm').querySelectorAll('input,select').forEach(e=>e.disabled=READONLY)}
}
async function openCentralPdv(pdv){
 const machine=branchProgress?.machines.find(m=>m.pdv===pdv);if(!machine){toast('Este PDV não está no plano atual. Confira a lista de equipamentos da filial.');return false}
 if(machine.execution){
  if(!await loadExecution(machine.execution.id))return false;
  centralPdv=pdv;renderCentral();$('centralFormHost').scrollIntoView?.({behavior:'smooth',block:'start'});return true;
 }
 if(!allowDiscard())return false;
 dirty=false;clearCurrentCutover();showBranchPdvs();centralPdv=pdv;renderCentral();return true;
}
async function startCentralPdv(){
 const b=currentBranch();if(!b||!DECIDE||!centralIdentityGuard())return;
 const existing=branchProgress?.machines.find(m=>m.pdv===centralPdv)?.execution;
 if(existing){await openCentralPdv(centralPdv);return}
 const pdv=centralPdv;const button=$('centralStartPdv');button.disabled=true;
 try{const r=await api('/api/cutovers','POST',{branch_id:b.id,pdv});await refreshList(r.id);await loadExecution(r.id);renderCentral();toast('PDV '+pdv+' iniciado. Marque os processos e use Salvar checklist.')}catch(e){toast(e.message);if($('centralStartPdv'))$('centralStartPdv').disabled=false}
}
async function renameCentralPdv(){
 if(!centralIdentityGuard())return;
 const m=centralMachine(),id=selectedBranchId,number=$('centralNewNumber').value.trim();
 if(!/^[0-9]{1,4}$/.test(number)||Number(number)<1||Number(number)>9999){$('centralRenameError').textContent='Informe um número de 1 a 9999.';return}
 const savedId=cutoverEditing&&Number(state.meta.pdv)===Number(m.pdv)?currentId:null;
 $('centralRenameConfirm').disabled=true;
 try{
  const r=await api('/api/rollout-base/branches/'+encodeURIComponent(id)+'/pdv-number','PUT',{from_pdv:m.pdv,to_pdv:number,plan_version:centralData.plan_version,inventory_version:m.version});
  centralPdv=r.pdv;centralData=null;clearCurrentCutover();showBranchPdvs();await loadCentralBase(true);await refreshList();
  if(savedId)await loadExecution(savedId);renderCentral();toast('Número atualizado com os registros e o histórico preservados.');
 }catch(e){if($('centralRenameError'))$('centralRenameError').textContent=e.message;if($('centralRenameConfirm'))$('centralRenameConfirm').disabled=false}
}
async function centralGoDecision(key){
 if(!cutoverEditing){if(!await openCentralPdv(centralPdv))return}
 $('search').value='';$('filter').value='all';applyFilter();
 const el=$(key+'-decision');if(el){el.scrollIntoView?.({behavior:'smooth',block:'center'});el.focus({preventScroll:true})}
}
async function openCentralFromDashboard(id,pdv=null){
 if(!allowDiscard())return false;dirty=false;
 if(!await switchBranch(id))return false;
 $('modal').close();document.querySelector('[data-view="run"]').click();
 if(pdv)await openCentralPdv(String(Number(pdv)).padStart(2,'0'));else showBranchPdvs();
 renderCentral();return true;
}
async function centralOnBranchSaved(id){
 if(!$('cutoverWorkspace').classList.contains('hidden')&&id){await switchBranch(id);await loadCentralBase(true)}
}
function initCentral(){
 const workspace=$('cutoverWorkspace'),selection=$('cutoverSelection'),editor=$('cutoverEditor');
 const layout=document.createElement('div');layout.id='centralWorkspace';layout.className='central-layout';layout.hidden=true;
 layout.innerHTML='<section class="central-pdv-rail" aria-label="PDVs da filial"><div class="central-rail-heading"><span class="eyebrow">EQUIPAMENTOS DA FILIAL</span><button type="button" id="centralAddPdv">+ Adicionar PDV</button></div></section><div class="central-main"><div class="central-branch-summary"><strong id="centralBranchLabel"></strong><button type="button" id="centralEditBranch">Editar filial</button></div><div id="centralFormHost"></div></div>';
 selection.after(layout);layout.querySelector('.central-pdv-rail').append($('branchProgress'));layout.querySelector('.central-main').append(editor);
 $('centralEditBranch').onclick=()=>{if(centralIdentityGuard())branchForm(currentBranch())};
 $('centralAddPdv').onclick=()=>editBranchPdvPlan(selectedBranchId);
 const oldPlan=editBranchPdvPlan;
 editBranchPdvPlan=async function(id){
  if(!centralIdentityGuard())return;
  await oldPlan(id);
  const form=$('pdvPlanForm');if(!form)return;const submit=form.onsubmit;
  form.onsubmit=async e=>{await submit(e);if(!$('modal').open&&selectedBranchId===id){centralData=null;await refreshList();await loadCentralBase()}};
 };
 allowDiscard=function(){
  if(saving||centralSaving){toast('Aguarde o salvamento terminar.');return false}
  if(!dirty&&!centralDirty)return true;
  if(!confirm('Há alterações não salvas no cadastro ou checklist. Cancele para salvar antes de trocar. Deseja descartar e continuar?'))return false;
  if(centralDirty){centralDirty=false;centralData=centralClone(centralSaved);renderCentral()}
  return true;
 };
 const oldRefresh=refreshList;refreshList=async function(...args){const result=await oldRefresh(...args);await loadCentralBase();return result};
 const oldProgress=renderBranchProgress;renderBranchProgress=function(){oldProgress();highlightCentralPdv();if(!centralDirty)renderCentral()};
 const oldRender=render;render=function(){oldRender();if(!centralDirty)renderCentral()};
 const oldSave=saveAndOfferPdf;saveAndOfferPdf=async function(...args){if(centralPending()){toast('Salve o cadastro acima antes de salvar o checklist.');return}return oldSave(...args)};
 window.addEventListener('beforeunload',e=>{if(centralPending()){e.preventDefault();e.returnValue=''}});
 if($('dashboardExecutivePdf'))$('dashboardExecutivePdf').onclick=()=>downloadRolloutExecutivePdf($('dashboardExecutivePdf'));
 $('centralNewBranch').hidden=!DECIDE;$('centralNewBranch').onclick=()=>{if(centralIdentityGuard())branchForm()};
 const runNav=document.querySelector('[data-view="run"]');runNav.title='Central de Cutover';runNav.setAttribute('aria-label','Central de Cutover');const label=runNav.querySelector('.nav-label');if(label)label.textContent='Central de Cutover';
 $('acceptanceNav').hidden=true;
 renderCentral();
}
initCentral();
