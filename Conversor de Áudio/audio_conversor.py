import sys
import subprocess
from pathlib import Path

# Garante que o static-ffmpeg disponibilize o binário automaticamente
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except ImportError:
    print("[Aviso] A biblioteca 'static-ffmpeg' não está instalada.")
    print("Execute no terminal: python -m pip install static-ffmpeg")
    sys.exit(1)


# ==============================================================================
# CONFIGURAÇÕES DO PROJETO
# ==============================================================================
# Nomes das pastas do sistema
PASTA_ENTRADA = "audio_original"
PASTA_SAIDA   = "audio_convertido"

# Arquivo e formato de teste
NOME_ARQUIVO  = "meu_arquivo.mp4"  # Coloque este arquivo dentro da pasta 'audio_original'
FORMATO_SAIDA = "mp3"              # Formato desejado (ex: mp3, wav, flac, ogg)
# ==============================================================================


# Lista de formatos de áudio de saída suportados
FORMATOS_SUPORTADOS = [
    "mp3",  # Padrão universal
    "wav",  # Sem compressão / Produção
    "flac", # Sem perda de qualidade (Lossless)
    "m4a",  # Padrão Apple / AAC
    "aac",  # Código de áudio avançado
    "ogg",  # Formato aberto / Jogos / Spotify
    "opus", # Baixa latência / Voz
    "wma",  # Windows Media Audio
    "aiff", # Áudio de alta qualidade Apple
    "alac", # Apple Lossless
    "amr"   # Gravadores / Voz
]


def preparar_diretorios(dir_entrada: Path, dir_saida: Path):
    """Garante que as pastas de entrada e saída existam no disco."""
    dir_entrada.mkdir(parents=True, exist_ok=True)
    dir_saida.mkdir(parents=True, exist_ok=True)


def converter_midia(nome_arquivo: str, extensao_saida: str) -> bool:
    """
    Função pura de conversão.
    Busca o arquivo na pasta de entrada e salva o resultado na pasta de saída.
    """
    path_entrada = Path(PASTA_ENTRADA)
    path_saida   = Path(PASTA_SAIDA)

    # Garante que as pastas existam antes de rodar
    preparar_diretorios(path_entrada, path_saida)

    # Monta os caminhos completos dos arquivos
    arquivo_in = (path_entrada / nome_arquivo).resolve()

    # 1. Validação do arquivo de entrada
    if not arquivo_in.exists():
        print(f"❌ [Erro] O arquivo '{nome_arquivo}' não foi encontrado na pasta '{PASTA_ENTRADA}/'!")
        print(f"   Por favor, coloque o arquivo em: {path_entrada.resolve()}")
        return False

    if not arquivo_in.is_file():
        print(f"❌ [Erro] O caminho '{arquivo_in}' não é um arquivo válido.")
        return False

    # 2. Normalização do formato de saída
    ext_limpa = extensao_saida.strip(".").lower()

    if ext_limpa not in FORMATOS_SUPORTADOS:
        print(f"❌ [Erro] O formato '.{ext_limpa}' não está na lista de formatos suportados.")
        print(f"   Formatos válidos: {', '.join(FORMATOS_SUPORTADOS)}")
        return False

    # Define o caminho do arquivo de saída na pasta 'audio_convertido'
    nome_saida = arquivo_in.stem + f".{ext_limpa}"
    arquivo_out = (path_saida / nome_saida).resolve()

    # 3. Montagem do comando FFmpeg
    comando = [
        "ffmpeg",
        "-y",               # Sobrescreve se o arquivo já existir na pasta de saída
        "-i", str(arquivo_in),
        "-vn",              # Descarta a faixa de vídeo (se houver) extraindo apenas áudio
        str(arquivo_out)
    ]

    print(f"\n[Iniciando Conversão]")
    print(f"  ➜ Origem:  {PASTA_ENTRADA}/{arquivo_in.name}")
    print(f"  ➜ Destino: {PASTA_SAIDA}/{arquivo_out.name}")

    try:
        processo = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if processo.returncode == 0:
            print(f"\n✅ [Sucesso] Arquivo gerado em:\n   {arquivo_out}")
            return True
        else:
            print(f"\n❌ [Erro no FFmpeg] Falha ao processar o arquivo:\n{processo.stderr}")
            return False

    except Exception as e:
        print(f"\n❌ [Erro Inesperado] {e}")
        return False


if __name__ == "__main__":
    print("==================================================")
    print("   CONVERSOR & EXTRATOR DE ÁUDIO UNIVERSAL (Python)")
    print("==================================================")

    # Executa a conversão
    converter_midia(NOME_ARQUIVO, FORMATO_SAIDA)