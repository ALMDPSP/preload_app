# Atualização v2.2 — acessos, saída e preenchimento simples

1. Substitua os arquivos no GitHub pelo conteúdo completo deste pacote. Envie também os novos `static/simple.js` e `static/simple.css`.
2. Mantenha as variáveis atuais do Render: `DATABASE_URL`, `SECRET_KEY` e, se já usada para cadastrar MFA, `MFA_ENCRYPTION_KEY`. Não é necessário criar novas variáveis.
3. Faça o deploy da versão mais recente. Mantenha os comandos de build e início já configurados.
4. Ao acessar, pressione **Ctrl+F5** se o navegador ainda mostrar o layout anterior.
5. No menu lateral, confira nome, perfil e **Sair da conta**. Administradores também terão **Gestão de acessos**.
6. Para iniciar uma execução, use **Novo cutover** e preencha Filial, PDV e Data. Nas etapas, informe responsável e resultado, depois clique em **Concluir**. Horários e observações ficam em **Mais informações**.

Os usuários, perfis, cadastros de MFA e cutovers existentes são preservados. O e-mail configurado no primeiro cadastro de administrador é o acesso que gerencia a equipe. Alterar `ADMIN_EMAIL` no Render não modifica perfis de contas existentes.

## Referência de configuração — versão 2.1

1. No GitHub, substitua os arquivos pelo conteúdo deste pacote. O ajuste principal está em `auth_mfa.py`; mantenha todos os arquivos do projeto atualizados.
2. No Render, preserve `DATABASE_URL` e `SECRET_KEY` existentes.
3. Se o deploy parou por falta de `MFA_ENCRYPTION_KEY`, não é necessário criar essa variável. Esta versão usa `SECRET_KEY` para derivar a proteção das credenciais do Authenticator.
4. Se você já definiu `MFA_ENCRYPTION_KEY` e ativou MFA na versão anterior, mantenha seu valor. Assim, os cadastros anteriores continuam legíveis.
5. Mantenha Build Command `pip install -r requirements.txt` e Start Command:

   ```sh
   python init_db.py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

6. Faça o deploy mais recente. Não é necessário apagar o banco ou criar tabelas manualmente.
7. Entre com seu usuário, cadastre o QR Code no Microsoft Authenticator (Outra conta) ou Google Authenticator e confirme o código. Guarde os códigos de recuperação.

Os quatro perfis, MFA obrigatório, troca de senha temporária e os registros existentes são preservados. Não altere a chave utilizada para criptografia após cadastrar os Authenticator: ela é necessária para ler os dados já gravados. O app permanece exigindo `SECRET_KEY` em produção; a proteção MFA continua ativa.
