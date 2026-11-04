/* Keep the existing records and API; simplify how operators fill them. */
const ME={id:document.body.dataset.userId,name:document.body.dataset.userName,email:document.body.dataset.userEmail};
const account=document.createElement('div');account.className='account-card';
account.innerHTML=`<strong>${esc(ME.name)}</strong><span class="account-role">${ROLES[ROLE]}</span><div class="account-email">${esc(ME.email)}</div><div class="account-last-login">Último acesso: ${esc($('lastLogin').textContent)}</div>`;
document.querySelector('aside').append(account);account.append($('password'),$('logoutForm'));
$('execution').closest('section').classList.add('execution-toolbar');
if($('users')){document.querySelector('.nav').append($('users'));$('users').textContent='⚙  Gestão de acessos';$('users').onclick=()=>showUsers()}
document.querySelectorAll('[data-view]').forEach(b=>{const old=b.onclick;b.onclick=()=>{document.body.classList.remove('access-mode');$('access').classList.add('hidden');if($('users'))$('users').classList.remove('active');old()}});
const gateLink=document.createElement('button');gateLink.className='gate-link no-print';gateLink.textContent='Ver liberação';gateLink.onclick=()=>document.querySelector('[data-view="decisions"]').click();$('gate').append(gateLink);
const help=document.createElement('div');help.className='simple-help no-print';help.innerHTML='<b>Preenchimento rápido</b> · 1. Selecione a execução. &nbsp; 2. Abra uma etapa. &nbsp; 3. Informe responsável e resultado. &nbsp; 4. Clique em Concluir.<br>Horários e observações adicionais ficam em “Mais informações”. As alterações são salvas automaticamente.';
$('tasks').before(help);
function showStepError(id,message,keys=[]){const el=$('error-'+id);if(el){el.textContent=message;el.hidden=false}for(const k of keys)$(id+'-'+k)?.classList.add('is-invalid');if(keys[0])$(id+'-'+keys[0])?.focus()}
function changeStepStatus(id,value){const select=$(id+'-status');select.value=value;select.dispatchEvent(new Event('change',{bubbles:true}))}
const existingRender=render;
render=function(){
 const opened=[...document.querySelectorAll('.task[open]')].map(d=>d.dataset.id);
 existingRender();
 const groups=[['01 · PREPARAÇÃO DO ORION',SOURCE.orion.slice(0,3)],['02 · RETIRADA DO LINX AGILIZA',SOURCE.linx],['03 · INSTALAÇÃO, TESTES E ACEITE',SOURCE.orion.slice(3)]];
 $('tasks').innerHTML=groups.map(([title,tasks])=>`<div class="group"><div class="phase-label">${title}</div>${tasks.map(t=>{
  const id=t.id,values=task(id),disabled=READONLY||!currentId?'disabled':'';
  return `<details class="task simple-task" data-id="${id}" ${opened.includes(id)?'open':''}><summary><div class="num">${String(t.number).padStart(2,'0')}</div><div><h3>${esc(t.title)}</h3><span class="team">${id.startsWith('orion')?'Orion':'Linx'} · Etapa ${t.number}</span></div><span class="team">${esc(t.team)}</span><span class="badge">${esc(status(id))}</span><span class="chev">⌄</span></summary><div class="detail"><p class="description">${esc(t.description)}</p><div class="condition"><small>PARA CONCLUIR ESTA ETAPA</small>${esc(t.gate)}</div><div class="essential-fields"><div><label for="${id}-owner">Quem está responsável? *</label><div class="owner-line"><input id="${id}-owner" data-task="${id}" data-key="owner" value="${esc(values.owner)}" placeholder="Nome do responsável" ${disabled}><button type="button" data-use-me="${id}" ${disabled}>Usar meu nome</button></div></div><div><label for="${id}-status">Como está esta etapa?</label><select id="${id}-status" data-task="${id}" data-key="status" ${disabled}>${STATUSES.map(s=>`<option ${status(id)===s?'selected':''}>${s}</option>`).join('')}</select></div><div class="result-field"><label for="${id}-evidence">Resultado ou evidência *</label><textarea id="${id}-evidence" data-task="${id}" data-key="evidence" rows="2" placeholder="Ex.: teste aprovado, número do chamado ou caminho do backup" ${disabled}>${esc(values.evidence)}</textarea><small class="field-hint">Para concluir, informe o que foi validado. Pode ser texto, link ou caminho do arquivo.</small></div></div><div class="field-error" id="error-${id}" role="alert" hidden></div><details class="extra-fields" data-id="${id}-extra"><summary>Mais informações · horários e observações</summary><div class="fields">${field(id,'start','Início previsto','datetime-local')}${field(id,'duration','Duração prevista (min)','number')}<div><label>Fim previsto</label><p data-end>${finishTime(values)}</p></div></div><label for="${id}-notes" style="margin-top:15px">Observações da execução</label><textarea id="${id}-notes" data-task="${id}" data-key="notes" ${disabled}>${esc(values.notes)}</textarea>${t.originalNote?`<div class="original" style="margin-top:12px"><b>Observação do planejamento:</b> ${esc(t.originalNote)}</div>`:''}</details><div class="step-actions"><small>${values.changedAt?'Status atualizado em '+esc(new Date(values.changedAt).toLocaleString('pt-BR')):'* Responsável e resultado são necessários para concluir.'}</small><div class="actions no-print"><button data-step-action="${id}" data-status="Em andamento" ${disabled}>Iniciar etapa</button><button class="primary" data-step-action="${id}" data-status="Concluído" ${disabled}>✓ Concluir</button></div></div></div></details>`
 }).join('')}</div>`).join('');
 document.querySelectorAll('[data-meta],[data-task],[data-decision]').forEach(e=>e.disabled=!currentId||READONLY||!!e.dataset.decision&&!DECIDE);
 document.querySelectorAll('[data-use-me]').forEach(b=>b.onclick=()=>{const input=$(b.dataset.useMe+'-owner');input.value=ME.name;input.dispatchEvent(new Event('input',{bubbles:true}));input.classList.remove('is-invalid')});
 document.querySelectorAll('[data-step-action]').forEach(b=>b.onclick=()=>changeStepStatus(b.dataset.stepAction,b.dataset.status));
 metrics();
};
document.addEventListener('change',e=>{
 const el=e.target,id=el.dataset.task;
 if(!id||el.dataset.key!=='status')return;
 const missing=el.value==='Concluído'?['owner','evidence'].filter(k=>!task(id)[k]?.trim()):[];
 if(missing.length){e.stopImmediatePropagation();el.value=status(id);showStepError(id,'Preencha o responsável e o resultado antes de concluir.',missing)}
},true);
document.addEventListener('input',e=>{if(e.target.dataset.task){e.target.classList.remove('is-invalid');const err=$('error-'+e.target.dataset.task);if(err)err.hidden=true}});
$('newExecution').onclick=()=>{
 if(dirty||saving){toast('Aguarde o salvamento ou exporte os registros antes de criar outra execução.');return}
 const d=new Date();d.setMinutes(d.getMinutes()-d.getTimezoneOffset());
 modal(`<h2 class="modal-heading">Novo cutover</h2><p class="modal-description">Informe a loja e o PDV que serão atendidos.</p><form id="newCutoverForm"><div class="form-grid"><div><label for="newBranch">Filial *</label><input id="newBranch" placeholder="Ex.: VD266" maxlength="60" required></div><div><label for="newPdv">PDV *</label><input id="newPdv" placeholder="Ex.: PDV 01" maxlength="60" required></div><div><label for="newDate">Data da execução *</label><input id="newDate" type="date" value="${d.toISOString().slice(0,10)}" required></div><div><label for="newCoordinator">Coordenador / contato</label><input id="newCoordinator" value="${esc(ME.name)}" maxlength="250" placeholder="Nome e telefone"></div></div><p id="newCutoverError" class="access-error" role="alert"></p><div class="dialog-actions"><button type="button" id="cancelNew">Cancelar</button><button class="primary" id="createCutoverButton">Criar cutover</button></div></form>`);
 $('newBranch').focus();$('cancelNew').onclick=()=>$('modal').close();
 $('newCutoverForm').onsubmit=async e=>{e.preventDefault();const title=$('newBranch').value.trim()+' / '+$('newPdv').value.trim();$('createCutoverButton').disabled=true;try{let r=await api('/api/cutovers','POST',{title,meta:{date:$('newDate').value,coordinator:$('newCoordinator').value}});$('modal').close();await refreshList(r.id);await loadExecution(r.id);toast('Cutover criado. Abra a primeira etapa para começar.')}catch(err){$('newCutoverError').textContent=err.message;$('createCutoverButton').disabled=false}};
};
$('logoutForm').onsubmit=async e=>{e.preventDefault();if(dirty||saving){await persist();if(saving){toast('Aguarde o salvamento antes de sair.');return}if(dirty&&!confirm('Há alterações que não foram salvas. Deseja sair e descartá-las?'))return}dirty=false;$('logoutForm').submit()};
render();
