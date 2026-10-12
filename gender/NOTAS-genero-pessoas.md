# Atribuição de género às pessoas sem género

Esclarecimentos metodológicos e dúvidas em aberto do preenchimento da coluna `Género` no ficheiro `livpoesia-t10-pessoa-2026-10-12_14-11.csv`.

## O que foi pedido

Que todas as pessoas do ficheiro tenham género atribuído, preenchendo unicamente as que não o tinham.

## Resultado

| | Antes | Depois |
|---|---|---|
| `Male` | 1706 | 1848 |
| `Female` | 800 | 849 |
| Sem género | 202 | 11 |
| Total de pessoas | 2708 | 2708 |

Das 202 pessoas sem género, 191 foram preenchidas (142 `Male`, 49 `Female`) e 11 ficaram em branco.

## Esclarecimentos: como foi feito

- **Só se preencheram células vazias.** As 2506 linhas que já tinham género não foram tocadas, nem os H-ID, nem os nomes.
- **Formato preservado.** O ficheiro mantém a codificação UTF-8 com BOM, o separador de tabulação e as aspas originais. Usaram-se os mesmos valores que já existiam na coluna: `Male` e `Female`.
- **Critério principal: o nome próprio.** A grande maioria foi atribuída pelo nome próprio, sem ambiguidade (Xosé, Manuel, Olalla, Iolanda, etc.).
- **Critério secundário: contexto bibliográfico.** Para nomes sem nome próprio, consultaram-se os livros associados à pessoa na exportação `Export_livpoesia_20261012104901.json` (datas de vida, função, coautores).
- **Pesquisa na web.** Tentou-se para os casos duvidosos, sem resultados úteis.
- **Sem valores inventados.** Quando nem o nome nem o contexto permitem determinar o género, a célula ficou em branco.
- **O género atribuído é o que o nome sugere.** Não foi verificado pessoa a pessoa; é uma inferência a partir do nome, não uma informação biográfica confirmada.

### Nomes que podem levantar dúvida e como foram tratados

| Nome | Género atribuído | Razão |
|---|---|---|
| Noa (11362) | `Female` | uso habitual na Galiza |
| Nair (11274) | `Female` | uso habitual na Galiza |
| Auria (11468) | `Female` | nome feminino |
| Olvido (10823) | `Female` | Olvido García Valdés, poeta |
| Erín (5989) | `Female` | Erín Moure, poeta canadiana |
| Aser (11465) | `Male` | nome masculino |
| Quico (11701) | `Male` | hipocorístico de Francisco |
| Guita Jr. (10599) | `Male` | poeta moçambicano; «Jr.» |
| Viale Moutinho (11520) | `Male` | José Viale Moutinho, escritor português |
| J. Domingos (11600) | `Male` | «Domingos» como nome próprio masculino |
| Joan Zorro (11602), Juan Bolseiro (11606), Nuno Fernandes Torneol (11627) | `Male` | trovadores e jograis medievais |

## Dúvidas em aberto

### 1. Pessoas que ficaram sem género (11)

É preciso identificá-las para as completar.

| H-ID | Nome | Porquê | Contexto no JSON |
|---|---|---|---|
| 6444 | Aramburo, M. | só inicial | *Material de soños* (2008), de Alexander Vórtice |
| 7306 | Mourente B., I. | só inicial | ilustração de *Os Trotasongs* (2019), de Iria Estévez |
| 7693 | Escandell, F. | só inicial | tradução catalã de *Poesía última de amor e enfermidade*, de Lois Pereiro (2016) |
| 6975 | Orballo | pseudónimo | ilustração em *O puño e a letra* (2018), de Yolanda Castaño |
| 7352 | Kólpez | pseudónimo | textos de *Para tus ojos hice yo mi voz* (2010) |
| 8708 | Perspicuo | pseudónimo | *Vilanova de Arousa, na voz dos poetas* (2008) |
| 10123 | D'Navalha | pseudónimo | ilustração de *As trovas de Midas* (2011); nascimento em 1977 |
| 9976 | Trespés | pode ser um coletivo | sem livros associados |
| 10838 | Sam, Duke | nome artístico | *Alguén que respira!* e *Trobeir\*s do século XXI* (2019) |
| 11253 | Zeta, Eli | «Eli» serve para os dois géneros | *Escolma salvaxe* (2014) |
| 11716 | de Moscoso, Malvares | nome artístico | *Trobeir\*s do século XXI* (2019) |

### 2. Pessoas preenchidas com menos certeza (6)

Ficaram todas como `Male`; convém confirmá-las.

| H-ID | Nome | Base da atribuição |
|---|---|---|
| 5763 | Lodeiro | o JSON dá «1930-1996, il.», que corresponde ao pintor Xosé Lodeiro |
| 7678 | Guidacci | o JSON dá «1939-, il.», que corresponde ao cartunista brasileiro Jorge Guidacci |
| 10741 | Bermúdez Jambrina, B. | assumiu-se que é Bernardo Bermúdez Jambrina, de memória, sem fonte verificada |
| 10777 | Baltrusch Montero, Kai L. | «Kai» é quase sempre masculino, mas não exclusivamente |
| 10848 | Velpister | nome artístico; atribuição de memória, sem fonte verificada |
| 10852 | Paredes, Ze | atribuído por «Zé» |

### 3. Entidades que podem não ser pessoas

«Trespés» (9976) não tem livros associados e pode ser um grupo. Se for um coletivo, o campo de género não se aplica e o registo talvez deva mudar de tipo.

### 4. Valor a usar quando não se consegue determinar

A coluna só tem `Male` e `Female`. Se o objetivo é que nenhuma célula fique vazia, é preciso decidir que valor usar nos casos indetermináveis ou em coletivos (por exemplo, um termo «desconhecido» no vocabulário do Heurist).

### 5. Provável duplicado

- 11723 — «Dopazo Etenza, Xosé Manuel»
- 11724 — «Dopazo Entenza, Xosé Manuel»

Parecem a mesma pessoa, com uma gralha no primeiro registo. Ambos ficaram como `Male`.

### 6. Nomes com forma irregular

Alguns registos não seguem o formato «Apelidos, Nome» e convém normalizá-los na BD:

- 10603 — «Luís Felipe Cristovão»
- 10828 — «Alba María»
- 11075 — «Herve ar Bihan»
- 11239 — «Valle, Juan Carlos Karlotti»
- 11716 — «de Moscoso, Malvares»
