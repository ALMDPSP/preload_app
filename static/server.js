let currentId=null,version=0,dirty=false,saving=false,timer=null,conflict=false;
const csrf=document.querySelector('meta[name="csrf-token"]').content;
const ROLE=document.body.dataset.role,READONLY=ROLE==='viewer',DECIDE=['admin','manager'].includes(ROLE);
const ROLES={admin:'Administrador',manager:'Gestor',operator:'Operador',viewer:'Consulta'};
const originalRender=render;
render=function(){originalRender();document.querySelectorAll('[data-meta],[data-task],[data-decision],[data-task-action],[data-use-name]').forEach(e=>e.disabled=!currentId||READONLY||!!e.dataset.decision&&!DECIDE)};
render();
const retryButton=document.createElement('button');retryButton.textContent='Tentar salvar';retryButton.onclick=()=>{if(conflict){toast('Exporte sua cópia e atualize os dados antes de continuar.');return}persist()};$('refreshExecution').after(retryButton);
if(!DECIDE)$('newExecution').hidden=true;if(READONLY){$('import').hidden=true;retryButton.hidden=true}
function syncText(text,bad=false){$('syncState').textContent=text;$('syncState').style.color=bad?'#ad332d':'#007f70'}
async function api(path,method='GET',body){let r=await fetch(path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:body===undefined?undefined:JSON.stringify(body)});let data=await r.json();if(!r.ok){let e=Error(data.error||'Falha na solicitação');e.status=r.status;if(r.status===401)syncText('Sessão expirada. Exporte os registros e faça login novamente.',true);throw e}return data}
function scheduleSave(){if(READONLY)return;if(!currentId){syncText('Crie ou selecione um cutover antes de preencher.',true);return}dirty=true;syncText('Alterações aguardando salvamento…');clearTimeout(timer);timer=setTimeout(persist,800)}
let pendingSave=null;
function persist(){
 clearTimeout(timer);
 if(saving)return pendingSave;
 if(conflict||!currentId)return Promise.resolve(false);
 if(!dirty)return Promise.resolve(true);
 saving=true;
 pendingSave=(async()=>{
  try{
   while(dirty){
    dirty=false;const id=currentId,snapshot=JSON.parse(JSON.stringify(state));syncText('Salvando…');
    const r=await api('/api/cutovers/'+id,'PUT',{state:snapshot,version});version=r.version;
    $('saved').textContent='Salvo por '+r.updated_by+' · '+new Date(r.updated_at).toLocaleString('pt-BR');
    syncText('Salvo · '+new Date(r.updated_at).toLocaleTimeString('pt-BR'));
    const option=$('execution').selectedOptions[0];if(option)option.textContent=snapshot.meta.branch;
   }
   return true;
  }catch(e){dirty=true;if(e.status===409)conflict=true;syncText(e.message+' Seus dados continuam na tela. Exporte uma cópia antes de atualizar.',true);return false}
  finally{saving=false;pendingSave=null}
 })();return pendingSave;
}
async function refreshList(selectId){let rows=await api('/api/cutovers');$('execution').innerHTML='<option value="">Selecione um cutover</option>'+rows.map(r=>`<option value="${esc(r.id)}">${esc(r.title)}</option>`).join('');$('execution').value=selectId||'';return rows}
async function loadExecution(id){if(!id)return;if(saving){toast('Aguarde o salvamento antes de trocar de cutover.');$('execution').value=currentId||'';return}if(dirty&&!confirm('Há alterações não salvas. Exporte uma cópia antes de trocar. Deseja descartar as alterações da tela?')){$('execution').value=currentId||'';return}try{clearTimeout(timer);let r=await api('/api/cutovers/'+id);currentId=id;version=r.version;state=validate(r.state);dirty=false;conflict=false;render();syncText('Dados carregados · '+new Date(r.updated_at).toLocaleString('pt-BR'));$('saved').textContent='Última atualização: '+r.updated_by+' · '+new Date(r.updated_at).toLocaleString('pt-BR')}catch(e){syncText(e.message,true)}}
$('execution').onchange=()=>loadExecution($('execution').value);$('refreshExecution').onclick=()=>currentId?loadExecution(currentId):refreshList();$('newExecution').onclick=()=>{if(saving||dirty){toast('Salve ou exporte as alterações antes de criar outro cutover.');return}modal('<h2>Novo cutover</h2><p>Informe a loja e o equipamento que será migrado.</p><form id="newExecutionForm" class="form-stack"><label for="newBranch">Filial</label><input id="newBranch" required maxlength="80" placeholder="Ex.: VD266"><label for="newPdv">PDV</label><input id="newPdv" required maxlength="40" placeholder="Ex.: 01"><button class="primary" type="submit">Criar execução</button><p id="newExecutionError" role="alert"></p></form>');$('newExecutionForm').onsubmit=async e=>{e.preventDefault();const submit=e.currentTarget.querySelector('button');submit.disabled=true;try{let r=await api('/api/cutovers','POST',{title:$('newBranch').value.trim()+' / PDV '+$('newPdv').value.trim()});await refreshList(r.id);await loadExecution(r.id);$('modal').close()}catch(err){$('newExecutionError').textContent=err.message;submit.disabled=false}}};
function modal(html){$('modalBody').innerHTML=html;$('modal').showModal()}$('closeModal').onclick=()=>$('modal').close();
$('history').onclick=async()=>{if(!currentId){toast('Selecione um cutover.');return}try{let rows=await api('/api/cutovers/'+currentId+'/audit');modal('<h2>Histórico de alterações</h2><p>Últimos 200 eventos. Horários exibidos no fuso do navegador.</p>'+rows.map(r=>`<details style="padding:15px;border-bottom:1px solid #ddd"><summary>${esc(new Date(r.created_at).toLocaleString('pt-BR'))} · ${esc(r.actor)} · ${esc(r.action)}</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere">${esc(JSON.stringify(JSON.parse(r.detail),null,2))}</pre></details>`).join(''))}catch(e){toast(e.message)}};
if($('users'))$('users').onclick=()=>showUsers();
$('password').onclick=()=>{modal('<h2>Alterar minha senha</h2><form id="passwordForm" class="form-stack"><label for="oldPassword">Senha atual</label><input id="oldPassword" type="password" autocomplete="current-password" required><label for="newPassword">Nova senha (mínimo 12 caracteres)</label><input id="newPassword" type="password" minlength="12" autocomplete="new-password" required><button class="primary">Salvar e entrar novamente</button><p id="passwordError" role="alert"></p></form>');$('passwordForm').onsubmit=async e=>{e.preventDefault();try{await api('/api/password','POST',{current:$('oldPassword').value,new:$('newPassword').value});location.href='/login'}catch(err){$('passwordError').textContent=err.message}}};
window.addEventListener('beforeunload',e=>{if(dirty||saving){e.preventDefault();e.returnValue=''}});
$('lastLogin').textContent=$('lastLogin').dataset.time?new Date($('lastLogin').dataset.time).toLocaleString('pt-BR'):'Primeiro acesso';
refreshList().then(rows=>{if(rows.length){$('execution').value=rows[0].id;return loadExecution(rows[0].id)}syncText('Clique em “Novo cutover” para cadastrar a primeira execução.');}).catch(e=>syncText(e.message,true));

function localDateTime(){const d=new Date();return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16)}
$('logoutForm').addEventListener('submit',async event=>{
 if(event.defaultPrevented)return;
 event.preventDefault();const form=event.currentTarget;
 if(saving){toast('Aguarde o salvamento antes de sair.');return}
 if(dirty){await persist();if(dirty){if(!confirm('Há alterações não salvas. Exporte os registros para guardar uma cópia. Deseja sair mesmo assim?'))return;dirty=false;clearTimeout(timer)}}
 // A saída é sempre uma requisição POST com o token de sessão existente.
 form.submit();
});
