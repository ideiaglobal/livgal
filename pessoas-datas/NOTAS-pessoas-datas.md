# Datas de nascimento e morte das pessoas

Esclarecimentos metodológicos e dúvidas em aberto de duas operações sobre as entidades **Pessoa** da exportação `Export_livpoesia_20261012104901.json`:

1. contar quantas pessoas têm as datas de nascimento e de morte preenchidas;
2. procurar na Wikidata as datas em falta.

- Script: `wikidata_pessoas_datas.py`
- Resultados: `pessoas-datas-importar.csv`, `pessoas-datas-wikidata.csv`
- Cache das respostas da Wikidata: `wikidata_cache.json`

## 1. Situação de partida

Contaram-se os campos «Data de nacemento» e «Data da morte».

| Situação | Pessoas | % do total |
|---|---|---|
| Nascimento e morte | 179 | 6,6 % |
| Só nascimento | 407 | 15,0 % |
| Só morte | 0 | 0 % |
| Nenhuma das duas | 2122 | 78,4 % |
| **Total** | **2708** | **100 %** |

Todas as pessoas com data de morte têm também data de nascimento. Há 596 pessoas com «ID da Wikidata» preenchido.

## 2. Pesquisa na Wikidata

### O que foi pedido

Um script em Python que procure os nomes na Wikidata para preencher as datas, na medida do possível.

### Como funciona

O script trata as 2529 pessoas a que falta pelo menos uma das duas datas, por duas vias:

- **Pessoas que já têm ID da Wikidata na BD (417):** as datas são lidas diretamente desse item.
- **Pessoas sem ID (2112):** o nome é pesquisado entre os itens humanos da Wikidata (P31 = Q5), primeiro como frase exata e, se não houver resultados, por palavras soltas.

Outros pontos:

- **Nome pesquisado.** «Apelidos, Nome» passa a «Nome Apelidos». As «Variantes de nome» também contam para a comparação.
- **Nomes não pesquisados.** Os nomes só com iniciais ou de uma só palavra (46) ficam de fora, por serem demasiado ambíguos.
- **Coincidência do nome.** É «exata» quando o nome da BD é igual a um rótulo ou alias do item (sem acentos nem maiúsculas); é «parcial» quando as palavras de um estão contidas no outro.
- **Precisão das datas.** Respeita-se a da Wikidata: só ano (`1962`), ano e mês (`1970-10`) ou data completa (`1964-07-30`).
- **Datas existentes.** Nunca se propõe substituir uma data que já esteja na BD.
- **Uso da Wikidata.** Só leitura, com pausas entre pedidos e repetição automática quando o serviço responde «ocupado».

### Níveis de confiança

| Nível | Critério |
|---|---|
| ID já na BD | a pessoa já estava ligada a um item |
| alta | nome exato, sem rival equivalente, e: descrita como galega com ocupação cultural ou nome igual ao rótulo principal; ou único humano com esse nome, com ocupação cultural e nome igual ao rótulo principal |
| média | há um candidato que se destaca, mas com menos garantias |
| baixa | vários candidatos equivalentes; é preciso escolher à mão |
| sem candidato | a pesquisa não devolveu nenhum humano com nome compatível |

- «Descrita como galega» significa que a descrição do item, em qualquer língua, contém «galeg-», «galleg-» ou «galic-».
- «Ocupação cultural» é uma lista fixa no script: escritor, poeta, tradutor, ilustrador, pintor, jornalista, filólogo, músico, fotógrafo, etc. «Político» não conta.

### Resultado

| Situação | Pessoas | Com data nova |
|---|---|---|
| ID da Wikidata já na BD | 417 | 3 |
| Confiança alta | 699 | 669 |
| Confiança média | 257 | 225 |
| Confiança baixa | 136 | 96 |
| Sem candidato | 974 | — |
| Nome insuficiente | 46 | — |
| **Total** | **2529** | **993** |

Se se importar o ficheiro `pessoas-datas-importar.csv` (ID já na BD e confiança alta):

| | Antes | Depois |
|---|---|---|
| Com data de nascimento | 586 (21,6 %) | 1251 (46,2 %) |
| Com data de morte | 179 (6,6 %) | 368 (13,6 %) |
| Com ambas | 179 (6,6 %) | 364 (13,4 %) |

### Ficheiros

**`pessoas-datas-importar.csv`** (702 linhas): só os casos fiáveis em que há algo novo.

- 665 datas de nascimento e 189 de morte.
- 699 linhas trazem também o ID e o URL da Wikidata, novos para a BD.
- 30 linhas só trazem o ID da Wikidata, sem datas.
- As 3 linhas de pessoas já ligadas são mortes de 2026: Xesús Alonso Montero, Antoni Marí e Isabel Blanco Rivas.

**`pessoas-datas-wikidata.csv`** (2529 linhas): todas as pessoas tratadas, com o candidato encontrado, a descrição, as ocupações, o país, as datas da Wikidata e da BD, os outros candidatos e notas.

## Limitações a ter em conta

- **Homónimos.** É o risco principal. Durante os testes, «Rodríguez, Luis» ficou ligado ao músico Luis Fonsi e «Sánchez García, Manuel» a um treinador galego; o critério de «alta» foi apertado duas vezes por isso, e esses casos estão agora em «média». Podem restar outros, sobretudo em nomes muito comuns.
- **Verificação por amostragem.** A qualidade foi verificada em amostras de cerca de 20 casos de cada vez, não pessoa a pessoa.
- **Sem data de morte não quer dizer viva.** A Wikidata pode simplesmente não ter a data. Das 417 pessoas já ligadas, 414 não têm nada de novo, o que sugere que estão vivas, mas não o garante.
- **Cobertura.** 974 pessoas não têm candidato na Wikidata. É de esperar para ilustradores, prologuistas, participantes em certames e autores com um único livro.
- **Dados da Wikidata.** As datas são as que lá estão, com os erros que possam ter. Em 5 itens há mais de um ano de nascimento registado; ficam assinalados na coluna «Notas».
- **A pesquisa reflete a Wikidata em 12 de outubro de 2026.** As respostas ficaram em cache; para voltar a consultar, apaga-se `wikidata_cache.json`.

## Dúvidas em aberto

### 1. Rever o ficheiro de importação antes de o usar

Recomenda-se percorrer as 699 linhas de confiança alta, comparando o nome com a descrição no ficheiro completo. Os casos a olhar com mais atenção são os 174 que não estão descritos como galegos. Quer-se uma coluna com a descrição diretamente no ficheiro de importação?

### 2. Importar também os ID da Wikidata?

O ficheiro de importação traz 699 ID novos. Importá-los liga as pessoas à Wikidata de forma permanente, o que é útil mas torna um eventual erro de homonímia mais visível. Há ainda os campos «URL da Wikidata», VIAF e GND na BD; o script só preenche os dois primeiros.

### 3. Que fazer com as confianças média e baixa

Há 321 datas possíveis a mais (225 em «média», 96 em «baixa»), que exigem escolha à mão. A coluna «Outros candidatos» dá os ID alternativos.

### 4. Datas guardadas como 1 de janeiro

Na BD, 162 datas de nascimento terminam em `-01-01`. Em vários casos a Wikidata só tem o ano, pelo que o dia e o mês parecem ter sido acrescentados numa importação anterior. O script não lhes toca. Devem ser corrigidas para só o ano?

### 5. Formato das datas novas

As datas novas vêm com a precisão da Wikidata (`1962`, `1970-10` ou `1964-07-30`). Confirma-se que a importação do Heurist aceita os três formatos no mesmo campo?

### 6. Data de nascimento no campo errado

Cristina Ferreirós Sánchez-Guisande (H-ID 5928) tem o ano de nascimento (1962) no campo genérico «Birth date» e não em «Data de nacemento». Não entra nas contagens e o script trata-a como não tendo data de nascimento.

### 7. Nomes não pesquisados (46)

São nomes só com iniciais ou de uma só palavra (pseudónimos, nomes artísticos). Só se resolvem identificando a pessoa por outra via. Coincidem em parte com as pessoas que ficaram sem género (ver `gender/NOTAS-genero-pessoas.md`).

### 8. Pessoas que não são pessoas

Alguns registos Pessoa podem ser coletivos ou nomes genéricos, para os quais as datas de nascimento e morte não se aplicam. Convém excluí-los antes de calcular percentagens de preenchimento.

### 9. Guardar a cache no repositório?

`wikidata_cache.json` ocupa cerca de 900 KB. Mantê-lo no GitHub permite reproduzir exatamente estes resultados; deixá-lo de fora obriga a nova consulta, com resultados que podem mudar com o tempo.
