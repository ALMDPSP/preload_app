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
