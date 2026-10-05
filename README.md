# AI Agents Thumbnails

Gera roteiro e três thumbnails para vídeos de YouTube sobre jogos retrô de Super Nintendo, usando CrewAI e DuckDuckGo. O resultado é exibido em uma página estática.

Desafio do curso IA para Devs da Rocketseat (Nível 5). Mais detalhes em [DESAFIO.md](DESAFIO.md).

## Requisitos

- Windows
- Python 3.10 a 3.13
- Chave da OpenAI

## Como rodar

Execute o `run.bat`. Na primeira vez ele cria o `.venv`, instala as dependências e abre o `.env` para você colocar a `OPENAI_API_KEY`. Salve e execute de novo.

Depois é só informar o tema do vídeo. O front abre no navegador em `http://localhost:8765` assim que os agentes começam, mostra que está gerando e se atualiza sozinho com as thumbnails e o roteiro quando terminar. Deixe a janela do terminal aberta: ao fechá-la, o front para de responder.

O tema também pode ir como argumento:

```bat
run.bat "Os chefes mais dificeis do SNES"
```

Ou direto pelo Python:

```bash
python main.py "RPGs esquecidos do Super Nintendo"
```

## Variáveis de ambiente

- `OPENAI_API_KEY`: obrigatória.
- `MODEL`: modelo de texto dos agentes. Padrão `gpt-4o-mini`.
- `IMAGE_MODEL`: `gpt-image-1` (padrão) ou `dall-e-3`.
- `FRONT_PORT`: porta do front. Padrão `8765`; se estiver ocupada, usa a próxima livre.

## Estrutura

```
ai-agents-thumbnails/
├── main.py
├── run.bat
├── requirements.txt
├── .env.example
├── front/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   ├── data.js
│   └── thumbnails/
└── output/
    └── roteiro.md
```

`front/data.js`, `front/thumbnails/` e `output/roteiro.md` são gerados a cada execução.

## Observações

- O front é servido pelo próprio `main.py`. Abrir o `index.html` direto do disco (`file://`) não funciona bem, porque o navegador isola arquivos locais.
- Cada execução gera três imagens na OpenAI, o que tem custo.
- O DuckDuckGo pode limitar as buscas se o script rodar várias vezes seguidas.
- Os modelos de imagem recusam nomes de personagens registrados, então o prompt descreve os personagens em vez de citá-los.
