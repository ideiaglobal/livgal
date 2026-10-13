# Edições eruditas na BD livpoesia — notas de contexto

Esclarecimentos metodológicos e dúvidas em aberto da primeira pesquisa de «edições eruditas» sobre a exportação `Export_livpoesia_20261012104901.json` (em `../atividade-editorial/`).

- Scripts: `candidatos_edicoes_eruditas.py` (gera a lista) e `sinais.py` (padrões de deteção e pesos)
- Resultados: `candidatos_edicoes_eruditas.xlsx` (abas «Candidatos» e «Resumo») e `candidatos_edicoes_eruditas.csv` (mesmo conteúdo da aba «Candidatos»)
- Data de produção: 13-10-2026, sobre a exportação de 12-10-2026

## O que foi pedido

Localizar na BD livpoesia não só as edições críticas em sentido estrito, mas todas as edições com notas, estudos introdutórios e aparato semelhante: «edições eruditas», por oposição a edições convencionais ou comerciais. Os nomes não são exatos; a fronteira é de grau.

O objetivo não é localizar de zero. Já existia uma seleção manual deste tipo de obras; pretende-se uma pesquisa abrangente que sirva para **completar e corrigir** essa seleção. Por isso a lista privilegia a cobertura e deixa a decisão final para revisão manual.

## Dados de partida

| | |
|---|---|
| Registos «Livro» no export | 3 149 |
| Livros com a etiqueta `edição_crítica` (seleção prévia) | 158 |
| Registos «Record relationship» com função | 4 308, dos quais 3 174 com função «nd» |
| Pessoas com data de morte | 179 de 2 708 |

A seleção prévia foi identificada pelo valor `edição_crítica` do campo «Etiqueta». Assumiu-se que corresponde à seleção manual referida no pedido; **convém confirmar**.

## Porque não se usa a CDU

Testou-se primeiro se a CDU permitia localizar estas edições. Não permite:

- As notações descrevem género, língua e período (`821.134.4-14"19"`, `869.9-1"19"`…) e são as mesmas em edições eruditas e comerciais.
- Os únicos auxiliares aparentados, `.07` e `.09`, aparecem em 53 livros e marcam sobretudo estudos *sobre* um autor, misturados com biografias e homenagens.
- O campo tem muitos valores espúrios (`X`, `"X`, `[2000]`, `2015`, aspas soltas).

A CDU foi por isso ignorada em toda a análise.

## Como foi calculado

### Onde se procura

Os sinais são expressões procuradas em texto livre, campo a campo:

- **Menções de responsabilidade**: «Autoria (marc_map)» e «Autores secundários (marc_map)», incluindo os códigos de função MARC (`ed. lit.`, `pr.`, `edt`…).
- **Notas**: «Nota geral», «Nota de título», «Conteúdos», «Nota de conteúdo», «Notas».
- **Título**: «Subtítulo» e títulos secundários. O «Título principal» só conta para «edição crítica» literal, porque gera muito ruído (*Notas a pé de barra*, *Glosarios*…).
- **Edição** e «Género_bne»: só para «edição crítica» e fac-símile.
- **Funções das relações** (editor/a, introduçom, notas, prologuista, compilador, organizador/a, revisor). Contribuem pouco porque a maioria das relações tem função «nd».

### Sinais e pesos

| sinal | o que apanha | peso | livros | já etiquetados |
|---|---|---|---|---|
| `critica` | «edición crítica», «aparato crítico» | 5 | 13 | 13 |
| `estudo` | estudo, ensaio introdutório, análise, comentários | 3 | 52 | 31 |
| `notas` | notas, anotada, glosario, vocabulario | 3 | 70 | 28 |
| `transcricao` | transcrição, fixação do texto, edição diplomática | 3 | 15 | 7 |
| `introducao` | introdución / introducción / estudo introdutorio | 3 | 117 | 92 |
| `edicao` | «edición de», «ao coidado de», `ed. lit.`, «editor literario» | 2 | 439 | 109 |
| `monografia` | estudo sobre um autor que inclui textos («Inclúe… selección de», «vida e obra») | 2 | 24 | 9 |
| `facsimile` | fac-símile, reprodução | 2 | 61 | 17 |
| `aparato` | bibliografia, cronologia, biografia, apêndices | 1 | 30 | 12 |
| `seleccao` | selección, escolma, recompilación, compilador | 1 | 134 | 31 |
| `prologo` | prólogo, limiar, epílogo, presentación, `pr.` | 0 | 531 | 46 |

Os pesos são uma escolha de quem fez a análise, orientada pela proporção de livros já etiquetados em cada sinal. Não são uma medida validada.

A pontuação de um livro é a soma dos pesos dos sinais presentes (cada sinal conta uma vez). Somam-se **2 pontos** quando o autor principal morreu antes do ano de publicação, desde que haja pelo menos outro sinal: uma edição póstuma com editor literário é quase sempre uma edição preparada.

`prologo` tem peso 0 e é só informativo: aparece em 531 livros de todo o universo e só 9% estão etiquetados, pelo que sozinho não gera candidato. Na folha só se vê nos 171 livros que entraram por outro motivo.

### Níveis

| nível | critério | já etiquetados | novos candidatos |
|---|---|---|---|
| **A** | «edição crítica» literal ou 5 pontos ou mais | 120 | 84 |
| **B** | 3–4 pontos | 28 | 167 |
| **C** | 1–2 pontos (sinal isolado e fraco) | 7 | 198 |
| **–** | etiquetado, mas sem nenhum sinal | 3 | — |

Total: 607 livros, dos quais 449 novos candidatos.

### Falsos positivos excluídos à partida

- «edición gráfica», «edición plástica», «edición castelá», «edición non venal», «numerada», «limitada».
- «edición do ano…» e «edición do certame» (edições de prémios).
- «notas á edición», «notas de lector», «notas biográficas», «notas de prensa».
- `ed. lit.` quando coincide com o autor principal e não há outra menção de edição: o sinal `edicao` é retirado e o livro fica marcado na coluna «editor = autor» (5 casos).

## Como ler a folha

| coluna | significado |
|---|---|
| `rec_ID` | identificador do registo Livro no Heurist |
| `nível`, `pontos` | ver acima; a folha vem ordenada por nível e pontuação |
| `estado` | «já etiquetado», «novo candidato» ou «já etiquetado, sem sinais (rever)» |
| `título`, `autoria`, `ano`, `editora`, `natureza` | dados do registo; o ano é o «Ano de publicação verificado» |
| colunas de sinais | `x` quando o sinal está presente |
| `autor falecido` | o autor principal tem data de morte anterior ao ano de publicação |
| `editor = autor` | o editor literário é o próprio autor |
| `outras etiquetas` | etiquetas úteis para filtrar: duplicados, coletivos, tradução, infantil, escolar, exposições, catálogos |
| `evidência` | trecho do campo que disparou cada sinal, com o nome do campo |
| `mençom de responsabilidade` | a versão mais longa de «Autoria (marc_map)» |
| `decisom (S/N/?)` | vazia, para a revisão manual |

## O que foi e não foi revisto

- **Nível A, novos (84)**: lidos todos. Parecem maioritariamente certos, com algum falso positivo solto.
- **Nível B, novos (167)**: vista uma amostra de 40. Predominam edições póstumas com «edición de X» sem mais aparato (79) e antologias com editor e selecionador.
- **Nível C, novos (198)**: não revisto. Quase tudo é «edición de» isolado (149), muitas vezes em volumes coletivos. É onde se espera mais ruído.
- **Etiquetados sem sinais (3)**: *Antón Tovar na Limia* (332), *Martín Codax e os xograres do mar de Vigo* (1445) e *Os poemas betanceiros* (1894). Os registos não têm no texto nada que os identifique; ou a etiqueta vem de conhecimento externo do livro, ou deve ser revista.

## Limitações

- **Só se vê o que está escrito no registo.** Um livro com estudo introdutório que a catalogação não menciona não aparece. A lista não prova que um livro *não* é edição erudita.
- **Registos duplicados.** A BD tem duplicados e aparecem duas vezes na lista (p. ex. *Coloquio en coplas galegas*, 735 e 736). A etiqueta `duplicados_poesia` aparece em «outras etiquetas» quando existe, mas não cobre todos os casos.
- **Data de morte incompleta.** Só 179 pessoas a têm; o bónus de autor falecido falha para os restantes, que ficam um nível abaixo do que deviam.
- **Volumes sem autoria principal** (567 livros). Neles «edición de» costuma indicar o organizador de uma antologia ou de um volume coletivo, não o editor de um texto alheio. Filtram-se por «(sem autoria principal)» na coluna `autoria`.
- **Nomes próprios e homónimos.** Alguns padrões apanham nomes de entidades («Estudio Hispano Árabe» conta como `estudo`). A coluna `evidência` permite detetá-los.
- **Traduções.** «tradución, introdución e notas de…» pontua alto. Se as traduções anotadas contam ou não como edição erudita é uma decisão de critério; a etiqueta `traduçom_para` ajuda a isolá-las.
- **A seleção prévia é ampla.** Inclui livros só com introdução, seleções por terceiros, fac-símiles e monografias sobre um autor com textos. Os padrões foram afinados para a reproduzir, pelo que herdam essa amplitude.

## Dúvidas em aberto

1. A etiqueta `edição_crítica` é mesmo a seleção prévia a completar?
2. Traduções com introdução e notas entram no conceito?
3. Antologias de vários autores com editor e introdução entram, ou só edições de um autor?
4. Monografias sobre um autor que incluem uma seleção de textos entram?
5. Fac-símiles sem estudo nem notas entram?

As respostas permitem ajustar os pesos em `sinais.py` e voltar a gerar a lista.

## Como voltar a gerar

```bash
python3 candidatos_edicoes_eruditas.py
```

Lê por omissão `../atividade-editorial/Export_livpoesia_20261012104901.json`; outro export pode ser passado como argumento. Precisa de `openpyxl`. Volta a escrever o `.xlsx` e o `.csv`, pelo que as decisões anotadas na folha devem ser guardadas noutra cópia antes de correr.
