# Operação 2 — Editoras da planilha CSV (2000-2019)

Esclarecimentos metodológicos e dúvidas em aberto da análise restringida às editoras de `ano início e fim editoras.csv`, cruzadas com a exportação `Export_livpoesia_20261012104901.json`.

- Script: `editoras_csv_ativas.py` (usa funções de `editoras_analise.py`)
- Resultados: `editoras_csv_ativas_por_ano.png`, `editoras_csv_entradas_saidas.png`, `editoras_csv_ativas.xlsx`

## O que foi pedido

Um gráfico de barras com o número de editoras ativas por ano, entre 2000 e 2019, só com as editoras do CSV, para ver quantas há em cada ano e como isso evolui no tempo.

As editoras da planilha seguem dois critérios: terem publicado mais de 5 livros em 2000-2019 e não serem instituições públicas (que estariam ativas todo o período e não informam sobre o ritmo de incorporação e desaparecimento).

## Dados de partida

| | |
|---|---|
| Editoras no CSV | 84 |
| Com «Último ano» preenchido | 30 |
| Identificador de ligação | `Editora H-ID` do CSV = `rec_ID` do registo Editora no JSON |
| Codificação do CSV | UTF-8 (convertido do original em Latin-1), separador `;` |

## Esclarecimentos: como foi calculado

### Editora ativa num ano

Uma editora conta como ativa num ano quando esse ano fica entre o «Primeiro ano» e o «Último ano» da planilha.

- Sem «Último ano»: considera-se ativa até 2019.
- Quando o JSON tem livros fora dessas datas, o período alarga-se para os cobrir.
- Tudo é cortado ao intervalo 2000-2019.

### Unidade de análise

Cada linha do CSV é uma editora e corresponde a um único registo Editora do JSON. Ao contrário da operação 1, **não** se agrupou pelo «Nome normalizado»: só contam os livros ligados ao registo com esse H-ID.

### Livros

Contam-se os registos Livro do JSON ligados à editora, com ano de publicação verificado entre 2000 e 2019. No gráfico, a parte azul escura de cada barra indica quantas das editoras ativas têm pelo menos um livro nesse ano.

### Incorporações e desaparecimentos

- **Incorporação:** primeiro ano de atividade, quando é 2000 ou posterior.
- **Desaparecimento:** último ano de atividade, quando está documentado e é 2019 ou anterior. A editora ainda conta como ativa nesse último ano.

## Resultados

| Ano | Ativas | Com livros no ano | Incorporações | Desaparecimentos |
|---|---|---|---|---|
| 2000 | 49 | 20 | 6 | 0 |
| 2001 | 51 | 23 | 2 | 0 |
| 2002 | 52 | 25 | 1 | 0 |
| 2003 | 56 | 28 | 4 | 0 |
| 2004 | 59 | 29 | 3 | 0 |
| 2005 | 62 | 28 | 3 | 1 |
| 2006 | 63 | 33 | 2 | 1 |
| 2007 | 65 | 38 | 3 | 0 |
| 2008 | 66 | 41 | 1 | 0 |
| 2009 | 67 | 37 | 1 | 0 |
| 2010 | 73 | 47 | 6 | 3 |
| 2011 | 71 | 37 | 1 | 1 |
| 2012 | 71 | 40 | 1 | 2 |
| 2013 | 71 | 42 | 2 | 1 |
| 2014 | 71 | 42 | 1 | 1 |
| 2015 | 72 | 39 | 2 | 2 |
| 2016 | 72 | 44 | 2 | 3 |
| 2017 | 69 | 38 | 0 | 4 |
| 2018 | 65 | 29 | 0 | 1 |
| 2019 | 64 | 33 | 0 | 2 |

Das 84 editoras, 43 já existiam antes de 2000 e 41 incorporam-se durante o período; 22 desaparecem até 2019.

## Limitações a ter em conta na leitura

- **Sem incorporações em 2017-2019.** É em parte efeito do critério de seleção: uma editora nascida nesses anos dificilmente chega a mais de 5 livros antes de 2019.
- **Editoras sem «Último ano».** Contam como ativas até 2019, mesmo que o último livro no corpus seja muito anterior. O número de desaparecimentos pode, por isso, estar subestimado.
- **Atividade não é só poesia.** Uma editora pode estar ativa num ano sem publicar poesia; daí a diferença entre a barra completa e a parte azul escura.

## Dúvidas em aberto

1. **Danú (H-ID 4051).** Este H-ID não existe no JSON. A editora Danú está no JSON com o H-ID 3033 e 14 livros; usou-se esse registo. Confirma-se a correspondência? Convém corrigir o H-ID na planilha.
2. **Editoras com exatamente 5 livros.** O critério é «mais de 5», mas seis editoras da planilha têm 5 livros no JSON: Bolanda, tarQus editorial, Belagua, Galebook, Scio e Asociación Cultural Río Xuvia. Mantiveram-se. O critério é «5 ou mais», ou faltam livros no JSON?
3. **Livros fora das datas da planilha.** Alargou-se o período para os cobrir. Deve corrigir-se a data da editora ou o ano do livro?

   | Editora | Datas no CSV | Livros fora das datas |
   |---|---|---|
   | Ediciós do Castro | 1968-2008 | 2011 |
   | Chan da Pólvora | 2017-2023 | 2016 (4) |
   | Edizer | 2009-2015 | 2016 (3), 2017 |
   | Q de Vian Cadernos | 2010-2015 | 2016 |
   | Técnicas & Gramaxe S.L. | 2006-2022 | 2003 |
   | Primerapersona | 2003-2013 | 2002 |
   | Irmandade Manuel María | 2012-2019 | 2010 |

4. **Datas diferentes entre o CSV e o JSON.** Três registos têm duas datas de início no JSON e o CSV ficou com a mais recente: Medulia (JSON 2014 e 2015; CSV 2015), Através Editora (2009 e 2010; CSV 2010) e Chan da Pólvora (2016 e 2017; CSV 2017). Qual é a correta?
5. **Fervenza e Técnicas & Gramaxe S.L.** Aparecem como duas editoras na planilha, mas o registo de Fervenza indica «Outro nome: Técnicas & Gramaxe, S.L.». Devem contar como uma só?
6. **Variantes do mesmo selo.** Como só contam os livros do registo com o H-ID da planilha, ficam de fora os livros de registos variantes (por exemplo, Chan da Pólvora tem 36 livros pelo seu registo e 38 se se somar «Biblioteca de Mesopotamia»). Prefere-se agrupar pelo «Nome normalizado», como na operação 1?
7. **Definição de «ativa».** Para ver o ritmo de incorporação e desaparecimento usou-se o período de atividade da planilha. Em alternativa, pode contar-se só quem publicou poesia em cada ano (a parte azul escura das barras). Qual das duas leituras se quer destacar?
8. **Instituições públicas.** Ficaram de fora, como proposto (cerca de 18 entidades). Se se quiser um gráfico de comparação com elas incluídas, é preciso a lista dos respetivos H-ID.
