#!/usr/bin/env python3
"""Editoras ativas por ano (2000-2019), restringindo às editoras da planilha CSV.

Uso: python3 -I editoras_csv_ativas.py <export.json> <editoras.csv> <pasta_saida>

O CSV (separador ';', UTF-8) traz: Editora H-ID; Nome completo; Primeiro ano; Último ano.
O H-ID corresponde ao rec_ID do registo Editora no JSON.

Produz:
  editoras_csv_ativas_por_ano.png      barras: editoras ativas em cada ano
  editoras_csv_entradas_saidas.png     barras: incorporaçons e desapariçons por ano
  editoras_csv_ativas.xlsx             tabelas
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # necessário com python -I

import matplotlib.pyplot as plt
import pandas as pd

from editoras_analise import (ANO_MAX, ANO_MIN, ANOS, AZUL, AZUL_CLARO, F_ANO, F_EDITORA,
                              MUDO, SUP, TINTA, TINTA2, estilo, vals)

LARANJA = "#eb6834"
# H-ID do CSV que no JSON aparece com outro identificador (mesmo nome)
CORRESPONDENCIAS = {"4051": "3033"}  # Danú


def carregar(json_path, csv_path):
    recs = json.load(open(json_path, encoding="utf-8"))["heurist"]["records"]
    editoras = {r["rec_ID"]: r for r in recs if r["rec_RecTypeName"] == "Editora"}
    anos = defaultdict(list)
    for r in recs:
        if r["rec_RecTypeName"] == "Livro":
            for v in vals(r, F_EDITORA):
                anos[v["id"]].append(vals(r, F_ANO)[0])

    linhas = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for hid, nome, ini, fim in list(csv.reader(f, delimiter=";"))[1:]:
            if not hid:
                continue
            jid = CORRESPONDENCIAS.get(hid, hid)
            if jid not in editoras:
                raise SystemExit(f"H-ID {hid} ({nome}) nom existe como Editora no JSON")
            ys = sorted(y for y in anos[jid] if ANO_MIN <= y <= ANO_MAX)
            ini, fim = int(ini), (int(fim) if fim else None)
            # período de atividade: datas da planilha, alargadas para cobrir os
            # livros observados no JSON e cortadas a 2000-2019
            a = max(ANO_MIN, min([ini] + ys[:1]))
            b = min(ANO_MAX, max([fim if fim is not None else ANO_MAX] + ys[-1:]))
            fora = [y for y in ys if y < ini or (fim is not None and y > fim)]
            linhas.append({
                "H-ID": hid,
                "H-ID no JSON": jid if jid != hid else "",
                "Editora": nome,
                "Primeiro ano (CSV)": ini,
                "Último ano (CSV)": fim,
                "Ativa desde (2000-2019)": a,
                "Ativa até (2000-2019)": b,
                "Livros 2000-2019": len(ys),
                "Anos com publicaçom": len(set(ys)),
                "Livros fora das datas do CSV": ", ".join(map(str, fora)),
                "_anos_pub": set(ys),
                # entrada/saída observáveis dentro da janela
                "_entrada": a if min([ini] + ys[:1]) >= ANO_MIN else None,
                "_saida": b if (fim is not None and max([fim] + ys[-1:]) <= ANO_MAX) else None,
            })
    return pd.DataFrame(linhas)


def por_ano(df):
    linhas = []
    for a in ANOS:
        ativas = df[(df["Ativa desde (2000-2019)"] <= a) & (df["Ativa até (2000-2019)"] >= a)]
        com_pub = int(sum(a in s for s in ativas["_anos_pub"]))
        linhas.append({
            "Ano": a,
            "Editoras ativas": len(ativas),
            "Com livros de poesia no ano": com_pub,
            "Ativas sem livros no ano": len(ativas) - com_pub,
            "Incorporaçons (primeiro ano)": int((df["_entrada"] == a).sum()),
            "Desapariçons (último ano)": int((df["_saida"] == a).sum()),
        })
    return pd.DataFrame(linhas)


def grafico_ativas(pa, n, destino):
    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=160, facecolor=SUP)
    estilo(ax)
    x, a, b = pa["Ano"], pa["Com livros de poesia no ano"], pa["Ativas sem livros no ano"]
    ax.bar(x, a, width=0.72, color=AZUL, edgecolor=SUP, linewidth=1.2, label="Com pelo menos um livro de poesia no ano")
    ax.bar(x, b, bottom=a, width=0.72, color=AZUL_CLARO, edgecolor=SUP, linewidth=1.2, label="Ativa, sem livros de poesia no ano")
    for xi, ai, ti in zip(x, a, a + b):
        ax.text(xi, ai - 1.2, str(ai), ha="center", va="top", fontsize=8.5, color="white")
        ax.text(xi, ti + 0.8, str(ti), ha="center", va="bottom", fontsize=9, color=TINTA, weight="bold")
    ax.set_xticks(list(x))
    ax.set_xlim(ANO_MIN - 0.7, ANO_MAX + 0.7)
    ax.set_ylim(0, (a + b).max() * 1.12)
    fig.suptitle("Editoras ativas por ano, 2000-2019", x=0.075, y=0.97, ha="left", fontsize=14, color=TINTA, weight="bold")
    ax.set_title(f"{n} editoras nom institucionais com mais de 5 livros de poesia no período. "
                 "Barra completa = editoras entre o seu primeiro e último ano de atividade",
                 loc="left", fontsize=9.5, color=TINTA2, pad=28)
    ax.legend(loc="upper left", bbox_to_anchor=(0, 1.085), ncol=2, frameon=False, fontsize=9.5, labelcolor=TINTA2)
    fig.tight_layout(rect=(0.03, 0, 1, 0.985))
    fig.savefig(destino, facecolor=SUP)
    plt.close(fig)


def grafico_entradas_saidas(pa, destino):
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=160, facecolor=SUP)
    estilo(ax)
    x, e, s = pa["Ano"], pa["Incorporaçons (primeiro ano)"], pa["Desapariçons (último ano)"]
    ax.bar(x, e, width=0.72, color=AZUL, label="Incorporaçons (primeiro ano de atividade)")
    ax.bar(x, -s, width=0.72, color=LARANJA, label="Desapariçons (último ano de atividade)")
    for xi, ei, si in zip(x, e, s):
        if ei:
            ax.text(xi, ei + 0.12, str(ei), ha="center", va="bottom", fontsize=9, color=TINTA2)
        if si:
            ax.text(xi, -si - 0.12, str(si), ha="center", va="top", fontsize=9, color=TINTA2)
    ax.axhline(0, color=MUDO, linewidth=0.8)
    ax.spines["bottom"].set_visible(False)
    ax.set_xticks(list(x))
    ax.set_xlim(ANO_MIN - 0.7, ANO_MAX + 0.7)
    ax.set_ylim(-s.max() - 1.2, e.max() + 1.2)
    ax.set_yticks(range(-int(s.max()), int(e.max()) + 1, 2))
    ax.set_yticklabels([str(abs(t)) for t in ax.get_yticks()])
    fig.suptitle("Incorporaçons e desapariçons de editoras por ano, 2000-2019", x=0.06, y=0.97, ha="left",
                 fontsize=14, color=TINTA, weight="bold")
    ax.legend(loc="upper left", bbox_to_anchor=(0, 1.13), ncol=2, frameon=False, fontsize=9.5, labelcolor=TINTA2)
    fig.tight_layout(rect=(0.03, 0, 1, 0.96))
    fig.savefig(destino, facecolor=SUP)
    plt.close(fig)


def main():
    json_path, csv_path, saida = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    df = carregar(json_path, csv_path)
    pa = por_ano(df)
    grafico_ativas(pa, len(df), saida / "editoras_csv_ativas_por_ano.png")
    grafico_entradas_saidas(pa, saida / "editoras_csv_entradas_saidas.png")

    det = df.assign(**{
        "Entrada no período": df["_entrada"], "Saída no período": df["_saida"],
    })[[c for c in df.columns if not c.startswith("_")] + ["Entrada no período", "Saída no período"]]
    det = det.sort_values(["Ativa desde (2000-2019)", "Editora"])
    notas = pd.DataFrame({"Notas metodológicas": [
        f"Fontes: {Path(json_path).name} e {Path(csv_path).name} ({len(df)} editoras).",
        "Editora ativa num ano = o ano fica entre o primeiro e o último ano da planilha (sem último ano = ativa até 2019).",
        "Quando o JSON tem livros fora dessas datas, o período alarga-se para os cobrir (coluna 'Livros fora das datas do CSV').",
        "Livros = registos Livro do JSON ligados ao registo Editora com esse H-ID (ano de publicaçom verificado 2000-2019).",
        "Incorporaçom = primeiro ano de atividade, se é 2000 ou posterior. Desapariçom = último ano de atividade, se é 2019 ou anterior e está documentado.",
        "O H-ID 4051 (Danú) nom existe no JSON; usou-se o registo Editora 3033 (Danú).",
    ]})
    with pd.ExcelWriter(saida / "editoras_csv_ativas.xlsx", engine="openpyxl") as xl:
        pa.to_excel(xl, sheet_name="Ativas por ano", index=False)
        det.to_excel(xl, sheet_name="Editoras", index=False)
        notas.to_excel(xl, sheet_name="Notas", index=False)
        for ws in xl.sheets.values():
            ws.freeze_panes = "A2"
            for col in ws.columns:
                larg = max(len(str(c.value)) if c.value is not None else 0 for c in col[:90])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, larg + 2), 60)

    print(pa.to_string(index=False))
    print("total incorporaçons:", pa.iloc[:, 4].sum(), "| desapariçons:", pa.iloc[:, 5].sum())
    print("poucos livros:", df[df["Livros 2000-2019"] <= 5][["H-ID", "Editora", "Livros 2000-2019"]].to_string(index=False))


if __name__ == "__main__":
    main()
