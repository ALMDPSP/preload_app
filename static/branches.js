let registeredBranches=[],switchingBranch=false,branchPage=1,branchSearchTimer=null;
const BRANCH_PAGE_SIZE=50;
function currentBranch(){return registeredBranches.find(b=>b.id===selectedBranchId)}
function showBranches(){
 $('cutoverWorkspace').classList.add('hidden');$('branchesPage').classList.remove('hidden');
 document.querySelectorAll('[data-view]').forEach(b=>b.classList.remove('active'));$('branchesNav').classList.add('active');branchPage=1;
 refreshBranches().catch(e=>toast(e.message));
}
function showCutoverWorkspace(){
 $('cutoverWorkspace').classList.remove('hidden');$('branchesPage').classList.add('hidden');$('branchesNav').classList.remove('active');
}
async function refreshBranches(){
 registeredBranches=await api('/api/branches');
 $('selectedBranch').innerHTML='<option value="">Selecione uma filial cadastrada</option>'+registeredBranches.map(b=>`<option value="${esc(b.id)}">${esc(b.code)} · ${esc(b.name)}${b.active?'':' (inativa)'}${b.needs_review?' (revisar vínculo)':''}</option>`).join('');
 $('selectedBranch').value=selectedBranchId;
 renderBranchRegistry();branchPermissions();
}
function renderBranchRegistry(){
 const q=$('branchSearch').value.toLocaleLowerCase('pt-BR');
 const rows=registeredBranches.filter(b=>(b.code+' '+b.name+' '+b.city+' '+b.uf).toLocaleLowerCase('pt-BR').includes(q));
 const pages=Math.max(1,Math.ceil(rows.length/BRANCH_PAGE_SIZE));branchPage=Math.min(Math.max(1,branchPage),pages);const start=(branchPage-1)*BRANCH_PAGE_SIZE,paged=rows.slice(start,start+BRANCH_PAGE_SIZE);
 $('branchTotals').textContent=registeredBranches.length+' filiais cadastradas · '+registeredBranches.filter(b=>b.active).length+' ativas · '+rows.length+' encontrada(s) na pesquisa';
 $('branchRegistry').innerHTML=rows.length?`<div class="panel branch-table-wrap"><table class="branch-table"><thead><tr><th>Filial</th><th>Cidade / UF</th><th>Cutovers</th><th>Situação</th><th></th></tr></thead><tbody>${paged.map(b=>`<tr><td><b>${esc(b.code)}</b><span>${esc(b.name)}</span></td><td>${esc([b.city,b.uf].filter(Boolean).join(' / '))||'Não informado'}</td><td>${b.cutover_count}</td><td><span class="badge ${b.needs_review?'blocked':b.active?'done':''}">${b.needs_review?'Revisar filial':b.active?'Ativa':'Inativa'}</span></td><td><div class="actions"><button data-open-branch="${esc(b.id)}">Abrir cutovers</button>${DECIDE?`<button data-edit-branch="${esc(b.id)}">Editar</button>`:''}</div></td></tr>`).join('')}</tbody></table></div>`:'<div class="panel empty">Nenhuma filial encontrada.'+(DECIDE?' Clique em Cadastrar filial para começar.':'')+'</div>';
 if(rows.length){$('branchRegistry').insertAdjacentHTML('beforeend',`<div class="branch-pagination"><span>${start+1} a ${Math.min(start+BRANCH_PAGE_SIZE,rows.length)} de ${rows.length} filiais</span><div class="actions"><button id="previousBranches" ${branchPage===1?'disabled':''}>Anterior</button><span>Página ${branchPage} de ${pages}</span><button id="nextBranches" ${branchPage===pages?'disabled':''}>Próxima</button></div></div>`);$('previousBranches').onclick=()=>{branchPage--;renderBranchRegistry()};$('nextBranches').onclick=()=>{branchPage++;renderBranchRegistry()}}
 document.querySelectorAll('[data-open-branch]').forEach(b=>b.onclick=async()=>{await switchBranch(b.dataset.openBranch);document.querySelector('[data-view="run"]').click()});
 document.querySelectorAll('[data-edit-branch]').forEach(b=>b.onclick=()=>branchForm(registeredBranches.find(x=>x.id===b.dataset.editBranch)));
}
function branchPermissions(){
 const branch=currentBranch();$('branchIdentity').textContent=branch?branch.code+' · '+branch.name:'Escolha uma loja para visualizar os cutovers.';
 $('newExecution').disabled=!branch||!branch.active||!!branch.needs_review||!DECIDE;
 $('addBranch').hidden=!DECIDE;
 $('branch').readOnly=true;
 if($('linkLegacy'))$('linkLegacy').remove();
 if(branch?.needs_review&&DECIDE){const button=document.createElement('button');button.id='linkLegacy';button.textContent='Vincular execução à filial correta';button.onclick=resolveLegacy;$('branchIdentity').append(document.createElement('br'),button)}
}
async function switchBranch(id){
 if(switchingBranch)return false;
 if(dirty||saving){if(!await persist()){$('selectedBranch').value=selectedBranchId;toast('Salve ou exporte as alterações antes de trocar de filial.');return false}}
 switchingBranch=true;$('selectedBranch').disabled=true;
 try{
  selectedBranchId=id;currentId=null;version=0;dirty=false;conflict=false;clearTimeout(timer);
  state={meta:{},tasks:{},decisions:{linx:{},orion:{}}};$('selectedBranch').value=id;render();
  const rows=await refreshList();
  if(rows.length){$('execution').value=rows[0].id;await loadExecution(rows[0].id)}
  else syncText(id?'Esta filial ainda não tem cutovers. Clique em Iniciar cutover.':'Selecione uma filial cadastrada.');
  branchPermissions();return true;
 }catch(e){syncText(e.message,true);return false}finally{switchingBranch=false;$('selectedBranch').disabled=false}
}
function branchForm(existing=null){
 modal(`<h2>${existing?'Editar filial':'Cadastrar filial'}</h2><p class="muted">Código e nome identificam a loja. Cidade e UF são opcionais.</p><form id="branchForm" class="form-stack"><label for="branchCode">Código da filial *</label><input id="branchCode" placeholder="VD266" maxlength="30" value="${esc(existing?.code)}" ${existing?'readonly':''} required><label for="branchName">Nome da loja *</label><input id="branchName" placeholder="Shopping Vila Lobos" maxlength="160" value="${esc(existing?.name)}" required><div class="row2"><div><label for="branchCity">Cidade</label><input id="branchCity" maxlength="100" value="${esc(existing?.city)}"></div><div><label for="branchUf">UF</label><select id="branchUf"><option value="">Não informada</option>${['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'].map(uf=>`<option ${existing?.uf===uf?'selected':''}>${uf}</option>`).join('')}</select></div></div>${existing?`<label for="branchActive">Situação</label><select id="branchActive"><option value="true" ${existing.active?'selected':''}>Ativa</option><option value="false" ${existing.active?'':'selected'}>Inativa - mantém o histórico</option></select>`:''}<p id="branchError" role="alert" class="sync-error"></p><button class="primary" id="saveBranch">Salvar filial</button></form>`);
 $('branchForm').onsubmit=async e=>{e.preventDefault();$('saveBranch').disabled=true;const body={code:$('branchCode').value.trim().toUpperCase(),name:$('branchName').value.trim(),city:$('branchCity').value.trim(),uf:$('branchUf').value,active:existing?$('branchActive').value==='true':true};try{const result=await api('/api/branches'+(existing?'/'+existing.id:''),existing?'PUT':'POST',body);$('modal').close();await refreshBranches();toast('Filial salva. Selecione-a na aba Cutover para iniciar uma execução.')}catch(err){$('branchError').textContent=err.message;$('saveBranch').disabled=false}};
}
function startBoundCutover(){
 const b=currentBranch();if(!b||!DECIDE||!b.active||b.needs_review)return;
 if(dirty||saving){toast('Aguarde o salvamento antes de iniciar outra execução.');return}
 modal(`<h2>Iniciar cutover</h2><div class="bound-store"><b>${esc(b.code)}</b><span>${esc(b.name)}</span></div><p class="muted">Esta execução ficará vinculada somente à loja acima.</p><form id="boundCutoverForm" class="form-stack"><label for="boundPdv">PDV que será atendido *</label><input id="boundPdv" placeholder="Ex.: 01" maxlength="40" required><p id="startCutoverError" role="alert" class="sync-error"></p><button class="primary" id="startBoundButton">Iniciar cutover desta filial</button></form>`);
 $('boundCutoverForm').onsubmit=async e=>{e.preventDefault();$('startBoundButton').disabled=true;try{const r=await api('/api/cutovers','POST',{branch_id:b.id,pdv:$('boundPdv').value.trim()});await refreshList(r.id);await loadExecution(r.id);$('modal').close();await refreshBranches();toast('Cutover iniciado para '+b.code+'.')}catch(err){$('startCutoverError').textContent=err.message;$('startBoundButton').disabled=false}};
}
function resolveLegacy(){
 if(!currentId){toast('Selecione a execução anterior para vincular.');return}
 modal(`<h2>Confirmar filial da execução anterior</h2><p>Os processos e observações serão mantidos. Este ajuste é permitido apenas para registros antigos sem uma filial identificada.</p><form id="legacyForm" class="form-stack"><label for="targetBranch">Filial correta</label><select id="targetBranch" required><option value="">Selecione</option>${registeredBranches.filter(b=>b.active&&!b.needs_review).map(b=>`<option value="${b.id}">${esc(b.code+' · '+b.name)}</option>`).join('')}</select><label for="legacyPdv">PDV (opcional)</label><input id="legacyPdv" maxlength="40"><p id="legacyError" role="alert" class="sync-error"></p><button class="primary">Confirmar vínculo</button></form>`);
 $('legacyForm').onsubmit=async e=>{e.preventDefault();if(dirty&&!await persist())return;try{const r=await api('/api/cutovers/'+currentId+'/branch','PUT',{branch_id:$('targetBranch').value,pdv:$('legacyPdv').value.trim(),version});$('modal').close();await refreshBranches();await switchBranch(r.branch_id)}catch(err){$('legacyError').textContent=err.message}};
}
function initBranches(){
 document.querySelector('main').append($('modal'));
 const nav=document.createElement('button');nav.id='branchesNav';nav.textContent='▦ Filiais';nav.onclick=showBranches;document.querySelector('.nav').prepend(nav);
 document.querySelectorAll('[data-view]').forEach(b=>{const prior=b.onclick;b.onclick=()=>{showCutoverWorkspace();prior()}});
 $('manageBranches').onclick=showBranches;$('addBranch').onclick=()=>branchForm();$('branchSearch').oninput=()=>{branchPage=1;clearTimeout(branchSearchTimer);branchSearchTimer=setTimeout(renderBranchRegistry,150)};
 $('selectedBranch').onchange=()=>switchBranch($('selectedBranch').value);
 $('execution').onchange=async()=>{
  const id=$('execution').value;if(id){await loadExecution(id);return}
  if((dirty||saving)&&!await persist()){$('execution').value=currentId||'';return}
  currentId=null;version=0;state={meta:{},tasks:{},decisions:{linx:{},orion:{}}};render();syncText('Selecione ou inicie um cutover desta filial.');
 };
 $('newExecution').textContent='▶ Iniciar cutover';$('newExecution').onclick=startBoundCutover;
 const priorRender=render;render=function(){priorRender();branchPermissions()};render();
 refreshBranches().then(()=>refreshList()).catch(e=>syncText(e.message,true));
}
