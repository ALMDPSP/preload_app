# Atualização v2.5 - Importar cerca de 1.800 filiais por planilha

1. Substitua os arquivos no GitHub pelo conteúdo completo deste pacote. Inclua `branch_import.py`, `static/branch-import.js` e o `requirements.txt` atualizado.
2. Mantenha as variáveis atuais no Render. Não há nova variável obrigatória.
3. Mantenha o Build Command `pip install -r requirements.txt` e o Start Command:

   ```sh
   python init_db.py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
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
