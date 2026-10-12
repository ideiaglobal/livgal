# Operação 1 — Todas as editoras da BD (2000-2019)

Esclarecimentos metodológicos e dúvidas em aberto da análise feita sobre todos os registos **Editora** da exportação `Export_livpoesia_20261012104901.json`.

- Script: `editoras_analise.py`
- Resultados: `editoras_ativas_por_ano.png`, `editoras_grupos.png`, `editoras_analise.xlsx`

## O que foi pedido

1. Gráfico de barras com o número de editoras ativas por ano, entre 2000 e 2019.
2. Média de livros publicados por ano por cada editora, tendo em conta as datas de atividade.
3. Classificação das editoras em grupos segundo essa média (menos de 1; 1 a 1,9; 2 a 2,9; 3 ou mais por ano).

## Dados de partida

| | |
|---|---|
| Registos Editora | 729 (2 sem nenhum livro associado) |
| Registos Livro | 3149, todos com ano de publicação verificado entre 2000 e 2019 |
| Livros sem editora associada | 42 |
| Livros com mais de uma editora | 183 |
| Editoras com data de início no registo | 109 |
| Editoras com data de fim no registo | 28 |

## Esclarecimentos: como foi calculado

### Unidade de análise

- Agrupou-se pelo campo **Nome normalizado**, que funde variantes do mesmo selo (por exemplo, os 37 registos de departamentos da Xunta de Galicia contam como uma só editora).
- Exceção: os 101 registos com nome normalizado «Edição de autor» contam cada um como editora própria, porque são autores-editores distintos.
- Resultado: **635 editoras** com livros, em vez de 727 registos. O cálculo alternativo, registo a registo, está na folha «Por registo (alternativa)» do Excel.

### Período de atividade

- Com datas no registo: usa-se a data de início e a de fim. Início sem fim significa «ativa até 2019».
- Sem datas no registo (526 das 635 editoras): o período vai do primeiro ao último livro que a editora tem no corpus.
- Quando há livros fora das datas documentadas, o período alarga-se para os cobrir.
- Tudo é cortado ao intervalo 2000-2019.
- Quando um registo tem duas datas de início (por exemplo, Chan da Pólvora: 2016 e 2017), usa-se a mais antiga.

### Média de livros por ano

Média = livros de 2000-2019 ÷ anos de atividade dentro de 2000-2019.

### Contagem de livros

- Um livro coeditado conta uma vez para cada editora que o assina. Por isso, a soma dos livros por editora (3330) é superior ao número de registos Livro (3149).
- Os 42 livros sem editora ficam de fora.
- Usaram-se os 3149 livros, e não apenas os 2737 com a etiqueta `Poesia_2000_2019`.

### «Editora ativa» no gráfico

O gráfico mostra duas medidas empilhadas:

- **Com pelo menos um livro publicado no ano** (azul escuro).
- **Em atividade, sem livros no ano** (azul claro): o ano cai dentro do período de atividade, mas não há livro no corpus.

A barra completa é o total de editoras dentro do seu período de atividade.

## Limitações a ter em conta na leitura

- **Efeito de borda.** Como a maioria dos períodos é inferida dos livros, o total de editoras «em atividade» fica subestimado nos extremos (2000-2001 e 2018-2019): uma editora sem datas só «existe» entre o seu primeiro e o seu último livro.
- **Artefacto da média 1,0.** Uma editora com um só livro tem um ano de atividade e, portanto, média de exatamente 1 livro por ano. Com os quatro grupos pedidos, 438 editoras (69 %) caem em «1 a 1,9 por ano», quase todas por esta razão. Do mesmo modo, quem publicou 2 ou 3 livros num único ano vai parar aos grupos mais altos.
- **Assimetria entre editoras com e sem datas.** Uma editora com início documentado e sem fim conta como ativa até 2019; uma sem datas só conta até ao seu último livro. Duas editoras com a mesma produção podem, por isso, ter médias diferentes.

## Classificação proposta

Para contornar o artefacto, propõe-se separar as editoras que publicaram num único ano e aplicar os quatro grupos às restantes:

| Grupo | Editoras | % editoras | % livros |
|---|---|---|---|
| 0. Pontual (publicou num único ano) | 409 | 64 % | 13 % |
| A. Menos de 1 por ano | 146 | 23 % | 23 % |
| B. 1 a 1,9 por ano | 61 | 10 % | 23 % |
| C. 2 a 2,9 por ano | 9 | 1 % | 8 % |
| D. 3 ou mais por ano | 10 | 2 % | 33 % |

O Excel traz as duas classificações (a pedida e a proposta), cada uma na sua coluna.

## Dúvidas em aberto

1. **Unidade de análise.** Confirma-se o agrupamento por «Nome normalizado»? Alguns agrupamentos podem não ser desejados para este fim (por exemplo, «Biblioteca de Mesopotamia» está normalizada como «Chan da Pólvora»).
2. **Auto-edições.** Devem entrar na análise como editoras individuais (como está), ficar agrupadas numa só categoria ou ser excluídas?
3. **Corpus.** Devem usar-se os 3149 livros ou só os 2737 com a etiqueta `Poesia_2000_2019`? Há ainda 81 livros com a etiqueta `duplicados_poesia` e 26 com `duvidosos_poesia` que foram contados.
4. **Editoras sem datas.** Aceita-se inferir o período a partir do primeiro e do último livro, ou prefere-se outro critério (por exemplo, considerar ativas durante todo o período as instituições públicas)?
5. **Classificação.** Aceita-se o grupo adicional «pontual»? O grupo «3 ou mais por ano» junta editoras muito diferentes (de 3 a 13 livros por ano); pode fazer sentido dividi-lo.
6. **Coedições.** Aceita-se contar o livro por inteiro para cada coeditora, ou prefere-se uma contagem fracionada?

## Dados a rever na BD

- **Livros fora das datas documentadas da editora** (6 casos):

  | Editora | Datas no registo | Livros fora das datas |
  |---|---|---|
  | Ediciós do Castro | 1968-2008 | 2011 |
  | Edizer | 2009-2015 | 2016 (3), 2017 |
  | Irmandade Manuel María | 2012-2019 | 2010 |
  | Q de Vian Cadernos | 2010-2015 | 2016 |
  | Primerapersona | 2003-2013 | 2002 |
  | Técnicas & Gramaxe S.L. | 2006-2022 | 2003 |

- **Editoras sem nenhum livro associado:** Xunta de Confrarías da Semana Santa de Viveiro; Pepitas de Calabaza.
- **Editora sem nome normalizado:** Dial Discos.
- **Registos com duas datas de início:** Chan da Pólvora (2016, 2017), Caldeirón (2000, 2002), Medulia (2014, 2015), Através Editora (2009, 2010).
- **Livros sem editora:** 42 registos.
