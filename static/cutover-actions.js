/* Explicit review and administrative deletion of a saved cutover. */
function updateCutoverActions(){
 $('rejectCutover').hidden=!DECIDE||!currentId||!cutoverEditing||!!currentRejection;
 $('deleteCutover').hidden=!OPERATIONS_ADMIN||!currentId||!cutoverEditing;
 const panel=$('cutoverRejection');panel.hidden=!currentRejection;
 panel.innerHTML=currentRejection?`<strong>Cutover rejeitado</strong><p>${esc(currentRejection.reason)}</p><small>${esc(currentRejection.actor)} · ${esc(new Date(currentRejection.created_at).toLocaleString('pt-BR'))}</small><p>Execução disponível para consulta. Solicite a exclusão a um Administrador ou Operador para refazer.</p>`:'';
 $('import').disabled=!!currentRejection||!currentId||!cutoverEditing;
 $('history').disabled=!currentId||!cutoverEditing;
}
function clearCurrentCutover(){
 currentId=null;currentRejection=null;version=0;dirty=false;conflict=false;clearTimeout(timer);
 state={meta:{},tasks:{},decisions:{linx:{},orion:{}}};render();
}
$('rejectCutover').onclick=()=>{
 if(!currentId||!DECIDE||currentRejection)return;
 if(dirty||saving){toast('Salve o checklist antes de rejeitar o cutover.');return}
 const id=currentId,expected=version;
 modal(`<h2>Rejeitar cutover</h2><p>${esc(state.meta.branch)}</p><p>O checklist salvo será mantido para consulta e ficará bloqueado para edição.</p><form id="rejectCutoverForm" class="form-stack"><label for="rejectionReason">Motivo da rejeição *</label><textarea id="rejectionReason" required minlength="3" maxlength="2000"></textarea><p id="rejectCutoverError" role="alert" class="sync-error"></p><div class="actions"><button type="button" id="cancelRejectCutover">Cancelar</button><button class="danger" id="confirmRejectCutover">Confirmar rejeição</button></div></form>`);
 $('cancelRejectCutover').onclick=()=>$('modal').close();
 $('rejectCutoverForm').onsubmit=async e=>{e.preventDefault();$('confirmRejectCutover').disabled=true;try{await api('/api/cutovers/'+id+'/reject','POST',{reason:$('rejectionReason').value.trim(),version:expected});$('modal').close();await refreshList(id);await loadExecution(id);toast('Cutover rejeitado. Motivo registrado no histórico.')}catch(err){$('rejectCutoverError').textContent=err.message;$('confirmRejectCutover').disabled=false}};
};
function confirmCutoverDeletion(execution){
 if(!OPERATIONS_ADMIN||!execution)return;
 if(saving||executionLoading){toast('Aguarde a operação atual terminar antes de excluir.');return}
 const {id,title,version:expected}=execution,branch=selectedBranchId;
 const discarding=currentId===id&&dirty;
 modal(`<h2>Excluir cutover</h2><p>Confirma excluir <b>${esc(title)}</b>?</p><p>O checklist desta execução será excluído. A filial e o plano de PDVs serão mantidos.</p>${discarding?'<p class="notice">As alterações não salvas deste checklist também serão descartadas.</p>':''}<p id="deleteCutoverError" role="alert" class="sync-error"></p><div class="actions"><button id="cancelDeleteCutover">Cancelar</button><button id="confirmDeleteCutover" class="danger">Excluir cutover</button></div>`);
 const button=$('confirmDeleteCutover'),cancel=$('cancelDeleteCutover'),error=$('deleteCutoverError');
 cancel.onclick=()=>$('modal').close();
 button.onclick=async()=>{
  if(saving||executionLoading||selectedBranchId!==branch)return;
  button.disabled=true;cancel.disabled=true;saving=true;
  try{
   await api('/api/cutovers/'+encodeURIComponent(id),'DELETE',{version:expected});
  }catch(err){
   error.textContent=err.message;button.disabled=false;cancel.disabled=false;return;
  }finally{saving=false}
  $('modal').close();
  if(currentId===id){cutoverEditing=false;clearCurrentCutover();showBranchPdvs()}
  toast('Cutover excluído.');
  try{await refreshList()}
  catch(err){toast('Cutover excluído. Atualize a lista para conferir. '+err.message)}
 };
}
$('deleteCutover').onclick=()=>{
 if(currentId&&cutoverEditing)confirmCutoverDeletion({id:currentId,title:state.meta.branch,version});
};
const renderBeforeCutoverActions=render;
render=function(){renderBeforeCutoverActions();updateCutoverActions()};
updateCutoverActions();
