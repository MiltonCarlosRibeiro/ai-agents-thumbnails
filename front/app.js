(function () {
  const $ = (id) => document.getElementById(id);
  const INTERVALO = 3000;
  let ultimo = null;

  function carregar() {
    const s = document.createElement("script");
    s.src = `data.js?t=${Date.now()}`;
    s.onload = s.onerror = () => {
      s.remove();
      atualizar(window.RESULTADO);
    };
    document.body.appendChild(s);
  }

  function atualizar(data) {
    const chave = data ? `${data.status}|${data.gerado_em}` : "vazio";
    if (chave !== ultimo) {
      ultimo = chave;
      render(data);
    }
    setTimeout(carregar, INTERVALO);
  }

  function limpar() {
    $("grid").innerHTML = "";
    $("roteiro").innerHTML = "";
    $("vazio").hidden = true;
    $("escolha").hidden = true;
    $("roteiro-box").hidden = true;
  }

  function render(data) {
    limpar();

    if (!data) {
      $("titulo").textContent = "SNES Thumbnails";
      $("meta").textContent = "Aguardando o run.bat…";
      $("vazio").innerHTML = "Nenhuma thumbnail gerada ainda.<br>Rode <code>run.bat</code> para começar.";
      $("vazio").hidden = false;
      return;
    }

    if (data.status === "gerando") {
      $("titulo").textContent = "Gerando…";
      $("meta").textContent = `Tema: ${data.query}`;
      $("meta").classList.add("pulsando");
      [1, 2, 3].forEach(() => {
        const card = document.createElement("article");
        card.className = "card carregando";
        card.innerHTML = '<div class="thumb"></div><div class="info"><span class="num">…</span></div>';
        $("grid").appendChild(card);
      });
      return;
    }

    $("meta").classList.remove("pulsando");

    if (data.status === "erro") {
      $("titulo").textContent = "Algo deu errado";
      $("meta").textContent = `Tema: ${data.query}`;
      $("vazio").textContent = data.mensagem || "Veja as mensagens no terminal.";
      $("vazio").hidden = false;
      return;
    }

    $("titulo").textContent = data.titulo_video;
    $("meta").textContent = `Tema: ${data.query} · gerado em ${new Date(data.gerado_em).toLocaleString("pt-BR")}`;
    document.title = data.titulo_video;

    const bust = encodeURIComponent(data.gerado_em);

    [...data.thumbnails]
      .sort((a, b) => a.numero - b.numero)
      .forEach((t) => {
        const escolhida = t.numero === data.escolhida;
        const card = document.createElement("article");
        card.className = "card" + (escolhida ? " escolhida" : "");
        card.innerHTML = `
          <div class="thumb">
            <span class="falta">imagem não encontrada</span>
            <img alt="">
            ${escolhida ? '<span class="badge">escolhida</span>' : ""}
          </div>
          <div class="info">
            <span class="num">#${t.numero}</span>
            <h3></h3>
            <p></p>
          </div>`;

        const img = card.querySelector("img");
        img.src = `${t.arquivo}?v=${bust}`;
        img.alt = t.titulo;
        img.onerror = () => img.remove();
        card.querySelector("h3").textContent = t.titulo;
        card.querySelector("p").textContent = t.descricao;
        $("grid").appendChild(card);
      });

    const escolhida = data.thumbnails.find((t) => t.numero === data.escolhida);
    const img = $("escolhida-img");
    img.hidden = !escolhida;
    if (escolhida) {
      img.src = `${escolhida.arquivo}?v=${bust}`;
      img.alt = escolhida.titulo;
      img.onerror = () => (img.hidden = true);
    }
    $("escolhida-num").textContent = `#${data.escolhida}`;
    $("justificativa").textContent = data.justificativa;
    $("escolha").hidden = false;

    secoes(data.roteiro).forEach(({ titulo, corpo }) => {
      const card = document.createElement("article");
      card.className = "card";
      const h3 = document.createElement("h3");
      h3.textContent = titulo;
      const corpoEl = document.createElement("div");
      if (window.marked) {
        corpoEl.innerHTML = marked.parse(corpo.replace(/^#{3,} /gm, "#### "));
      } else {
        card.classList.add("texto");
        corpoEl.textContent = corpo;
      }
      card.append(h3, corpoEl);
      $("roteiro").appendChild(card);
    });
    $("roteiro-box").hidden = false;
  }

  function secoes(md) {
    const limpo = md
      .split("\n")
      .filter((l) => !/^# /.test(l) && !/^-{3,}\s*$/.test(l))
      .join("\n");
    return limpo
      .split(/^## /m)
      .map((bloco, i) => {
        if (i === 0) return { titulo: "Abertura", corpo: bloco.trim() };
        const [titulo, ...resto] = bloco.split("\n");
        return { titulo: titulo.trim(), corpo: resto.join("\n").trim() };
      })
      .filter((s) => s.corpo);
  }

  carregar();
})();
