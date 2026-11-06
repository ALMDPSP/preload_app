# Recuperar a senha do Administrador

A mensagem “E-mail ou senha inválidos” é anterior à etapa do Authenticator. Também pode aparecer se o e-mail não existir ou a conta estiver inativa. Não altere o banco, SECRET_KEY ou MFA_ENCRYPTION_KEY para corrigir esse erro.

ADMIN_PASSWORD é usada apenas no primeiro cadastro. Mudar essa variável não troca a senha de uma conta existente.

## Com Shell no Render

Após atualizar `manage.py` deste pacote no GitHub e publicar no Render, execute no Shell do serviço:

```sh
python manage.py reset-password alexandre.martins@dpsp.com.br
```

Digite e confirme uma senha temporária de pelo menos 12 caracteres no terminal. O comando não exibe os caracteres digitados. Depois entre no site, defina a senha definitiva quando solicitado e confirme o Authenticator já cadastrado. A conta é reativada e as sessões antigas são invalidadas.

## Sem Shell no Render

1. Atualize os arquivos deste pacote no GitHub e publique no Render.
2. Em Environment, crie `ADMIN_RESET_PASSWORD` com uma senha temporária de pelo menos 12 caracteres, escolhida por você. Não a coloque no código nem envie no chat.
3. Altere temporariamente o Start Command para:

```sh
python manage.py reset-password alexandre.martins@dpsp.com.br && bash start.sh
```

4. Faça o deploy e espere o serviço ficar disponível. O log informa “Senha temporária aplicada”, sem mostrar a senha.
5. Entre usando o e-mail e a senha temporária. Crie a senha definitiva e confirme o Authenticator atual.
6. Assim que recuperar o acesso, restaure o Start Command para `bash start.sh` e remova `ADMIN_RESET_PASSWORD`. Essa etapa evita redefinir a senha novamente em cada reinício. Salve as alterações no Render.

O comando só opera em uma conta existente com perfil admin. Se aparecer “Administrador não encontrado”, confira se é esse o e-mail cadastrado e se o serviço aponta para o Neon correto. Não há criação automática de administrador nem troca de perfil neste comando.

A recuperação preserva filiais, checklists, dashboard e MFA. Só o hash da senha, a situação ativa e a versão das sessões são alterados; a senha temporária deve ser trocada no próximo acesso.
