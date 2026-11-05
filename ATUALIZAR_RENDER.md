# Atualização v2.3 - Checklist simples e PDF para download

1. Substitua os arquivos do projeto `preload_app` no GitHub pelo conteúdo desta pasta. Envie também `pdf_report.py`, `static/checklist.js`, `static/checklist.css` e o `requirements.txt` atualizado.
2. Mantenha as variáveis do Render. Não há nova variável obrigatória. Não altere `DATABASE_URL`, `SECRET_KEY` ou uma chave MFA já em uso.
3. Mantenha Build Command `pip install -r requirements.txt` e Start Command:

   ```sh
   python init_db.py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

4. Faça o deploy da versão mais recente e pressione Ctrl+F5 ao abrir a página.
5. Marque os processos concluídos. Observações são opcionais. **Salvar checklist** confirma o salvamento no banco e abre o aviso de download do PDF. Clique em **Baixar checklist em PDF** e salve em Downloads, se o navegador perguntar a pasta. O site não pode impor a pasta no computador; a configuração do navegador define o destino.
6. Para criar pessoas, entre com o perfil Administrador e clique em **Cadastrar usuário** ou **Usuários e acessos**. O cadastro utiliza senha temporária e mantém a configuração obrigatória do Authenticator.
7. Se a sua conta existente não tiver o perfil Administrador, um administrador poderá ajustar seu perfil. Como proprietário do serviço, você também pode recuperar o acesso pelo Shell do Render:

   ```sh
   python manage.py set-admin SEU_EMAIL_JA_CADASTRADO
   ```

   Substitua pelo e-mail exato já cadastrado no Cutover e entre novamente. O comando preserva a senha e o MFA. Alterar apenas ADMIN_EMAIL no painel não promove usuários existentes. Se o plano não tiver Shell, as instruções de recuperação da versão anterior estão no README. Não deixe um comando de promoção/redefinição permanente no Start Command.

O banco, usuários, MFA e registros anteriores são preservados. As condições de liberação operacional continuam válidas: Orion 4 depende do GO da retirada, e testes e aceite seguem a sequência. Gestor e Administrador registram as decisões; Operador marca os processos; Consulta acompanha e baixa PDFs.
