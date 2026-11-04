# Cutover Linx Agiliza → Orion · Render + Neon · v2.2

## Interface simplificada na versão 2.2

- **Sua conta:** nome, e-mail, perfil, último acesso, **Minha senha** e **Sair da conta** ficam no menu lateral. O botão de saída encerra a sessão e tenta salvar alterações pendentes; se houver falha, solicita confirmação antes de descartá-las.
- **Administrador:** use **Gestão de acessos** no menu lateral para cadastrar usuários, pesquisar pessoas e gerenciar perfis, bloqueios, senhas temporárias e Authenticator. O botão **Minha conta** identifica seu próprio acesso administrativo e impede bloqueio ou alteração do próprio perfil pela tela.
- **Novo cutover:** formulário com Filial, PDV e Data, mais coordenador opcional. Não precisa juntar todos os dados num único campo. Ao criar, os dados são gravados juntos no banco.
- **Etapas:** abra uma etapa e preencha responsável e resultado. Use **Usar meu nome**, **Iniciar etapa** ou **Concluir**. Campos obrigatórios ausentes ficam destacados com mensagem na própria etapa. O status também pode ser escolhido na lista.
- **Detalhes opcionais:** horários e observações ficam em **Mais informações**, preservando os dados já cadastrados. As condições para avançar continuam visíveis.

O usuário criado pelo primeiro cadastro (`ADMIN_EMAIL`) tem perfil Administrador. Entre com esse e-mail para gerenciar os acessos. Alterar `ADMIN_EMAIL` no Render depois que o banco já possui usuários não promove outra conta. Para alterar uma conta existente, entre com um administrador e ajuste seu perfil em **Gestão de acessos**.

Para atualizar, envie todos os arquivos deste pacote ao GitHub, inclusive `static/simple.js`, `static/simple.css` e o novo template. Mantenha as variáveis atuais no Render e faça o deploy. Não há novas variáveis obrigatórias nem alteração da estrutura do banco nesta versão.

## Configuração preservada da versão 2.1

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
6. Acesse a URL do Render, entre com o administrador, crie sua senha definitiva e configure o Authenticator. Guarde os códigos de recuperação e crie o primeiro cutover. Remova `ADMIN_PASSWORD` de Environment após confirmar o acesso; ela só é usada quando ainda não há usuários. Alterá-la no painel não redefine uma senha já cadastrada.

Alternativa: o `render.yaml` permite cadastrar por Blueprint e solicitar as variáveis. Escolha no painel o plano adequado; este projeto não cria um banco adicional no Render.

## Uso em equipe

- **Novo cutover:** informe filial, PDV e identificação/data da execução. Cada cadastro possui dados próprios e fica disponível no seletor.
- **Usuários:** o administrador cria contas nos quatro perfis acima, altera perfis, bloqueia/reativa acessos e redefine senhas temporárias ou MFA de outros usuários. Não existe cadastro público. A troca da senha temporária é obrigatória. Troca de senha, bloqueio, redefinição e mudança de perfil invalidam sessões anteriores.
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

Os testes automatizados usam SQLite temporário e cobrem troca obrigatória de senha, MFA e criptografia, rejeição de código reutilizado, recuperação de uso único, redefinições administrativas, limitação de tentativas, CSRF, quatro perfis, bloqueio e revogação de sessões, salvamento compartilhado, conflitos, GO e migração da versão 1. A conexão real ao seu Neon e o deploy no seu Render dependem das suas configurações e precisam ser validados após a publicação. Sem `MFA_ENCRYPTION_KEY`, a chave de criptografia é derivada de `SECRET_KEY` também em produção. A configuração explícita já utilizada na v2.0 continua compatível.

## Referências oficiais

- https://render.com/docs/deploy-flask
- https://neon.com/docs/get-started/connect-neon
- https://flask.palletsprojects.com/en/stable/deploying/gunicorn/

Developed by ALM - Expansão de TI
