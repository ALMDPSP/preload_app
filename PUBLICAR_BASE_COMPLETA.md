# Publicar base completa 5.1.33

1. Extraia este ZIP no computador.
2. Abra a raiz do repositório ALMDPSP/preload_app, na branch main, e escolha Add file > Upload files.
3. Arraste as pastas static e templates inteiras, junto com todos os arquivos da raiz extraída. Não arraste somente os arquivos de dentro das pastas para a raiz do GitHub. Não envie o ZIP fechado.
4. Confirme em Commit changes e aguarde o deploy automático no Render ficar Live.
5. Mantenha o Start Command como bash start.sh. O log deve mostrar: Base completa conferida - versão 5.1.33.
6. Abra o site e use Ctrl + Shift + R. O topo deve ter sete indicadores, incluindo Lojas totalmente viradas, mesmo quando o valor for zero.

Se a conferência informar arquivos ausentes ou diferentes, reenvie os caminhos indicados pelo log nas pastas correspondentes. A conferência ocorre antes de acessar o banco.

O pacote contém o programa. Nenhum banco de produção, usuário, checklist ou dado operacional precisa ser apagado ou reimportado. A contagem de lojas totalmente viradas exige Orion OK em todos os PDVs previstos para cada filial.
