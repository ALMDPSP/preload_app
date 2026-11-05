# Atualização v2.4 - Filiais cadastradas e cutover vinculado

1. Substitua os arquivos do `preload_app` no GitHub pelo conteúdo completo deste pacote, incluindo os novos `branches.py`, `static/branches.js` e `static/branches.css`.
2. Mantenha todas as variáveis atuais do Render. Não há variável nova obrigatória.
3. Mantenha Build Command `pip install -r requirements.txt` e Start Command:

   ```sh
   python init_db.py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

4. Faça o deploy. `init_db.py` cria as tabelas de filiais e vínculos, sem apagar o conteúdo existente. As execuções antigas são vinculadas conforme a identificação da loja; dados ambíguos aparecem como **Revisar filial**.
5. Pressione Ctrl+F5 ao abrir a página. Na aba **Filiais cadastradas**, cadastre as lojas ou complete os nomes importados. Administrador e Gestor podem cadastrar/editar; os demais perfis consultam.
6. Na aba **Cutover**, selecione uma filial e clique em **Iniciar cutover**. Informe o PDV e confirme. A loja selecionada fica fixa nessa execução.
7. Para um cutover antigo marcado **Revisar filial**, abra-o e clique em **Vincular execução à filial correta**. Selecione a loja já cadastrada. Os dados anteriores são mantidos e o vínculo confirmado não pode mais ser trocado.
8. Continue marcando os processos, com observações opcionais. **Salvar checklist** mantém o popup para baixar o PDF.

Uma loja pode ter vários cutovers independentes. Para outra loja, selecione a outra filial e inicie outra execução. Não é necessário alterar SECRET_KEY, recadastrar usuários ou reconfigurar o Authenticator.

As instruções de recuperação do Administrador (`python manage.py set-admin SEU_EMAIL_JA_CADASTRADO`) e de MFA continuam disponíveis no README.
