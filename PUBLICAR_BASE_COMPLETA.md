# Publicar base completa 5.1.36

1. Extraia este ZIP no computador.
2. Na raiz do repositório ALMDPSP/preload_app (main), use Add file > Upload files.
3. Envie todos os arquivos extraídos, incluindo release-assets.zip, restore_release_assets.py, release_manifest.json e start.sh. Envie também as pastas static e templates completas.
4. Confirme em Commit changes e aguarde o deploy ficar Live. Mantenha o Start Command como bash start.sh.
5. A inicialização prepara automaticamente os arquivos de static e templates a partir de release-assets.zip e confere a integridade antes de acessar o banco.
6. No log, confira: Interface 5.1.36 conferida e Base completa conferida - versão 5.1.36.
7. Atualize o navegador com Ctrl + Shift + R e baixe novamente o PDF executivo.

IMPORTANTE: release-assets.zip é um arquivo do programa e deve permanecer fechado na raiz do GitHub. O próprio serviço o utiliza para preparar as pastas de interface.

Esta preparação altera somente os arquivos de interface do programa. Não apague, restaure ou reimporte os dados do Neon. Os usuários, cutovers, PDVs e históricos já salvos permanecem no banco existente.
