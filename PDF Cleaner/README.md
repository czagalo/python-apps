# 📄 PDF Cleaner

O **PDF Cleaner** é um utilitário em Python projetado para remover marcas d'água, licenças e assinaturas personalizadas de arquivos PDF de forma cirúrgica, preservando 100% da integridade do texto original, fontes e imagens de fundo.

Diferente de métodos tradicionais de substituição bruta, o PDF Cleaner utiliza uma **arquitetura de execução em cascata** alimentada por um **loop de feedback de visão computacional/layout**, garantindo que apenas a camada da marca d'água seja removida, evitando falsos positivos que tornam o conteúdo do documento invisível.

---

## 💡 Como Funciona

A aplicação executa um fluxo inteligente de 6 etapas por página, operando em modo de parada imediata assim que a limpeza é confirmada:

1. **Mapeamento e Detecção de Posição ($Y$):**
   A aplicação analisa a página em busca do `texto_alvo` (ou de palavras-chave derivadas dele, com tolerância a variações de acentuação, espaços e codificações de fonte). Ela mapeia a coordenada exata de altura ($Y$) onde a marca d'água reside na página.

2. **Captura Dinâmica de Idioma e Estrutura:**
   Com base na coordenada $Y$ identificada, o sistema lê a linha do PDF para capturar dinamicamente a frase completa impressa. Essa etapa permite limpar automaticamente variações da licença em português (*"Licenciado para..."*), inglês (*"Licensed to..."*) ou qualquer outro idioma, sem a necessidade de alterar as configurações do script.

3. **Limpeza Primária no Stream (ASCII):**
   Acontece a primeira tentativa de remoção direta no código-fonte bruto do PDF (*Content Stream*), substituindo os caracteres do texto por espaços em branco para manter a estrutura e a contagem de bytes do arquivo intactas.

4. **Inspeção por Visão Computacional (Feedback Loop):**
   A aplicação renderiza e analisa em tempo real apenas a faixa de altura $Y$ mapeada no Passo 1, verificando se restaram resíduos visíveis (como parênteses soltos, glifos de fontes customizadas ou pontuações órfãs).
   - **Se a faixa estiver 100% limpa:** O processo para imediatamente para aquela página, salvando o documento e protegendo o conteúdo do livro.
   - **Se detectar resíduos:** A aplicação aciona automaticamente a próxima camada da cascata.

5. **Tratamento de Glifos e Injeção de Transparência `3 Tr` (Fallback 1):**
   Trata os resíduos como glifos mapeados por fontes internas e injeta a instrução de renderização invisível (`3 Tr ... 0 Tr`) exclusivamente nos operadores daquela faixa $Y$. A visão computacional inspeciona a linha novamente; se limpa, encerra o processamento da página.

6. **Redação Vetorial de Precisão (Fallback Final):**
   Se o resíduo persistir (caracteres desenhados como curvas/vetores *Line Art*), a aplicação aplica uma anotação de redação cirúrgica com opacidade neutra (`fill=None` e `images=0`), eliminando os traços vetoriais sem afetar elementos visuais ou ilustrações de fundo do documento.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.12+**
- **PyMuPDF (`fitz`)**: Manipulação de streams de PDF, parsing de layout e motor de renderização visual.
- **Regex (`re`)**: Análise e manipulação cirúrgica de instruções PostScript no *Content Stream*.