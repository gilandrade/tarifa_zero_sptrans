// Indice lateral de navegacao das paginas do relatorio.
//
// Escrito a mao. NAO colocar este codigo em tabelas.js: aquele arquivo e gerado e
// sobrescrito por scripts/gera_tabelas.py a cada execucao.
//
// Monta o indice a partir dos titulos da propria pagina, entao secoes novas aparecem
// sozinhas — nao ha lista de secoes para manter em sincronia.

(function () {
  "use strict";

  // Só entram os títulos que são filhos diretos de <main>. Os h3 que titulam caixas
  // (div.caixa) ficam de fora por construção — são rótulos de quadro, não subseções.
  var SELETOR_TITULOS = "main > h2, main > h3";
  var LARGURA_LATERAL = "(min-width: 1080px)";
  var OFFSET_ATIVO = 80; // px abaixo do topo: alinha o scrollspy com a nav sticky

  var caixa = document.getElementById("indice");
  if (!caixa) return;

  var lista = caixa.querySelector("ul");
  var titulos = Array.prototype.slice.call(document.querySelectorAll(SELETOR_TITULOS));

  // Página sem seções (mapas.html) não ganha índice.
  if (!lista || titulos.length < 2) {
    caixa.hidden = true;
    return;
  }

  // ==== ids ==========================================================================

  function slug(texto) {
    return texto
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "") // tira os diacriticos separados pelo NFD
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  var usados = {};
  titulos.forEach(function (titulo) {
    // ids que já existem no HTML são preservados: há links internos apontando para
    // #resumo, #territorio, #oferta, #confiavel, #ressalvas.
    if (!titulo.id) {
      var base = slug(titulo.textContent) || "secao";
      var id = base;
      var n = 2;
      while (usados[id] || document.getElementById(id)) {
        id = base + "-" + n++;
      }
      titulo.id = id;
    }
    usados[titulo.id] = true;
  });

  // ==== montagem =====================================================================

  var links = titulos.map(function (titulo) {
    var item = document.createElement("li");
    item.className = titulo.tagName === "H2" ? "n2" : "n3";

    var link = document.createElement("a");
    link.href = "#" + titulo.id;
    link.textContent = titulo.textContent;

    item.appendChild(link);
    lista.appendChild(item);
    return link;
  });

  // ==== scrollspy ====================================================================

  var ativo = null;

  function marcaAtivo() {
    var indice = 0;
    for (var i = 0; i < titulos.length; i++) {
      if (titulos[i].getBoundingClientRect().top <= OFFSET_ATIVO) {
        indice = i;
      } else {
        break; // titulos estao em ordem de documento
      }
    }

    var link = links[indice];
    if (link === ativo) return;

    if (ativo) {
      ativo.classList.remove("ativo");
      ativo.removeAttribute("aria-current");
    }
    link.classList.add("ativo");
    link.setAttribute("aria-current", "true");
    ativo = link;

    // Mantem o item ativo visivel quando o proprio indice tem barra de rolagem.
    if (caixa.scrollHeight > caixa.clientHeight) {
      var alvo = link.getBoundingClientRect();
      var moldura = caixa.getBoundingClientRect();
      if (alvo.top < moldura.top || alvo.bottom > moldura.bottom) {
        caixa.scrollTop += alvo.top - moldura.top - moldura.height / 2;
      }
    }
  }

  var agendado = false;
  function aoRolar() {
    if (agendado) return;
    agendado = true;
    window.requestAnimationFrame(function () {
      agendado = false;
      marcaAtivo();
    });
  }

  window.addEventListener("scroll", aoRolar, { passive: true });
  window.addEventListener("resize", aoRolar);
  marcaAtivo();

  // ==== aberto na lateral, recolhido em tela estreita =================================

  var telaLarga = window.matchMedia(LARGURA_LATERAL);

  function sincronizaAbertura(mq) {
    caixa.open = mq.matches;
  }

  sincronizaAbertura(telaLarga);
  if (telaLarga.addEventListener) {
    telaLarga.addEventListener("change", sincronizaAbertura);
  } else {
    telaLarga.addListener(sincronizaAbertura); // Safari < 14
  }

  // Em tela estreita, escolher um destino fecha o indice para nao tapar o conteudo.
  lista.addEventListener("click", function (evento) {
    if (evento.target.tagName === "A" && !telaLarga.matches) {
      caixa.open = false;
    }
  });
})();
