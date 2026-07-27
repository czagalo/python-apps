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


def remover_marca_dagua_por_texto_alvo(pdf_entrada: str, pdf_saida: str, texto_alvo: str):
    doc = fitz.open(pdf_entrada)
    paginas_modificadas = 0

    # --- MONTAGEM DAS ÂNCORAS DERIVADAS EXCLUSIVAMENTE DO TEXTO_ALVO ---
    ancoras_busca = [texto_alvo]
    
    # Adiciona versão do texto_alvo sem acentos
    texto_sem_acento = remover_acentos(texto_alvo)
    if texto_sem_acento != texto_alvo:
        ancoras_busca.append(texto_sem_acento)

    # Extrai palavras significativas (mais de 3 letras) do próprio texto_alvo
    # Exemplo: de "Licenciado para Célio", extrai "Licenciado", "Célio", "Celio"
    palavras_alvo = []
    for palavra in texto_alvo.split():
        p_limpa = palavra.strip("()[]{}|*#-,.")
        if len(p_limpa) > 3:
            palavras_alvo.append(p_limpa)
            palavras_alvo.append(remover_acentos(p_limpa))

    print(f"Iniciando Pipeline via Texto Alvo: '{texto_alvo}'...\n")

    for num_pagina, pagina in enumerate(doc, start=1):
        modificou = False

        # --- PASSO 1: Mapeia as coordenadas X, Y usando o texto_alvo e derivadas ---
        rects_encontrados = []
        
        # 1º Tenta a frase exata ou sem acentos
        for anc in ancoras_busca:
            ocorrencias = pagina.search_for(anc)
            for r in ocorrencias:
                rects_encontrados.append(r)

        # 2º Se não achou a frase inteira, usa as palavras longas do texto_alvo
        if not rects_encontrados:
            for pal in set(palavras_alvo):
                ocorrencias = pagina.search_for(pal)
                for r in ocorrencias:
                    rects_encontrados.append(r)

        if not rects_encontrados:
            continue

        # Agrupa faixas Y (suporta licenças no topo E no rodapé)
        faixas_y = []
        for r in rects_encontrados:
            y_min = r.y0 - 3.0
            y_max = r.y1 + 3.0
            if not any(abs(f[0] - y_min) < 5.0 for f in faixas_y):
                faixas_y.append((y_min, y_max))

        # Processa cada faixa Y identificada
        for y_min, y_max in faixas_y:
            
            # Descobre o texto impresso naquela linha específica
            rect_faixa = fitz.Rect(0, y_min - 2.0, pagina.rect.width, y_max + 2.0)
            texto_frase_detectada = pagina.get_text("text", clip=rect_faixa).strip()
            
            fragmentos_linha = [
                p.strip("()[]{}|*#-,.") 
                for p in texto_frase_detectada.split() 
                if len(p.strip("()[]{}|*#-,.")) > 1
            ]

            # --- TENTATIVA 1: Substituição no Stream Direto ---
            for stream_id in pagina.get_contents():
                stream_bytes = doc.xref_stream(stream_id)
                if not stream_bytes:
                    continue

                stream_texto = stream_bytes.decode("latin1", errors="ignore")
                stream_alterado = stream_texto

                # Limpa a frase detectada e fragmentos do texto_alvo
                if texto_frase_detectada and texto_frase_detectada in stream_alterado:
                    stream_alterado = stream_alterado.replace(
                        texto_frase_detectada, " " * len(texto_frase_detectada)
                    )
                    modificou = True

                for p in fragmentos_linha:
                    if p in stream_alterado:
                        stream_alterado = stream_alterado.replace(p, " " * len(p))
                        modificou = True

                if modificou:
                    doc.update_stream(stream_id, stream_alterado.encode("latin1"))

            if modificou:
                pagina.clean_contents()

            # VISÃO COMPUTACIONAL CHECA (Pós-Tentativa 1)
            residuos = obter_residuos_visiveis_na_faixa_y(pagina, y_min, y_max)
            if not residuos:
                print(f"-> [Pág {num_pagina}] Sucesso na Tentativa 1 (ASCII)! Faixa Y 100% limpa.")
                continue  # PARAGEM IMEDIATA!

            # --- TENTATIVA 2: Injeção do '3 Tr' (Invisibilidade de Glifos) ---
            print(f"-> [Pág {num_pagina}] Resíduo na faixa Y: {residuos}. Aplicando Tentativa 2 (3 Tr)...")
            for stream_id in pagina.get_contents():
                stream_bytes = doc.xref_stream(stream_id)
                if not stream_bytes:
                    continue

                stream_texto = stream_bytes.decode("latin1", errors="ignore")

                def anular_instrucao_segura(match):
                    instrucao = match.group(0)
                    if any(res in instrucao for res in residuos):
                        return f"\n3 Tr\n{instrucao}\n0 Tr\n"
                    return instrucao

                stream_alterado = re.sub(
                    r"(\[.*?\]|\(.*?\))\s*(Tj|TJ)",
                    anular_instrucao_segura,
                    stream_texto,
                    flags=re.DOTALL
                )

                if stream_alterado != stream_texto:
                    doc.update_stream(stream_id, stream_alterado.encode("latin1"))
                    modificou = True

            if modificou:
                pagina.clean_contents()

            # VISÃO COMPUTACIONAL CHECA (Pós-Tentativa 2)
            residuos = obter_residuos_visiveis_na_faixa_y(pagina, y_min, y_max)
            if not residuos:
                print(f"-> [Pág {num_pagina}] Sucesso na Tentativa 2 (3 Tr)! Resíduos zerados.")
                continue  # PARAGEM IMEDIATA!

            # --- TENTATIVA 3: Redação Vetorial Estrita ---
            print(f"-> [Pág {num_pagina}] Resíduo persistente: {residuos}. Aplicando Tentativa 3 (Redação de Caixa)...")
            caixa_resíduo = fitz.Rect(0, y_min - 3.0, pagina.rect.width, y_max + 3.0)
            pagina.add_redact_annot(caixa_resíduo, fill=None)
            pagina.apply_redactions(graphics=1, text=1, images=0)
            modificou = True

            if modificou:
                pagina.clean_contents()

        if modificou:
            paginas_modificadas += 1

    doc.save(
        pdf_saida,
        garbage=4,
        deflate=True,
        clean=True,
    )
    doc.close()

    print(f"\nConcluído com sucesso! {paginas_modificadas} páginas salvas.")


if __name__ == "__main__":
    PASTA_BASE = Path(__file__).parent
    ARQUIVO_ENTRADA = PASTA_BASE / "pdfs_originais" / "nome_pdf.pdf"
    ARQUIVO_SAIDA = PASTA_BASE / "pdfs_limpos" / "nome_pdf_limpo.pdf"

    # Informe a frase do texto_alvo normalmente
    texto_alvo = "Informe o texto que deverá ser removido aqui!"

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