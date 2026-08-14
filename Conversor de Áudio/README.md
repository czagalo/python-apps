# 🎵 Conversor & Extrator de Áudio Universal (Python)

Uma aplicação em Python desenvolvida para conversão de formatos de áudio e extração automatizada de trilhas sonoras a partir de arquivos de vídeo. O projeto utiliza o **FFmpeg** gerenciado via `static-ffmpeg`, garantindo portabilidade total sem a necessidade de configurações manuais de ambiente no sistema operacional.

---

## 🚀 Funcionalidades

- **Entrada Universal:** Aceita qualquer formato de vídeo (`.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, etc.) ou áudio (`.wav`, `.flac`, `.ogg`, `.m4a`, etc.).
- **Extração de Áudio:** Remove automaticamente a faixa de vídeo caso o arquivo de entrada seja uma mídia de vídeo, gerando apenas o áudio resultante.
- **Organização Automática:** Gerencia e cria pastas isoladas de entrada (`audio_original/`) e saída (`audio_convertido/`).
- **Pronto para a Nuvem:** Utiliza binários estáticos via `static-ffmpeg`, tornando a aplicação 100% compatível com servidores Web e PaaS gratuitos (como **Render Free**, Railway, Fly.io e instâncias Linux).

---

## 🛠️ Pré-requisitos

- **Python 3.10+** (Testado no Python 3.12 no Windows 10)
- **Ambiente Virtual (`venv`)** ativado

---

## 📁 Estrutura de Pastas

```text
Conversor de Áudio/
│
├── audio_original/      # 📂 Coloque aqui os arquivos de vídeo ou áudio que deseja converter
├── audio_convertido/     # 📂 Pasta onde os arquivos convertidos serão salvos
├── audio_conversor.py    # 📄 Código principal da aplicação
├── README.md             # 📄 Documentação do projeto
```
---

## ⚙️ Como Usar

1. Coloque o arquivo de mídia que deseja converter dentro da pasta audio_original/.
2. Abra o arquivo audio_conversor.py e ajuste as variáveis de configuração no topo do script:

```python
NOME_ARQUIVO  = "seu_video_ou_audio.mp4" # Nome do arquivo que está em audio_original/
FORMATO_SAIDA = "mp3"                    # Extensão desejada para o arquivo final
```
3. Execute o script no terminal:
```python
python audio_conversor.py
```
4. O arquivo convertido será gerado dentro da pasta audio_convertido/.
---

## 🎧 Formatos de Saída Suportados

A aplicação suporta conversão para os seguintes formatos de áudio:

| Extensão | Descrição |
| :--- | :--- |
| **`.mp3`** | Padrão universal para música e áudio geral |
| **`.wav`** | Áudio sem compressão (qualidade de estúdio) |
| **`.flac`** | Compressão sem perda de qualidade (*Lossless*) |
| **`.m4a` / `.aac`** | Áudio de alta eficiência (Padrão Apple / Web) |
| **`.ogg`** | Formato livre e aberto (muito usado em jogos) |
| **`.opus`** | Formato otimizado para transmissões de voz e chamadas |
| **`.wma`** | Windows Media Audio |
| **`.aiff` / `.alac`** | Formatos Apple de alta fidelidade |
| **`.amr`** | Otimizado para gravação de voz humana |
---
