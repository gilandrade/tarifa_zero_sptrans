"""Gera docs/tabelas.js a partir das tabelas de resultado exportadas pelos notebooks.

Etapa B do fluxo de publicação (ver PLAN.md / CLAUDE.md, seção "Publicação"). Os notebooks
(Etapa A) exportam cada DataFrame de resultado em ``.to_parquet(...)``; este script só lê,
formata em HTML (separador decimal brasileiro, milhar com ponto) e escreve um único
``docs/tabelas.js`` com o dicionário ``TABELAS`` consumido pelas páginas do site.

Uso:
    python scripts/gera_tabelas.py

Roda a partir da raiz do repositório. Falha explicitamente (mensagem clara, sem gerar um
tabelas.js pela metade) se um parquet esperado não existir — rodar sem antes reexecutar os
notebooks deve ser óbvio, não produzir um site silenciosamente incompleto.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_TABELAS_03 = RAIZ / "outputs" / "03" / "tabelas"
PARQUET_DIAG = RAIZ / "outputs" / "01" / "diag_bases_por_domingo.parquet"
PARQUET_OFICIAL = RAIZ / "outputs" / "01" / "Dados_4Meses_Domingos_2023_2024_site.parquet"
SAIDA_JS = RAIZ / "docs" / "tabelas.js"


# ==== formatação ======================================================================

def fmt_num(v, casas: int) -> str:
    """Formata um número no padrão brasileiro (vírgula decimal, ponto de milhar)."""
    if pd.isna(v):
        return "—"
    texto = f"{v:,.{casas}f}"  # ex.: "1,234.5" (vírgula = separador de milhar, ponto = decimal)
    # troca via placeholder: "," (milhar) -> "@", "." (decimal) -> ",", "@" -> "."
    texto = texto.replace(",", "@").replace(".", ",").replace("@", ".")
    return texto


def formata_valor(v, casas: int) -> str:
    if pd.isna(v):
        return "—"
    if isinstance(v, (int, float, np.integer, np.floating)):
        v = float(v)
        if casas == 0 or v == int(v):
            return fmt_num(v, 0 if casas == 0 else casas)
        return fmt_num(v, casas)
    return str(v)


@dataclass
class Coluna:
    nome: str
    rotulo: str | None = None
    casas: int = 1
    destaque: bool = False


@dataclass
class Tabela:
    """Especificação de uma tabela: de onde ler e como formatar."""

    chave: str
    fonte: Path
    rotulo_indice: str
    colunas: list[Coluna]
    ordenar_por: str | None = None
    ascendente: bool = True

    def carrega(self) -> pd.DataFrame:
        if not self.fonte.exists():
            raise FileNotFoundError(
                f"Tabela '{self.chave}': esperava encontrar {self.fonte}, mas o arquivo não existe.\n"
                f"  -> rode (ou reexecute) o notebook que exporta essa tabela antes de rodar este script."
            )
        df = pd.read_parquet(self.fonte)
        if self.ordenar_por is not None:
            if self.ordenar_por in df.columns:
                df = df.sort_values(self.ordenar_por, ascending=self.ascendente)
            elif df.index.name == self.ordenar_por:
                df = df.sort_index(ascending=self.ascendente)
        return df

    def renderiza(self) -> str:
        df = self.carrega()
        colunas_faltando = [c.nome for c in self.colunas if c.nome not in df.columns]
        if colunas_faltando:
            raise KeyError(
                f"Tabela '{self.chave}' ({self.fonte.name}): colunas esperadas ausentes {colunas_faltando}. "
                f"Colunas disponíveis: {list(df.columns)} (índice: {df.index.name})"
            )

        cabecalho = "".join(f"<th>{c.rotulo or c.nome}</th>" for c in self.colunas)
        linhas_html = [f"<thead><tr><th>{self.rotulo_indice}</th>{cabecalho}</tr></thead>"]

        corpo = []
        for idx, linha in df.iterrows():
            celulas = [f"<td>{idx}</td>"]
            for c in self.colunas:
                texto = formata_valor(linha[c.nome], c.casas)
                if c.destaque:
                    texto = f"<b>{texto}</b>"
                celulas.append(f"<td>{texto}</td>")
            corpo.append(f"<tr>{''.join(celulas)}</tr>")
        linhas_html.append(f"<tbody>{''.join(corpo)}</tbody>")

        return f'<table class="tabela">{"".join(linhas_html)}</table>'


# ==== recomputado direto dos parquets de outputs/01/ (sem tocar notebook algum) ======
# Réplica de 01_criacao_de_bases/04_diagnostico_domingos_antiga_vs_nova.ipynb, Seção 5 —
# a razão entre a bilhetagem de domingo (bruta e com linha) e o total oficial do mesmo
# domingo, por ano. Só usa outputs/01/diag_bases_por_domingo.parquet e a série oficial já
# compilada (outputs/01/Dados_4Meses_Domingos_2023_2024_site.parquet) — nenhum dos dois
# depende de reexecutar notebook 04, então esta tabela não é um to_parquet de notebook, é
# calculada aqui. Valores conferidos contra o notebook: 2023 r_com_linha=1,035±0,038,
# r_bruto=1,397±0,099; 2024 r_com_linha=0,999±0,037, r_bruto=1,269±0,040 (93 domingos
# comparáveis).

def tabela_razao_base_oficial() -> pd.DataFrame:
    if not PARQUET_DIAG.exists() or not PARQUET_OFICIAL.exists():
        faltando = [p for p in (PARQUET_DIAG, PARQUET_OFICIAL) if not p.exists()]
        raise FileNotFoundError(
            f"razao_base_oficial: arquivo(s) ausente(s): {[str(p) for p in faltando]}"
        )
    diag = pd.read_parquet(PARQUET_DIAG, columns=["data", "nova_bruto", "nova_com_linha"])
    site = pd.read_parquet(PARQUET_OFICIAL, columns=["data", "tipo_dia", "of_total"])
    oficial_domingo = (
        site.loc[site["tipo_dia"] == "domingo"]
        .groupby("data")["of_total"].sum()
        .rename("oficial_total")
    )
    m = diag.merge(oficial_domingo, on="data", how="inner")
    if m.empty:
        raise ValueError("razao_base_oficial: merge entre diag e oficial não encontrou domingos em comum.")
    m["Ano"] = m["data"].str[:4]
    m["r_bruto"] = m["nova_bruto"] / m["oficial_total"]
    m["r_com_linha"] = m["nova_com_linha"] / m["oficial_total"]
    return m.groupby("Ano").agg(
        r_com_linha_media=("r_com_linha", "mean"),
        r_com_linha_dp=("r_com_linha", "std"),
        r_bruto_media=("r_bruto", "mean"),
        r_bruto_dp=("r_bruto", "std"),
    )


def renderiza_computada(df: pd.DataFrame, rotulo_indice: str, colunas: list[Coluna]) -> str:
    """Mesmo formatador de Tabela.renderiza(), mas para DataFrames já computados em memória."""
    colunas_faltando = [c.nome for c in colunas if c.nome not in df.columns]
    if colunas_faltando:
        raise KeyError(f"colunas ausentes {colunas_faltando}; disponíveis: {list(df.columns)}")
    cabecalho = "".join(f"<th>{c.rotulo or c.nome}</th>" for c in colunas)
    linhas_html = [f"<thead><tr><th>{rotulo_indice}</th>{cabecalho}</tr></thead>"]
    corpo = []
    for idx, linha in df.iterrows():
        celulas = [f"<td>{idx}</td>"]
        for c in colunas:
            texto = formata_valor(linha[c.nome], c.casas)
            if c.destaque:
                texto = f"<b>{texto}</b>"
            celulas.append(f"<td>{texto}</td>")
        corpo.append(f"<tr>{''.join(celulas)}</tr>")
    linhas_html.append(f"<tbody>{''.join(corpo)}</tbody>")
    return f'<table class="tabela">{"".join(linhas_html)}</table>'


# ==== catálogo de tabelas exportadas pelos notebooks (Etapa A) =======================
# Cada entrada aqui tem um espelho em docs/index.html ou docs/metodologia.html como
# <div data-tabela="<chave>">. Se as chaves divergirem dos data-tabela dos HTMLs, a tabela
# fica com placeholder "não gerada" nas páginas mesmo depois de rodar este script.

TABELAS: dict[str, Tabela] = {}


def registra(t: Tabela) -> None:
    TABELAS[t.chave] = t


registra(Tabela(
    chave="resumo_fontes",
    fonte=DIR_TABELAS_03 / "resumo_fontes.parquet",
    rotulo_indice="fonte",
    colunas=[
        Coluna("PctDiff_domingo", "Δ% domingo", 2),
        Coluna("PctDiff_util", "Δ% dia útil", 2),
        Coluna("Sinal_tarifa_zero", "sinal (p.p.)", 1, destaque=True),
    ],
))

registra(Tabela(
    chave="tiers_periferia",
    fonte=DIR_TABELAS_03 / "tiers_periferia.parquet",
    rotulo_indice="tier",
    colunas=[
        Coluna("count", "nº de zonas", 0),
        Coluna("dist_media_km", "dist. média ao centro (km)", 1),
    ],
))

registra(Tabela(
    chave="sinal_por_tier_zona",
    fonte=DIR_TABELAS_03 / "sinal_por_tier_zona.parquet",
    rotulo_indice="tier",
    colunas=[
        Coluna("count", "nº de zonas", 0),
        Coluna("mediana", "mediana (p.p.)", 1, destaque=True),
        Coluna("media", "média (p.p.)", 1),
    ],
))

registra(Tabela(
    chave="robustez_zona_vs_linha",
    fonte=DIR_TABELAS_03 / "robustez_zona_vs_linha.parquet",
    rotulo_indice="tier",
    colunas=[
        Coluna("por_zona", "sinal por zona (p.p.)", 1),
        Coluna("por_linha", "sinal por linha (p.p.)", 1),
        Coluna("diferenca_pp", "diferença (p.p.)", 1),
    ],
))

registra(Tabela(
    chave="resumo_genero",
    fonte=DIR_TABELAS_03 / "resumo_genero.parquet",
    rotulo_indice="gênero",
    colunas=[
        Coluna("domingo_2023", "domingo 2023", 0),
        Coluna("domingo_2024", "domingo 2024", 0),
        Coluna("util_2023", "útil 2023", 0),
        Coluna("util_2024", "útil 2024", 0),
        Coluna("PctDiff_domingo", "Δ% domingo", 2),
        Coluna("PctDiff_util", "Δ% dia útil", 2),
        Coluna("Sinal_tarifa_zero", "sinal (p.p.)", 2, destaque=True),
    ],
))

registra(Tabela(
    chave="sinal_tier_genero",
    fonte=DIR_TABELAS_03 / "sinal_tier_genero.parquet",
    rotulo_indice="tier",
    colunas=[
        Coluna("F", "feminino (p.p.)", 1),
        Coluna("M", "masculino (p.p.)", 1),
    ],
))

registra(Tabela(
    chave="resumo_idade",
    fonte=DIR_TABELAS_03 / "resumo_idade.parquet",
    rotulo_indice="grupo etário",
    colunas=[
        Coluna("domingo_2023", "domingo 2023", 0),
        Coluna("domingo_2024", "domingo 2024", 0),
        Coluna("util_2023", "útil 2023", 0),
        Coluna("util_2024", "útil 2024", 0),
        Coluna("PctDiff_domingo", "Δ% domingo", 2),
        Coluna("PctDiff_util", "Δ% dia útil", 2),
        Coluna("Sinal_tarifa_zero", "sinal (p.p.)", 2, destaque=True),
    ],
))

registra(Tabela(
    chave="sinal_tier_idade",
    fonte=DIR_TABELAS_03 / "sinal_tier_idade.parquet",
    rotulo_indice="tier",
    colunas=[
        Coluna("60+", "60 anos ou mais (p.p.)", 1),
        Coluna("<60", "menos de 60 (p.p.)", 1),
    ],
))

registra(Tabela(
    chave="ratio_oferta_demanda_tier",
    fonte=DIR_TABELAS_03 / "ratio_oferta_demanda_tier.parquet",
    rotulo_indice="tier",
    colunas=[
        Coluna("Diff_Ratio_domingo", "Δ ratio domingo", 3),
        Coluna("Diff_Ratio_util", "Δ ratio dia útil", 3),
    ],
))

registra(Tabela(
    chave="heterogeneidade_frota",
    fonte=DIR_TABELAS_03 / "heterogeneidade_frota.parquet",
    rotulo_indice="métrica",
    colunas=[
        Coluna("valor", "valor", 1),
    ],
))

registra(Tabela(
    chave="validacao_por_linha",
    fonte=DIR_TABELAS_03 / "validacao_por_linha.parquet",
    rotulo_indice="ano / tipo de dia",
    colunas=[
        Coluna("count", "nº de linhas", 0),
        Coluna("p05", "p5", 3),
        Coluna("p25", "p25", 3),
        Coluna("p50", "mediana", 3, destaque=True),
        Coluna("p75", "p75", 3),
        Coluna("p95", "p95", 3),
    ],
))

registra(Tabela(
    chave="linhas_divergentes",
    fonte=DIR_TABELAS_03 / "linhas_divergentes.parquet",
    rotulo_indice="linha",
    colunas=[
        Coluna("Ano", "ano", 0),
        Coluna("oficial", "oficial", 0),
        Coluna("bilhetagem", "bilhetagem", 0),
        Coluna("razao", "razão", 3, destaque=True),
    ],
    ordenar_por="razao",
    ascendente=False,
))

registra(Tabela(
    chave="niveis_mes_ano",
    fonte=DIR_TABELAS_03 / "niveis_mes_ano.parquet",
    rotulo_indice="mês-ano",
    colunas=[
        Coluna("oficial_domingo", "oficial domingo", 0),
        Coluna("bilhetagem_domingo", "bilhetagem domingo", 0),
        Coluna("delta_domingo_pct", "Δ domingo (%)", 1, destaque=True),
        Coluna("oficial_util", "oficial útil", 0),
        Coluna("bilhetagem_util", "bilhetagem útil", 0),
        Coluna("delta_util_pct", "Δ útil (%)", 1, destaque=True),
    ],
))

registra(Tabela(
    chave="sinal_mes_ano",
    fonte=DIR_TABELAS_03 / "sinal_mes_ano.parquet",
    rotulo_indice="mês",
    colunas=[
        Coluna("oficial_dom_pct", "Δ% domingo (oficial)", 1),
        Coluna("oficial_util_pct", "Δ% útil (oficial)", 1),
        Coluna("oficial_sinal", "sinal oficial (p.p.)", 1, destaque=True),
        Coluna("bilhetagem_dom_pct", "Δ% domingo (bilhet.)", 1),
        Coluna("bilhetagem_util_pct", "Δ% útil (bilhet.)", 1),
        Coluna("bilhetagem_sinal", "sinal bilhetagem (p.p.)", 1, destaque=True),
    ],
))

registra(Tabela(
    chave="oficial_media_dia",
    fonte=DIR_TABELAS_03 / "oficial_media_dia.parquet",
    rotulo_indice="ano",
    colunas=[
        Coluna("domingo", "domingo (mi/dia)", 2),
        Coluna("sabado", "sábado (mi/dia)", 2),
        Coluna("util", "dia útil (mi/dia)", 2),
    ],
))


# ==== main =============================================================================

def main() -> int:
    saida: dict[str, str] = {}
    erros: list[str] = []

    for chave, tabela in TABELAS.items():
        try:
            saida[chave] = tabela.renderiza()
            print(f"  ok     {chave:28s} <- {tabela.fonte.relative_to(RAIZ)}")
        except (FileNotFoundError, KeyError) as e:
            erros.append(str(e))
            print(f"  FALHOU {chave:28s} {e}")

    try:
        saida["razao_base_oficial"] = renderiza_computada(
            tabela_razao_base_oficial(),
            rotulo_indice="ano",
            colunas=[
                Coluna("r_com_linha_media", "razão (com linha), média", 3, destaque=True),
                Coluna("r_com_linha_dp", "desvio-padrão", 3),
                Coluna("r_bruto_media", "razão (bruta), média", 3),
                Coluna("r_bruto_dp", "desvio-padrão", 3),
            ],
        )
        print(f"  ok     {'razao_base_oficial':28s} <- calculada de diag + série oficial")
    except (FileNotFoundError, KeyError, ValueError) as e:
        erros.append(str(e))
        print(f"  FALHOU {'razao_base_oficial':28s} {e}")

    if erros:
        print(
            f"\n{len(erros)} tabela(s) não puderam ser geradas (ver acima). "
            f"As demais {len(saida)} foram escritas normalmente em {SAIDA_JS.relative_to(RAIZ)}.",
            file=sys.stderr,
        )

    linhas_js = ["// GERADO por scripts/gera_tabelas.py — não editar à mão.", "const TABELAS = {"]
    for chave, html in saida.items():
        html_escapado = html.replace("\\", "\\\\").replace("`", "\\`")
        linhas_js.append(f'  "{chave}": `{html_escapado}`,')
    linhas_js.append("};")

    SAIDA_JS.write_text("\n".join(linhas_js) + "\n", encoding="utf-8")
    total = len(TABELAS) + 1  # +1 = razao_base_oficial, computada em vez de registrada
    print(f"\n{len(saida)}/{total} tabelas escritas em {SAIDA_JS.relative_to(RAIZ)}")

    return 1 if erros else 0


if __name__ == "__main__":
    raise SystemExit(main())
