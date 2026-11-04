# Atualização v2 — perfis e Authenticator

1. No GitHub, envie o conteúdo completo desta pasta para a raiz do repositório do Cutover. Preserve os nomes `static`, `templates` e `requirements.txt`.
2. No Render, abra seu Web Service → **Environment**.
3. Mantenha `DATABASE_URL` e `SECRET_KEY` atuais. Adicione **MFA_ENCRYPTION_KEY**.
4. Para gerar o valor dessa nova variável, execute no PowerShell:

   ```powershell
   $bytes = New-Object byte[] 32
   $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
   $rng.GetBytes($bytes)
   [Convert]::ToBase64String($bytes).Replace('+','-').Replace('/','_')
   $rng.Dispose()
   ```

   Copie a linha resultante, incluindo `=` no final, para o valor da variável. Gere uma única vez e guarde a chave com segurança para os próximos deploys.

5. Confirme Build Command:

   ```sh
   pip install -r requirements.txt
   ```

6. Confirme Start Command:

   ```sh
   python init_db.py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

7. Salve as variáveis e faça o deploy da versão mais recente. Mantenha `/healthz` como Health Check Path.
8. Entre com seu usuário existente. Será solicitado o cadastro do Authenticator. Se ainda for o primeiro administrador do banco novo, antes disso será solicitada a troca da senha temporária.
9. Microsoft Authenticator: adicionar **Outra conta**. Google Authenticator: ler QR Code. Confirme o código e guarde os oito códigos de recuperação.
10. No menu **Usuários**, ajuste os perfis: Administrador, Gestor, Operador e Consulta. Novos usuários devem receber senha temporária com pelo menos 12 caracteres.

Não é necessário apagar banco nem executar SQL manualmente. A inicialização cria a tabela adicional de autenticação e preserva o conteúdo anterior. Confira o salvamento de um cutover e o acesso de um usuário Consulta após publicar. Os detalhes de permissões e recuperação estão em `README.md`.
