# Atualização v2.1 — MFA seguindo o Controle de Ativos

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
