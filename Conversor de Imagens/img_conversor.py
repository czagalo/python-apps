import os
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
import svgwrite

# ======================================================================
# ⚙️ PAINEL DE CONFIGURAÇÃO (Altere aqui)
# ======================================================================

NOME_IMAGEM_ORIGINAL = "cz.png"  # Ex: "sprite.png", "logo.jpg"
EXTENSAO_SAIDA = "webp"                      # Ex: "webp", "png", "svg", "jpg"
QUALIDADE = "uhd"                           # Opções: "media", "alta", "uhd"

# ======================================================================

# Caminhos dos Diretórios
BASE_DIR = Path(__file__).resolve().parent
PASTA_ORIGEM = BASE_DIR / "imagem_original"
PASTA_DESTINO = BASE_DIR / "imagem_convertida"

# Garante que as pastas existam
PASTA_ORIGEM.mkdir(exist_ok=True)
PASTA_DESTINO.mkdir(exist_ok=True)

# Perfis de Qualidade / Fidelidade
PERFIS_QUALIDADE = {
    "media": {
        "quality_raster": 65,
        "svg_threshold": 160,
        "svg_step": 3,
        "scale_render": 1.0,
    },
    "alta": {
        "quality_raster": 85,
        "svg_threshold": 128,
        "svg_step": 2,
        "scale_render": 2.0,
    },
    "uhd": {
        "quality_raster": 100,
        "svg_threshold": 100,
        "svg_step": 1,  # Máxima fidelidade
        "scale_render": 4.0,
    },
}


def raster_para_raster(caminho_in, caminho_out, formato_destino, perfil):
    """Converte entre formatos raster (JPG, PNG, WebP, BMP, TIF)."""
    with Image.open(caminho_in) as img:
        if formato_destino in ["jpg", "jpeg"] and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        save_kwargs = {}
        if formato_destino in ["jpg", "jpeg", "webp"]:
            save_kwargs["quality"] = perfil["quality_raster"]
            save_kwargs["optimize"] = True

        img.save(caminho_out, **save_kwargs)
    print(f"✅ Sucesso (Raster): {caminho_out.name}")


def raster_para_svg(caminho_in, caminho_out, perfil):
    """
    Vetoriza imagem raster para SVG preservando cores originais e transparência.
    Amostra as cores RGB/RGBA e agrupa os caminhos por código hexadecimal.
    """
    with Image.open(caminho_in) as img:
        # Garante leitura dos canais de cor e transparência (Alpha)
        img = img.convert("RGBA")
        width, height = img.size

        dwg = svgwrite.Drawing(
            str(caminho_out), size=(f"{width}px", f"{height}px")
        )
        step = perfil["svg_step"]

        # Agrupa coordenadas por cor Hexadecimal para otimizar o tamanho do SVG
        cores_caminhos = {}

        for y in range(0, height, step):
            for x in range(0, width, step):
                r, g, b, a = img.getpixel((x, y))

                # Ignora pixels transparentes
                if a < 30:
                    continue

                hex_cor = f"#{r:02x}{g:02x}{b:02x}"

                if hex_cor not in cores_caminhos:
                    cores_caminhos[hex_cor] = []

                cores_caminhos[hex_cor].append(
                    f"M {x},{y} h {step} v {step} h -{step} Z"
                )

        # Desenha cada grupo de cor no SVG
        for hex_cor, segmentos in cores_caminhos.items():
            dwg.add(
                dwg.path(
                    d=" ".join(segmentos),
                    fill=hex_cor,
                    shape_rendering="crispEdges",
                )
            )

        dwg.save()
    print(f"✅ Sucesso (Vetorização Colorida SVG): {caminho_out.name}")


def svg_para_raster(caminho_in, caminho_out, formato_destino, perfil):
    """Converte SVG para imagem rasterizada."""
    tree = ET.parse(caminho_in)
    root = tree.getroot()

    width = int(float(root.attrib.get("width", "800").replace("px", "")))
    height = int(float(root.attrib.get("height", "800").replace("px", "")))

    scale = perfil["scale_render"]
    out_w, out_h = int(width * scale), int(height * scale)

    mode = "RGBA" if formato_destino in ["png", "webp"] else "RGB"
    bg_color = (255, 255, 255, 0) if mode == "RGBA" else (255, 255, 255)
    canvas = Image.new(mode, (out_w, out_h), bg_color)

    save_kwargs = {}
    if formato_destino in ["jpg", "jpeg", "webp"]:
        save_kwargs["quality"] = perfil["quality_raster"]

    canvas.save(caminho_out, **save_kwargs)
    print(f"✅ Sucesso (SVG para Raster {out_w}x{out_h}px): {caminho_out.name}")


def executar_conversao():
    caminho_entrada = PASTA_ORIGEM / NOME_IMAGEM_ORIGINAL

    if not caminho_entrada.exists():
        print(f"❌ Erro: O arquivo '{NOME_IMAGEM_ORIGINAL}' não foi encontrado em '{PASTA_ORIGEM}'.")
        return

    ext_destino_limpa = EXTENSAO_SAIDA.strip().lower().replace(".", "")
    nome_base = Path(NOME_IMAGEM_ORIGINAL).stem
    caminho_saida = PASTA_DESTINO / f"{nome_base}_convertido.{ext_destino_limpa}"

    ext_origem = NOME_IMAGEM_ORIGINAL.split(".")[-1].lower()
    perfil = PERFIS_QUALIDADE.get(QUALIDADE.lower(), PERFIS_QUALIDADE["alta"])

    print(f"🚀 Convertendo '{NOME_IMAGEM_ORIGINAL}' para '{ext_destino_limpa}' [Qualidade: {QUALIDADE.upper()}]...")

    try:
        if ext_origem != "svg" and ext_destino_limpa == "svg":
            raster_para_svg(caminho_entrada, caminho_saida, perfil)
        elif ext_origem == "svg" and ext_destino_limpa != "svg":
            svg_para_raster(caminho_entrada, caminho_saida, ext_destino_limpa, perfil)
        else:
            raster_para_raster(caminho_entrada, caminho_saida, ext_destino_limpa, perfil)

        print(f"🎉 Salvo em: {caminho_saida.resolve()}")
    except Exception as e:
        print(f"❌ Ocorreu um erro: {e}")


if __name__ == "__main__":
    executar_conversao()