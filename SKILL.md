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

# séries de um ativo: código, strike, CALL/PUT, vencimento, semanal e margem exigida (R$)
python3 scripts/listar_ativos.py PETR4
python3 scripts/listar_ativos.py VALE3 --tipo put --venc 11/2026   # MM/AAAA ou DD/MM/AAAA
python3 scripts/listar_ativos.py VALE3 --venc 11/2026 --semana M   # W1, W2, W4, W5 ou M (mensal); aceita W1,M
python3 scripts/listar_ativos.py BOVA11 --csv                      # também --json
python3 scripts/listar_ativos.py VALE3 --semana W2 --cotacao 60   # linha da cotação num valor dado
python3 scripts/listar_ativos.py PETR4 --sem-b3                    # não consulta a B3 (sem strike/cotação)
```

O ativo pode ser o ticker (`PETR4`, `PETR3`, `EMBR3`) ou a raiz (`PETR`, `EMBJ`).

Requisito: `pdftotext` (pacote `poppler-utils`). Sem dependências Python externas.

O PDF é salvo em `~/.cache/margens-btg/margens.pdf` e reaproveitado por 6 horas.
O download leva ~2 minutos (≈8 MB, servidor lento) — use um timeout generoso.

**Strike e vencimento** vêm do cadastro de instrumentos da B3 (`InstrumentsConsolidatedFile`, data do PDF
ou até 7 dias antes), salvo filtrado em `~/.cache/margens-btg/instrumentos-AAAA-MM-DD.csv` (~2 MB).
A API da B3 às vezes dá 504; o script tenta 3 vezes e, se falhar, segue com strike `?` e vencimento
inferido pela letra. O PDF do BTG **não traz o strike** — só código e margem exigida.

Em cada grupo (vencimento + CALL/PUT) uma linha `=== cotacao VALE3 R$ 64,67 ===` separa os strikes
abaixo e acima da cotação atual (API `cotacao.b3.com.br`, atraso ~15 min; ticker do ativo-objeto
tirado do cadastro da B3). `--cotacao VALOR` substitui; sem cotação, não há linha.

## Como o script identifica as coisas

- A URL `https://investimentos.btgpactual.com/opcoes/margens/` **devolve o PDF direto**
  (`Content-Type: application/pdf`); não há página HTML para raspar.
- Cada código na tabela é `RAIZ(4) + LETRA + NÚMERO [+ W<n>]`, ex. `PETRJ350`, `BPACV516W4`. O número
  **não é o strike** (só lembra: `VALEK353` = 35,39; `BOVAJ1` = 178,00) — o strike vem da B3.
  A raiz identifica o ativo-objeto; o dicionário `ATIVOS` no script mapeia raiz → ticker + nome.
- A letra codifica mês e tipo: `A–L` = call jan–dez, `M–X` = put jan–dez. O ano **não** está
  no PDF. Sem a B3, é inferido pela escada de 12 meses a partir do "Atualizado em:" — e erra para
  séries longas (ex.: `PETRJ5` e `BOVAJ1` vencem em 15/10/**2027**, não 2026).
- Vencimento mensal = 3ª sexta-feira; `W1/W2/W4/W5` = as outras sextas do mês (`W3` não existe,
  é a semana do mensal). Se a sexta for feriado, a B3 **antecipa** para o dia útil anterior
  (ex.: VALEK de nov/2026 vence em 19/11, porque 20/11 é Consciência Negra). A inferência sem B3
  não trata feriados; o calendário de `--vencimentos` também usa só a inferência.

## Manutenção

Raízes novas (IPO, troca de nome, fusão) aparecem na saída como
`XXXX? (nao identificado - raiz nova no PDF)`. Quando isso acontecer, acrescente a entrada em
`ATIVOS` no script. Casos em que a raiz difere do ticker antigo: `EMBJ` → EMBJ3 (ex-EMBR3), `AXIA` → ex-ELET3/ELET6;
os tickers antigos ficam em `APELIDOS`.
Sufixos que não são 3/4/11: `CPLE6`, `USIM5`, `BRAP4`, `GGBR4`, `GOAU4`, `POMO4`, `CMIG4`, `ISAE4`.
Quando a raiz tem duas classes com opções (PETR3/PETR4, BBDC3/BBDC4, CMIG3/CMIG4, ITSA3/ITSA4),
o PDF usa a mesma raiz para as duas e o script mostra a classe líquida.
