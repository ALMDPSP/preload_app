/* Process checklist: check to complete, notes optional, save then download PDF. */
function renderChecklistTasks(openIds=[]){
 const groups=[['01','Preparação do Orion',SOURCE.orion.slice(0,3)],['02','Retirada do Linx Agiliza',SOURCE.linx],['03','Instalação, testes e aceite',SOURCE.orion.slice(3)]];
 $('tasks').innerHTML=groups.map(([number,title,list])=>{const complete=list.filter(t=>done(t.id)).length;return `<section class="group"><div class="phase-heading"><span class="phase-number">${number}</span><div><h3>${title}</h3><span>${complete} de ${list.length} concluídos</span></div><div class="phase-track"><span style="width:${complete/list.length*100}%"></span></div></div>${list.map(t=>{
 const id=t.id,record=task(id);return `<article class="task process-card" data-id="${id}"><div class="process-head"><input class="process-check" type="checkbox" id="check-${id}" data-check="${id}" ${done(id)?'checked':''} aria-label="Concluir processo: ${esc(t.title)}"><label for="check-${id}" class="process-title"><strong>${esc(t.title)}</strong><span>${id.startsWith('orion')?'Orion':'Linx'} · Etapa ${t.number} · ${esc(t.team)}</span></label><span class="badge">${esc(status(id))}</span></div><div class="process-notes"><label for="${id}-notes">Observações <span>opcional</span></label><textarea rows="2" id="${id}-notes" data-task="${id}" data-key="notes" placeholder="Se precisar, deixe um comentário sobre este processo.">${esc(record.notes)}</textarea></div><details class="more-info" data-more-id="${id}" ${openIds.includes(id)?'open':''}><summary>Ver orientações e informações adicionais</summary><p>${esc(t.description)}</p><div class="condition"><small>CONDIÇÃO PARA AVANÇAR</small>${esc(t.gate)}</div><div class="essentials"><div><label for="${id}-owner">Responsável (preenchido ao marcar)</label><input id="${id}-owner" data-task="${id}" data-key="owner" value="${esc(record.owner)}" placeholder="Seu nome será registrado automaticamente"></div><div><label for="${id}-status">Status detalhado</label><select id="${id}-status" data-task="${id}" data-key="status">${STATUSES.map(s=>`<option ${s===status(id)?'selected':''}>${s}</option>`).join('')}</select></div></div><div class="fields" style="margin-top:15px">${field(id,'start','Início previsto','datetime-local')}${field(id,'duration','Duração prevista (min)','number')}<div><label>Fim previsto</label><div data-end></div></div></div><label for="${id}-evidence">Link ou evidência adicional (opcional)</label><textarea id="${id}-evidence" data-task="${id}" data-key="evidence" placeholder="Chamado, link ou caminho do backup, se necessário.">${esc(record.evidence)}</textarea>${t.originalNote?`<p class="original"><b>Observação do planejamento:</b> ${esc(t.originalNote)}</p>`:''}${record.changedAt?`<p class="muted">Última marcação: ${esc(new Date(record.changedAt).toLocaleString('pt-BR'))}</p>`:''}</details></article>`
 }).join('')}</section>`}).join('');
}
function processPermissions(){
 document.querySelectorAll('[data-check]').forEach(c=>c.disabled=!currentId||READONLY);
 if($('saveChecklist'))$('saveChecklist').disabled=!currentId||READONLY;
 document.querySelectorAll('.phase-heading').forEach(h=>{const group=h.closest('.group'),ids=[...group.querySelectorAll('.task')].map(x=>x.dataset.id),n=ids.filter(done).length;h.querySelector('h3').nextElementSibling.textContent=n+' de '+ids.length+' concluídos';h.querySelector('.phase-track span').style.width=(n/ids.length*100)+'%'});
 if($('dockProgress'))$('dockProgress').textContent=ALL.filter(t=>done(t.id)).length+' de '+ALL.length+' processos marcados';
}
function setProcessStatus(id,next,control){
 if(READONLY||!currentId){if(control?.type==='checkbox')control.checked=done(id);return}
 if(['Em andamento','Concluído'].includes(next)&&id==='orion4'&&!authorized()){
  if(control?.type==='checkbox')control.checked=done(id);else if(control)control.value=status(id);
  toast('Antes da instalação, registre o GO da retirada em Decisões e aceite.');return;
 }
 if(next==='Concluído'&&(id==='orion5'&&!done('orion4')||id==='orion6'&&!done('orion5'))){if(control?.type==='checkbox')control.checked=done(id);else if(control)control.value=status(id);toast('Marque a etapa anterior do Orion antes de continuar.');return}
 const r=state.tasks[id]||={};r.status=next;r.changedAt=new Date().toISOString();
 if(next==='Concluído'&&!r.owner?.trim())r.owner=document.body.dataset.userName||'';
 if(next!=='Concluído'){
  if(!prerequisites()){state.decisions.linx.value='Pendente';if(['Em andamento','Concluído'].includes(status('orion4')))state.tasks.orion4.status='Pendente'}
  if(id==='orion4'||!prerequisites()){if(state.tasks.orion5)state.tasks.orion5.status='Pendente';if(state.tasks.orion6)state.tasks.orion6.status='Pendente'}
  if(id==='orion5'&&state.tasks.orion6)state.tasks.orion6.status='Pendente';
  state.decisions.orion.value='Pendente';
 }
 save();render();
}
async function saveAndOfferPdf(){
 if(!currentId){toast('Crie ou selecione uma execução antes de salvar.');return}
 const button=$('saveChecklist');button.disabled=true;button.textContent='Salvando…';
 try{
  if(!await persist())return;
  const count=ALL.filter(t=>done(t.id)).length;
  modal(`<div class="saved-icon">✓</div><h2>Checklist salvo!</h2><p class="muted">${esc(state.meta.branch)} · ${count} de ${ALL.length} processos marcados.</p>${count<ALL.length?'<p class="notice">Esta é uma versão parcial do checklist. Os processos pendentes também aparecerão no relatório.</p>':''}<div class="download-note"><b>Salve uma cópia em PDF na pasta Downloads.</b><p>Clique abaixo para baixar o arquivo. Se o navegador perguntar onde salvar, escolha a pasta <b>Downloads</b>.</p></div><div class="dialog-actions"><button id="continueChecklist">Continuar preenchendo</button><button class="primary" id="downloadChecklist">↓ Baixar checklist em PDF</button></div><p id="pdfError" role="alert"></p>`);
  $('continueChecklist').onclick=()=>$('modal').close();$('downloadChecklist').onclick=()=>downloadChecklistPdf();
 }finally{button.disabled=READONLY||!currentId;button.textContent='Salvar checklist'}
}
async function downloadChecklistPdf(){
 const button=$('downloadChecklist');if(button){button.disabled=true;button.textContent='Gerando PDF…'}
 try{
  if(!currentId)throw Error('Selecione uma execução.');
  const response=await fetch('/api/cutovers/'+currentId+'/pdf?version='+version,{credentials:'same-origin'});
  if(!response.ok){let payload=await response.json();throw Error(payload.error||'Não foi possível gerar o PDF.')}
  const content=await response.blob(),url=URL.createObjectURL(content),a=document.createElement('a');
  const header=response.headers.get('Content-Disposition')||'',match=header.match(/filename="?([^";]+)"?/i);
  a.href=url;a.download=match?match[1]:'Checklist_Cutover.pdf';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
  toast('Download solicitado. Confira a pasta Downloads ou a pasta escolhida no navegador.');
 }catch(e){if($('pdfError'))$('pdfError').textContent=e.message;else toast(e.message)}finally{if(button){button.disabled=false;button.textContent='↓ Baixar checklist em PDF'}}
}
function initChecklistUX(){
 const priorRender=render;render=function(){priorRender();processPermissions()};render();
 document.addEventListener('change',e=>{if(e.target.dataset.check)setProcessStatus(e.target.dataset.check,e.target.checked?'Concluído':'Pendente',e.target)});
 $('saveChecklist').onclick=()=>saveAndOfferPdf();
 if(READONLY)$('saveChecklist').hidden=true;
 $('print').textContent='↓ Baixar PDF';$('print').onclick=async()=>{if(!currentId){toast('Selecione uma execução.');return}if(await persist())await downloadChecklistPdf()};
 if($('quickCreateUser'))$('quickCreateUser').onclick=async()=>{await showUsers();$('userName')?.focus();$('userName')?.scrollIntoView?.({behavior:'smooth',block:'center'})};
 if($('users')){const nav=document.createElement('button');nav.textContent='⚙ Usuários e acessos';nav.onclick=()=>showUsers();document.querySelector('.nav').append(nav)}
 const originalSync=syncText;syncText=function(message,bad){originalSync(message,bad);$('dockSync').textContent=message;$('dockSync').classList.toggle('sync-error',!!bad)};
 const filters=[['all','Todos'],['Pendente','Pendentes'],['Concluído','Concluídos']];
 $('quickFilters').innerHTML=filters.map(([s,label])=>`<button data-quick-filter="${s}" class="${s==='all'?'selected':''}">${label}</button>`).join('');
 document.querySelectorAll('[data-quick-filter]').forEach(b=>b.onclick=()=>{$('filter').value=b.dataset.quickFilter;applyFilter();document.querySelectorAll('[data-quick-filter]').forEach(x=>x.classList.toggle('selected',x===b))});
 $('filter').addEventListener('change',()=>document.querySelectorAll('[data-quick-filter]').forEach(b=>b.classList.toggle('selected',b.dataset.quickFilter===$('filter').value)));
 const oldMetrics=metrics;metrics=function(){oldMetrics();processPermissions()};metrics();
}
