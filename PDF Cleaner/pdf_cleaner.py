from pathlib import Path
import re
import unicodedata
import fitz  # PyMuPDF


def remover_acentos(texto: str) -> str:
    """Normaliza o texto e remove caracteres acentuados (ex: 'Célio' -> 'Celio')."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def obter_residuos_visiveis_na_faixa_y(pagina, y_min: float, y_max: float) -> list[str]:
    """Passo de Visão Computacional: lê estritamente a faixa Y da licença."""
    rect_linha = fitz.Rect(0, y_min - 3.0, pagina.rect.width, y_max + 3.0)
    texto_visivel = pagina.get_text("text", clip=rect_linha).strip()

    if not texto_visivel:
        return []

    return [frag.strip() for frag in texto_visivel.split() if len(frag.strip()) > 0]


def gerar_padroes_contextuais_dinamicos(texto_alvo: str, texto_frase_detectada: str) -> list[str]:
    """Gera combinações de vizinhança (N-Grams) de forma 100% dinâmica a partir do texto_alvo."""
    padroes = []

    # 1. Frase completa detectada na faixa Y (Prioridade Máxima)
    if texto_frase_detectada:
        padroes.append(texto_frase_detectada)

    # 2. Frase completa passada no texto_alvo
    if texto_alvo and texto_alvo not in padroes:
        padroes.append(texto_alvo)

    # Limpa pontuações para quebrar em palavras limpas
    palavras = [p.strip("()[]{}|*#-,.<>") for p in texto_alvo.split() if len(p.strip("()[]{}|*#-,.<>")) > 0]

    # 3. Gera N-Grams de vizinhança (blocos de 4, 3 e 2 palavras vizinhas)
    for n in range(min(4, len(palavras)), 1, -1):
        for i in range(len(palavras) - n + 1):
            bloco = " ".join(palavras[i : i + n])
            if len(bloco) >= 5 and bloco not in padroes:
                padroes.append(bloco)

    # 4. Captura termos de alta fidelidade (E-mails, códigos com @ ou números longos)
    for p in palavras:
        if "@" in p or (len(p) > 6 and any(c.isdigit() for c in p)):
            if p not in padroes:
                padroes.append(p)

    return padroes


def remover_marca_dagua_por_texto_alvo(pdf_entrada: str, pdf_saida: str, texto_alvo: str):
    doc = fitz.open(pdf_entrada)
    paginas_modificadas = 0

    # Âncoras primárias derivadas exclusivamente da entrada
    ancoras_busca = [texto_alvo]
    texto_sem_acento = remover_acentos(texto_alvo)
    if texto_sem_acento != texto_alvo:
        ancoras_busca.append(texto_sem_acento)

    # Termos significativos (mais de 3 letras) para localização inicial da coordenada Y
    palavras_alvo_busca = []
    for palavra in texto_alvo.split():
        p_limpa = palavra.strip("()[]{}|*#-,.<>")
        if len(p_limpa) > 3:
            palavras_alvo_busca.append(p_limpa)
            palavras_alvo_busca.append(remover_acentos(p_limpa))

    palavras_alvo_busca = list(set(palavras_alvo_busca))

    print(f"Iniciando Pipeline Dinâmico por Vizinhança para: '{texto_alvo}'...\n")

    for num_pagina, pagina in enumerate(doc, start=1):
        modificou = False

        # --- PASSO 1: Mapeia as coordenadas X, Y usando o texto_alvo e derivadas ---
        rects_encontrados = []
        
        for anc in ancoras_busca:
            ocorrencias = pagina.search_for(anc)
            for r in ocorrencias:
                rects_encontrados.append(r)

        if not rects_encontrados:
            for pal in palavras_alvo_busca:
                ocorrencias = pagina.search_for(pal)
                for r in ocorrencias:
                    rects_encontrados.append(r)

        if not rects_encontrados:
            continue

        # Agrupa faixas Y estritas no topo/rodapé
        faixas_y = []
        for r in rects_encontrados:
            y_min = r.y0 - 4.0
            y_max = r.y1 + 4.0
            if not any(abs(f[0] - y_min) < 6.0 for f in faixas_y):
                faixas_y.append((y_min, y_max))

        for y_min, y_max in faixas_y:
            rect_faixa = fitz.Rect(0, y_min, pagina.rect.width, y_max)
            texto_frase_detectada = pagina.get_text("text", clip=rect_faixa).strip()

            # GERADOR DINÂMICO DE PADRÕES CONTEXTUAIS
            padroes_contextuais = gerar_padroes_contextuais_dinamicos(
                texto_alvo=texto_alvo,
                texto_frase_detectada=texto_frase_detectada
            )

            # --- TENTATIVA 1: Substituição Segura por Padrões Contextuais (Preserva Bytes) ---
            for stream_id in pagina.get_contents():
                stream_bytes = doc.xref_stream(stream_id)
                if not stream_bytes:
                    continue

                stream_texto = stream_bytes.decode("latin1", errors="ignore")
                stream_alterado = stream_texto

                for padrao in padroes_contextuais:
                    if padrao in stream_alterado:
                        stream_alterado = stream_alterado.replace(padrao, " " * len(padrao))
                        modificou = True

                if modificou:
                    doc.update_stream(stream_id, stream_alterado.encode("latin1"))

            # VISÃO COMPUTACIONAL CHECA (Pós-Tentativa 1)
            residuos = obter_residuos_visiveis_na_faixa_y(pagina, y_min, y_max)
            if not residuos:
                print(f"-> [Pág {num_pagina}] Sucesso na Tentativa 1! Faixa Y 100% limpa.")
                continue

            # --- TENTATIVA 2: Injeção do '3 Tr' para Combinações do Alvo na Faixa Y ---
            print(f"-> [Pág {num_pagina}] Resíduo na faixa Y: {residuos}. Aplicando Tentativa 2 (3 Tr por Vizinhança)...")
            for stream_id in pagina.get_contents():
                stream_bytes = doc.xref_stream(stream_id)
                if not stream_bytes:
                    continue

                stream_texto = stream_bytes.decode("latin1", errors="ignore")

                def anular_instrucao_contextual(match):
                    instrucao = match.group(0)
                    if any(padrao in instrucao for padrao in padroes_contextuais if len(padrao) >= 4):
                        return f"\n3 Tr\n{instrucao}\n0 Tr\n"
                    return instrucao

                stream_alterado = re.sub(
                    r"(\[.*?\]|\(.*?\))\s*(Tj|TJ)",
                    anular_instrucao_contextual,
                    stream_texto,
                    flags=re.DOTALL
                )

                if stream_alterado != stream_texto:
                    doc.update_stream(stream_id, stream_alterado.encode("latin1"))
                    modificou = True

            # VISÃO COMPUTACIONAL CHECA (Pós-Tentativa 2)
            residuos = obter_residuos_visiveis_na_faixa_y(pagina, y_min, y_max)
            if not residuos:
                print(f"-> [Pág {num_pagina}] Sucesso na Tentativa 2! Resíduos zerados.")
                continue

            # --- TENTATIVA 3: Substituição Contextual Segura dentro de XObjects ---
            print(f"-> [Pág {num_pagina}] Resíduo em XObject: {residuos}. Aplicando Tentativa 3 (XObject Contextual)...")
            
            xobjects_pagina = pagina.get_xobjects()
            for xobj in xobjects_pagina:
                xref = xobj[0]
                stream_xobj = doc.xref_stream(xref)
                if not stream_xobj:
                    continue

                texto_xobj = stream_xobj.decode("latin1", errors="ignore")
                texto_xobj_alterado = texto_xobj
                alterou_xobj = False

                for padrao in padroes_contextuais:
                    if padrao in texto_xobj_alterado:
                        texto_xobj_alterado = texto_xobj_alterado.replace(padrao, " " * len(padrao))
                        alterou_xobj = True

                if alterou_xobj:
                    doc.update_stream(xref, texto_xobj_alterado.encode("latin1"))
                    modificou = True

            # VISÃO COMPUTACIONAL CHECA (Pós-Tentativa 3)
            residuos = obter_residuos_visiveis_na_faixa_y(pagina, y_min, y_max)
            if not residuos:
                print(f"-> [Pág {num_pagina}] Sucesso na Tentativa 3 (XObject Contextual)! Faixa Y limpa.")
                continue

            # --- TENTATIVA 4: Substituição do Resíduo de Parênteses Escapados Cercados por Espaços ---
            print(f"-> [Pág {num_pagina}] Resíduos visíveis: {residuos}. Aplicando Tentativa 4 (Limpeza de Resíduos Escapados com Espaços)...")

            def limpar_parenteses_com_espacos_residuais(match):
                instrucao_completa = match.group(0)
                conteudo = match.group(1)

                # Identifica se a instrução tem parênteses escapados (\( ou \)) cercados por 2 ou mais espaços
                tem_parentese_orfao_com_espacos = (
                    bool(re.search(r"\s{2,}\\\(\s*", conteudo)) or 
                    bool(re.search(r"\s*\\\)\s{2,}", conteudo)) or
                    bool(re.search(r"\s+\\\(\s+", conteudo)) or
                    bool(re.search(r"\s+\\\)\s+", conteudo))
                )

                if tem_parentese_orfao_com_espacos:
                    # Troca apenas o \( e o \) escapados que sobraram isolados por dois espaços '  '
                    conteudo_limpo = conteudo.replace(r"\(", "  ").replace(r"\)", "  ")
                    # Mantém a estrutura exterior da instrução TJ/Tj intacta
                    return instrucao_completa.replace(conteudo, conteudo_limpo)

                return instrucao_completa

            # 1. Aplica nos Streams de Conteúdo Principais
            for stream_id in pagina.get_contents():
                stream_bytes = doc.xref_stream(stream_id)
                if not stream_bytes:
                    continue

                stream_texto = stream_bytes.decode("latin1", errors="ignore")
                stream_alterado = re.sub(
                    r"(\[.*?\]|\(.*?\))\s*(TJ|Tj)",
                    limpar_parenteses_com_espacos_residuais,
                    stream_texto,
                    flags=re.DOTALL
                )

                if stream_alterado != stream_texto:
                    doc.update_stream(stream_id, stream_alterado.encode("latin1"))
                    modificou = True

            # 2. Aplica nos XObjects da Página
            for xobj in xobjects_pagina:
                xref = xobj[0]
                stream_xobj = doc.xref_stream(xref)
                if not stream_xobj:
                    continue

                texto_xobj = stream_xobj.decode("latin1", errors="ignore")
                texto_xobj_alterado = re.sub(
                    r"(\[.*?\]|\(.*?\))\s*(TJ|Tj)",
                    limpar_parenteses_com_espacos_residuais,
                    texto_xobj,
                    flags=re.DOTALL
                )

                if texto_xobj_alterado != texto_xobj:
                    doc.update_stream(xref, texto_xobj_alterado.encode("latin1"))
                    modificou = True

            # VISÃO COMPUTACIONAL CHECA (Pós-Tentativa 4)
            residuos = obter_residuos_visiveis_na_faixa_y(pagina, y_min, y_max)
            if not residuos:
                print(f"-> [Pág {num_pagina}] Sucesso na Tentativa 4! Faixa Y 100% limpa.")
                continue

        if modificou:
            paginas_modificadas += 1

    doc.save(
        pdf_saida,
        garbage=3,
        deflate=True,
    )
    doc.close()

    print(f"\nConcluído com sucesso! {paginas_modificadas} páginas salvas.")


if __name__ == "__main__":
    PASTA_BASE = Path(__file__).parent
    ARQUIVO_ENTRADA = PASTA_BASE / "pdfs_originais" / "nome_pdf.pdf"
    ARQUIVO_SAIDA = PASTA_BASE / "pdfs_limpos" / "nome_pdf_limpo.pdf"

    texto_alvo = "Escreva aqui o texto alvo que deseja remover do PDF."

    (PASTA_BASE / "pdfs_originais").mkdir(exist_ok=True)
    (PASTA_BASE / "pdfs_limpos").mkdir(exist_ok=True)

    if ARQUIVO_ENTRADA.exists():
        remover_marca_dagua_por_texto_alvo(
            pdf_entrada=str(ARQUIVO_ENTRADA),
            pdf_saida=str(ARQUIVO_SAIDA),
            texto_alvo=texto_alvo,
        )
    else:
        print(f"Coloque o seu arquivo PDF em: {ARQUIVO_ENTRADA}")