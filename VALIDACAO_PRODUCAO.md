# Validação após publicação — v5.0

Este roteiro **não foi executado no Neon/Render de produção**. Os testes locais usaram banco temporário; o PostgreSQL local não pôde iniciar pela restrição de sockets do ambiente. Registre resultado, data e responsável de cada conferência.

## Preparação

- Preserve backup nativo do banco e as chaves permanentes fora do repositório.
- Publique o pacote completo e confirme commit Live, /healthz com version 5.0 e ausência de falhas de migração nos logs.
- Separe uma filial/PDV de teste e usuários Administrador, Gestor, Operador e Consulta. Não use aceites fictícios em equipamento real.

## Operação e concorrência

1. Na Central, edite cadastro, observação e checklist incompleto. Confirme que nenhuma alteração é gravada antes de Salvar tudo. Salve, busque novamente a filial e confira número do PDV, valores e pendências.
2. Abra o mesmo PDV em duas sessões. Salve na primeira e tente salvar o rascunho antigo na segunda. Deve surgir conflito sem gravação parcial. Recarregue os dados e confira que a primeira alteração permanece.
3. Edite PDVs diferentes da mesma loja. Havendo conflito da versão comum da filial, recarregue e repita; nenhuma alteração salva deve se perder.
4. Atribua executor e validador. Confira que Operador não atribui responsáveis nem concede GO; Consulta não grava; outro Gestor não concede o aceite reservado. Administrador pode intervir. Exercite rejeição/retomada apenas no PDV de teste, conforme as permissões existentes.
5. Crie uma onda de teste, vincule a filial e confira todos os PDVs, responsáveis e datas preservados. Confira Fila do dia, Meus PDVs, atrasos e atalhos para o equipamento correto.
6. Registre ocorrência com impacto e prazo; resolva e confirme a mudança nos alertas.

## Conferência executiva

1. Compare uma amostra real de lojas/PDVs com a Base, cadastro de quantidade/numeração, implantação declarada e aceites Orion.
2. Compare os totais de previstos, implantados, validados e pendentes. Implantação declarada pode existir sem validação; não some essas contagens.
3. Selecione semana atual e período personalizado. Confira datas, comparação com intervalo anterior, atrasos atuais e distribuição por GR/regional.
4. Baixe o PDF executivo e CSV operacional. Confira filial/PDV, responsáveis, datas e critérios do período. O PDF não deve carregar checklists de todas as lojas; o PDF individual continua separado.
5. Em Gestão de dados, execute Conferir integridade e totais. Investigue avisos antes de considerar a base reconciliada. Registre também os tempos reais de abertura, salvamento e download.

## Recuperação em ambiente separado

1. Exporte o backup operacional como Administrador e guarde o arquivo com acesso restrito.
2. Em ambiente de teste compatível e com a mesma SECRET_KEY, importe o arquivo e confira a prévia. Usuários/senhas/MFA não são restaurados; vínculos indisponíveis são avisados.
3. Digite RESTAURAR, confirme e compare contagens e uma amostra de registros. Verifique contas preservadas e refaça a conferência de integridade.
4. Não restaure produção apenas para cumprir este teste. Uma recuperação real exige janela de manutenção, todas as instâncias atualizadas e backup nativo prévio. A prévia expira em dez minutos ou quando os dados/perfis mudam.

## Aceite da atualização

Conclua somente após registrar os resultados acima. Se houver falha, preserve os rascunhos, logs e identificação da filial/PDV, sem divulgar senhas, DATABASE_URL ou chaves. O pacote local não equivale a uma atualização já implantada no Render.
