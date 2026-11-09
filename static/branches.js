let registeredBranches=[],switchingBranch=false,branchPage=1,branchSearchTimer=null;
const BRANCH_PAGE_SIZE=50;
function currentBranch(){return registeredBranches.find(b=>b.id===selectedBranchId)}
function showBranches(){
 if(typeof hideOperations==='function')hideOperations();
 $('usersPage').classList.add('hidden');$('usersNav')?.classList.remove('active');
 $('dashboardPage').classList.add('hidden');$('dashboardNav')?.classList.remove('active');
 $('reportsPage').classList.add('hidden');$('reportsNav')?.classList.remove('active');
 $('cutoverWorkspace').classList.add('hidden');$('branchesPage').classList.remove('hidden');
 document.querySelectorAll('[data-view]').forEach(b=>b.classList.remove('active'));$('branchesNav').classList.add('active');branchPage=1;
 refreshBranches().catch(e=>toast(e.message));
}
function showCutoverWorkspace(){
 if(!registeredBranches.length)ensureBranches().catch(e=>toast(e.message));
 if(typeof updateGuidedChecklist==='function')updateGuidedChecklist();
 if(typeof hideOperations==='function')hideOperations();
 $('usersPage').classList.add('hidden');$('usersNav')?.classList.remove('active');
 $('dashboardPage').classList.add('hidden');$('dashboardNav')?.classList.remove('active');
 $('reportsPage').classList.add('hidden');$('reportsNav')?.classList.remove('active');
 $('cutoverWorkspace').classList.remove('hidden');$('branchesPage').classList.add('hidden');$('branchesNav').classList.remove('active');
}
async function refreshBranches(){
 registeredBranches=await api('/api/branches');
 syncBranchPicker();
 renderBranchRegistry();branchPermissions();
}
let branchOptionIndex=-1;
function branchLabel(branch){return branch?branch.code+' · '+branch.name+(branch.opening_soon?' (a inaugurar)':branch.active?'':' (inativa)'):''}
function closeBranchPicker(){
 $('branchOptions').hidden=true;$('branchPicker').setAttribute('aria-expanded','false');$('branchPicker').removeAttribute('aria-activedescendant');branchOptionIndex=-1;
}
function syncBranchPicker(){
 $('selectedBranch').value=selectedBranchId;$('branchPicker').value=branchLabel(currentBranch());closeBranchPicker();$('branchPickerHint').textContent='';
}
function renderBranchOptions(query=''){
 const normalize=text=>String(text||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');
 const q=normalize(query.trim());
 const matches=registeredBranches.filter(b=>normalize(b.code+' '+b.name+' '+b.city+' '+b.uf).includes(q));
 $('branchOptions').innerHTML=matches.length?matches.slice(0,100).map((b,i)=>`<button type="button" id="branch-option-${i}" role="option" tabindex="-1" aria-selected="${b.id===selectedBranchId}" data-pick-branch="${esc(b.id)}"><strong>${esc(b.code)}</strong><span>${esc(b.name)}</span><small>${esc(b.opening_soon?'A inaugurar':b.active?'Ativa':'Inativa')}</small></button>`).join(''):'<div class="branch-option-empty">Nenhuma filial encontrada.</div>';
 $('branchPickerHint').textContent=matches.length+' filial(is) encontrada(s).'+(matches.length>100?' Digite para refinar os primeiros 100 resultados.':'');
 branchOptionIndex=-1;$('branchPicker').removeAttribute('aria-activedescendant');
 document.querySelectorAll('[data-pick-branch]').forEach(button=>{
  button.onmousedown=e=>e.preventDefault();
  button.onclick=async()=>{await switchBranch(button.dataset.pickBranch);syncBranchPicker()};
 });
}
function openBranchPicker(query=''){
 renderBranchOptions(query);$('branchOptions').hidden=false;$('branchPicker').setAttribute('aria-expanded','true');
}
function initBranchPicker(){
 const input=$('branchPicker');
 input.onfocus=()=>{input.select();openBranchPicker()};input.onclick=()=>{if($('branchOptions').hidden)openBranchPicker()};input.oninput=()=>openBranchPicker(input.value);
 input.onkeydown=e=>{
  if(e.key==='Escape'){syncBranchPicker();return}
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){
   e.preventDefault();if($('branchOptions').hidden)openBranchPicker();
   const options=[...document.querySelectorAll('[data-pick-branch]')];if(!options.length)return;
   branchOptionIndex=branchOptionIndex<0?(e.key==='ArrowDown'?0:options.length-1):(branchOptionIndex+(e.key==='ArrowDown'?1:options.length-1))%options.length;
   options.forEach((b,i)=>b.classList.toggle('keyboard-focus',i===branchOptionIndex));
   input.setAttribute('aria-activedescendant',options[branchOptionIndex].id);options[branchOptionIndex].scrollIntoView?.({block:'nearest'});
  }else if(e.key==='Enter'&&!$('branchOptions').hidden){
   e.preventDefault();const options=[...document.querySelectorAll('[data-pick-branch]')];
   if(branchOptionIndex>=0)options[branchOptionIndex]?.click();else if(options.length===1)options[0].click();
  }
 };
 input.onblur=()=>syncBranchPicker();
 document.addEventListener('mousedown',e=>{if(!e.target.closest('.branch-combobox'))syncBranchPicker()});
 syncBranchPicker();
}
function renderBranchRegistry(){
 const q=$('branchSearch').value.toLocaleLowerCase('pt-BR');
 const rows=registeredBranches.filter(b=>(b.code+' '+b.name+' '+b.city+' '+b.uf+' '+(b.opening_soon?'A inaugurar':b.active?'Ativa':'Inativa')).toLocaleLowerCase('pt-BR').includes(q));
 const pages=Math.max(1,Math.ceil(rows.length/BRANCH_PAGE_SIZE));branchPage=Math.min(Math.max(1,branchPage),pages);const start=(branchPage-1)*BRANCH_PAGE_SIZE,paged=rows.slice(start,start+BRANCH_PAGE_SIZE);
 $('branchTotals').textContent=registeredBranches.length+' filiais cadastradas · '+registeredBranches.filter(b=>b.active&&!b.opening_soon).length+' ativas · '+registeredBranches.filter(b=>b.opening_soon).length+' a inaugurar · '+rows.length+' encontrada(s) na pesquisa';
 $('branchRegistry').innerHTML=rows.length?`<div class="panel branch-table-wrap"><table class="branch-table"><thead><tr><th>Filial</th><th>Cidade / UF</th><th>Cutovers</th><th>Situação</th><th></th></tr></thead><tbody>${paged.map(b=>`<tr><td><b>${esc(b.code)}</b><span>${esc(b.name)}</span></td><td>${esc([b.city,b.uf].filter(Boolean).join(' / '))||'Não informado'}</td><td>${b.cutover_count}</td><td><span class="badge ${b.needs_review?'blocked':b.active?'done':''}">${b.needs_review?'Revisar filial':b.opening_soon?'A inaugurar':b.active?'Ativa':'Inativa'}</span></td><td><div class="actions"><button data-open-branch="${esc(b.id)}">Abrir cutovers</button>${DECIDE?`<button data-edit-branch="${esc(b.id)}">Editar</button>`:''}${document.body.dataset.role==='admin'?`<button class="danger" data-delete-branch="${esc(b.id)}">Excluir</button>`:''}</div></td></tr>`).join('')}</tbody></table></div>`:'<div class="panel empty">Nenhuma filial encontrada.'+(DECIDE?' Clique em Cadastrar filial para começar.':'')+'</div>';
 if(rows.length){$('branchRegistry').insertAdjacentHTML('beforeend',`<div class="branch-pagination"><span>${start+1} a ${Math.min(start+BRANCH_PAGE_SIZE,rows.length)} de ${rows.length} filiais</span><div class="actions"><button id="previousBranches" ${branchPage===1?'disabled':''}>Anterior</button><span>Página ${branchPage} de ${pages}</span><button id="nextBranches" ${branchPage===pages?'disabled':''}>Próxima</button></div></div>`);$('previousBranches').onclick=()=>{branchPage--;renderBranchRegistry()};$('nextBranches').onclick=()=>{branchPage++;renderBranchRegistry()}}
 document.querySelectorAll('[data-open-branch]').forEach(b=>b.onclick=async()=>{await switchBranch(b.dataset.openBranch);document.querySelector('[data-view="run"]').click()});
 document.querySelectorAll('[data-delete-branch]').forEach(b=>b.onclick=()=>deleteBranch(b.dataset.deleteBranch));
 document.querySelectorAll('[data-edit-branch]').forEach(b=>b.onclick=()=>branchForm(registeredBranches.find(x=>x.id===b.dataset.editBranch)));
}
async function deleteBranch(id){
 const branch=registeredBranches.find(b=>b.id===id);if(!branch)return;
 modal(`<h2>Excluir filial</h2><p>Confirma excluir <b>${esc(branch.code+' · '+branch.name)}</b>?</p><p class="muted">Filiais com cutovers vinculados devem ser inativadas para manter o histórico.</p><p id="deleteBranchError" role="alert" class="sync-error"></p><div class="actions"><button id="cancelBranchDelete">Cancelar</button><button class="danger" id="confirmBranchDelete">Excluir filial</button></div>`);
 $('cancelBranchDelete').onclick=()=>$('modal').close();
 $('confirmBranchDelete').onclick=async()=>{const button=$('confirmBranchDelete');button.disabled=true;try{await api('/api/branches/'+id,'DELETE');$('modal').close();if(selectedBranchId===id)await switchBranch('');await refreshBranches();toast('Filial excluída.')}catch(e){$('deleteBranchError').textContent=e.message;button.disabled=false}};
}
function branchPermissions(){
 if($('cutoverEditor'))$('cutoverEditor').classList.toggle('hidden',!currentId||!cutoverEditing);
 const branch=currentBranch();$('branchIdentity').textContent=branch?branch.code+' · '+branch.name:'Escolha uma loja para visualizar os cutovers.';
 $('newExecution').disabled=!branch||!branch.active||!!branch.needs_review||!DECIDE;
 $('addBranch').hidden=!DECIDE;
 $('addStorePdv').hidden=!DECIDE||!branch;
 $('addStorePdv').disabled=!branch||!!branch.needs_review;
 $('branch').readOnly=true;
 if($('linkLegacy'))$('linkLegacy').remove();
 if(branch?.needs_review&&DECIDE){const button=document.createElement('button');button.id='linkLegacy';button.textContent='Vincular execução à filial correta';button.onclick=resolveLegacy;$('branchIdentity').append(document.createElement('br'),button)}
}
async function switchBranch(id){
 if(!registeredBranches.length)await ensureBranches();
 if(switchingBranch)return false;
 if(id===selectedBranchId){syncBranchPicker();return true}
 if(!allowDiscard()){syncBranchPicker();return false}
 switchingBranch=true;$('branchPicker').disabled=true;closeBranchPicker();
 try{
  selectedBranchId=id;syncBranchPicker();currentRejection=null;currentId=null;cutoverEditing=false;branchProgress=null;version=0;dirty=false;conflict=false;clearTimeout(timer);
  state={meta:{},tasks:{},decisions:{linx:{},orion:{}}};$('saveFeedback').hidden=true;$('selectedBranch').value=id;render();renderBranchProgress();
  const rows=await refreshList();
  $('execution').value='';syncText(id?'Selecione um PDV abaixo para abrir, editar ou iniciar o checklist.':'Selecione uma filial cadastrada.');
  branchPermissions();return true;
 }catch(e){syncText(e.message,true);return false}finally{switchingBranch=false;$('branchPicker').disabled=false;syncBranchPicker()}
}
function branchForm(existing=null){
 modal(`<h2>${existing?'Editar filial':'Cadastrar filial'}</h2><p class="muted">Código e nome identificam a loja. Cidade e UF são opcionais.</p><form id="branchForm" class="form-stack"><label for="branchCode">Código da filial *</label><input id="branchCode" placeholder="VD266" maxlength="30" value="${esc(existing?.code)}" ${existing?'readonly':''} required><label for="branchName">Nome da loja *</label><input id="branchName" placeholder="Shopping Vila Lobos" maxlength="160" value="${esc(existing?.name)}" required><div class="row2"><div><label for="branchCity">Cidade</label><input id="branchCity" maxlength="100" value="${esc(existing?.city)}"></div><div><label for="branchUf">UF</label><select id="branchUf"><option value="">Não informada</option>${['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'].map(uf=>`<option ${existing?.uf===uf?'selected':''}>${uf}</option>`).join('')}</select></div></div><label for="branchActive">Situação</label><select id="branchActive"><option value="Ativa" ${!existing||existing.active&&!existing.opening_soon?'selected':''}>Ativa</option><option value="A inaugurar" ${existing?.opening_soon?'selected':''}>A inaugurar</option><option value="Inativa" ${existing&&!existing.active?'selected':''}>Inativa - mantém o histórico</option></select><p id="branchError" role="alert" class="sync-error"></p><button class="primary" id="saveBranch">Salvar filial</button></form>`);
 $('branchForm').onsubmit=async e=>{e.preventDefault();$('saveBranch').disabled=true;const body={code:$('branchCode').value.trim().toUpperCase(),name:$('branchName').value.trim(),city:$('branchCity').value.trim(),uf:$('branchUf').value,status:$('branchActive').value};try{const result=await api('/api/branches'+(existing?'/'+existing.id:''),existing?'PUT':'POST',body);$('modal').close();await refreshBranches();if(typeof centralOnBranchSaved==='function')await centralOnBranchSaved(result.id||existing?.id);toast('Filial salva. Cadastro disponível na Central de Cutover.')}catch(err){$('branchError').textContent=err.message;$('saveBranch').disabled=false}};
}
function startBoundCutover(pdv=''){
 if(typeof pdv!=='string')pdv='';
 const b=currentBranch();if(!b||!DECIDE||!b.active||b.needs_review)return;
 if(dirty||saving){toast('Salve o checklist antes de iniciar outra execução.');return}
 modal(`<h2>Iniciar cutover</h2><div class="bound-store"><b>${esc(b.code)}</b><span>${esc(b.name)}</span></div><p class="muted">Esta execução ficará vinculada somente à loja acima.</p><form id="boundCutoverForm" class="form-stack"><label for="boundPdv">PDV que será atendido *</label><input id="boundPdv" value="${esc(pdv)}" placeholder="Ex.: 01" maxlength="40" required><p id="startCutoverError" role="alert" class="sync-error"></p><button class="primary" id="startBoundButton">Iniciar cutover desta filial</button></form>`);
 $('boundCutoverForm').onsubmit=async e=>{e.preventDefault();$('startBoundButton').disabled=true;try{const entered=$('boundPdv').value.trim(),normalized=String(Number(entered.replace(/^PDV[\s_-]*/i,''))).padStart(2,'0');const existing=branchProgress?.machines.find(m=>m.pdv===normalized&&m.execution)?.execution;if(existing){if(await loadExecution(existing.id)){$('modal').close();$('context').scrollIntoView?.({behavior:'smooth',block:'start'})}else $('startBoundButton').disabled=false;return}const r=await api('/api/cutovers','POST',{branch_id:b.id,pdv:entered});await refreshList(r.id);await loadExecution(r.id);$('modal').close();await refreshBranches();toast('Cutover iniciado para '+b.code+'.')}catch(err){$('startCutoverError').textContent=err.message;$('startBoundButton').disabled=false}};
}
function resolveLegacy(){
 if(!currentId){toast('Selecione a execução anterior para vincular.');return}
 modal(`<h2>Confirmar filial da execução anterior</h2><p>Os processos e observações serão mantidos. Este ajuste é permitido apenas para registros antigos sem uma filial identificada.</p><form id="legacyForm" class="form-stack"><label for="targetBranch">Filial correta</label><select id="targetBranch" required><option value="">Selecione</option>${registeredBranches.filter(b=>b.active&&!b.needs_review).map(b=>`<option value="${b.id}">${esc(b.code+' · '+b.name)}</option>`).join('')}</select><label for="legacyPdv">PDV (opcional)</label><input id="legacyPdv" maxlength="40"><p id="legacyError" role="alert" class="sync-error"></p><button class="primary">Confirmar vínculo</button></form>`);
 $('legacyForm').onsubmit=async e=>{e.preventDefault();if(dirty||saving){$('legacyError').textContent='Salve o checklist antes de alterar o vínculo.';return;}try{const r=await api('/api/cutovers/'+currentId+'/branch','PUT',{branch_id:$('targetBranch').value,pdv:$('legacyPdv').value.trim(),version});$('modal').close();await refreshBranches();await switchBranch(r.branch_id)}catch(err){$('legacyError').textContent=err.message}};
}
function initBranches(){
 document.querySelector('main').append($('modal'));
 const nav=document.createElement('button');nav.id='branchesNav';nav.textContent='▦ Filiais';nav.onclick=showBranches;document.querySelector('.nav').prepend(nav);
 document.querySelectorAll('[data-view]').forEach(b=>{const prior=b.onclick;b.onclick=()=>{showCutoverWorkspace();prior()}});
 $('addStorePdv').onclick=()=>editBranchPdvPlan(selectedBranchId);
 $('manageBranches').onclick=showBranches;$('addBranch').onclick=()=>branchForm();$('branchSearch').oninput=()=>{branchPage=1;clearTimeout(branchSearchTimer);branchSearchTimer=setTimeout(renderBranchRegistry,150)};
 initBranchPicker();
 $('selectedBranch').onchange=()=>switchBranch($('selectedBranch').value);
 $('execution').onchange=async()=>{
  const id=$('execution').value;if(id){await loadExecution(id);return}
  if(!allowDiscard()){$('execution').value=currentId||'';return}
  dirty=false;conflict=false;
  currentId=null;currentRejection=null;version=0;state={meta:{},tasks:{},decisions:{linx:{},orion:{}}};render();syncText('Selecione ou inicie um cutover desta filial.');
 };
 $('newExecution').textContent='▶ Iniciar cutover';$('newExecution').onclick=startBoundCutover;
 const priorRender=render;render=function(){priorRender();branchPermissions()};render();
 // Registry and execution lists are loaded when the user opens Cutover or Filiais.
}

let branchesLoading=null;
async function ensureBranches(){if(registeredBranches.length)return registeredBranches;if(branchesLoading)return branchesLoading;$('branchPicker').disabled=true;branchesLoading=refreshBranches().then(()=>{if(!selectedBranchId)syncText('Selecione uma filial cadastrada para começar.');return refreshList()}).finally(()=>{branchesLoading=null;$('branchPicker').disabled=false});await branchesLoading;return registeredBranches}
