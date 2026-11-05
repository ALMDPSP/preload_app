function openBranchImport(){
 modal(`<h2>Importar filiais</h2><p class="muted">Cadastre sua lista de lojas em uma única importação. Primeiro você confere a prévia; os dados só são gravados ao confirmar.</p><div class="import-template"><b>Colunas do modelo</b><p><strong>Código e nome</strong> são obrigatórios. Cidade, UF e situação são opcionais.</p><a href="/api/branches/import-template" download>↓ Baixar modelo CSV</a><small>Substitua as lojas de exemplo pelas suas filiais. No Excel, mantenha os códigos como texto para preservar zeros à esquerda.</small></div><form id="branchImportForm" class="form-stack"><label for="branchImportFile">Planilha de lojas</label><input type="file" id="branchImportFile" accept=".xlsx,.csv" required><small>Excel .xlsx ou CSV · até 10 MB e 10 mil linhas. No Excel, os dados devem estar na primeira aba.</small><label for="branchImportMode">O que fazer com códigos já cadastrados?</label><select id="branchImportMode"><option value="create_only">Cadastrar apenas novas filiais</option><option value="upsert">Cadastrar novas e atualizar existentes</option></select><p class="muted">As atualizações usam o código como referência e preservam os vínculos com os cutovers. Campos opcionais vazios mantêm os valores existentes.</p><p id="branchImportError" role="alert" class="sync-error"></p><button class="primary" id="analyzeBranches">Analisar arquivo</button></form>`);
 $('branchImportForm').onsubmit=async e=>{
  e.preventDefault();const file=$('branchImportFile').files[0];if(!file)return;
  if(file.size>10*1024*1024){$('branchImportError').textContent='Limite de 10 MB por arquivo.';return}
  const button=$('analyzeBranches');button.disabled=true;button.textContent='Analisando…';
  const data=new FormData();data.append('file',file);data.append('mode',$('branchImportMode').value);
  try{
   const response=await fetch('/api/branches/import/preview',{method:'POST',headers:{'X-CSRF-Token':csrf},body:data});
   let result;try{result=await response.json()}catch(err){throw Error('Não foi possível analisar o arquivo. Atualize a página e tente novamente.')}
   if(!response.ok)throw Error(result.error||'Não foi possível analisar o arquivo.');
   renderImportPreview(result);
  }catch(err){$('branchImportError').textContent=err.message;button.disabled=false;button.textContent='Analisar arquivo'}
 };
}
function renderImportPreview(result){
 const labels={new:'Nova',update:'Atualizar',unchanged:'Sem alteração',ignored:'Já cadastrada'};
 $('modalBody').innerHTML=`<h2>Confira a importação</h2><p class="muted">${result.total} linha(s) · origem: ${esc(result.sheet)} · ${result.mode==='create_only'?'somente novos cadastros':'novos cadastros e atualizações'}</p><div class="import-counts"><div><strong>${result.counts.new}</strong><span>Novas</span></div><div><strong>${result.counts.update}</strong><span>Atualizações</span></div><div><strong>${result.counts.ignored+result.counts.unchanged}</strong><span>Sem gravação</span></div><div class="${result.error_count?'has-errors':''}"><strong>${result.error_count}</strong><span>Erros</span></div></div>${result.error_count?`<div class="import-errors"><b>Corrija os erros antes de importar. Nenhuma filial foi gravada.</b><ul>${result.errors.map(e=>`<li>Linha ${e.line}${e.code?' · '+esc(e.code):''}: ${esc(e.message)}</li>`).join('')}</ul>${result.error_count>result.errors.length?`<p>Exibindo os primeiros ${result.errors.length} erros de ${result.error_count}.</p>`:''}</div>`:''}<div class="import-preview-table"><table class="branch-table"><thead><tr><th>Linha</th><th>Código</th><th>Nome</th><th>Ação</th></tr></thead><tbody>${result.rows.map(r=>`<tr><td>${r.line}</td><td>${esc(r.code)}</td><td>${esc(r.name)}</td><td>${labels[r.action]}</td></tr>`).join('')}</tbody></table></div><p class="muted">A prévia mostra até ${result.preview_limit} linhas. A confirmação processa todas as linhas válidas do arquivo, sem apagar filiais nem cutovers. A prévia expira em 20 minutos.</p><p id="confirmImportError" role="alert" class="sync-error"></p><div class="dialog-actions"><button id="changeImportFile">Escolher outro arquivo</button><button class="primary" id="confirmBranchImport" ${result.import_id?'':'disabled'}>Confirmar importação</button></div>${!result.import_id&&!result.error_count?'<p>Nenhuma gravação necessária neste modo. Para atualizar nomes e dados existentes, escolha o modo de atualização.</p>':''}`;
 $('changeImportFile').onclick=()=>{$('modal').close();openBranchImport()};
 $('confirmBranchImport').onclick=async()=>{
  const button=$('confirmBranchImport');button.disabled=true;button.textContent='Importando…';
  try{
   const saved=await api('/api/branches/import/confirm','POST',{import_id:result.import_id});
   $('modal').close();branchPage=1;await refreshBranches();
   $('branchImportSummary').textContent=`Importação concluída: ${saved.created} nova(s), ${saved.updated} atualizada(s) e ${saved.ignored+saved.unchanged} sem alteração.`;
   $('branchImportSummary').hidden=false;toast('Filiais importadas. Você já pode selecioná-las para iniciar os cutovers.');
  }catch(err){$('confirmImportError').textContent=err.message;button.disabled=false;button.textContent='Confirmar importação'}
 };
}
function initBranchImport(){
 $('importBranches').hidden=!DECIDE;$('importBranches').onclick=openBranchImport;
}
