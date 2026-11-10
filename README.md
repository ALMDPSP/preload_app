# Cutover Linx Agiliza → Orion · v5.0.1

Na aba **Pendências**, o Administrador encontra **Excluir** em cada registro. A confirmação identifica título, filial e PDV; Cancelar mantém o registro. A exclusão é permanente, exige a versão atual e fica registrada na auditoria. Checklist e aceites permanecem intactos. Gestor, Operador e Consulta não podem excluir pendências.

Atualize o pacote completo e mantenha `bash start.sh`. Não há nova chave, dependência ou migração nesta correção. A v5.0 permanece incluída no pacote.

# Cutover Linx Agiliza → Orion · v5.0

## Operação e gestão do rollout

Esta versão reúne cadastro, execução, responsáveis e ocorrências por filial e número de PDV. As instruções desta seção substituem os fluxos de salvamento descritos nas versões anteriores.

- **Salvar tudo:** na Central, grava o cadastro do PDV selecionado, seus responsáveis e o checklist aberto na mesma transação. Se houver conflito ou falha, nenhuma parte dessa operação é gravada. Pendências não impedem salvar; navegar não salva. Uma alteração feita enquanto a gravação está em andamento permanece como rascunho.
- **Executor e validador:** Administrador/Gestor define os usuários por PDV, a onda e a data prevista. O executor pode preencher conforme seu perfil. Havendo validador indicado, os aceites ficam restritos a ele; o Administrador mantém a possibilidade de intervenção. Operador não concede aceite. Consulta continua somente leitura. Cadastros existentes começam sem responsáveis/ondas até serem atribuídos.
- **Fila do dia:** exibe filial, PDV, responsáveis, prazo e situação, com filtros para meus PDVs, atrasados, aguardando aceite e concluídos. Abertura direta na Central e paginação de 40 equipamentos.
- **Ondas de rollout:** períodos, situação administrativa, justificativa de atraso e avanço. É possível vincular todos os PDVs previstos de uma filial à onda, preservando responsáveis e datas específicas. Marcar a onda como concluída não concede aceite aos equipamentos.
- **Ocorrências:** registre responsável, prazo, criticidade, impacto e resolução, inclusive na própria Central. Pendências abertas ajudam a ordenar as prioridades.
- **Dashboard:** mantém a Base de Rollout como leitura principal e separa implantação declarada de validação Orion. Acrescenta planejado, validado, pendente, atrasos, aceites e ausência de responsáveis. O período inicial é a semana atual, de segunda a domingo, comparada ao intervalo anterior de igual duração.
- **Relatórios:** o PDF executivo com período tem quatro páginas, com comparação e ondas prioritárias, seguido do panorama atual. A geração sem período mantém três páginas. O CSV operacional detalha filial/PDV, responsáveis, onda, prazo, situação, ocorrências e impacto; inclui equipamentos com prazo ou última gravação no período. O PDF individual continua disponível.
- **Gestão de dados:** exclusiva do Administrador, oferece backup operacional, prévia de restauração e conferência de integridade/totais.

### Critérios dos indicadores

Implantação declarada e Orion OK são medidas distintas. A comparação considera a posição atualmente salva e as datas identificadas dos registros que continuam válidos; não reconstrói fotografias históricas. Datas de implantação ausentes não são estimadas pela última edição. Atrasos e alertas gerais representam a posição atual. Os filtros/períodos e critérios aparecem no painel e nos relatórios.

### Backup e restauração

O arquivo operacional contém lojas, planos de PDV, execução, auditoria e gestão do rollout. **Não contém senhas, segredos MFA, sessões nem chaves e não recupera usuários ou acesso.** Referências de responsáveis são remapeadas para contas existentes compatíveis; vínculos indisponíveis são informados na prévia. A assinatura exige a mesma SECRET_KEY, que deve ser preservada separadamente.

A restauração substitui os dados operacionais, preserva as contas existentes e exige prévia, o mesmo arquivo e digitação de RESTAURAR. A prévia vence em dez minutos e fica inválida se os dados ou os perfis mudarem. Falhas revertem a transação. Limites: 10 MiB compactados, 32 MiB descompactados, 200 mil registros e verificação conservadora de tamanho antes da exportação. Para bases maiores ou recuperação completa do PostgreSQL, mantenha também backup nativo do banco. Teste a restauração primeiro em ambiente separado, com versão compatível; use janela de manutenção e todas as instâncias na v5.0 para uma restauração de produção.

### Atualização e validação

Envie o pacote completo à raiz do GitHub. Mantenha `pip install -r requirements.txt` e **`bash start.sh`**. Não há novas dependências ou chaves. A inicialização adiciona as tabelas de ondas e responsáveis e a coluna de impacto; dados existentes não são reimportados. Confira v5.0 no menu e em `/healthz` após o deploy.

Validação local: **83 testes Python aprovados**, incluindo conflitos concorrentes, permissões, reversão de salvamento/restauração e relatório; interface integrada ao Flask em banco temporário nos quatro perfis; quatro páginas do PDF renderizadas e conferidas. PostgreSQL local indisponível por restrição de sockets do ambiente. **Neon/Render de produção não acessados nem validados nesta entrega.** Siga `VALIDACAO_PRODUCAO.md` após publicar.

## Histórico de versões anteriores

As seções abaixo registram o comportamento das versões antigas; para instalar e operar a v5.0, siga as orientações acima.


Consulte `ATUALIZAR_RENDER.md` para atualizar o Start Command para `bash start.sh` e acompanhar os novos logs de inicialização.

## Central de Cutover e leitura executiva — v4.5

A navegação **Central de Cutover** reúne a operação em uma tela. Busque a filial, selecione o PDV na lateral e preencha o cadastro e o checklist. Em telas menores, os cartões de PDV ficam em uma faixa horizontal.

- **Cadastro da filial e do PDV:** GR, regional, implantação declarada, versão, data e observações, em um bloco expansível. Salvar cadastro grava somente a filial e o PDV selecionado na Base; mantém os dados dos outros PDVs e não salva o checklist. Recarregar cadastro permite resolver conflitos sem descartar o checklist aberto.
- **PDVs:** selecionar um equipamento abre sua execução salva. Um PDV sem checklist é selecionado sem criação automática; Administrador/Gestor pode clicar em Iniciar PDV. Nova filial, edição da filial e ajuste da quantidade continuam no contexto da central (formulários auxiliares sobre a mesma página).
- **Numeração:** Editar número do PDV fica na central. Exige salvar os rascunhos antes; migra os registros e o histórico conforme a proteção transacional anterior. PDVs fora do plano continuam acessíveis para consulta/edição do checklist, com aviso para ajustar o plano antes de editar seu cadastro.
- **Checklist e aceites:** fases recolhíveis, observações opcionais fechadas quando vazias e GO da retirada / aceite Orion na sequência dos processos. Atalhos rolam até os aceites do PDV atual. A aba separada de aceites fica oculta para evitar duplicação.
- **Salvamento manual:** Salvar checklist mantém o fluxo de gravação e retomada com pendências. Se houver alterações no cadastro, salve primeiro o cadastro pelo botão próprio. Trocas de filial/PDV pedem confirmação antes de descartar rascunhos; sair/fechar a página também protege o preenchimento.
- **Leituras concorrentes:** a última seleção de PDV prevalece, mesmo quando respostas chegam fora de ordem. Uma leitura iniciada antes de novas edições não substitui o rascunho digitado.

No Dashboard, a faixa de leitura executiva separa o percentual implantado do validado e mostra os implantados ainda sem Orion OK. A prioridade destaca ocorrências críticas, prazos vencidos ou validações pendentes, conforme os dados salvos. Até três lojas com atenção têm atalho Atender na central; o PDF executivo também fica acessível no cabeçalho. Os totais e as regras de implantação/aceite não mudam.

O PDF executivo mantém três páginas e acrescenta a prioridade de atuação e a diferença entre implantação e validação. O PDF individual do PDV abre com resumo da loja/equipamento, situação, cadastro de implantação/versão quando disponível, progresso por fase, aceites e próximo passo. Em seguida mantém o checklist detalhado, observações e referências. Datas são apresentadas no formato brasileiro; fontes incorporadas e blocos agrupados melhoram a leitura.

**Permissões:** Administrador/Gestor inicia, ajusta PDVs e concede aceites; Operador preenche cadastro do PDV e checklist, sem alterar GR/regional ou dar GO; Consulta permanece somente leitura. Execuções rejeitadas continuam bloqueadas; exclusão continua exclusiva do Administrador.

**Atualização:** substitua o pacote completo, incluindo `static/central.js`, `static/central.css`, `static/server.js`, `static/checklist.js`, `static/branches.js`, `static/rollout-base.js`, `templates`, `pdf_report.py`, `rollout_executive_report.py`, `app.py` e `release.py`. Mantenha `bash start.sh`. Não há nova chave, dependência ou tabela. Validação local: 72 testes Python, verificações DOM de administrador/consulta (cadastro, renumeração, início, aceite, rascunhos e respostas fora de ordem) e renderização dos PDFs. Render/Neon de produção não foi alterado nesta entrega.

## PDF executivo geral em Relatórios — v4.4.1

Na aba **Relatórios**, o botão **PDF executivo geral** gera um consolidado dos dados salvos de todas as filiais ativas e abertas no escopo. Os filtros da lista/CSV não alteram esse PDF; isso aparece informado na tela. Perfis Administrador, Gestor, Operador e Consulta podem baixar, mantendo o acesso autenticado.

O relatório contém três páginas:
1. **Visão executiva:** PDVs previstos, implantados e pendentes; lojas atualizadas; avanço do parque; versões instaladas; PDVs Orion OK, pendentes de validação e lojas completas.
2. **Cobertura e evolução:** avanço por GR/regional, até seis grupos priorizados por PDVs sem implantação e demais grupos consolidados; gráfico dos PDVs atualmente Orion OK por data de aprovação nos últimos 14 dias; aprovações vigentes dos últimos sete dias.
3. **Atenção e atualizações:** totais de ocorrências abertas/críticas, PDVs atrasados e lojas com atenção; até quatro lojas prioritárias com seus números de PDV; até cinco registros atualizados recentemente de cutover, implantação e GR/regional; critérios e qualidade do cadastro.

Todos os grupos e versões entram nos totais. As listas são limitadas e agrupadas para manter o documento executivo, com três páginas e sem carregar o checklist de cada loja. Registros recentes representam a última gravação por registro, não uma listagem de todos os eventos de auditoria. O gráfico de aprovações não é uma fotografia histórica do parque e exclui datas estimadas. A implantação declarada não substitui os aceites do cutover.

A geração ocorre ao clicar no botão, consulta os dados atuais e inicia o download; não salva mudanças abertas no checklist, não altera usuários e não grava o PDF no banco. A resposta não é armazenada em cache. Falhas são exibidas sem deixar o botão bloqueado. O relatório usa a marca ALM e fontes incorporadas do ReportLab já instalado. O módulo de geração é carregado somente no download para não aumentar o trabalho de inicialização do serviço.

**Atualização:** substitua todos os arquivos do pacote, especialmente `rollout_executive_report.py`, `reports.py`, `static/reports.js`, `templates` e `release.py`. Mantenha Start Command **`bash start.sh`**. Nenhuma dependência, chave ou tabela nova é necessária. Validação local: 70 testes Python, fluxos DOM de administrador/consulta e renderização das três páginas, inclusive com muitos grupos e versões.

## Dashboard organizado — v4.4

O painel tem três visões, com apenas uma aberta por vez:

- **Resumo do rollout** (inicial): quatro indicadores — PDVs previstos, implantados, pendentes e lojas atualizadas —, gráfico do avanço do parque, versões instaladas e até cinco regionais por avanço.
- **GR e regionais**: tabelas completas com lojas previstas, atualizadas e percentual. O grupo Não informado mantém os cadastros incompletos nos totais.
- **Validação do cutover**: Orion OK, pendências operacionais e consulta por filial/PDV. As análises mais extensas ficam em Análise detalhada do cutover; CSV e PDF continuam sendo relatórios de validação.

As três visões usam o mesmo filtro de loja/UF. Trocar de visão não faz nova consulta nem salva checklists. O menu Minha conta reúne os acessos administrativos, instalação, senha e saída. A aba Base de Rollout e seus botões Alterar número, Cutover da filial e Abrir cutover do PDV permanecem disponíveis com as mesmas permissões e salvamento explícito.

**Confirmação da publicação:** o menu mostra v4.4; a resposta de `/healthz` inclui `"version":"4.4"` e o cabeçalho HTTP X-App-Version informa a versão servida. A inicialização registra a versão nos logs. A confirmação depende de o Render efetivamente receber o pacote atualizado; não é feita por esta entrega local.

**Formato do ZIP:** os arquivos estão diretamente na raiz, sem pasta preload_app-main intermediária. Extraia e envie app.py, release.py, templates, static e os demais arquivos para a raiz do GitHub, substituindo os existentes. Não envie a pasta inteira para dentro de outra pasta do repositório. Mantenha Start Command `bash start.sh`; não há novas chaves, dependências ou migrações nesta atualização.

Validação: testes Python da aplicação e testes DOM de administrador/consulta, abas, teclado, filtros, renumeração, navegação e salvamento manual. Produção Render/Neon não acessada por esta entrega.

## Dashboard principal e numeração dos PDVs — v4.3.1

O Dashboard abre com a **Base de Rollout como visão principal**: percentual do parque implantado, PDVs previstos/implantados/pendentes, lojas previstas/atualizadas e avanço das lojas, além da distribuição por versão, GR e regional. Os filtros de loja e UF continuam valendo. Os indicadores de aceite, Orion OK, processos, evolução e pendências operacionais ficam na seção expansível **Validação do cutover**, inicialmente recolhida. CSV e PDF de validação estão nessa seção.

Na Base de Rollout, **Cutover da filial** abre a loja já selecionada e mostra seus PDVs. Dentro do cadastro, **Abrir cutover do PDV** abre a execução existente; se não houver execução, Administrador/Gestor recebe o formulário de início com o PDV preenchido, sem criação automática. Operador/Consulta acessam as execuções conforme suas permissões.

Administrador e Gestor podem usar **Alterar número** no cadastro de cada PDV. A confirmação troca a identificação nos PDVs previstos, no cadastro da implantação, nos cutovers existentes (incluindo execuções históricas), no cronograma e nas pendências da mesma filial. Os IDs, processos, aceites, observações e datas da última gravação dos checklists são preservados; a alteração tem auditoria própria. Nenhuma outra filial é alterada. O destino deve ser um número livre entre 1 e 9999. Para adicionar equipamentos, continue usando Ajustar PDVs; renumerar não acrescenta equipamentos.

A alteração é transacional, verifica versões e bloqueia destinos com registros existentes. Uma tela antiga deve ser reaberta se houver conflito. Salve o cadastro da Base antes de renumerar ou abrir seus atalhos; salve o checklist em edição antes de renumerar. Os atalhos não gravam o checklist. Os critérios de implantação e aceite permanecem distintos.

Atualize o pacote completo, especialmente `pdv_renumber.py`, `app.py`, `operations.py`, `static/rollout-base.js`, `static/rollout-priority.css` e `templates`. Start Command: **`bash start.sh`**. Não há novas dependências, chaves ou tabelas nesta versão. Validação local: 66 testes Python e verificações DOM dos fluxos de administrador/consulta, navegação, renumeração e salvamento manual; ambiente Neon/Render não executado localmente.

## Base de Rollout e indicadores gerais — v4.3

Nova aba **Base de Rollout**, com cadastro e edição por filial. GR e regional são dados da filial; situação declarada, versão instalada, data opcional e observações opcionais são registradas individualmente por número de PDV. A quantidade e a numeração vêm da lista de PDVs previstos, ajustável na aba Filiais. O cadastro usa as lojas existentes e não cria lojas ou equipamentos duplicados.

Administrador e Gestor podem alterar GR, regional e os dados dos PDVs. Operador pode registrar implantação/versão/data/observações; Consulta somente lê. Salvamento próprio explícito, proteção contra edições concorrentes e histórico de alterações. O salvamento da Base não grava um checklist aberto, não emite GO e não muda as regras de aceite.

O dashboard inclui PDVs rolloutados, percentual atualizado dos PDVs, lojas atualizadas, avanço percentual das lojas, distribuição por versão instalada, avanço por GR e por regional. Os grupos mostram lojas previstas, atualizadas e percentual, com os PDVs esperados/implantados como apoio. Os mesmos filtros de loja/UF do painel delimitam os novos indicadores.

**Critérios de contagem:**
- PDV previsto: número no plano de uma filial ativa, aberta e sem cadastro a revisar, dentro dos filtros do dashboard.
- PDV rolloutado/implantado: situação Implantado registrada na Base **ou** Orion OK no checklist salvo. A mesma máquina (filial + PDV) conta uma única vez.
- Loja atualizada: pelo menos um PDV implantado. É diferente de Loja completa, que continua exigindo todos os PDVs Orion OK.
- Distribuição por versão: apenas PDVs implantados. A categoria Não informada mantém visíveis os equipamentos sem versão preenchida.
- GR/regional não preenchidos: grupo Não informado; a filial permanece no denominador. Percentual = lojas atualizadas / lojas previstas daquele grupo; denominador zero resulta em 0%.

A Base lista filiais fora do escopo (inativas, a inaugurar ou a revisar) para consulta/cadastro, mas elas não entram no resumo executivo ativo. Registros de PDVs retirados do plano ficam preservados e deixam de compor os totais atuais. Os indicadores de histórico diário e Orion OK mantêm os critérios anteriores de aceite, não sendo substituídos pela declaração de implantação.

**Atualização:** envie todos os arquivos ao GitHub, incluindo `rollout_base.py`, `static/rollout-base.*` e `templates`. Mantenha `pip install -r requirements.txt` no Build Command e **`bash start.sh`** no Start Command. As duas tabelas novas são criadas automaticamente na inicialização. Nenhuma nova dependência ou chave é necessária; cadastros, logins e checklists existentes são preservados. O logo ALM e as otimizações da versão anterior continuam ativos.

## Exibição do logo — v4.2.4

O logo ALM tem espaço fixo no menu compartilhado por todas as páginas, sem encolher em telas baixas. O menu compacto mantém a identificação ALM. Login, ativação de senha, Authenticator e recuperação também exibem a marca. Uma alternativa em texto (ALM / Expansão de TI / Cutover online) permanece visível enquanto a imagem não carrega ou em caso de falha.

Atualize todos os arquivos do pacote, incluindo `static/brand-logo.js`, `static/alm-brand.css`, `static/alm-expansao-cutover.png` e `templates`. Mantenha `bash start.sh`. Nenhuma alteração de banco ou chave é necessária.

## Identidade ALM — v4.2.3

O logo da Drogaria São Paulo foi retirado do menu e do login, substituído pela imagem ALM / Expansão de TI / Cutover online, sem o símbolo de colchetes. O arquivo utilizado é `static/alm-expansao-cutover.png`, com fundo transparente, e sua apresentação é definida em `static/alm-brand.css`. O mesmo nome identifica a verificação de acesso. As cores e funções da versão anterior foram preservadas. Atualize os arquivos do pacote no GitHub; o Start Command continua `bash start.sh`.

## Salvar, localizar e continuar por PDV — v4.2.2

Ao selecionar uma filial na aba Cutover, o sistema apresenta os PDVs previstos e as execuções existentes. Cada cartão informa situação, processos marcados, última gravação e responsável. PDVs sem execução aparecem como Não iniciado; os demais têm Abrir e editar (ou consulta, conforme o perfil/rejeição). A lista Todas as execuções preserva o acesso ao histórico e a outras execuções da mesma filial/PDV. Registros fora da numeração prevista aparecem identificados, sem desaparecer.

**Salvar checklist** confirma a gravação no servidor mesmo quando o preenchimento está incompleto. Após a confirmação, o editor é recolhido e a tela retorna aos PDVs da filial, com mensagem de sucesso e opções para ver os PDVs, continuar editando ou baixar o PDF. O PDF é opcional; não é necessário baixá-lo para manter os dados salvos. Uma falha/conflito mantém as alterações no editor. Novas alterações feitas durante um salvamento continuam exigindo outro clique em Salvar checklist.

O botão Voltar aos PDVs permite sair do editor e pede confirmação antes de descartar alterações não salvas. Ao tentar iniciar um PDV já existente, a interface abre o checklist salvo para continuar. Não é preciso excluir um checklist concluído ou parcial para editar seus campos; permissões, bloqueio de execuções rejeitadas, pré-requisitos GO e controle de versão continuam vigentes.

Atualize os arquivos do pacote, incluindo `branch_progress.py`, `static/branch-progress.js`, `static/branch-progress.css` e os demais arquivos alterados. Mantenha `bash start.sh` no Render. Não há nova chave, dependência ou migração de dados nesta correção.

## Paleta Drogaria São Paulo — v4.2.1

Login, MFA, navegação e dashboard usam vermelho, azul-claro, azul-escuro e superfícies neutras, tomando como referência a marca publicada pelo Grupo DPSP: https://www.grupodpsp.com.br/marcas/ . O arquivo `static/drogaria-sao-paulo.png` é o logo publicado nessa página, sem alteração. Vermelho de referência `#FB363D`, azul-claro `#A8DDEB` e azul-escuro `#242735`; ações usam vermelho mais escuro (`#CE2431`) para melhorar a leitura. São adaptações de interface, sem substituir um manual de identidade visual corporativo. O verde permanece semântico para conclusão; amarelo indica pendência/atenção. Gráficos de evolução usam azul.

Não houve alteração de regras de aprovação, perfis ou banco. O vínculo nominal a um analista validador é uma sugestão de próxima evolução, ainda não implementada nesta atualização de cores. A atualização mantém o carregamento otimizado e o salvamento manual. Envie os arquivos ao GitHub e mantenha `bash start.sh` no Render. Não são necessárias novas chaves.

## Dashboard executivo e carregamento — v4.2

O dashboard abre com uma única consulta principal, trazendo resumo executivo e 25 lojas por página. As listas de PDVs e as outras páginas carregam quando solicitadas; o cadastro de filiais deixa de concorrer com o painel na abertura. Os números continuam vindo dos registros salvos, sem cache de totais entre usuários ou salvamento automático do checklist.

A nova leitura executiva inclui estágio de todos os PDVs, lojas sem execução/com execução aberta/completas, aprovações vigentes dos últimos sete dias, volume por UF, prazos vencidos e pendências críticas. A lista de atenção prioriza pendências críticas, PDVs atrasados e demais ocorrências. Os indicadores respeitam os filtros de loja/UF; metas semanais e alertas globais continuam identificados como globais. Datas legadas estimadas não entram na contagem dos últimos sete dias.

O cálculo passou a usar um índice por filial, eliminando a passagem repetida por todas as execuções. Datas de aprovação são reaproveitadas em uma tabela derivada vinculada à versão do cutover; novas versões invalidam esse reaproveitamento. Novos índices e a tabela derivada são criados na inicialização. Não são alterados os dados do checklist ou os aceites.

Arquivos públicos não abrem conexões no Neon. CSS, JavaScript e ícones têm cache de navegador com versão; páginas privadas e APIs mantêm `no-store`. Respostas JSON maiores usam gzip quando aceito pelo navegador. Dentro de uma requisição, os acessos ao PostgreSQL reutilizam a conexão e preservam os commits/rollbacks e limites de tempo de cada operação; a conexão é encerrada ao final da requisição.

**Teste local sintético (1.800 lojas, 7.200 PDVs):** mediana do cálculo de aproximadamente 1,11 s para 0,31 s; JSON completo de cerca de 4,38 MB para 34 KB no resumo paginado. Essa comparação é de CPU e tamanho de resposta em SQLite local. Não é uma medição do Render/Neon nem uma garantia de tempo em produção. O primeiro cálculo pode precisar reconstruir datas de aprovação; os seguintes reaproveitam as versões válidas.

Atualize todos os arquivos do pacote no GitHub, preservando as pastas. Mantenha **`bash start.sh`** no Start Command e `pip install -r requirements.txt` no Build Command. Não há nova dependência nem chave obrigatória. Se alterar arquivos estáticos em versões futuras, atualize o identificador `?v=4.2` nas páginas para renovar o cache. O PDF executivo permanece macro, de uma página.

## Identidade visual — v4.1

Login com painel de apresentação em verde petróleo, formulário redesenhado e botão Mostrar/Ocultar senha. O mesmo padrão foi aplicado ao MFA, à ativação de senha e aos códigos de recuperação. Menu com ícones vetoriais consistentes, grupos de navegação e opção de recolher no computador; no celular, o menu abre pelo botão Menu e fecha após selecionar uma página. A preferência de menu compacto é guardada somente no navegador, sem dados de acesso.

Dashboard, tabelas, filtros, formulários, caixas de diálogo, marcações do checklist e barra de salvamento seguem a nova identidade visual, com estados de foco e suporte a movimento reduzido. Todos os recursos anteriores permanecem; nenhuma alteração no banco, nas permissões ou no salvamento manual é necessária para esta atualização visual.

Atualize os arquivos do pacote no GitHub, incluindo `static/auth-design.css`, `static/auth-design.js`, `static/design.css` e `static/design.js`. Mantenha o Start Command **`bash start.sh`**. Não há novas dependências ou variáveis obrigatórias.

## Gestão profissional do rollout — v4.0

- **Dashboard acionável:** clique nos cartões para ver os PDVs correspondentes; metas semanais, atrasos de cronograma e pendências abertas têm atalhos próprios. Os filtros de loja/UF valem para o parque; metas e alertas são identificados como visão global.
- **Cronograma:** responsável, início previsto, prazo e observações por filial/PDV. A conclusão vem do checklist salvo e dos aceites. Datas antigas sem auditoria são identificadas como referência estimada. Administrador e Gestor podem planejar; demais perfis consultam.
- **Pendências:** filial/PDV, prioridade, responsável, prazo, tratamento e resolução obrigatória ao encerrar. Administrador, Gestor e Operador registram; Consulta somente lê. Resolver pendência não marca processos nem emite GO.
- **Histórico diário:** gráfico, comparativos semanais/mensais, consulta por período e CSV. O dia atual é provisório; dias passados permanecem preservados. Variações são líquidas entre registros, podem ser negativas e não representam volume bruto de instalações. Datas-base aparecem nos comparativos; sem base, o sistema mostra “—”.
- **Checklist guiado:** cinco etapas, próxima ação, acesso ao impedimento e aviso de alterações não salvas. O botão **Salvar checklist** continua sendo o único que grava alterações no checklist.
- **Interface:** indicadores de carregamento, estados vazios, foco acessível, navegação e adaptação para celular.

### Atualizar no Render

Substitua no GitHub os arquivos desta versão (incluindo `operations.py`, `static/operations.js`, `static/guided.js` e `static/professional.*`). Mantenha o Build Command `pip install -r requirements.txt` e o Start Command **`bash start.sh`**. A inicialização cria as novas tabelas sem apagar usuários, filiais ou cutovers existentes. Não há novas dependências nem variáveis de ambiente obrigatórias. Não coloque novamente o comando temporário de recuperação de senha no Start Command.

### Como o histórico é registrado

Os consolidados começam a partir da instalação desta versão. Consultas do dashboard global, abertura da visão operacional e alterações salvas de filiais/PDVs/cutovers atualizam o dia corrente no horário de São Paulo. Ao mudar o dia, o último registro capturado do dia anterior fica preservado com seu horário; isso não garante uma captura exatamente à meia-noite. Dias sem uso/captura ficam ausentes, sem preenchimento estimado. O gráfico usa as datas reais dos registros disponíveis.

Para uma captura diária mesmo sem usuários conectados, pode-se configurar um agendador externo no mesmo banco/ambiente com `python manage.py snapshot-rollout`. Esse agendamento não é criado pelo pacote; o histórico durante o uso funciona sem ele. O comando altera apenas o consolidado atual. Não troque o Start Command do serviço web para esse comando.

Os registros usam versão para impedir que edições concorrentes sobrescrevam alterações silenciosamente. Se outro usuário salvar antes, atualize a tela. Metas, cronograma e pendências têm salvamentos próprios e não gravam o checklist aberto. O relatório executivo continua macro, em uma página, sem listar todas as lojas.

## Executivo macro — v3.1.1

O botão **Executivo resumido PDF** gera uma página com PDVs previstos/Orion OK/pendentes, percentual, lojas completas, gráfico de execução do parque e curva das aprovações vigentes. Não há listagem individual de filiais, máquinas ou exceções. Os totais usam os mesmos filtros e critérios do dashboard. O detalhamento permanece na tela e no CSV.

## Mais PDVs, aceites na sequência e página de usuários — v3.1

Na tela do Cutover, escolha a filial e use **+ Adicionar PDV à loja**. No Dashboard, **Ajustar PDVs** abre o mesmo cadastro. Use **+ Adicionar próximo PDV** para passar de 4 para 5, 6 ou mais; ou informe a quantidade e clique em **Aumentar até essa quantidade**. Os números existentes são mantidos. Salve em **Salvar PDVs previstos** para atualizar a meta. O limite é 50 PDVs por filial; números reais diferentes podem ser editados na lista.

As decisões agora aparecem no checklist: **Entrega do Linx** após os processos de retirada e antes da instalação do Orion; **Aceite do Orion** após instalação, testes e aceite da loja. O menu **Aceites do cutover** leva até a primeira decisão no próprio fluxo. As validações e o salvamento pelo botão **Salvar checklist** permanecem.

**Usuários e acessos** agora abre uma página no mesmo padrão de Filiais, Relatórios e Dashboard, com cartões, pesquisa, lista de permissões e formulário de cadastro. **Novo usuário** ou o atalho do cabeçalho abre o formulário na página. Redefinição de senha/MFA mantém uma confirmação específica. A área é exclusiva do Administrador e continua protegida pela API.

## Recuperação de senha — v3.0.1

Use `python manage.py reset-password email-do-administrador` em terminal interativo ou consulte `RECUPERAR_SENHA_ADM.md` para recuperação sem Shell. O comando preserva dados e MFA, reativa a conta admin existente, invalida sessões e exige senha definitiva no próximo acesso. Alterar `ADMIN_PASSWORD` não troca senhas existentes.

## Dashboard por loja e número de PDV — v3.0

A página inicial agora é **Dashboard**. A meta padrão é **4 PDVs (01, 02, 03, 04) por filial ativa e aberta**. Filiais inativas, a inaugurar e cadastros legados que exigem revisão não entram nesse recorte. Os demais módulos continuam no menu.

Cada máquina é identificada por filial + número do PDV. 1, 01 e PDV 1 representam a mesma máquina; a execução mais recente prevalece, sem somar repetidas tentativas. **Orion OK** exige todos os processos concluídos e GO da retirada/operação com responsável e data. Todos os demais casos, inclusive sem cutover e rejeitado, contam como pendentes.

**Ajustar PDVs**, disponível para Administrador/Gestor, permite informar a lista real de números por loja, entre 1 e 50 equipamentos. A quantidade da meta corresponde ao tamanho dessa lista. Números observados fora dela ou não identificados geram alertas e ficam fora das métricas até ajuste. Cutovers existentes não são apagados ao mudar o plano.

O dashboard exibe PDVs previstos, virados e OK, pendentes, percentual e lojas completas. Os filtros de loja/UF valem para os totais e para o **Relatório executivo PDF**. A tabela e o CSV mostram os números OK e pendentes por filial. O PDF executivo apresenta somente a visão macro com indicadores e gráficos.

A curva mostra as aprovações dos **PDVs atualmente OK**, com transições identificadas no histórico. Quando não há histórico suficiente, usa a última gravação como referência e sinaliza essa limitação. Não é uma fotografia histórica de todo o parque: nova execução, rejeição, exclusão ou alteração do plano podem mudar esse recorte.

## Aplicativo com ícone e Relatórios — v2.9

Clique em **Instalar aplicativo** para instalar no computador ou celular. O navegador poderá mostrar a confirmação ou as instruções específicas do aparelho. No iPhone/iPad, abra no Safari e use Compartilhar → Adicionar à Tela de Início. O aplicativo abre em janela própria com ícone de checklist; mantém o login e o Authenticator. Precisa de internet para consultar e salvar os dados.

A aba **Relatórios** está disponível para todos os perfis autenticados. Mostra dados efetivamente salvos e separa Concluído, Pendente, Em andamento, Bloqueado, Aguardando aceite, Rejeitado e Sem cutover. Concluído exige todos os 11 processos e GO da retirada e da operação com responsável/data. Marcação completa sem aceite aparece como Aguardando aceite. Os filtros por filial/loja/PDV, situação e UF atualizam os totais. **Ver pendências** detalha os processos; **Abrir cutover** leva à execução selecionada. **Exportar CSV** baixa os registros filtrados.

Cada execução é contada separadamente; a mesma filial pode ter mais de um cutover/PDV. Filiais sem execução também aparecem. Cadastros inativos e lojas a inaugurar são identificados. Processos não concluídos incluem Pendente, Em andamento e Bloqueado; a rejeição é contabilizada separadamente nos cartões. Os totais de processos incluem execuções rejeitadas e são identificados na tela.

## Seleção com busca, rejeição e exclusão — v2.8

Digite diretamente em **Selecione a filial** para listar as lojas por código, nome ou localidade. Clique em um resultado ou use as setas e Enter; Escape cancela. A lista mostra até 100 resultados por busca, preservando a seleção enquanto você digita. O campo separado de pesquisa foi removido.

**Rejeitar cutover** fica disponível para Administrador e Gestor, com motivo obrigatório. Mantém o checklist para consulta, registra autor/data e bloqueia novas edições. A rejeição aparece no seletor, no histórico e no PDF.

**Excluir cutover** é exclusivo do Administrador, exige confirmação e verifica a versão atual para evitar apagar uma execução alterada por outra pessoa. Remove o checklist e seu vínculo, preserva a filial e os eventos de auditoria, e permite iniciar outra execução do zero para o mesmo PDV. Baixe o PDF antes de excluir se precisar manter uma cópia do checklist.

O preenchimento continua sendo gravado somente por **Salvar checklist**. Rejeição e exclusão são ações explícitas, confirmadas separadamente. Salve ou descarte alterações pendentes antes de usá-las.

## Filiais a inaugurar e exclusão — v2.6

Cadastre ou importe a situação **A inaugurar**. Administradores podem excluir filiais sem cutovers; cadastros com histórico devem ser inativados. A importação aceita nomes completos dos estados e siglas. Consulte `ATUALIZAR_RENDER.md`.

## Importação de filiais por planilha - v2.5

A aba **Filiais** permite cadastrar listas como a de aproximadamente 1.800 lojas de uma vez. A lista tem busca e paginação de 50 registros para manter a utilização simples.

1. Entre como Administrador ou Gestor e abra **Filiais → Importar lojas**.
2. Baixe o **modelo CSV** dentro da janela. Substitua as duas linhas de exemplo pela sua lista. Você também pode usar Excel `.xlsx`, com os dados na primeira aba. Arquivos antigos `.xls` devem ser salvos como `.xlsx`.
3. Utilize as colunas abaixo. Variações usuais de cabeçalho, como Filial/Código da filial, Descrição/Nome da loja e Município/Cidade, são reconhecidas.

   | Coluna do modelo | Obrigatória | Como preencher |
   |---|---|---|
   | `codigo` | Sim | Código único, como VD266, L2621 ou 0012; 2 a 30 caracteres |
   | `nome` | Sim | Nome da loja, até 160 caracteres |
   | `cidade` | Não | Nome da cidade, até 100 caracteres |
   | `uf` | Não | Sigla, como SP ou RJ |
   | `ativo` | Não | Ativa/Inativa, Sim/Não ou 1/0 |

4. Escolha **Cadastrar apenas novas filiais** (padrão, preserva todos os cadastros existentes) ou **Cadastrar novas e atualizar existentes** (usa o código como referência).
5. Clique em **Analisar arquivo**. Nenhum cadastro é alterado nessa fase. Confira os totais, a amostra de até 100 linhas e eventuais erros. Se houver erro em alguma linha ou código repetido no arquivo, corrija e envie novamente; a confirmação permanece bloqueada. A janela mostra até 200 erros por vez.
6. Clique em **Confirmar importação**. Todas as linhas planejadas são processadas juntas, em uma transação. O resultado informa novas lojas, atualizações e registros mantidos. Os IDs das filiais existentes e seus vínculos com cutovers são preservados. O processo não apaga filiais ou cutovers.
7. A prévia expira em 20 minutos. Se alguém editar um cadastro que seria alterado ou inserir o mesmo código entre prévia e confirmação, o sistema pede uma nova análise para evitar sobrescritas. Repetir a confirmação da mesma prévia concluída não duplica a importação.

Limites: até 10 MB, 10 mil linhas e 30 colunas. Somente `.xlsx` e `.csv`; fórmulas no Excel não são aceitas (cole como valores). CSV UTF-8 e Windows-1252 são aceitos, com separação por ponto e vírgula, vírgula ou tabulação. Para preservar zeros à esquerda, prefira códigos como texto; formatos numéricos simples de zeros no Excel também são reconhecidos.

Na atualização, cidade, UF ou situação ausentes/vazias mantêm o cadastro anterior. Para novas filiais, situação vazia significa Ativa. Registros antigos marcados **Revisar filial** precisam ter seu vínculo confirmado pelo fluxo de revisão; a importação não resolve vínculos ambíguos automaticamente. Ações de importação ficam registradas com autor, modo e totais no histórico administrativo do banco.

A tabela `ct_branch_imports` é criada automaticamente pelo `init_db.py`. Ela guarda a prévia para confirmação; após aplicar, os dados temporários são removidos do registro, mantendo o resultado e a identificação da operação. Os arquivos originais enviados não são armazenados.

## Filiais cadastradas e início de cutover - v2.4

1. Na aba **Filiais cadastradas**, Administrador ou Gestor cadastra código e nome da loja. Cidade e UF são opcionais. O código não muda depois do cadastro; o nome, cidade, UF e situação podem ser editados.
2. Na aba **Cutover**, selecione **uma filial**. O seletor de execuções mostra somente os cutovers dessa loja.
3. Clique em **Iniciar cutover**, confirme a loja exibida e informe o PDV. Os processos Linx e Orion pertencem a essa mesma execução e filial.
4. Uma filial pode ter várias execuções/PDVs, com IDs e registros independentes. Marcar, salvar ou gerar PDF em uma execução não altera outras. A loja não pode ser trocada no meio de um cutover.
5. Para atender outra loja, selecione a outra filial e inicie uma execução própria. O site aguarda salvar os dados atuais antes de trocar de filial; se houver erro ou conflito, a troca é impedida para preservar as alterações.
6. Filiais inativas mantêm seu histórico, mas não recebem novos cutovers. Gestor e Administrador gerenciam o cadastro; Operador e Consulta podem consultar as filiais conforme suas permissões existentes.

### Registros anteriores

A inicialização cria `ct_branches` e `ct_cutover_branch` e um índice para consulta por loja. O vínculo tem chave única por execução e referência à filial. Não é necessário executar SQL manualmente.

Execuções anteriores com código de filial reconhecido no início da identificação (VD, L ou código numérico) são agrupadas nesse cadastro. Complete o nome da loja em **Editar**. Identificações ambíguas recebem um cadastro temporário marcado **Revisar filial**; nenhuma loja é presumida nesses casos. Abra o cutover antigo e use **Vincular execução à filial correta**. Somente Administrador/Gestor pode confirmar esse vínculo; processos e observações são mantidos. Após a confirmação, o vínculo passa a ser permanente. Os usuários, MFA, senhas, versões e registros existentes são preservados na migração.

Importações precisam corresponder à identidade da execução selecionada: o servidor rejeita dados de outra filial, em vez de trocar o vínculo. O PDF identifica o código/PDV e o nome da loja registrado na execução.

Atualização aplicada exclusivamente ao projeto `preload_app` do anexo. Este pacote não contém o Controle de Ativos/Estoque.

- Conta conectada e botão **Sair da conta** no topo, inclusive no celular. A saída usa POST com proteção CSRF; alterações pendentes são tratadas antes de encerrar a sessão.
- Administrador tem o botão **Gerenciar acessos** em destaque: pesquisar usuários, cadastrar contas, escolher os quatro perfis, bloquear/reativar e redefinir senha temporária ou Authenticator. A própria conta é identificada e protegida contra bloqueio ou perda acidental do perfil.
- Processos em formato de checklist: marque a caixa ao concluir. Observações são opcionais. O responsável e a autoria são registrados automaticamente. Dados antigos, horários, evidências e orientações continuam disponíveis em **Ver orientações e informações adicionais**.
- Novo cutover por formulário de filial e PDV, sem prompt do navegador.
- Mantém os 11 passos, os pré-requisitos de GO, MFA, recuperação, histórico, impressão/PDF, dados existentes e controle de concorrência. Não é necessário criar novas variáveis de ambiente ou alterar o banco manualmente.

## Garantir o perfil de Administrador da sua conta

Se sua conta já é Administrador, basta entrar normalmente. Caso uma conta existente esteja com outro perfil ou bloqueada, quem tem acesso ao servidor pode aplicar o perfil administrativo:

```sh
python manage.py set-admin SEU_EMAIL_CADASTRADO
```

O comando atua somente na conta indicada, registra a ação no histórico e encerra suas sessões anteriores. Ele preserva senha, Authenticator e cutovers. Entre novamente com sua senha e seu MFA habituais. Não existe promoção automática de perfil pela página de login.

No Render sem Shell, execute o comando uma única vez entre `python init_db.py &&` e o Gunicorn no Start Command, usando seu e-mail já cadastrado. Após confirmar o acesso, remova essa etapa do Start Command. Não mantenha recuperação administrativa automática no reinício.

## Publicação

Envie os arquivos de dentro de `preload_app-main/` para a raiz do repositório do **Cutover**. Preserve `DATABASE_URL`, `SECRET_KEY` e a configuração MFA existente. Consulte `ATUALIZAR_RENDER.md` para os passos de atualização. Testes locais usam SQLite temporário; a conexão real ao Neon e o deploy continuam dependendo do ambiente do Render.

---

# Cutover Linx Agiliza → Orion · Render + Neon · v2.1

## Configuração mantida desde a versão 2.1

1. Substitua os arquivos do projeto no GitHub pelo conteúdo desta pasta. Preserve os nomes `static`, `templates` e `requirements.txt`.
2. Mantenha `DATABASE_URL` e `SECRET_KEY` atuais no Render. Não é necessário cadastrar `MFA_ENCRYPTION_KEY`: quando ela não existe, a aplicação deriva a chave de criptografia de `SECRET_KEY`, seguindo o comportamento do Controle de Ativos.
3. Se você já configurou `MFA_ENCRYPTION_KEY` na versão 2.0 e ativou algum Authenticator, preserve seu valor. Esta versão continua usando a chave Fernet explícita anterior para conseguir ler os cadastros existentes. A interpretação dessa variável é mantida como na versão 2.0 do Cutover; não copie chaves de outro aplicativo.
4. Faça o deploy com o Start Command já usado. `init_db.py` cria a tabela adicional `ct_auth` sem apagar usuários, senhas ou cutovers. Usuários que ainda não ativaram MFA serão direcionados para o cadastro no próximo login.
5. Usuários existentes mantêm seu perfil e senha. Administradores podem escolher os novos perfis em **Usuários**. Quem for novo ou tiver uma senha temporária redefinida precisará criar uma nova senha antes de configurar/validar o Authenticator.

A chave usada precisa permanecer estável: sem variável adicional, preserve `SECRET_KEY`; com variável adicional já em uso, preserve `MFA_ENCRYPTION_KEY`. Alterar a chave de criptografia sem migrar os dados impede a leitura dos cadastros MFA existentes.

## Perfis e permissões

| Recurso | Administrador | Gestor | Operador | Consulta |
|---|---|---|---|---|
| Ver cutovers, rede e histórico | Sim | Sim | Sim | Sim |
| Exportar JSON e imprimir/PDF | Sim | Sim | Sim | Sim |
| Atualizar etapas, responsáveis e evidências | Sim | Sim | Sim | Não |
| Criar cutovers | Sim | Sim | Não | Não |
| Registrar/alterar decisões GO e NO-GO | Sim | Sim | Não | Não |
| Importar registros | Sim | Sim | Somente sem mudar decisões reservadas | Não |
| Criar usuários, alterar perfis e bloquear acessos | Sim | Não | Não | Não |
| Redefinir senha temporária ou MFA de outros usuários | Sim | Não | Não | Não |
| Trocar a própria senha | Sim | Sim | Sim | Sim |

As permissões são verificadas no servidor, inclusive em solicitações diretas à API. Os perfis valem para todos os cutovers; não há restrição por filial. Operadores podem voltar uma aprovação para Pendente ao reabrir uma etapa, mas não podem emitir GO/NO-GO ou editar seus dados.

## Authenticator e recuperação

MFA é obrigatório para todos. Na primeira entrada, cadastre o QR Code em **Microsoft Authenticator → adicionar Outra conta** ou no Google Authenticator como conta por QR Code. É uma conta TOTP própria do sistema, sem integração com o login corporativo Microsoft. O QR Code é gerado no próprio servidor, sem enviar a chave para serviços externos.

Confirme com o código de seis dígitos. Após ativar, guarde os oito códigos de recuperação mostrados uma única vez. Cada um permite completar um login com a senha e é descartado após o uso. São armazenados somente hashes desses códigos. O segredo TOTP fica criptografado no banco. Um mesmo código TOTP não é aceito novamente após uso, inclusive se você tentar entrar em outra aba; aguarde o próximo código. O horário do celular deve estar automático.

Se perder o aparelho, entre com sua senha, marque **Estou usando um código de recuperação** e informe um código ainda não utilizado. Depois, peça a um administrador para redefinir seu MFA, confirme novamente a senha no login e cadastre o novo aparelho. O administrador confirma sua própria senha para redefinir o MFA de outro usuário. Verifique a identidade do colaborador antes dessa ação. Redefinir MFA invalida o aplicativo e os códigos de recuperação anteriores. Redefinir somente a senha mantém o MFA existente.

Se o único administrador perder também os códigos de recuperação, alguém com acesso ao ambiente do servidor poderá executar:

```sh
python manage.py reset-mfa email-do-administrador
```

O comando invalida as sessões e o MFA desse administrador, preservando a senha. Se o plano do Render não disponibilizar Shell, use temporariamente o comando como etapa do Start Command depois de `python init_db.py &&` e antes do Gunicorn. Após executar uma única vez, remova a etapa de recuperação para que ela não rode novamente a cada reinício. Nunca deixe recuperação automática configurada.

Aplicação Flask com login e dados compartilhados em PostgreSQL. Mantém as 11 etapas das planilhas, requisitos de rede, observações, responsáveis, evidências, decisões e PDF para download. O aceite Orion foi corrigido para a etapa 6 (a planilha referenciava uma etapa 7 inexistente).

## Publicar no Render

1. Extraia este ZIP. Crie um repositório privado no GitHub e envie os arquivos **de dentro da pasta `cutover-render`**. O arquivo `app.py` deve ficar na raiz do repositório. Não envie `.env`, senhas ou registros reais de teste.
2. No Neon, abra o projeto/banco e clique em **Connect**. Copie a connection string PostgreSQL, preferencialmente a conexão pooled oferecida pelo painel. Preserve os parâmetros de segurança fornecidos, inclusive `sslmode=require` e `channel_binding=require` quando presentes. Use um banco ou branch dedicado a este aplicativo.
3. No Render, crie um **Web Service** conectado ao repositório. Use runtime **Python 3**, Build Command `pip install -r requirements.txt` e Start Command:

   ```sh
   bash start.sh
   ```

4. Em **Environment**, configure:

   | Variável | Conteúdo |
   |---|---|
   | `DATABASE_URL` | Connection string do Neon, com usuário, senha, host, banco e parâmetros TLS |
   | `SECRET_KEY` | Chave aleatória longa e permanente; gere com `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `ADMIN_EMAIL` | Seu e-mail para o primeiro administrador |
   | `ADMIN_PASSWORD` | Senha inicial forte, com pelo menos 12 caracteres |
   | `ADMIN_NAME` | Alexandre Martins, ou nome desejado |
   | `PYTHON_VERSION` | `3.12.8` |

   Não defina `APP_ENV=development` no Render. A aplicação exige Neon e cookies HTTPS em produção.

5. Configure Health Check Path `/healthz` e faça o deploy. A inicialização cria somente tabelas com prefixo `ct_`; não apaga tabelas existentes. O usuário do banco precisa poder criar essas tabelas.
6. Acesse a URL do Render, entre com o administrador, crie sua senha definitiva e configure o Authenticator. Guarde os códigos de recuperação e crie o primeiro cutover. Remova `ADMIN_PASSWORD` de Environment após confirmar o acesso; ela só é usada quando ainda não há usuários. Alterá-la no painel não redefine uma senha já cadastrada.

Alternativa: o `render.yaml` permite cadastrar por Blueprint e solicitar as variáveis. Escolha no painel o plano adequado; este projeto não cria um banco adicional no Render.

## Uso em equipe

O administrador tem também **Cadastrar usuário** no topo e **Usuários e acessos** no menu lateral. O botão abre diretamente o formulário de novo usuário. Contas Gestor, Operador ou Consulta não podem cadastrar pessoas nem se promover a administrador.

- **Novo cutover:** informe filial, PDV e identificação/data da execução. Cada cadastro possui dados próprios e fica disponível no seletor.
- **Usuários:** o administrador cria contas nos quatro perfis acima, altera perfis, bloqueia/reativa acessos e redefine senhas temporárias ou MFA de outros usuários. Não existe cadastro público. A troca da senha temporária é obrigatória. Troca de senha, bloqueio, redefinição e mudança de perfil invalidam sessões anteriores.
- **Salvamento:** somente ao clicar em **Salvar checklist**. Marcar processos, preencher observações, pesquisar filiais, baixar PDF ou sair não grava o checklist automaticamente. Ao trocar de filial/cutover, atualizar ou sair com alterações pendentes, cancele para salvar ou confirme o descarte. Em erro de conexão, os dados continuam na tela; tente salvar novamente ou use **Exportar registros**. Não feche a aba enquanto houver alterações pendentes.
- **Concorrência:** o servidor rejeita gravações com versão antiga. Exporte sua cópia, atualize e reaplique as alterações necessárias. A página não combina edições nem atualiza automaticamente a tela de outros usuários; use **Atualizar dados** para consultar mudanças da equipe.
- **Importação:** selecione ou crie a execução de destino e importe o JSON exportado na versão HTML. Os dados ficam na tela até clicar em **Salvar checklist**; o servidor valida a gravação nesse momento. Exporte uma cópia do destino antes de importar.
- **Histórico:** registra autor, horário e valores anteriores/novos das alterações; mostra os últimos 200 eventos do cutover. É histórico operacional, sem assinatura digital.
- **Evidências:** são links ou texto. Esta versão não recebe anexos de arquivos.
- **Salvar e PDF:** use **Salvar checklist**. Somente após o servidor confirmar o salvamento aparece um popup com o botão **Baixar checklist em PDF**. O relatório é gerado no servidor, inclui processos, marcações, observações preenchidas, decisões e rede, e é enviado como arquivo para download. A pasta final é determinada pelo navegador; normalmente Downloads. Se aparecer o seletor de pasta, escolha Downloads. O relatório parcial também pode ser salvo e mostra os processos pendentes. O PDF corresponde à versão salva; se outra pessoa atualizar antes do download, o sistema pede para atualizar e gerar novamente.
- **Horários:** eventos do servidor são armazenados em UTC e exibidos no fuso do navegador. Horários previstos são informados como hora local da operação.

## Regras de execução

Orion 1–3 e Linx 1–5 devem estar concluídos antes do GO da retirada. Para iniciar Orion 4, esse GO precisa ter responsável e data/hora preenchidos; as observações são opcionais. Etapas podem ser concluídas apenas pela marcação, sem evidência textual obrigatória; o servidor registra automaticamente quem marcou e quando. Orion 5 depende de Orion 4 concluído e Orion 6 depende de Orion 5. GO da operação exige todas as etapas concluídas. Preenchimento é declaração do operador, não teste automático dos equipamentos. Ao desmarcar um pré-requisito na tela, a liberação e as etapas dependentes voltam a Pendente para manter a coerência do roteiro.

## Desenvolvimento e testes

```sh
python -m venv .venv
# Ative o ambiente virtual conforme seu sistema.
pip install -r requirements.txt
```

Defina `APP_ENV=development`, `SECRET_KEY`, `ADMIN_EMAIL` e `ADMIN_PASSWORD` no ambiente e execute `python app.py`. Sem `DATABASE_URL`, **apenas em desenvolvimento**, utiliza SQLite em `dev.sqlite`. O arquivo `.env.example` é um modelo; o programa não o carrega automaticamente. Para testar Neon localmente, configure `DATABASE_URL`.

```sh
pip install pytest==8.4.2 pypdf
python -m pytest -q
```

Os testes automatizados usam SQLite temporário e cobrem troca obrigatória de senha, MFA e criptografia, rejeição de código reutilizado, recuperação de uso único, redefinições administrativas, limitação de tentativas, CSRF, quatro perfis, bloqueio e revogação de sessões, salvamento compartilhado, conflitos, GO e migração da versão 1. A conexão real ao seu Neon e o deploy no seu Render dependem das suas configurações e precisam ser validados após a publicação. Sem `MFA_ENCRYPTION_KEY`, a chave de criptografia é derivada de `SECRET_KEY` também em produção. A configuração explícita já utilizada na v2.0 continua compatível.

## Referências oficiais

- https://render.com/docs/deploy-flask
- https://neon.com/docs/get-started/connect-neon
- https://flask.palletsprojects.com/en/stable/deploying/gunicorn/

Developed by ALM - Expansão de TI
