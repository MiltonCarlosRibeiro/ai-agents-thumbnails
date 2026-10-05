import base64
import json
import os
import sys
import threading
import traceback
import webbrowser
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import List, Type

from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool
from dotenv import load_dotenv
from openai import BadRequestError, OpenAI
from pydantic import BaseModel, Field

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

load_dotenv()

ROOT = Path(__file__).parent
FRONT_DIR = ROOT / "front"
THUMBS_DIR = FRONT_DIR / "thumbnails"
OUTPUT_DIR = ROOT / "output"

DEFAULT_QUERY = "Os 5 melhores jogos de SNES de todos os tempos"
LLM = os.getenv("MODEL", "gpt-4o-mini")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-1")
FRONT_PORT = int(os.getenv("FRONT_PORT", "8765"))

IDIOMA = (
    " Escreva sempre em portugues do Brasil, mesmo que as fontes da pesquisa "
    "estejam em ingles, espanhol ou outro idioma. Nunca responda em outra lingua."
)

THUMB_STYLE = (
    " Style: YouTube thumbnail, 16:9, bold composition, 16-bit 1990s pixel art "
    "aesthetic, saturated retro colors, CRT glow, high contrast, original "
    "characters, no text, no logos."
)

THUMB_FALLBACK = (
    "An original retro adventure scene in pixel art: a heroic adventurer in a "
    "colorful fantasy landscape with castles, glowing collectibles and a dramatic sky."
)


class SearchInput(BaseModel):
    query: str = Field(..., description="Termo de busca")


class DuckDuckGoSearchTool(BaseTool):
    name: str = "duckduckgo_search"
    description: str = (
        "Pesquisa na web usando o DuckDuckGo. Use para buscar fatos, datas de "
        "lancamento, curiosidades e recepcao de jogos de SNES."
    )
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, query: str) -> str:
        try:
            results = DDGS().text(query, region="br-pt", max_results=6)
        except Exception as e:
            return f"Erro na pesquisa: {e}"
        if not results:
            return "Nenhum resultado encontrado."
        return "\n\n".join(
            f"- {r.get('title')}\n  {r.get('body')}\n  Fonte: {r.get('href')}"
            for r in results
        )


class ThumbnailInput(BaseModel):
    numero: int = Field(..., description="Numero da thumbnail: 1, 2 ou 3")
    prompt: str = Field(
        ...,
        description=(
            "Descricao visual detalhada da cena, em ingles. Descreva cenario, "
            "personagens e cores sem citar marcas ou nomes registrados."
        ),
    )


class ThumbnailGeneratorTool(BaseTool):
    name: str = "thumbnail_generator"
    description: str = (
        "Gera uma imagem de thumbnail e salva como thumb_<numero>.png. "
        "Chame uma vez para cada thumbnail (numero 1, 2 e 3)."
    )
    args_schema: Type[BaseModel] = ThumbnailInput

    def _run(self, numero: int, prompt: str) -> str:
        if numero not in (1, 2, 3):
            return "Erro: numero deve ser 1, 2 ou 3."

        try:
            data = generate_image(prompt)
            aviso = ""
        except BadRequestError as e:
            if "safety" not in str(e):
                return f"Erro ao gerar a imagem: {e}"
            try:
                data = generate_image(THUMB_FALLBACK)
                aviso = " O prompt original foi recusado; foi usada uma cena generica."
            except Exception as e2:
                return f"Erro ao gerar a imagem (reescreva o prompt e tente de novo): {e2}"
        except Exception as e:
            return f"Erro ao gerar a imagem (reescreva o prompt e tente de novo): {e}"

        file = f"thumbnails/thumb_{numero}.png"
        (FRONT_DIR / file).write_bytes(data)
        return f"Thumbnail {numero} salva em '{file}'.{aviso}"


def generate_image(prompt: str) -> bytes:
    kwargs = {"model": IMAGE_MODEL, "prompt": prompt + THUMB_STYLE, "n": 1}
    if IMAGE_MODEL.startswith("dall-e"):
        kwargs.update(size="1792x1024", response_format="b64_json")
    else:
        kwargs.update(size="1536x1024", moderation="low")
    resp = OpenAI().images.generate(**kwargs)
    return base64.b64decode(resp.data[0].b64_json)


class Thumbnail(BaseModel):
    numero: int = Field(..., description="1, 2 ou 3")
    titulo: str = Field(..., description="Texto curto e chamativo para a thumbnail")
    descricao: str = Field(..., description="Descricao da cena, em portugues")
    arquivo: str = Field(..., description="Ex.: thumbnails/thumb_1.png")


class Resultado(BaseModel):
    titulo_video: str
    roteiro: str = Field(..., description="Roteiro final revisado, em Markdown")
    thumbnails: List[Thumbnail]
    escolhida: int = Field(..., description="Numero da thumbnail escolhida")
    justificativa: str


def build_crew() -> Crew:
    roteirista = Agent(
        role="Roteirista de Video",
        goal="Pesquisar e escrever um roteiro completo e envolvente para YouTube sobre {query}",
        backstory=(
            "Voce e um roteirista especialista em storytelling para canais de games "
            "retro. Cresceu jogando Super Nintendo e conhece a fundo a era 16-bit, "
            "mas sempre confirma fatos com pesquisa antes de escrever."
            + IDIOMA
        ),
        tools=[DuckDuckGoSearchTool()],
        llm=LLM,
        verbose=True,
    )

    designer = Agent(
        role="Criador de Thumbnail",
        goal="Criar tres thumbnails chamativas e distintas inspiradas no roteiro",
        backstory=(
            "Voce e um designer grafico especializado em thumbnails de alto CTR para "
            "o YouTube, com paixao por pixel art e pela estetica do SNES."
            + IDIOMA
        ),
        tools=[ThumbnailGeneratorTool()],
        llm=LLM,
        verbose=True,
    )

    revisor = Agent(
        role="Revisor",
        goal="Revisar o roteiro, montar a versao final e escolher a melhor thumbnail",
        backstory=(
            "Voce e um editor-chefe exigente de um canal de games. Corrige texto, "
            "ritmo e fatos e decide qual thumbnail tem mais chance de gerar cliques."
            + IDIOMA
        ),
        llm=LLM,
        verbose=True,
    )

    tarefa_roteiro = Task(
        description=(
            "Pesquise com a ferramenta de busca sobre: {query}. Foque em jogos de "
            "Super Nintendo (SNES). Escreva um roteiro em portugues do Brasil para "
            "um video de 8 a 12 minutos com: gancho inicial, introducao, um bloco "
            "por jogo (historia, curiosidades, por que marcou epoca) e conclusao "
            "com call to action."
            + IDIOMA
        ),
        expected_output="Roteiro completo em Markdown, em portugues do Brasil, com titulos por secao.",
        agent=roteirista,
    )

    tarefa_thumbs = Task(
        description=(
            "Com base no roteiro, crie TRES conceitos de thumbnail bem diferentes "
            "entre si (ex.: nostalgia, acao, misterio). Para cada um, chame a "
            "ferramenta thumbnail_generator com numero 1, 2 e 3 e um prompt visual "
            "em ingles. Nao cite nomes de personagens ou marcas registradas no "
            "prompt e nao descreva consoles, controles ou mascotes reais; crie "
            "cenas e personagens originais que lembrem a epoca."
        ),
        expected_output=(
            "Lista com as 3 thumbnails: numero, titulo curto, descricao da cena em "
            "portugues e arquivo gerado."
        ),
        agent=designer,
        context=[tarefa_roteiro],
    )

    tarefa_revisao = Task(
        description=(
            "Revise o roteiro (gramatica, ritmo, precisao) e monte a versao final. "
            "Inclua as 3 thumbnails exatamente com os arquivos gerados e escolha a "
            "melhor para o video, justificando em uma ou duas frases. Se algum "
            "trecho do roteiro estiver em outro idioma, traduza para portugues."
            + IDIOMA
        ),
        expected_output="Resultado estruturado com roteiro, thumbnails e a escolhida.",
        agent=revisor,
        context=[tarefa_roteiro, tarefa_thumbs],
        output_pydantic=Resultado,
    )

    return Crew(
        agents=[roteirista, designer, revisor],
        tasks=[tarefa_roteiro, tarefa_thumbs, tarefa_revisao],
        process=Process.sequential,
        verbose=True,
    )


def write_status(query: str, status: str, **extra) -> None:
    payload = {
        "status": status,
        "query": query,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        **extra,
    }
    (FRONT_DIR / "data.js").write_text(
        "window.RESULTADO = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


def save(query: str, resultado: Resultado) -> None:
    write_status(query, "pronto", **resultado.model_dump())

    roteiro = resultado.roteiro.strip()
    md = [] if roteiro.startswith("# ") else [f"# {resultado.titulo_video}", ""]
    md += [roteiro, "", "## Thumbnails", ""]
    for t in resultado.thumbnails:
        marca = " (escolhida)" if t.numero == resultado.escolhida else ""
        md += [f"### {t.numero}. {t.titulo}{marca}", "", t.descricao, "",
               f"![thumb {t.numero}](../front/{t.arquivo})", ""]
    md += ["## Por que essa thumbnail?", "", resultado.justificativa, ""]
    (OUTPUT_DIR / "roteiro.md").write_text("\n".join(md), encoding="utf-8")


class FrontHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONT_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


class FrontServer(ThreadingHTTPServer):
    allow_reuse_address = False


def start_front() -> str:
    for port in range(FRONT_PORT, FRONT_PORT + 20):
        try:
            server = FrontServer(("127.0.0.1", port), FrontHandler)
        except OSError:
            continue
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return f"http://localhost:{port}/"
    raise RuntimeError("Nenhuma porta livre para o front.")


def main() -> None:
    query = " ".join(sys.argv[1:]).strip() or DEFAULT_QUERY

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    for old in THUMBS_DIR.glob("thumb_*.png"):
        old.unlink()

    write_status(query, "gerando")
    url = start_front()
    print(f"Front em {url}\n")
    webbrowser.open(url)

    ok = True
    try:
        result = build_crew().kickoff(inputs={"query": query})
        save(query, result.pydantic)
        print(f"\nPronto! Resultado em {url} e em output/roteiro.md.")
    except Exception as e:
        ok = False
        write_status(query, "erro", mensagem=str(e))
        traceback.print_exc()
    except BaseException as e:
        write_status(query, "erro", mensagem=f"Execucao interrompida ({type(e).__name__}).")
        raise

    input("\nPressione ENTER para fechar o front...")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
