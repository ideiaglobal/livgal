"""Sinais textuais de «ediçom erudita» nos registos Livro do export Heurist livpoesia."""
import json, re, collections

RESP = ['Autoria (marc_map)', 'Autores secundários (marc_map)']      # mençons de responsabilidade
NOTES = ['Nota geral', 'Nota de título', 'Conteúdos', 'Nota de conteúdo', 'Notas']
TITLE = ['Subtítulo', 'Título secundário 1', 'Título secundário 2']
EDIT = ['Edição', 'Género_bne']

# Cada sinal: (código, descriçom, peso, campos onde se procura, regex)
SIGNALS = [
    ('critica', 'ediçom crítica (literal)', 5, RESP + NOTES + TITLE + EDIT + ['Título principal'],
     r'\bed(?:ici[oó]n|içom|ição|\.)\s+(?:\w+\s+){0,2}cr[ií]tica|aparato cr[ií]tico|\bcr[ií]tica textual'),
    ('estudo', 'estudo / ensaio / comentário', 3, RESP + NOTES + TITLE,
     r'\bestud[io]os?\b(?! da literatura)|\bensaios? (?:introdut|prelim)|\bensayo (?:introduc|prelim)|\ban[aá]lises?\b(?! e estudo)'
     r'|\ban[aá]lisis\b|\bcomentarios?\b(?! biogr)|\bcomentad[oa]s?\b|\bedici[oó]n comentada'),
    ('notas', 'notas / anotaçom / glossário', 3, RESP + NOTES + TITLE,
     r'(?<!\bde )\bnotas?\b(?!\s+(?:biogr|de prensa|de lector|musicais|para\b))|\banota(?:d[oa]s?|ci[oó]ns?|ções)\b'
     r'|\bglosario|\bglossário|\bvocabulario'),
    ('transcricao', 'transcriçom / fixaçom do texto', 3, RESP + NOTES + TITLE,
     r'\btranscri[cp]|\bpaleogr|\bfixaci[oó]n d[oe]l? texto|\bedici[oó]n diplom|\brevisi[oó]n(?: d[oe]l?)? texto'
     r'|\bmodernizaci[oó]n|\bversi[oó]n (?:ao|al) galego moderno'),
    ('edicao', 'ediçom literária / ao cuidado de', 2, RESP,
     r'\bedici[oó]ns?(?:\s+bilingüe)?(?:\s*,|\s+e\b|\s+y\b|\s+de\b|\s+do\b|\s+da\b|\s+por\b|\s*:|\s*\]?\s+[A-ZÁÉÍÓÚX])'
     r'|\bedici[oó]n liter[aá]ria|\bedi(?:ção|çom)\s+(?:de|e|,)|\bao? c[ou]idado de|\b[oó] coidado de|\bal cuidado de'
     r'|\bedici[oó]n a cargo de|\bed\.\s?lit\.|\bd\. lit\.|editor(?:a|es)? liter[aá]ri[oa]s?|\bedt\b|\beditado por'
     r'|\bedited by|\b(?:ed|eds)\.\s+[A-ZÁÉÍÓÚX]|\(eds?\.\)|\beditor(?:a|es)?,? [A-ZÁÉÍÓÚX]'),
    ('introducao', 'introduçom', 3, RESP + NOTES,
     r'\bintrodu(?:ci[oó]ns?|cci[oó]n|ção|çom|ções|tori[oa]|ctori[oa])\b'),
    ('monografia', 'estudo sobre um autor que inclui textos', 2, NOTES + TITLE,
     r'\bincl[uú][yi]?e\b.{0,40}\b(?:selecci[oó]n|escolma|antolox[ií]a|antolog[ií]a|poemas|poes[ií]as|textos|obras?) d'
     r'|\bvida [ey] obra\b|\bobra po[eé]tica de\b|\bescrita l[ií]ri[ct]a de\b'),
    ('facsimile', 'fac-símile / reproduçom', 2, RESP + NOTES + TITLE + EDIT,
     r'\bfacs|\bfasc\.|\bfacsimilar|\breprod(?:\.|ucci[oó]n|uci[oó]n)\b'),
    ('aparato', 'bibliografia / cronologia / biografia / apêndices', 1, RESP + NOTES,
     r'\bbibliograf[ií]a|\bcronolox[ií]a|\bcronolog[ií]a|\bcronobiograf|\bbiograf[ií]a\b|\bap[eé]ndices?\b|\bhemerograf'
     r'|\b[ií]ndices? (?:de|onom)'),
    ('seleccao', 'selecçom / escolma por terceiros', 1, RESP + NOTES,
     r'\bselecci[oó]ns?\b|\bseleção|\bescolma\s*(?:,|e\b|de\b|por\b)|\brecompilaci[oó]n|\bcompilaci[oó]n|\brecopilaci[oó]n'
     r'|\bcompilador|\brecopilador|\bantoloxía (?:de|e|por|,) [A-ZÁÉÍÓÚX]|\bsel\.|\bedc\b'),
    ('prologo', 'prólogo / limiar / epílogo', 0, RESP + NOTES,
     r'\bpr[oó]logos?\b|\blimiar(?:es)?\b|\bprefacio|\bprefácio|\bep[ií]logo|\bpresentaci[oó]n\b|,\s*pr\.|\be pr\.'
     r'|\bpórtico\b|\bposfacio|\bpalabras? previas?|\baui\b'),
]
# falsos positivos de «ediçom» (produçom gráfica, ediçom do prémio, etc.)
EDICAO_EXCL = re.compile(r'\bedici[oó]n\s+(?:gr[aá]fica|pl[aá]stica|castel[aá]|non venal|numerada|limitada|d[oe] ano|do certame)'
                         r'|\bcoordinaci[oó]n d[ae]sta edici[oó]n|\bnotas á edici[oó]n', re.I)
SIGNALS = [(c, d, w, f, re.compile(rx, re.I)) for c, d, w, f, rx in SIGNALS]
WEIGHT = {c: w for c, d, w, f, rx in SIGNALS}

# Funçons das relaçons (Record relationship) que apontam para paratexto erudito
REL_MAP = {'editor/a': 'edicao', 'introduçom': 'introducao', 'notas': 'notas', 'prologuista': 'prologo',
           'compilador': 'seleccao', 'organizador/a': 'seleccao', 'revisor': 'transcricao'}

TAG = 'edição_crítica'


def load(path):
    R = json.load(open(path, encoding='utf-8'))['heurist']['records']
    books = [r for r in R if r['rec_RecTypeName'] == 'Livro']
    rels = collections.defaultdict(list)
    for r in R:
        if r['rec_RecTypeName'] != 'Record relationship':
            continue
        d = {x['fieldName']: x for x in r['details']}
        if 'Livro' in d and 'Função' in d:
            rels[d['Livro']['value']['id']].append(
                (d['Função'].get('termLabel'), d.get('Produtor', {}).get('value', {}).get('title', '')))
    people = {r['rec_ID']: r for r in R if r['rec_RecTypeName'] == 'Pessoa'}
    return books, rels, people


def vals(r, f):
    out = []
    for d in r['details']:
        if d['fieldName'] == f:
            v = d['value']
            out.append(v['title'] if isinstance(v, dict) else str(v))
    return out


def term(r, f):
    return [d.get('termLabel') or str(d['value']) for d in r['details'] if d['fieldName'] == f]


def detect(r, rels):
    """Devolve {sinal: [(campo, trecho), ...]}"""
    found = collections.defaultdict(list)
    for code, _, _, fields, rx in SIGNALS:
        for f in fields:
            for v in vals(r, f):
                for m in rx.finditer(v):
                    a, b = max(0, m.start() - 40), min(len(v), m.end() + 60)
                    if code == 'edicao' and EDICAO_EXCL.search(v[max(0, m.start() - 20):b]):
                        continue
                    found[code].append((f, v[a:b].strip()))
                    break
    for func, who in rels.get(r['rec_ID'], []):
        if func in REL_MAP:
            found[REL_MAP[func]].append(('Função', f'{func}: {who}'))
    return found


def score(found):
    return sum(WEIGHT[c] for c in found)
