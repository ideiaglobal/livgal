#!/usr/bin/env python3
"""
Procura as entidades Pessoa da exportação JSON do Heurist (livpoesia) no
catálogo de autoridades da BUSC (Biblioteca Universitaria de Santiago de
Compostela), centrado em autorias galegas, para trazer as datas de nascimento
e morte, e confronta-as com as da BD, da BNE e da Wikidata.

Uso:
    pip install requests
    python3 busc_pessoas.py Export_livpoesia.json [pasta_saida] [--limite N]

Se existir na pasta de saída o ficheiro pessoas-bne.csv (produzido por
bne_pessoas.py), as datas da BNE e da Wikidata entram no confronto.

Saídas (UTF-8 com BOM, separador TAB, como as exportações do Heurist):
  pessoas-busc.csv            todas as pessoas, com o registo da BUSC
                              encontrado e o confronto das quatro fontes
  pessoas-busc-importar.csv   só as datas que a BUSC acrescenta: a BD não as
                              tem e pessoas-bne-importar.csv não as propõe;
                              inclui as confianças alta e média, identificadas
                              numa coluna

As respostas do catálogo ficam em busc_cache.json; se repetir a execução, só
se pedem os nomes que ainda não estão lá.

Como se escolhe o registo
  O nome da BD («Apelidos, Nome» e as variantes) tem de coincidir exatamente,
  sem acentos nem maiúsculas, com o nome do registo ou com uma das suas formas
  alternativas. Evidência que confirma a escolha:
    - ano MARC   ano de nascimento junto ao nome nos campos MARC dos livros
    - ano BD     ano de nascimento já registado na BD
    - ano BNE    ano de nascimento do registo da BNE (confiança alta)
    - título     um título de um livro da pessoa citado nas fontes do registo
  Confiança: alta = um único registo confirmado; média = sem confirmação, mas
  só há um registo com esse nome; baixa = vários registos possíveis.
"""
import csv
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))  # necessário com python -I
from bne_pessoas import ano, carregar_bd, escrever, normalizar  # noqa: E402

API = "https://cisug-usc.primo.exlibrisgroup.com/primaws/rest/pub/authority/authoritySearch"
VID = "34CISUG_USC:NDE"
HEADERS = {"User-Agent": "LivroGalegoPessoas/1.0 (https://github.com/ideiaglobal/livgal; mailto:info@heurisko.io)"}
PAUSA = 0.4          # segundos entre pedidos (é o catálogo público de uma biblioteca)
POR_PAGINA = 50
MAX_RESULTADOS = 150
CACHE = "busc_cache.json"

RE_DATAS = re.compile(r",?\s*(?:--\s*)?\(?\s*(?:ca\.\s*)?(\d{3,4})?\s*\??\s*-\s*(\d{3,4})?\s*\??\s*\)?\s*$")


def nome_e_datas(cabecalho):
    """«Criado, Felipe, 1928-2013 » -> («Criado, Felipe», «1928», «2013»)."""
    cabecalho = cabecalho.strip()
    m = RE_DATAS.search(cabecalho)
    if m and (m.group(1) or m.group(2)):
        return cabecalho[:m.start()].strip(" ,"), m.group(1) or "", m.group(2) or ""
    return cabecalho.strip(" ,"), "", ""


def pedir(nome, offset):
    params = {"searchTerm": nome, "searchField": "personalname", "searchOperator": "contains",
              "sort": "rank", "offset": offset, "limit": POR_PAGINA, "vid": VID, "lang": "gl"}
    for tentativa in range(6):
        try:
            r = requests.get(API, params=params, headers=HEADERS, timeout=60)
            if r.status_code == 200:
                time.sleep(PAUSA)
                return r.json()
            print(f"  (HTTP {r.status_code}; nova tentativa)", file=sys.stderr)
        except (requests.RequestException, ValueError) as e:
            print(f"  (erro: {e}; nova tentativa)", file=sys.stderr)
        time.sleep(10 * (tentativa + 1))
    raise SystemExit("O catálogo da BUSC não respondeu depois de várias tentativas.")


def pesquisar(nome, cache):
    """Registos de nome pessoal que contêm as palavras do nome (guardados de forma resumida)."""
    if nome not in cache:
        docs, offset, total = [], 0, None
        while total is None or (offset < total and offset < MAX_RESULTADOS):
            dados = pedir(nome, offset)
            total = dados.get("info", {}).get("total", 0)
            for d in dados.get("docs", []):
                v = d["pnx"]["display"]
                if "personalname" not in v.get("authority_type", []):
                    continue
                docs.append({
                    "id": v.get("source_id") or d["pnx"].get("control", {}).get("recordid", [""])[0],
                    "nome": (v.get("heading") or [""])[0],
                    "variantes": v.get("see_from_tracing") or [],
                    "fontes": v.get("source_data_found") or [],
                    "datas_codificadas": v.get("special_coded_dates") or [],
                    "ocupacao": v.get("subject_occupation") or [],
                    "lugar": v.get("associated_place") or [],
                    "atividade": v.get("field_of_activity") or [],
                })
            offset += POR_PAGINA
            if not dados.get("docs"):
                break
        cache[nome] = {"total": total or 0, "docs": docs}
    return cache[nome]


def candidatos(p, resultado):
    """Registos cujo nome ou forma alternativa coincide exatamente com um nome da BD."""
    cands = []
    for d in resultado["docs"]:
        nome, nasc, morte = nome_e_datas(d["nome"])
        if normalizar(nome) in p["chaves"]:
            tipo = "nome"
        elif any(normalizar(nome_e_datas(v.split(" -- ")[0])[0]) in p["chaves"] for v in d["variantes"]):
            tipo = "variante"
        else:
            continue
        cands.append(dict(d, nome_limpo=nome, nasc=nasc, morte=morte, tipo=tipo))
    return cands


def escolher(p, cands, bne):
    """Devolve (confiança, registo, evidências, outros registos)."""
    if not cands:
        return "sem correspondência", None, [], []
    anos_marc = {a for a, _ in p["anos_marc"]}
    avaliados = []
    for c in cands:
        fortes = []
        if c["nasc"] and c["nasc"] in anos_marc:
            fortes.append("ano MARC")
        if c["nasc"] and ano(p["nasc"]) == c["nasc"]:
            fortes.append("ano BD")
        if c["nasc"] and bne and bne["nasc"] == c["nasc"]:
            fortes.append("ano BNE")
        fontes = normalizar(" ".join(c["fontes"]))
        if fontes and any(t in fontes for t in p["titulos"]):
            fortes.append("título")
        avaliados.append((len(fortes), c["tipo"] == "nome", bool(c["nasc"]), c, fortes))
    avaliados.sort(key=lambda a: a[:3], reverse=True)
    melhor = avaliados[0]
    empate = len(avaliados) > 1 and avaliados[1][0] == melhor[0]
    if melhor[0] and not empate:
        conf = "alta"
    elif len(avaliados) == 1:
        conf = "média"
    else:
        conf = "baixa"
    return conf, melhor[3], melhor[4], [a[3] for a in avaliados[1:]]


def carregar_bne(caminho):
    """Dados da BNE e da Wikidata já apurados por bne_pessoas.py, por H-ID."""
    dados = {}
    if not os.path.exists(caminho):
        return dados
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            alta = r["Confiança BNE"] == "alta"
            wd_ok = r["Confiança Wikidata"] in ("alta", "ID já na BD") and \
                not r["Confronto ID da Wikidata"].startswith("DIVERGE")
            dados[r["Pessoa H-ID"]] = {
                "nasc": r["Data de nacemento (BNE)"] if alta else "",
                "morte": r["Data da morte (BNE)"] if alta else "",
                "wd_nasc": r["Data de nacemento (Wikidata)"] if wd_ok else "",
                "wd_morte": r["Data da morte (Wikidata)"] if wd_ok else "",
                "prop_nasc": r["Proposta: nascimento"], "prop_morte": r["Proposta: morte"],
                "fonte_nasc": r["Fonte nascimento"], "fonte_morte": r["Fonte morte"],
            }
    return dados


def confrontar(**fontes):
    """Compara os anos das fontes que têm valor."""
    anos = {k: ano(v) for k, v in fontes.items() if v}
    if not anos:
        return ""
    if len(anos) == 1:
        return f"só {next(iter(anos))}"
    if len(set(anos.values())) == 1:
        return "coincidem (" + ", ".join(anos) + ")"
    return "DIVERGEM: " + ", ".join(f"{k} {v}" for k, v in anos.items())


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    limite = int(sys.argv[sys.argv.index("--limite") + 1]) if "--limite" in sys.argv else None
    if limite is not None:
        args = [a for a in args if a != str(limite)]
    if not args:
        raise SystemExit(__doc__)
    saida = args[1] if len(args) > 1 else "."
    cache_path = os.path.join(saida, CACHE)

    pessoas = carregar_bd(args[0])
    if limite:
        pessoas = pessoas[:limite]
    print(f"{len(pessoas)} pessoas", file=sys.stderr)
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)

    def guardar_cache():
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)

    for n, p in enumerate(pessoas, 1):
        novo = p["nome"] not in cache
        pesquisar(p["nome"], cache)
        if novo and len(cache) % 50 == 0:
            guardar_cache()
            print(f"  pesquisas: {n}/{len(pessoas)}", file=sys.stderr)
    guardar_cache()

    bne_dados = carregar_bne(os.path.join(saida, "pessoas-bne.csv"))
    cab = ["Pessoa H-ID", "Nome completo", "Confiança BUSC", "Evidência", "Coincidência", "ID BUSC",
           "Nome na BUSC", "Data de nacemento (BUSC)", "Data da morte (BUSC)", "Outras formas do nome (BUSC)",
           "Fontes (BUSC)", "Datas codificadas (BUSC)", "Ocupação (BUSC)", "Área de atividade (BUSC)",
           "Lugar (BUSC)", "N.º de candidatos BUSC", "Outros candidatos BUSC",
           "Data de nacemento (BD)", "Data da morte (BD)", "Data de nacemento (BNE)", "Data da morte (BNE)",
           "Data de nacemento (Wikidata)", "Data da morte (Wikidata)", "Confronto nascimento",
           "Confronto morte", "Proposta anterior: nascimento", "Proposta anterior: morte",
           "Novo com a BUSC: nascimento", "Novo com a BUSC: morte"]
    linhas, importar, resumo = [], [], Counter()
    for p in pessoas:
        b = bne_dados.get(p["id"], {})
        cands = candidatos(p, cache[p["nome"]])
        conf, c, evid, outros = escolher(p, cands, b)
        fiavel = conf == "alta"
        nasc, morte = (c["nasc"], c["morte"]) if fiavel else ("", "")
        c_nasc = confrontar(BD=p["nasc"], BNE=b.get("nasc"), Wikidata=b.get("wd_nasc"), BUSC=nasc)
        c_morte = confrontar(BD=p["morte"], BNE=b.get("morte"), Wikidata=b.get("wd_morte"), BUSC=morte)
        # o que a BUSC acrescenta (confiança alta ou média; a coluna de confiança distingue-as)
        util = conf in ("alta", "média")
        novo_nasc = c["nasc"] if util and not p["nasc"] and not b.get("prop_nasc") else ""
        novo_morte = c["morte"] if util and not p["morte"] and not b.get("prop_morte") else ""
        linhas.append([
            p["id"], p["nome"], conf, ", ".join(evid), c["tipo"] if c else "", c["id"] if c else "",
            c["nome"].strip() if c else "", c["nasc"] if c else "", c["morte"] if c else "",
            " | ".join(c["variantes"]) if c else "", " | ".join(c["fontes"])[:600] if c else "",
            " | ".join(c["datas_codificadas"]) if c else "", " | ".join(c["ocupacao"]) if c else "",
            " | ".join(c["atividade"]) if c else "", " | ".join(c["lugar"]) if c else "",
            len(cands), " ; ".join(f"{o['nome'].strip()} [{o['id']}]" for o in outros[:8]),
            p["nasc"], p["morte"], b.get("nasc", ""), b.get("morte", ""), b.get("wd_nasc", ""),
            b.get("wd_morte", ""), c_nasc, c_morte, b.get("prop_nasc", ""), b.get("prop_morte", ""),
            novo_nasc, novo_morte,
        ])
        resumo[conf] += 1
        if novo_nasc or novo_morte:
            importar.append([p["id"], p["nome"], c["id"], c["nome"].strip(), novo_nasc, novo_morte,
                             conf, ", ".join(evid), " | ".join(c["fontes"])[:300]])

    escrever(os.path.join(saida, "pessoas-busc.csv"), cab, linhas)
    escrever(os.path.join(saida, "pessoas-busc-importar.csv"),
             ["Pessoa H-ID", "Nome completo", "ID BUSC", "Nome na BUSC", "Data de nacemento",
              "Data da morte", "Confiança BUSC", "Evidência", "Fontes (BUSC)"], importar)

    print("\nCorrespondência com a BUSC:")
    for k in ("alta", "média", "baixa", "sem correspondência"):
        print(f"  {resumo[k]:5d}  {k}")
    print(f"\n{len(importar)} linhas em pessoas-busc-importar.csv")
    for k in ("alta", "média"):
        sub = [l for l in importar if l[6] == k]
        print(f"  {k}: {sum(1 for l in sub if l[4])} nascimentos, {sum(1 for l in sub if l[5])} mortes")
    j = {c: n for n, c in enumerate(cab)}
    for c in ("Confronto nascimento", "Confronto morte"):
        print(f"\n{c}:")
        for k, v in Counter(re.sub(r":.*", "", l[j[c]]) for l in linhas if l[j[c]]).most_common():
            print(f"  {v:5d}  {k}")


if __name__ == "__main__":
    main()
