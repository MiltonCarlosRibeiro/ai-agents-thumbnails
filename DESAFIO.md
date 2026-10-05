# Desafio Agentes IA

## Enunciado

Criar um sistema que gere roteiros para vídeos sobre videogames e, a partir do roteiro, produza três opções de thumbnail e escolha uma delas. A biblioteca sugerida é o CrewAI, e a entrada é um tema, por exemplo `inputs={'query': 'Melhores jogos de 2020'}`.

Nesta versão o tema é sempre ligado a jogos de Super Nintendo, e a pesquisa é feita no DuckDuckGo, que não precisa de chave de API.

## Fluxo

1. O Roteirista pesquisa o tema e escreve o roteiro.
2. O Criador de Thumbnail lê o roteiro, cria três ideias e gera uma imagem para cada.
3. O Revisor corrige o roteiro, junta tudo e escolhe a melhor thumbnail.

As tarefas rodam em sequência e cada uma recebe o resultado das anteriores.

## Agentes

**Roteirista de Vídeo.** Usa a busca do DuckDuckGo para levantar informações e escreve um roteiro de 8 a 12 minutos com gancho, introdução, um bloco por jogo e conclusão.

**Criador de Thumbnail.** Propõe três conceitos diferentes entre si e gera as imagens em `front/thumbnails/thumb_1.png`, `thumb_2.png` e `thumb_3.png`.

**Revisor.** Revisa texto e fatos, monta a versão final e indica qual thumbnail usar, com uma justificativa curta.

## Ferramentas

`DuckDuckGoSearchTool` faz a busca com o pacote `ddgs`, em português, e devolve título, resumo e link de cada resultado.

`ThumbnailGeneratorTool` recebe o número da thumbnail e um prompt em inglês. Ao prompt é somado um estilo fixo de pixel art 16-bit para as três imagens ficarem coerentes com o tema. A imagem é salva no disco, para não depender de links temporários.

## Saída

A tarefa do Revisor retorna um modelo Pydantic com título do vídeo, roteiro, as três thumbnails, o número da escolhida e a justificativa. Com isso o `main.py` grava:

- `front/data.js`, lido pela página;
- `output/roteiro.md`, com o roteiro e as imagens.

## Front

Página estática em `front/index.html`, com fonte Ubuntu e tema claro e escuro. Mostra as três thumbnails, destaca a escolhida, exibe a justificativa e o roteiro completo.

## Diferenças para a resolução oficial

- Tema focado em SNES em vez de um tema genérico.
- Busca pelo DuckDuckGo.
- Imagens salvas localmente em vez de links temporários.
- Saída estruturada com Pydantic.
- Página para visualizar o resultado e um `.bat` para rodar tudo.

## Melhorias possíveis

- Buscar datas e notas em APIs como IGDB ou MobyGames.
- Escrever o título na imagem com Pillow, já que os modelos de imagem costumam errar letras.
- Permitir votar na thumbnail pela página e usar o histórico para ajustar os prompts.
