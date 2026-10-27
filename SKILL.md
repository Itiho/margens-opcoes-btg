---
name: margens-btg
description: Baixa o PDF de Margem Exigida - Opções do BTG (https://investimentos.btgpactual.com/opcoes/margens/) e imprime a lista de ativos-objeto (ticker + nome), a contagem de séries e o calendário de vencimentos. Use quando o usuário pedir para listar os ativos/ações com opções na tabela de margens do BTG, atualizar essa lista, conferir quais tickers têm opções aceitas em margem, ver quantas séries existem por ativo, ou quando mencionar o arquivo "margens.pdf" / a página de margens de opções do BTG.
---

# Margens de opções do BTG — lista de ativos-objeto

O PDF de margens do BTG tem centenas de páginas e dezenas de milhares de séries de opções,
mas se refere a ~80 ativos-objeto. Este script baixa o arquivo e reduz tudo à lista de ativos.

## Uso

```bash
python3 scripts/listar_ativos.py                 # tabela: TICKER | NOME | nº de séries
python3 scripts/listar_ativos.py --vencimentos   # + calendário de vencimentos
python3 scripts/listar_ativos.py --csv           # CSV: ticker,nome,raiz_opcao,series
python3 scripts/listar_ativos.py --json
python3 scripts/listar_ativos.py --pdf ARQ.pdf   # usa um PDF local (não baixa)
python3 scripts/listar_ativos.py --force         # ignora o cache

# séries de um ativo: código, CALL/PUT, data de vencimento, semanal e margem (R$)
python3 scripts/listar_ativos.py PETR4
python3 scripts/listar_ativos.py VALE3 --tipo put --venc 11/2026   # MM/AAAA ou DD/MM/AAAA
python3 scripts/listar_ativos.py VALE3 --venc 11/2026 --semana M   # W1, W2, W4, W5 ou M (mensal); aceita W1,M
python3 scripts/listar_ativos.py BOVA11 --csv                      # também --json
```

O ativo pode ser o ticker (`PETR4`, `PETR3`, `EMBR3`) ou a raiz (`PETR`, `EMBJ`).

Requisito: `pdftotext` (pacote `poppler-utils`). Sem dependências Python externas.

O PDF é salvo em `~/.cache/margens-btg/margens.pdf` e reaproveitado por 6 horas.
O download leva ~2 minutos (≈8 MB, servidor lento) — use um timeout generoso.

## Como o script identifica as coisas

- A URL `https://investimentos.btgpactual.com/opcoes/margens/` **devolve o PDF direto**
  (`Content-Type: application/pdf`); não há página HTML para raspar.
- Cada código na tabela é `RAIZ(4) + LETRA + STRIKE [+ W<n>]`, ex. `PETRJ350`, `BPACV516W4`.
  A raiz identifica o ativo-objeto; o dicionário `ATIVOS` no script mapeia raiz → ticker + nome.
- A letra codifica mês e tipo: `A–L` = call jan–dez, `M–X` = put jan–dez. O ano **não** está
  no PDF — é inferido pela escada de 12 meses a partir do "Atualizado em:" do próprio arquivo.
- Vencimento mensal = 3ª sexta-feira; `W1/W2/W4/W5` = as outras sextas do mês (`W3` não existe,
  é a semana do mensal). Se a sexta for feriado na B3, o vencimento vai para o dia útil seguinte
  (ex.: 20/11 — Consciência Negra).

## Manutenção

Raízes novas (IPO, troca de nome, fusão) aparecem na saída como
`XXXX? (nao identificado - raiz nova no PDF)`. Quando isso acontecer, acrescente a entrada em
`ATIVOS` no script. Casos em que a raiz difere do ticker: `EMBJ` → EMBR3, `AXIA` → ex-ELET3/ELET6.
Sufixos que não são 3/4/11: `CPLE6`, `USIM5`, `BRAP4`, `GGBR4`, `GOAU4`, `POMO4`, `CMIG4`, `ISAE4`.
Quando a raiz tem duas classes com opções (PETR3/PETR4, BBDC3/BBDC4, CMIG3/CMIG4, ITSA3/ITSA4),
o PDF usa a mesma raiz para as duas e o script mostra a classe líquida.
