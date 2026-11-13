# Atualização v5.1.8

No celular, o Cutover Online usa um cabeçalho compacto, indicadores em duas colunas, rolagem dentro das tabelas e campos maiores para toque. O menu se fecha ao escolher uma seção. A Central mantém a lista de PDVs na horizontal e o botão de salvar ao alcance no checklist.

Envie o conteúdo do ZIP para a raiz do GitHub. Mantenha o Start Command `bash start.sh` e confirme a versão 5.1.8 em /healthz após o deploy.

# Atualização v5.1.7

A curva de evolução acumulada do Orion OK aparece abaixo da faixa de avanço e atenção do Dashboard. Alterne entre 7, 14 e 30 dias e consulte o total acumulado e as aprovações do dia. O PDF executivo inclui a curva dos últimos 14 dias na primeira página. A curva usa as datas identificadas de aprovação dos PDVs atualmente Orion OK, com saldo anterior ao período.

Envie o conteúdo do ZIP para a raiz do GitHub. Mantenha o Start Command `bash start.sh` e confirme a versão 5.1.7 em /healthz após o deploy.

# Atualização v5.1.5

O PDF executivo abre com os seis indicadores do Dashboard e gráficos de implantação, Orion OK e aprovações dos últimos 14 dias. A primeira página também destaca atrasos, pendências críticas e a prioridade de atuação. O comparativo de período, quando selecionado, aparece após o painel. Cobertura por GR e regional, versões e prioridades por filial e PDV ficam no detalhamento.

Envie o conteúdo do ZIP para a raiz do GitHub. Mantenha o Start Command `bash start.sh` e confirme a versão 5.1.5 em /healthz após o deploy.

# Atualização v5.1.4

A visão executiva mostra os seis indicadores logo abaixo do título. A faixa de avanço compara a implantação com o Orion OK e destaca os PDVs atrasados, os implantados que ainda precisam de aceite e as pendências críticas do recorte. As lojas prioritárias aparecem antes da análise do período, das versões e do avanço por regional.

Envie o conteúdo do ZIP para a raiz do GitHub. Mantenha o Start Command `bash start.sh` e confirme a versão 5.1.4 em /healthz após o deploy.

# Atualização v5.1.3

O Dashboard mostra **Pendências abertas** e quantas estão com prazo vencido. O total considera os registros abertos e em tratamento da Central de Pendências. Clique em **Ver pendências** para abrir a lista já filtrada.

Envie o conteúdo do ZIP para a raiz do GitHub. Mantenha o Start Command `bash start.sh` e confirme a versão 5.1.3 em /healthz após o deploy.

# Atualização v5.1.2

O card **PDVs pendentes** do Dashboard abre a lista paginada dos equipamentos sem implantação no recorte atual. A lista segue o formato de **PDVs implantados** e permite abrir cada equipamento na Central.

Envie o conteúdo do ZIP para a raiz do GitHub. Mantenha o Start Command `bash start.sh` e confirme a versão 5.1.2 em /healthz após o deploy.

# Atualização v5.1.1

O Dashboard mostra o total de filiais ativas no escopo do rollout em toda a rede. A busca por filial e os filtros continuam aplicados aos indicadores do recorte.

Na Central, Administrador e Gestor podem remover um PDV previsto pelo botão no cartão. A confirmação retira o número do plano e das contagens do rollout. Checklists salvos continuam no histórico da filial. Cada plano deve ter pelo menos um PDV previsto.

Envie o conteúdo do ZIP para a raiz do GitHub. Mantenha o Start Command `bash start.sh` e confirme a versão 5.1.1 em /healthz após o deploy.

# Atualização v5.1.0

- No Dashboard, clique em **PDVs implantados** para ver filial, equipamento, situação, versão e data cadastrada. O botão de cada linha abre o PDV na Central.
- Lojas que usam o plano padrão passam a ter os PDVs 01 a 05. Planos personalizados continuam com a numeração cadastrada.
- A distribuição no Dashboard e no PDF executivo exibe apenas versões registradas e calcula os percentuais sobre esses equipamentos.
- **Cronograma → Importar planilha** aceita Excel (.xlsx) ou CSV para Administrador e Gestor. Baixe o modelo, preencha Filial, PDV, Responsável e Prazo, confira a prévia e confirme. Início e Observações são opcionais. A importação pula combinações de filial e PDV já cadastradas e bloqueia a gravação se houver linhas inválidas.

Envie o conteúdo do ZIP para a raiz do GitHub. Mantenha o Start Command `bash start.sh` e confirme a versão 5.1.0 em /healthz após o deploy.

# Atualização v5.0.2 — Marca Cutover online

O logo da navegação, login e autenticação passa a mostrar apenas **Cutover online**, em azul claro e ciano. A marca é texto, sem dependência do carregamento da imagem anterior, e se adapta ao celular e ao menu recolhido. Os créditos de desenvolvimento no rodapé foram preservados.

Envie o pacote completo para a raiz do GitHub, mantenha `bash start.sh` no Render e confirme version 5.0.2 em /healthz após o deploy. Atualize com Ctrl+Shift+R. Nenhuma chave, dependência ou migração nova é necessária.

# Correção v5.0.1 — Excluir pendências

Envie o conteúdo completo do ZIP para a raiz do GitHub, substituindo os arquivos. Mantenha `bash start.sh` no Render e aguarde o commit ficar Live. Atualize a página com Ctrl+Shift+R e confirme version 5.0.1 em /healthz.

Entre como Administrador → Pendências → Excluir → confira filial/PDV e confirme. A ação apaga somente a pendência, preservando checklist e aceites, com auditoria. Se o registro tiver mudado, atualize a lista antes de excluir. Cancelar não apaga nada. Os demais perfis não têm permissão para excluir.

Nenhuma configuração nova é necessária. As funcionalidades da v5.0 estão mantidas. Publicação e validação no Neon/Render ainda devem ser realizadas após o envio.

# Atualização v5.0 — Rollout operacional e executivo

1. Extraia o ZIP. Envie **todo o conteúdo para a raiz do GitHub ALMDPSP/preload_app**, substituindo os arquivos e preservando static/ e templates/. Não envie o próprio ZIP nem crie uma pasta intermediária.
2. Render → serviço → Settings: Build Command `pip install -r requirements.txt`; Start Command **`bash start.sh`**. Preserve DATABASE_URL, SECRET_KEY, MFA_ENCRYPTION_KEY e as demais configurações existentes. Não repita a recuperação de senha.
3. Aguarde o commit novo ficar Live. A inicialização executa as migrações aditivas de ondas, responsáveis e impacto. Não é preciso reimportar lojas nem criar chaves.
4. Abra /healthz e confirme version 5.0. Recarregue o site com Ctrl+Shift+R e confira v5.0 no menu.
5. Na Central, selecione filial/PDV. Administrador/Gestor pode atribuir executor, validador, onda e prazo. Preencha Base e checklist e clique em **Salvar tudo**. O salvamento é manual e conjunto; pode guardar pendências para continuar depois.
6. Consulte Fila do dia e Ondas de rollout. No Dashboard/Relatórios selecione o período para comparação, PDF executivo e CSV operacional.
7. Execute os passos de VALIDACAO_PRODUCAO.md. Gestão de dados é exclusiva do Administrador. Faça um backup operacional e confira sua prévia; teste restauração em ambiente separado antes de usar em produção.

Os usuários e registros existentes são preservados pela atualização. Responsáveis/ondas começam em branco até serem atribuídos. O backup operacional não contém credenciais nem substitui backup nativo completo do Neon.

**Situação desta entrega:** 83 testes locais aprovados e interface validada nos quatro perfis. Produção Neon/Render pendente de validação após o deploy. O desempenho real depende também da instância e da conexão com o banco.

## Histórico das instruções de versões anteriores

Use as instruções v5.0 acima; o conteúdo abaixo é histórico.

## Atualização v4.5 — Central de Cutover

1. Extraia o ZIP e envie **todo o conteúdo para a raiz do GitHub**, preservando as pastas e substituindo os arquivos anteriores. Inclua especialmente static/central.js, static/central.css, app.py, release.py e templates.
2. Mantenha Build Command `pip install -r requirements.txt` e Start Command **`bash start.sh`** no Render. Aguarde o novo commit ficar Live.
3. Recarregue com Ctrl+Shift+R. O menu deve mostrar **v4.5**. /healthz informa version 4.5.
4. Abra **Central de Cutover**, busque a filial e selecione o PDV. Expanda Cadastro da filial e do PDV para editar implantação/versão/GR/regional. Clique em Salvar cadastro para gravar essa parte.
5. Abra o checklist existente ou clique em Iniciar PDV. Preencha as fases e aceites e clique em **Salvar checklist**, mesmo com pendências.
6. Use Editar número do PDV ou Adicionar PDV na própria central, com os rascunhos previamente salvos. No Dashboard, Atender na central abre a filial e o equipamento da prioridade.

Salvar cadastro e Salvar checklist são operações explícitas e independentes. Navegar não salva. Implantação declarada não concede GO. Perfis de acesso, usuários, lojas, checklists e históricos existentes são preservados.

Relatórios mantém o PDF executivo geral; o Dashboard também oferece o download. O PDF individual do checklist passa a abrir com um resumo por filial/PDV.

Nenhuma chave, dependência, migração ou reimportação é necessária.

## Atualização v4.4.1 — PDF executivo geral na aba Relatórios

1. Extraia o ZIP e envie todo o conteúdo para a raiz do GitHub, preservando as pastas e substituindo os arquivos anteriores. Inclua `rollout_executive_report.py`, `reports.py`, `static/reports.js`, `templates` e `release.py`.
2. No Render, mantenha Build Command `pip install -r requirements.txt` e Start Command **`bash start.sh`**. Aguarde o novo deploy ficar Live.
3. Recarregue o site com Ctrl+Shift+R e confira v4.4.1 no menu. A rota /healthz também informa version 4.4.1.
4. Abra **Relatórios → PDF executivo geral**. Aguarde a geração e confira o PDF nos downloads do navegador.

O PDF tem três páginas e considera todo o escopo ativo, independentemente dos filtros da consulta/CSV. Mostra o resumo da implantação, validação do cutover, versões, GR/regional, gráfico de aprovações vigentes e prioridades com filial/PDV. As listas recentes/prioridades são limitadas para manter a apresentação executiva; os totais abrangem o escopo completo.

Não são necessárias novas chaves, tabelas, dependências ou reimportação. O download não salva um checklist em edição.

## Atualização v4.4 — dashboard organizado e confirmação da versão

1. Extraia o ZIP. **Os arquivos já estão diretamente na raiz**: app.py, release.py, start.sh, templates/, static/ e os demais arquivos.
2. No GitHub ALMDPSP/preload_app → branch main → Add file → Upload files: envie o conteúdo extraído, preservando as pastas e substituindo os arquivos existentes. Não crie uma pasta preload_app-main dentro do repositório.
3. Antes do commit, confira que templates/index.html contém dashboard-clean.css e v4.4, static/rollout-base.js contém Resumo do rollout e release.py contém APP_VERSION = "4.4".
4. No Render, mantenha Build Command `pip install -r requirements.txt` e Start Command **`bash start.sh`**. Aguarde o novo commit ficar Live.
5. Abra https://cutover-orion-linx.onrender.com/healthz. A resposta deve incluir **"version":"4.4"**. Se mostrar outra versão ou nenhuma versão, o servidor ainda não está com este pacote.
6. Atualize o site com Ctrl+Shift+R. O menu mostra v4.4 e o painel abre em Resumo do rollout, com as abas GR e regionais e Validação do cutover.

Nenhuma chave, redefinição de senha ou reimportação de lojas é necessária. Os cadastros, checklists, permissões e edição da numeração do PDV da v4.3.1 continuam preservados.

## Atualização v4.3.1 — Rollout principal e edição de numeração

1. Extraia o ZIP e envie **o conteúdo da pasta preload_app-main** para a raiz do repositório GitHub, preservando as pastas. Inclua todos os arquivos, especialmente `pdv_renumber.py`, `static/rollout-priority.css`, `static/rollout-base.js`, `app.py`, `operations.py` e `templates`.
2. No Render, mantenha Build Command `pip install -r requirements.txt` e Start Command **`bash start.sh`**. Nenhuma chave nova é necessária. Não execute novamente a recuperação de senha.
3. Aguarde o deploy terminar e recarregue com Ctrl+F5. O painel principal passa a ser a Base de Rollout; expanda Validação do cutover para consultar os indicadores de aceite.
4. Abra Base de Rollout → Abrir cadastro → Alterar número no PDV desejado → informe um número livre → Confirmar alteração. Disponível para Administrador/Gestor. Salve mudanças no cadastro ou checklist antes dessa operação.
5. Use Cutover da filial na lista, ou Abrir cutover do PDV no cadastro, para continuar o preenchimento na loja correta. Os atalhos não salvam alterações do checklist.

A renumeração acompanha os registros da mesma filial, sem duplicar equipamentos ou perder o checklist. O número de destino não pode ter cadastro ou cutover existente. Uma edição concorrente exige reabrir o cadastro. As datas da última gravação dos checklists e os IDs das execuções são preservados; a correção fica auditada separadamente.

## Atualização v4.3 — Base de Rollout

Envie ao GitHub todos os arquivos do pacote, preservando as pastas, incluindo `rollout_base.py`, `static/rollout-base.js`, `static/rollout-base.css`, `app.py`, `executive_dashboard.py` e as páginas. Mantenha Start Command **`bash start.sh`** e Build Command `pip install -r requirements.txt`. As tabelas da Base são criadas automaticamente no Neon. Não são necessárias novas chaves.

Depois do deploy, abra Base de Rollout → Cadastrar informações → escolha a filial. Preencha GR, regional e os dados dos PDVs. Ao abrir o Dashboard, os novos indicadores refletem os cadastros. Inicialmente GR/regional não preenchidos e versões em branco aparecem como Não informado; nenhum valor da imagem de referência é importado automaticamente.

## Correção v4.2.2 — salvamento e retomada por PDV

Substitua no GitHub os arquivos deste pacote, incluindo `branch_progress.py` e os arquivos `static/branch-progress.*`. Mantenha Start Command **`bash start.sh`** e Build Command `pip install -r requirements.txt`. Não há novas chaves ou necessidade de reimportar filiais.

Depois do deploy, busque uma filial em Cutover: os cartões mostram os PDVs e seus checklists salvos. Abra um PDV, altere uma observação e salve. O sistema confirma a gravação e volta aos PDVs; use Abrir e editar para continuar. Checklists incompletos também podem ser salvos.

## Atualização v4.2 — desempenho e painel executivo

1. Substitua no GitHub todos os arquivos do pacote, incluindo `executive_dashboard.py` e `static/executive-dashboard.*`.
2. Mantenha Build Command `pip install -r requirements.txt` e Start Command **`bash start.sh`**.
3. A inicialização cria automaticamente o índice de auditoria e a tabela derivada de datas de aprovação, preservando cadastros, usuários e cutovers.
4. Após o deploy, abra o Dashboard, filtre uma UF e consulte os PDVs pelo indicador. As lojas agora aparecem em páginas de 25; listas de PDVs, em páginas de 40.

Nenhuma chave nova é necessária. Não redefina senhas nem reimporte filiais. O primeiro carregamento pode reconstruir o histórico de aprovação; os seguintes usam o índice e as versões já calculadas. Os tempos reais de produção devem ser conferidos após a atualização.

## Atualização visual v4.1

Substitua os arquivos do pacote no GitHub, preservando as pastas `templates` e `static`. Esta versão inclui novos estilos e scripts para o login, MFA e navegação. Mantenha **`bash start.sh`** como Start Command. Após o deploy, recarregue a página para carregar os novos estilos. Não é necessário redefinir senhas, alterar chaves ou importar as filiais novamente.

## Atualização v4.0

Envie ao GitHub todos os arquivos do pacote, preservando a estrutura de pastas. O Start Command continua **`bash start.sh`**, e o Build Command continua `pip install -r requirements.txt`. Não há novas variáveis obrigatórias. As tabelas de cronograma, pendências, metas e histórico são criadas automaticamente no Neon durante a inicialização.

Após o deploy, confirme Dashboard, Cronograma, Pendências e Histórico diário. As novas metas e o cronograma começam vazios; preencha os responsáveis e prazos reais. O histórico começa nesta versão e não reconstrói dias anteriores. O checklist continua salvando somente ao clicar em Salvar checklist. Consulte o README para os detalhes e o comando opcional de captura agendada.

# Atualização v3.1.1 — Relatório executivo macro em uma página

1. Atualize no GitHub o pacote completo. As alterações principais estão em `executive_report.py`, `dashboard.py`, `templates/index.html` e `static/dashboard.js`.
2. Faça o deploy no Render mantendo as variáveis e o Start Command `bash start.sh`. Nenhuma nova chave ou migração é necessária.
3. Atualize a página com Ctrl+F5. No Dashboard, use **Executivo resumido PDF**.

O arquivo agora apresenta somente indicadores gerais: PDVs previstos, Orion OK, pendentes, percentual, lojas completas, gráfico de execução e curva de evolução das aprovações vigentes. A geração do documento não percorre listagens de lojas/PDVs e o endpoint envia ao gerador somente o resumo calculado. Os cálculos continuam consultando os registros salvos para manter os totais corretos.

A listagem individual de lojas e máquinas foi removida do executivo. Não há apêndice de numeração a revisar; aparece apenas a quantidade de alertas. O detalhamento continua no Dashboard, em Ver PDVs e nos CSVs.

Validação: 40 testes automatizados. O executivo foi verificado com meta de 7.200 PDVs em 1.800 lojas: mantém uma página e não acessa os objetos de detalhamento de lojas/máquinas. O layout foi renderizado e conferido visualmente. Sem teste de tempo no Neon/Render do usuário.

# Atualização v3.1 — Quantidade de PDVs, aceites e usuários

1. Atualize no GitHub os arquivos completos deste pacote. As mudanças estão em `dashboard.py`, `templates/index.html`, `static/dashboard.js`, `static/checklist.js`, `static/users.js`, `static/branches.js`, `static/reports.js` e `static/branches.css`.
2. No Render, mantenha as variáveis atuais e Start Command **`bash start.sh`**. A recuperação de senha não precisa ser executada novamente.
3. Faça o deploy e atualize a página com Ctrl+F5.

## Mais de 4 PDVs por loja

Na tela Cutover, selecione a filial e clique em **+ Adicionar PDV à loja**. O mesmo formulário aparece no Dashboard em **Ajustar PDVs**. Disponível para Administrador e Gestor.

- **+ Adicionar próximo PDV** acrescenta um equipamento à lista sem remover os atuais; 01-04 passa para 01-05 e pode continuar crescendo.
- **Quantidade desejada → Aumentar até essa quantidade** acrescenta o necessário até o total informado.
- Se a loja usa números diferentes, edite a lista real. Para reduzir a quantidade, remova os números manualmente na lista.
- Confirme em **Salvar PDVs previstos**. A meta do Dashboard e do relatório executivo usa a lista salva, com limite de 50 equipamentos por filial.
- O cadastro do plano não apaga os cutovers e não cria automaticamente um checklist. Depois use **Iniciar cutover** e informe o número do novo PDV.

## Aceites na sequência

O aceite da retirada (Entrega do Linx / GO para formatação) está logo após os processos Linx, antes de instalar Orion. O aceite da operação está após instalação, testes e aceite da loja. O atalho **Aceites do cutover** apenas rola para a decisão dentro do checklist. A antiga aba separada foi removida. Operador/Consulta continuam sem permissão para aprovar GO, e os pré-requisitos continuam validados no servidor.

As observações das decisões são opcionais. Decisões e campos do checklist só são gravados ao clicar em **Salvar checklist**.

## Usuários como página

A gestão de usuários agora ocupa uma página no mesmo padrão dos demais módulos, com resumo de ativos/bloqueados/MFA pendente, pesquisa, tabela e **Novo usuário**. O cadastro abre na própria página. Confirmações de redefinição de senha e MFA continuam em janela específica. As restrições sobre a própria conta do Administrador permanecem.

Validação: 38 testes automatizados com SQLite, incluindo leitura e ampliação do plano 4 → 6, versão concorrente, preservação dos cutovers e perfis. Testes de interface para Administrador e Consulta confirmam cadastro de usuário em página, pesquisa e navegação, confirmação de MFA, aceites na ordem correta, bloqueio de GO sem pré-requisitos e adição do quinto/sexto PDV sem gravação automática do checklist. Sem deploy no Render ou conexão ao Neon do usuário.

# Atualização v3.0.1 — Recuperação de senha administrativa

Inclui `manage.py reset-password email` para recuperar uma conta administrativa existente, mantendo dados e Authenticator. Confira `RECUPERAR_SENHA_ADM.md`. Nenhuma recuperação automática foi adicionada ao `start.sh`. Use o comando somente quando necessário.

# Atualização v3.0 — Dashboard e relatório executivo por PDV

1. Atualize o conteúdo completo no GitHub. Inclua os novos `dashboard.py`, `executive_report.py`, `static/dashboard.js`, e os arquivos atualizados `app.py`, `branches.py`, `templates/index.html`, `static/branches.js`, `static/reports.js` e `static/branches.css`.
2. No Render, mantenha as variáveis existentes, Build Command `pip install -r requirements.txt` e Start Command `bash start.sh`. Nenhuma nova chave é necessária.
3. Faça o deploy. A tabela `ct_branch_pdv_plan` é criada automaticamente, sem apagar lojas, cutovers ou usuários.
4. Atualize a página com Ctrl+F5. O Dashboard passa a ser a página inicial; os módulos anteriores ficam no menu.

## Contagem

- Padrão: **4 PDVs por filial ativa**, com números **01, 02, 03 e 04**. Lojas a inaugurar e vínculos legados em revisão ficam fora do escopo de ativas abertas.
- Uma máquina = filial + número do PDV. Diferentes grafias numéricas, como 1, 01 ou PDV 1, são normalizadas. Só a execução mais recente entra; não se somam tentativas repetidas.
- **Orion OK**: todos os 11 processos concluídos e os dois GO com responsável/data. Sem cutover, em andamento, bloqueado, rejeitado e aguardando aceite permanecem pendentes.
- Se uma filial tiver outra quantidade/numeração, Administrador e Gestor usam **Ajustar PDVs**. Edite a lista real ou gere de 01 até a quantidade desejada. O tamanho da lista define a meta daquela loja. O cadastro verifica versão para evitar sobrescrever alterações de outra pessoa.
- Execuções com número não identificado ou fora do plano aparecem em Numeração para revisar e não entram no numerador/denominador. Corrija o plano ou refaça a execução com o número correto antes de considerá-las na meta.
- A alteração do plano não apaga os cutovers existentes. O checklist continua sendo gravado exclusivamente por Salvar checklist.

## Dashboard e executivo

Cartões de máquinas previstas, viradas e OK, pendentes e lojas completas; percentual; filtros por loja/UF; evolução das aprovações; tabela com cada filial e seus números de PDV; detalhamento da execução mais recente. A tabela pagina 25 lojas por vez.

**Relatório executivo PDF** inclui resumo, curva, critério de OK, lojas e números dos PDVs OK/pendentes e exceções de numeração. O CSV exporta uma linha por máquina planejada. Os filtros aplicados valem para os dois arquivos. Downloads exigem usuário autenticado.

A curva é uma visão dos PDVs que estão OK no momento, por data de aprovação obtida do histórico. Ela não representa fotos antigas do parque inteiro. Sem transição de aprovação identificável, a última gravação é usada como referência e o relatório informa a quantidade desses casos. Não são inventadas datas reais de virada. Mudanças de plano, novas tentativas, rejeições ou exclusões podem alterar esse recorte.

Validação: 35 testes automatizados com SQLite, incluindo 1.800 lojas ativas = 7.200 PDVs pendentes, deduplicação de numeração, última execução rejeitada, plano por loja, acesso por perfil, concorrência de versão, persistência, curva e PDF. Interface testada para Administrador e Consulta. PDF executivo renderizado e conferido visualmente com dados de demonstração. Não foi realizado deploy no Render nem conexão ao Neon do usuário.

# Atualização v2.9 — Aplicativo instalável e Relatórios

1. Atualize no GitHub o conteúdo completo deste pacote. Inclua os novos `reports.py`, `pwa.py`, `static/reports.js`, `static/pwa.js`, `static/sw.js` e ícones PNG, além de `app.py`, templates e demais arquivos estáticos.
2. No Render, mantenha as variáveis atuais, o Build Command `pip install -r requirements.txt` e o Start Command `bash start.sh`. Não há nova chave ou banco para configurar.
3. Faça o deploy e atualize a página com Ctrl+F5.

## Aplicativo

O botão **Instalar aplicativo** aparece no login e na conta conectada. Em navegadores compatíveis, abre a confirmação de instalação. Quando essa confirmação ainda não estiver disponível, mostra instruções. Em iPhone/iPad, abra pelo Safari e use Compartilhar → Adicionar à Tela de Início. A confirmação deve ser realizada no aparelho de cada usuário.

Nome: Cutover. Ícone próprio com checklist e seta. Abre em janela independente nos ambientes que suportam o modo standalone. O acesso continua exigindo a mesma conta e MFA; os dados são os mesmos do site. O aplicativo precisa de internet. Não são armazenados checklists, relatórios, respostas de API ou sessões em cache offline.

## Relatórios

Aba disponível a todos os perfis com acesso autenticado. O painel consulta somente os registros salvos, sem gravar preenchimentos pendentes.

- Cartões de concluídos, com pendências, rejeitados e filiais sem cutover.
- Situações detalhadas: Concluído, Pendente, Em andamento, Bloqueado, Aguardando aceite, Rejeitado e Sem cutover.
- Filtros por código/nome/PDV, situação e UF; paginação de 50 linhas; exportação CSV dos resultados filtrados.
- Detalhamento dos 11 processos e observações, além de atalhos para abrir a filial/execução.
- Concluído exige todos os processos e os dois GO com responsável e data. Aguardando aceite identifica checklist marcado sem liberação completa.
- Cada execução/PDV entra separadamente. Contagem de filiais usa lojas distintas. As filiais inativas e a inaugurar continuam identificadas. Os totais de processos incluem as execuções rejeitadas, conforme aviso na tela.

Validação: 31 testes automatizados com SQLite, incluindo regras de situação, dados salvos, acesso aos relatórios, rejeição/exclusão, manifesto, ícones e service worker. Interface verificada para Administrador e Consulta: filtros, detalhes, navegação, instalação simulada e preservação do salvamento manual. Sem conexão ao Neon ou deploy no Render do usuário; instalação em dispositivo real depende da publicação e do navegador utilizado.

# Atualização v2.8 — Busca na seleção, rejeição e exclusão de cutovers

1. Substitua no GitHub os arquivos pelo conteúdo completo deste pacote. Inclua o novo `static/cutover-actions.js`, além de `app.py`, `branches.py`, `pdf_report.py`, `templates/index.html` e os demais arquivos estáticos atualizados.
2. No Render, mantenha as variáveis atuais, Build Command `pip install -r requirements.txt` e Start Command `bash start.sh`.
3. Faça o deploy. A tabela adicional de rejeições é criada automaticamente; filiais, usuários e checklists existentes são preservados.
4. Use Ctrl+F5 para carregar os arquivos novos.

## Usar

- Em **Selecione a filial**, clique no próprio campo e digite código ou nome. Os resultados aparecem abaixo. Escolha por clique ou setas/Enter. Não há mais um campo separado de pesquisa. Só selecionar um resultado troca a filial; as proteções de alterações pendentes continuam disponíveis.
- Administrador e Gestor podem clicar em **Rejeitar cutover**, informar o motivo e confirmar. A execução fica bloqueada para edição, mas permanece disponível para consulta e download de PDF com o motivo registrado.
- O Administrador pode clicar em **Excluir cutover** e confirmar **Excluir e liberar para refazer**. A filial permanece e o botão **Iniciar cutover** permite refazer o checklist do zero, inclusive para o mesmo PDV. A exclusão não restaura os processos anteriores; baixe o PDF antes se precisar guardá-los. Os eventos de auditoria permanecem no banco.
- As ações verificam a versão para rejeitar solicitações desatualizadas. Gestor, Operador e Consulta não conseguem excluir nem pela API.
- Os campos do checklist continuam sendo gravados apenas ao clicar em **Salvar checklist**.

Validação desta revisão: testes automatizados de permissões, CSRF, versão desatualizada, motivo obrigatório, bloqueio da edição rejeitada, PDF, exclusão e nova execução; testes de interface de busca integrada (incluindo teclado, acentos e nenhum resultado), manutenção do salvamento manual, rejeição, cancelamento e confirmação da exclusão. Testes usam SQLite e simulação de interface. Não foi executado deploy no Render nem conexão ao Neon do usuário.

# Atualização v2.7 — Check, salvamento manual e pesquisa

1. Atualize o conteúdo completo deste pacote no GitHub, incluindo `templates/index.html`, `static/server.js`, `static/checklist.js`, `static/checklist.css`, `static/branches.js` e `static/branches.css`.
2. Faça o deploy no Render mantendo as variáveis e o Start Command `bash start.sh`.
3. Atualize a página com Ctrl+F5.

- Ícone de conclusão redesenhado e centralizado, com borda, foco de teclado e estado desabilitado.
- O preenchimento do checklist só é gravado ao clicar em **Salvar checklist**. Trocar de filial, trocar de execução, atualizar dados, sair e baixar PDF não fazem gravação automática.
- Ao navegar com alterações pendentes, Cancelar mantém o preenchimento. Confirmar descarta as alterações da tela. A página avisa também ao fechar ou recarregar a aba.
- PDF exige que o checklist esteja salvo. Após salvar com sucesso, o popup de download continua disponível.
- Edições feitas durante uma gravação permanecem pendentes para outro clique em Salvar checklist; não são enviadas em segundo plano.
- **Pesquisar filial** aparece abaixo do seletor. Aceita código, nome, cidade ou UF; ignora acentos e mantém a filial/cutover atual durante a busca.

Iniciar cutover continua criando uma execução, e os botões de cadastro/edição/importação de filiais mantêm suas próprias confirmações. O salvamento manual aqui se refere aos campos e processos do checklist.

Validação desta revisão: interface automatizada para Administrador e Consulta, edição sem gravação após o antigo intervalo automático, salvamento por clique, falha e nova tentativa, edições durante a requisição, PDF sem gravação, troca de filial/atualização/saída com cancelamento, descarte explícito e pesquisa sem alterar a seleção. Nenhuma alteração do backend ou das tabelas nesta revisão. Deploy no Render não executado.

# Atualização v2.6.1 — Painel único da filial

O bloco superior duplicado foi removido. O painel “Execução da loja” agora se chama “Filial deste cutover” e reúne a seleção da filial, do cutover e todos os botões atuais. O acesso a Filiais cadastradas continua nesse painel.

Atualize os arquivos deste pacote no GitHub e faça o deploy no Render. Mantenha as variáveis, o Build Command e o Start Command `bash start.sh`. Depois use Ctrl+F5 para atualizar a página.

Esta mudança é de interface. Mantém os cadastros, vínculos, importação, situação A inaugurar e exclusão administrativa da v2.6.

# Atualização v2.6 — Filiais a inaugurar e exclusão

1. Substitua no GitHub os arquivos pelo conteúdo completo deste pacote, incluindo o novo `branch_values.py`.
2. No Render, mantenha o Build Command `pip install -r requirements.txt` e o Start Command `bash start.sh`. Mantenha as variáveis atuais.
3. Faça o deploy. A coluna adicional é criada automaticamente, preservando filiais, usuários e cutovers existentes.
4. Atualize a página com Ctrl+F5. Abra **Filiais** e cadastre/edite usando **Ativa**, **Inativa** ou **A inaugurar**.
5. Na importação, a coluna Situação/Ativo aceita **A inaugurar**. Estado/UF aceita nomes completos ou siglas; por exemplo, São Paulo é convertido para SP. Confira a situação na prévia antes de confirmar.
6. Para excluir, entre como Administrador e clique em **Excluir**, depois confirme na janela. Se houver cutovers vinculados, a exclusão é bloqueada; use **Editar → Inativa** para preservar o histórico.

Lojas a inaugurar aparecem identificadas no cadastro, na pesquisa e no seletor de filiais. Elas permitem iniciar cutovers de preparação. A situação é independente da conclusão do checklist.

Importações permanecem em duas etapas, com confirmação, limite de 10 MB/10 mil linhas e preservação dos vínculos. Prévia gerada antes desta atualização deve ser analisada novamente. Os nomes dos 27 estados/DF são reconhecidos com ou sem acento.

Validação: 26 testes automatizados com SQLite e simulação dos parâmetros PostgreSQL; verificação da interface para Administrador e Consulta, com importação, paginação, situação A inaugurar, edição e confirmação de exclusão. Sem deploy ou teste no Neon do usuário. A planilha FILIAL.xlsx não estava disponível no ambiente desta revisão; os formatos foram validados com arquivos de teste.

# Atualização v2.5.1 - Revisão da inicialização e importação de filiais

1. Substitua os arquivos no GitHub pelo conteúdo completo deste pacote. Inclua `branch_import.py`, `static/branch-import.js` e o `requirements.txt` atualizado.
2. Mantenha as variáveis atuais no Render. Não há nova variável obrigatória.
3. No painel do serviço Render, em Settings → Build & Deploy, mantenha o Build Command `pip install -r requirements.txt` e altere o Start Command para:

   ```sh
   bash start.sh
   ```

4. Faça o deploy. A tabela que guarda as prévias de importação é criada automaticamente. Nenhuma filial, usuário ou cutover existente é apagado.
5. Abra a página e pressione Ctrl+F5 para carregar os arquivos novos.
6. Entre como Administrador ou Gestor e abra a aba **Filiais**. Clique em **Importar lojas** e baixe o modelo CSV dentro da janela.
7. Substitua as lojas de exemplo pela sua lista e envie `.xlsx` ou `.csv`. Código e nome são obrigatórios; cidade, UF e situação são opcionais. No Excel, use a primeira aba, com cabeçalho na primeira linha e códigos preferencialmente como texto.
8. Analise a prévia. Por padrão, somente novas lojas serão cadastradas. Escolha o modo de atualização se também quiser alterar os nomes/dados dos códigos já existentes.
9. Corrija possíveis erros e clique em **Confirmar importação**. A tela informa quantas lojas foram criadas/atualizadas. Use a pesquisa ou as páginas de 50 registros para consultar a lista.
10. Na aba Cutover, selecione a filial e clique em **Iniciar cutover**. Os vínculos antigos são mantidos, inclusive quando o nome da filial é atualizado pela importação.

Limites por envio: 10 MB, 10 mil linhas e 30 colunas. Se o arquivo for `.xls`, salve como `.xlsx`. Fórmulas devem ser convertidas para valores. A prévia expira em 20 minutos. Se os cadastros mudarem durante a revisão, analise novamente o arquivo.

As funções de checklist, PDF, usuários, perfis, senha e Authenticator continuam disponíveis. Para recuperar um Administrador existente, consulte o comando `python manage.py set-admin SEU_EMAIL_JA_CADASTRADO` no README.

## Revisão v2.5.1

- Inclua também `start.sh` e `init_db.py` deste pacote. Alterar apenas `render.yaml` não atualiza necessariamente um serviço criado manualmente; confira o Start Command no painel.
- Logs com etapas e duração, incluindo antes de carregar a aplicação.
- Migração de vínculos antigos em lote, preservando IDs e cadastros existentes.
- PostgreSQL: conexão com limite de 15 segundos, comandos com limite de 45 segundos e espera por bloqueios com limite de 8 segundos. Falhas interrompem a transação; a inicialização pode ser repetida após resolver a causa.
- A verificação `/healthz` usa limites menores e não carrega a sessão do usuário.
- O servidor respeita `WEB_CONCURRENCY`; usa um worker se essa variável estiver ausente.

O log enviado terminou em cancelamento manual depois de um build bem-sucedido. Ele não permite atribuir a demora a uma falha do código. O pacote melhora o desempenho da migração e permite identificar em qual etapa uma próxima tentativa demora. Não troque `SECRET_KEY`, `MFA_ENCRYPTION_KEY` ou `DATABASE_URL` durante esta atualização.

Validação: testes automatizados com SQLite, incluindo migração de 1.800 registros, repetição sem duplicação, rollback, autenticação, perfis, importação e PDF. A partida real do Gunicorn, os logs e a resposta HTTP de `/healthz` foram verificados com um worker. Os parâmetros de conexão PostgreSQL foram verificados com simulação; o ambiente de revisão não permitiu iniciar o PostgreSQL local. A conexão com seu Neon e o deploy no Render precisam ser verificados pelos próximos logs.
