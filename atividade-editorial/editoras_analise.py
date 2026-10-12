#!/usr/bin/env python3
"""Análise das editoras (tipo de registo Heurist "Editora") da BD livpoesia.

Uso: python3 -I editoras_analise.py <export.json> <pasta_saida>

Produz:
  editoras_ativas_por_ano.png   gráfico de barras 2000-2019
  editoras_grupos.png           distribuiçom das editoras por grupo de produçom
  editoras_analise.xlsx         tabelas completas
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ANO_MIN, ANO_MAX = 2000, 2019
ANOS = list(range(ANO_MIN, ANO_MAX + 1))

# dty_ID dos campos usados
F_NOME, F_NORMALIZADO, F_INICIO, F_FIM = 1, 1038, 10, 11
F_EDITORA, F_ANO, F_NATUREZA = 950, 952, 999
AUTOEDICAO = "Edição de autor"

GRUPOS = [  # (rótulo, limite inferior inclusivo)
    ("A. menos de 1 por ano", 0),
    ("B. 1 a 1,9 por ano", 1),
    ("C. 2 a 2,9 por ano", 2),
    ("D. 3 ou mais por ano", 3),
]
PONTUAL = "0. pontual (publicou num único ano)"


def vals(rec, dty):
    return [d["value"] for d in rec["details"] if d["dty_ID"] == dty]


def grupo(media):
    rotulo = GRUPOS[0][0]
    for r, lim in GRUPOS:
        if media >= lim:
            rotulo = r
    return rotulo


def carregar(caminho):
    recs = json.load(open(caminho, encoding="utf-8"))["heurist"]["records"]
    editoras = [r for r in recs if r["rec_RecTypeName"] == "Editora"]
    livros = [r for r in recs if r["rec_RecTypeName"] == "Livro"]
    return editoras, livros


def analisar(editoras, livros, por_registo=False):
    """Devolve um DataFrame com uma linha por editora.

    Unidade: o "Nome normalizado" (que funde variantes do mesmo selo), exceto
    nas auto-edições, onde cada registo é um autor-editor distinto. Com
    por_registo=True usa-se cada registo Editora como unidade.
    """
    chave_de = {}
    unidades = defaultdict(lambda: {"registos": [], "inicio": [], "fim": [], "aberto": False})
    for r in editoras:
        nome = (vals(r, F_NOME) or [r["rec_Title"]])[0]
        norm = (vals(r, F_NORMALIZADO) or [None])[0]
        auto = norm == AUTOEDICAO
        if por_registo or auto or not norm:
            chave, rotulo = "id:" + r["rec_ID"], nome
        else:
            chave, rotulo = "n:" + norm, norm
        chave_de[r["rec_ID"]] = chave
        u = unidades[chave]
        u["nome"], u["auto"] = rotulo, auto
        u["registos"].append(nome)
        ini, fim = vals(r, F_INICIO), vals(r, F_FIM)
        u["inicio"] += ini
        u["fim"] += fim
        if ini and not fim:
            u["aberto"] = True  # início documentado, sem data de fim: continua ativa

    # cada livro conta uma vez para cada editora (unidade) que o assina
    anos_livros = defaultdict(list)
    natureza = defaultdict(Counter)
    for l in livros:
        ano = vals(l, F_ANO)[0]
        nat = [d.get("termLabel") for d in l["details"] if d["dty_ID"] == F_NATUREZA]
        for chave in {chave_de[v["id"]] for v in vals(l, F_EDITORA)}:
            anos_livros[chave].append(ano)
            natureza[chave].update(nat)

    linhas = []
    for chave, u in unidades.items():
        ys = sorted(y for y in anos_livros[chave] if ANO_MIN <= y <= ANO_MAX)
        if not ys:
            continue
        doc_ini = min(u["inicio"]) if u["inicio"] else None
        doc_fim = None if (u["aberto"] or not u["fim"]) else max(u["fim"])
        # período de atividade: datas documentadas quando existem; senom, do
        # primeiro ao último livro no corpus. Alarga-se sempre para cobrir os
        # livros observados e corta-se a 2000-2019.
        ini = doc_ini if doc_ini is not None else ys[0]
        fim = doc_fim if doc_fim is not None else (ANO_MAX if doc_ini is not None else ys[-1])
        ini, fim = max(ANO_MIN, min(ini, ys[0])), min(ANO_MAX, max(fim, ys[-1]))
        fora = (doc_ini is not None and ys[0] < doc_ini) or (doc_fim is not None and ys[-1] > doc_fim)
        n_anos = fim - ini + 1
        media = len(ys) / n_anos
        linhas.append({
            "Editora": u["nome"],
            "Auto-edição": "sim" if u["auto"] else "",
            "Natureza (mais frequente)": natureza[chave].most_common(1)[0][0] if natureza[chave] else "",
            "N.º registos Editora": len(u["registos"]),
            "Início documentado": doc_ini,
            "Fim documentado": doc_fim,
            "Fonte das datas": "documentada" if doc_ini is not None else "inferida dos livros",
            "Livros fora das datas documentadas": "sim" if fora else "",
            "Ativa desde (2000-2019)": ini,
            "Ativa até (2000-2019)": fim,
            "Anos de atividade": n_anos,
            "Livros 2000-2019": len(ys),
            "Anos com publicaçom": len(set(ys)),
            "Média livros/ano": round(media, 3),
            "Grupo": grupo(media),
            "Grupo (com pontuais à parte)": PONTUAL if len(set(ys)) == 1 else grupo(media),
            "_anos_pub": set(ys),
            "Variantes (registos)": " | ".join(sorted(set(u["registos"]))) if len(u["registos"]) > 1 else "",
        })
    df = pd.DataFrame(linhas).sort_values(["Média livros/ano", "Livros 2000-2019"], ascending=False)
    return df.reset_index(drop=True)


def por_ano(df):
    linhas = []
    for a in ANOS:
        em_ativ = df[(df["Ativa desde (2000-2019)"] <= a) & (df["Ativa até (2000-2019)"] >= a)]
        com_pub = int(sum(a in s for s in df["_anos_pub"]))
        linhas.append({
            "Ano": a,
            "Editoras com publicaçom no ano": com_pub,
            "Em atividade sem publicaçom no ano": len(em_ativ) - com_pub,
            "Editoras em atividade (total)": len(em_ativ),
        })
    return pd.DataFrame(linhas)


def resumo(df, coluna):
    g = df.groupby(coluna).agg(
        Editoras=("Editora", "size"),
        Livros=("Livros 2000-2019", "sum"),
        Mediana_anos_atividade=("Anos de atividade", "median"),
    ).reset_index()
    g["% editoras"] = (100 * g["Editoras"] / g["Editoras"].sum()).round(1)
    g["% livros"] = (100 * g["Livros"] / g["Livros"].sum()).round(1)
    return g.rename(columns={"Mediana_anos_atividade": "Mediana anos de atividade"})


# --- gráficos -------------------------------------------------------------
SUP, TINTA, TINTA2, MUDO, GRELHA = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e6e5e0"
AZUL, AZUL_CLARO = "#2a78d6", "#9ec5f4"


def estilo(ax):
    ax.set_facecolor(SUP)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUDO)
    ax.tick_params(colors=TINTA2, length=0, labelsize=10)
    ax.yaxis.grid(True, color=GRELHA, linewidth=0.8)
    ax.set_axisbelow(True)


def grafico_ano(pa, destino):
    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=160, facecolor=SUP)
    estilo(ax)
    x = pa["Ano"]
    a, b = pa["Editoras com publicaçom no ano"], pa["Em atividade sem publicaçom no ano"]
    ax.bar(x, a, width=0.72, color=AZUL, edgecolor=SUP, linewidth=1.2, label="Com pelo menos um livro publicado no ano")
    ax.bar(x, b, bottom=a, width=0.72, color=AZUL_CLARO, edgecolor=SUP, linewidth=1.2,
           label="Em atividade, sem livros no ano")
    for xi, ai, ti in zip(x, a, a + b):
        ax.text(xi, ai - 3, str(ai), ha="center", va="top", fontsize=8.5, color="white")
        ax.text(xi, ti + 2, str(ti), ha="center", va="bottom", fontsize=8.5, color=TINTA2)
    ax.set_xticks(list(x))
    ax.set_xlim(ANO_MIN - 0.7, ANO_MAX + 0.7)
    ax.set_ylim(0, (a + b).max() * 1.12)
    fig.suptitle("Editoras ativas por ano, 2000-2019", x=0.075, y=0.97, ha="left", fontsize=14, color=TINTA, weight="bold")
    ax.set_title("N.º de editoras de poesia. Barra completa = editoras dentro do seu período de atividade",
                 loc="left", fontsize=10, color=TINTA2, pad=28)
    ax.legend(loc="upper left", bbox_to_anchor=(0, 1.085), ncol=2, frameon=False, fontsize=9.5, labelcolor=TINTA2)
    fig.tight_layout(rect=(0.03, 0, 1, 0.985))
    fig.savefig(destino, facecolor=SUP)
    plt.close(fig)


def grafico_grupos(res, destino):
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=160, facecolor=SUP)
    estilo(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=GRELHA, linewidth=0.8)
    rot = list(res.iloc[:, 0])[::-1]
    n = list(res["Editoras"])[::-1]
    liv = list(res["% livros"])[::-1]
    pe = list(res["% editoras"])[::-1]
    ax.barh(rot, n, height=0.6, color=AZUL)
    for i, (ni, p, pl) in enumerate(zip(n, pe, liv)):
        ax.text(ni + max(n) * 0.012, i, f"{ni} editoras ({p:.0f} %) · {pl:.0f} % dos livros".replace(".", ","),
                va="center", fontsize=9.5, color=TINTA2)
    ax.set_xlim(0, max(n) * 1.85)
    ax.tick_params(axis="y", labelsize=10.5, colors=TINTA)
    fig.suptitle("Editoras por média de livros publicados por ano de atividade", x=0.03, ha="left",
                 fontsize=13, color=TINTA, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(destino, facecolor=SUP)
    plt.close(fig)


def main():
    origem, saida = sys.argv[1], Path(sys.argv[2])
    editoras, livros = carregar(origem)
    df = analisar(editoras, livros)
    pa = por_ano(df)
    res4 = resumo(df, "Grupo")
    res5 = resumo(df, "Grupo (com pontuais à parte)")
    df_reg = analisar(editoras, livros, por_registo=True)

    grafico_ano(pa, saida / "editoras_ativas_por_ano.png")
    grafico_grupos(res5, saida / "editoras_grupos.png")

    notas = pd.DataFrame({"Notas metodológicas": [
        f"Fonte: {Path(origem).name}. {len(editoras)} registos Editora, {len(livros)} registos Livro (anos {ANO_MIN}-{ANO_MAX}).",
        "Unidade de análise: 'Nome normalizado' da editora (funde variantes do mesmo selo); nas auto-edições cada registo conta como editora própria.",
        "Livros coeditados contam uma vez para cada editora. Livros sem editora associada ficam de fora.",
        "Período de atividade: datas Start/End do registo quando existem (sem End = ativa até 2019); "
        "senom, do primeiro ao último livro no corpus. Alargado para cobrir livros fora das datas documentadas; cortado a 2000-2019.",
        "Média livros/ano = livros 2000-2019 / anos de atividade dentro de 2000-2019.",
        "Editora 'com publicaçom no ano' = pelo menos um livro com esse ano de publicaçom verificado.",
        "Folha 'Por registo (alternativa)': mesmos cálculos tomando cada registo Editora como unidade, sem normalizar.",
    ]})
    cols = [c for c in df.columns if not c.startswith("_")]
    with pd.ExcelWriter(saida / "editoras_analise.xlsx", engine="openpyxl") as xl:
        pa.to_excel(xl, sheet_name="1 Ativas por ano", index=False)
        df[cols].to_excel(xl, sheet_name="2 Média por editora", index=False)
        res4.to_excel(xl, sheet_name="3 Grupos", index=False, startrow=1)
        res5.to_excel(xl, sheet_name="3 Grupos", index=False, startrow=len(res4) + 5)
        df_reg[cols].to_excel(xl, sheet_name="Por registo (alternativa)", index=False)
        notas.to_excel(xl, sheet_name="Notas", index=False)
        ws = xl.sheets["3 Grupos"]
        ws.cell(1, 1, "Classificaçom pedida (4 grupos)")
        ws.cell(len(res4) + 5, 1, "Classificaçom proposta (editoras que publicárom num único ano à parte)")
        for ws in xl.sheets.values():
            ws.freeze_panes = "A2" if ws.title != "3 Grupos" else None
            for col in ws.columns:
                larg = max(len(str(c.value)) if c.value is not None else 0 for c in col[:60])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, larg + 2), 60)

    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_rows", 200)
    print("unidades:", len(df), "| por registo:", len(df_reg))
    print(pa.to_string(index=False))
    print(res4.to_string(index=False))
    print(res5.to_string(index=False))
    print(resumo(df_reg, "Grupo").to_string(index=False))
    print(df["Fonte das datas"].value_counts().to_string())
    print("livros fora das datas:", (df["Livros fora das datas documentadas"] == "sim").sum())

if __name__ == "__main__":
    main()
