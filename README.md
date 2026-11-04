# Cutover Linx Agiliza → Orion · Render + Neon

Aplicação Flask com login e dados compartilhados em PostgreSQL. Mantém as 11 etapas das planilhas, requisitos de rede, observações, responsáveis, evidências, decisões e impressão pelo navegador. O aceite Orion foi corrigido para a etapa 6 (a planilha referenciava uma etapa 7 inexistente).

## Publicar no Render

1. Extraia este ZIP. Crie um repositório privado no GitHub e envie os arquivos **de dentro da pasta `cutover-render`**. O arquivo `app.py` deve ficar na raiz do repositório. Não envie `.env`, senhas ou registros reais de teste.
2. No Neon, abra o projeto/banco e clique em **Connect**. Copie a connection string PostgreSQL, preferencialmente a conexão pooled oferecida pelo painel. Preserve os parâmetros de segurança fornecidos, inclusive `sslmode=require` e `channel_binding=require` quando presentes. Use um banco ou branch dedicado a este aplicativo.
3. No Render, crie um **Web Service** conectado ao repositório. Use runtime **Python 3**, Build Command `pip install -r requirements.txt` e Start Command:

   ```sh
   python init_db.py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
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
6. Acesse a URL do Render, entre com o administrador e crie o primeiro cutover. Depois do primeiro login, altere a senha em **Minha senha**. Remova `ADMIN_PASSWORD` de Environment após confirmar o acesso; ela só é usada quando ainda não há usuários. Alterá-la no painel não redefine uma senha já cadastrada.

Alternativa: o `render.yaml` permite cadastrar por Blueprint e solicitar as variáveis. Escolha no painel o plano adequado; este projeto não cria um banco adicional no Render.

## Uso em equipe

- **Novo cutover:** informe filial, PDV e identificação/data da execução. Cada cadastro possui dados próprios e fica disponível no seletor.
- **Usuários:** o administrador cria contas de administrador ou operador e pode bloquear/reativar acessos. Operadores podem consultar e editar todos os cutovers. Não existe cadastro público. A senha inicial é definida pelo administrador e pode ser trocada pelo usuário.
- **Salvamento:** automático após a edição. Confira o aviso “Salvo no banco”. Em erro de conexão, os dados continuam na tela; use **Exportar registros** e tente **Atualizar dados** após resolver a conexão. Não feche a aba enquanto houver alterações pendentes.
- **Concorrência:** o servidor rejeita gravações com versão antiga. Exporte sua cópia, atualize e reaplique as alterações necessárias. A página não combina edições nem atualiza automaticamente a tela de outros usuários; use **Atualizar dados** para consultar mudanças da equipe.
- **Importação:** selecione ou crie a execução de destino e importe o JSON exportado na versão HTML. Os dados substituem o conteúdo desse cutover após passarem pelas validações do servidor. Exporte uma cópia do destino antes de importar.
- **Histórico:** registra autor, horário e valores anteriores/novos das alterações; mostra os últimos 200 eventos do cutover. É histórico operacional, sem assinatura digital.
- **Evidências:** são links ou texto. Esta versão não recebe anexos de arquivos.
- **PDF:** utilize **Imprimir / PDF** e selecione **Salvar como PDF** no navegador. O relatório inclui roteiro, rede e decisões. Antes de imprimir, confira o salvamento; textos muito longos em campos podem exigir ajuste na impressão.
- **Horários:** eventos do servidor são armazenados em UTC e exibidos no fuso do navegador. Horários previstos são informados como hora local da operação.

## Regras de execução

Orion 1–3 e Linx 1–5 devem estar concluídos antes do GO da retirada. Para iniciar Orion 4, esse GO precisa ter responsável, data/hora e motivo preenchidos. Etapas concluídas exigem responsável e evidência. Orion 5 depende de Orion 4 concluído e Orion 6 depende de Orion 5. GO da operação exige todas as etapas concluídas. Preenchimento é declaração do operador, não teste automático dos equipamentos. Se reabrir um pré-requisito depois de iniciar a instalação, ajuste também o status das etapas posteriores e a decisão antes de salvar.

## Desenvolvimento e testes

```sh
python -m venv .venv
# Ative o ambiente virtual conforme seu sistema.
pip install -r requirements.txt
```

Defina `APP_ENV=development`, `SECRET_KEY`, `ADMIN_EMAIL` e `ADMIN_PASSWORD` no ambiente e execute `python app.py`. Sem `DATABASE_URL`, **apenas em desenvolvimento**, utiliza SQLite em `dev.sqlite`. O arquivo `.env.example` é um modelo; o programa não o carrega automaticamente. Para testar Neon localmente, configure `DATABASE_URL`.

```sh
pip install pytest==8.4.2
python -m pytest -q
```

Os testes automatizados usam SQLite temporário e cobrem autenticação, CSRF, perfis, bloqueio de acesso, salvamento compartilhado, conflito de versões, GO e troca de senha. A conexão real ao seu Neon e o deploy no seu Render dependem das suas configurações e precisam ser validados após a publicação.

## Referências oficiais

- https://render.com/docs/deploy-flask
- https://neon.com/docs/get-started/connect-neon
- https://flask.palletsprojects.com/en/stable/deploying/gunicorn/

Developed by ALM - Expansão de TI
