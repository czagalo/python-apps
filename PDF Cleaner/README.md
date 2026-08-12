# 📄 PDF Cleaner

O **PDF Cleaner** é uma ferramenta em Python criada para remover marcas d'água, licenças e assinaturas personalizadas de arquivos PDF de forma cirúrgica, preservando 100% da integridade do texto original, da formatação e dos gráficos de fundo.

Diferente de ferramentas convencionais que aplicam tarjas ou cortes brutos, o PDF Cleaner utiliza uma **arquitetura de execução em cascata** guiada por um **loop de verificação visual em tempo real**. Isso garante que apenas os resíduos da marca d'água sejam removidos, sem apagar o conteúdo legítimo do documento.

---

## 💡 Como Funciona

A aplicação utiliza uma estratégia inteligente dividida em duas fases: **Preparação Dinâmica** e **Pipeline de Limpeza em Cascata (4 Tentativas)**.

### 📍 Fase 1: Mapeamento e Análise Dinâmica
1. **Mapeamento de Coordenadas ($Y$):** O script localiza o texto-alvo na página e identifica a altura exata ($Y$) onde a marca d'água está impressa.
2. **Gerador Contextual de Padrões:** A partir do texto-alvo e da linha lida na página, a aplicação gera dinamicamente várias combinações de palavras (N-Grams) e variações sem acento. Isso permite limpar licenças em português, inglês ou qualquer outro idioma de forma automática.

---

### 🔄 Fase 2: Pipeline de Limpeza em Cascata

A página passa por até **4 tentativas de limpeza**. Após cada tentativa, um inspetor de **Visão Computacional** lê exclusivamente a faixa $Y$ do rodapé/topo. Se a faixa estiver 100% limpa, o script interrompe o processo naquela página e salva o arquivo, protegendo o restante do livro.

```text
[Mapeamento Y] ➔ [Tentativa 1] ➔ Limpo? ➔ (Fim da Página)
│ (Não)
[Tentativa 2] ➔ Limpo? ➔ (Fim da Página)
│ (Não)
[Tentativa 3] ➔ Limpo? ➔ (Fim da Página)
│ (Não)
[Tentativa 4] ➔ Limpo? ➔ (Fim da Página)
```

#### 🛡️ As 4 Camadas de Remoção:

* **Tentativa 1: Substituição Direta no Stream (Preservação de Bytes)**
  Substitui os padrões de texto da licença por espaços em branco no código bruto do PDF (*Content Stream*). Mantém o tamanho exato do arquivo sem corromper a estrutura.

* **Tentativa 2: Modo de Renderização Invisível (`3 Tr`)**
  Caso o texto persista por conta de codificações especiais de fonte, a aplicação injeta instruções sintáticas do PDF para tornar a renderização daqueles caracteres invisível (`3 Tr`), sem afetar a linha ao redor.

* **Tentativa 3: Varredura em Formulários e Objetos Aninhados (XObjects)**
  Procura e limpa os padrões da licença em sub-streams e recursos gráficos compartilhados (*XObjects/Forms*), cobrindo marcas d'água inseridas como modelos externos.

* **Tentativa 4: Remoção de Símbolos e Parênteses Escapados (`\(` e `\)`)**
  Para casos difíceis em que a licença usa parênteses no e-mail ou símbolos de escape do PDF. Quando a Tentativa 1 limpa o e-mail, restam parênteses isolados em meio a espaços vazios. A Tentativa 4 identifica cirurgicamente esses parênteses órfãos cercados por espaços e os anula, eliminando os resíduos finais sem tocar nos parênteses do texto do livro.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.12+**
- **PyMuPDF (`fitz`)**: Extração de layout, parsing de streams e motor de inspeção visual.
- **Regex (`re`)**: Manipulação e análise cirúrgica das instruções de texto no *Content Stream*.

---