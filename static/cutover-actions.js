/* Explicit review and administrative deletion of a saved cutover. */
function updateCutoverActions(){
 $('rejectCutover').hidden=!DECIDE||!currentId||!!currentRejection;
 $('deleteCutover').hidden=ROLE!=='admin'||!currentId;
 const panel=$('cutoverRejection');panel.hidden=!currentRejection;
 panel.innerHTML=currentRejection?`<strong>Cutover rejeitado</strong><p>${esc(currentRejection.reason)}</p><small>${esc(currentRejection.actor)} · ${esc(new Date(currentRejection.created_at).toLocaleString('pt-BR'))}</small><p>Execução disponível para consulta. Solicite ao Administrador a exclusão para refazer.</p>`:'';
 $('import').disabled=!!currentRejection;
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
$('deleteCutover').onclick=()=>{
 if(!currentId||ROLE!=='admin')return;
 if(dirty||saving){toast('Salve o checklist ou descarte as alterações antes de excluir.');return}
 const id=currentId,expected=version;
 modal(`<h2>Excluir cutover</h2><p>Confirma excluir <b>${esc(state.meta.branch)}</b>?</p><p>O checklist desta execução será removido. A filial continuará cadastrada e você poderá iniciar outro cutover do zero para o mesmo PDV. Baixe o PDF antes, se precisar guardar uma cópia.</p><p id="deleteCutoverError" role="alert" class="sync-error"></p><div class="actions"><button id="cancelDeleteCutover">Cancelar</button><button id="confirmDeleteCutover" class="danger">Excluir e liberar para refazer</button></div>`);
 $('cancelDeleteCutover').onclick=()=>$('modal').close();
 $('confirmDeleteCutover').onclick=async()=>{$('confirmDeleteCutover').disabled=true;try{await api('/api/cutovers/'+id,'DELETE',{version:expected});$('modal').close();clearCurrentCutover();await refreshList();await refreshBranches();syncText('Cutover excluído. Clique em Iniciar cutover para refazer nesta filial.');toast('Execução excluída. Filial liberada para refazer.')}catch(err){$('deleteCutoverError').textContent=err.message;$('confirmDeleteCutover').disabled=false}};
};
const renderBeforeCutoverActions=render;
render=function(){renderBeforeCutoverActions();updateCutoverActions()};
updateCutoverActions();
