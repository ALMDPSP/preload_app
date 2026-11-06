# Cutover Linx Agiliza → Orion · v3.0

Consulte `ATUALIZAR_RENDER.md` para atualizar o Start Command para `bash start.sh` e acompanhar os novos logs de inicialização.

## Dashboard por loja e número de PDV — v3.0

A página inicial agora é **Dashboard**. A meta padrão é **4 PDVs (01, 02, 03, 04) por filial ativa e aberta**. Filiais inativas, a inaugurar e cadastros legados que exigem revisão não entram nesse recorte. Os demais módulos continuam no menu.

Cada máquina é identificada por filial + número do PDV. 1, 01 e PDV 1 representam a mesma máquina; a execução mais recente prevalece, sem somar repetidas tentativas. **Orion OK** exige todos os processos concluídos e GO da retirada/operação com responsável e data. Todos os demais casos, inclusive sem cutover e rejeitado, contam como pendentes.

**Ajustar PDVs**, disponível para Administrador/Gestor, permite informar a lista real de números por loja, entre 1 e 50 equipamentos. A quantidade da meta corresponde ao tamanho dessa lista. Números observados fora dela ou não identificados geram alertas e ficam fora das métricas até ajuste. Cutovers existentes não são apagados ao mudar o plano.

O dashboard exibe PDVs previstos, virados e OK, pendentes, percentual e lojas completas. Os filtros de loja/UF valem para os totais e para o **Relatório executivo PDF**. A tabela e o PDF mostram os números OK e pendentes por filial; o CSV detalha cada PDV.

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
