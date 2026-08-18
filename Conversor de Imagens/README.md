# Conversor de Imagens

Uma ferramenta automatizada em Python desenvolvida para conversão de ativos visuais. O script permite converter imagens entre diversos formatos rasterizados (PNG, JPG, WEBP, BMP, TIF) e vetoriais (SVG), preservando cores originais, transparência (canal alpha) e aplicando diferentes perfis de fidelidade/qualidade de saída.
---
## Como Funciona

O aplicativo executa três fluxos principais de conversão dependendo dos formatos de origem e destino selecionados:

- **Raster para Raster (ex: PNG $\rightarrow$ WEBP / JPG):** Processa e otimiza a grade de pixels com controle de compressão, tratando canais de transparência para evitar fundos pretos indesejados ao exportar para formatos sem canal alpha.
- **Raster para Vetor (ex: PNG/JPG $\rightarrow$ SVG):** Realiza a amostragem de cores RGB/RGBA por blocos, descarta pixels transparentes e agrupa coordenadas de mesma tonalidade em caminhos vetoriais (<path>), gerando arquivos SVG coloridos e escaláveis sem perder as cores da arte original.
- **Vetor para Raster (ex: SVG $\rightarrow$ PNG/WEBP):** Analisa a estrutura XML do arquivo vetorial e o renderiza em uma tela bitmap com multiplicador de escala ajustável de acordo com o perfil de qualidade desejado (chegando a renderizações em alta resolução).
---
## Bibliotecas Utilizadas
- **Pillow (PIL):** Processamento, manipulação de pixels, canais de cor e exportação de formatos rasterizados.
- **svgwrite:** Construção e geração do documento XML e elementos vetoriais SVG.
- **Pathlib / os (Módulos Nativos):** Manipulação e validação de caminhos do sistema de arquivos.
- **xml.etree.ElementTree (Módulo Nativo):** Leitura e extração de metadados de arquivos SVG.
---
## Estrutura de Diretórios

O script assume e cria automaticamente a seguinte organização de pastas na raiz do projeto:

```text
Conversor de Imagens/
├── img_conversor.py
├── imagem_original/     <-- Coloque a imagem de entrada aqui
└── imagem_convertida/    <-- O resultado processado será salvo aqui
```
---
## Passo a Passo para Utilização

1. Posicione o arquivo de origem:
Insira o arquivo de imagem que deseja converter dentro da pasta imagem_original/.
2. Edite o painel de configuração no código:
Abra o arquivo conversor.py no seu editor e altere os valores das variáveis localizadas no bloco ⚙️ PAINEL DE CONFIGURAÇÃO:

```python
# Exemplo de configuração no topo do arquivo conversor.py
NOME_IMAGEM_ORIGINAL = "personagem.png"  # Nome exato do arquivo na pasta imagem_original
EXTENSAO_SAIDA = "svg"                   # Formato final desejado (webp, png, svg, jpg, etc.)
QUALIDADE = "uhd"                        # Nível de fidelidade: "media", "alta" ou "uhd"
```

3. Perfis de Qualidade Disponíveis:
- **media:** Foco em otimização e tamanho reduzido de arquivo (ideal para jogos web leves).
- **alta:** Equilíbrio padrão entre peso e qualidade visual.
- **uhd:** Amostragem máxima pixel a pixel para vetorização detalhada ou renderização em resoluções elevadas.

4. Execute o script:
Rode o arquivo conversor.py. Ao finalizar o processamento, a mensagem de confirmação indicará o caminho do novo arquivo, localizado dentro da pasta imagem_convertida/ sob o nome nome_original_convertido.extensao.
