# margens-opcoes-btg

Skill para o [Claude Code](https://claude.com/claude-code) (e script Python independente) que baixa o
PDF de **Margem Exigida – Opções** do BTG Pactual e o reduz à lista de ativos-objeto: ticker, nome,
número de séries e, opcionalmente, o calendário de vencimentos.

O PDF oficial (<https://investimentos.btgpactual.com/opcoes/margens/>) tem centenas de páginas e
dezenas de milhares de séries, mas se refere a apenas ~80 ativos-objeto. Esta skill responde rápido
a perguntas como "quais ações têm opções aceitas em margem no BTG?" ou "quantas séries de PETR existem?".

## Requisitos

- Python 3.8+ (somente biblioteca padrão)
- `pdftotext`, do pacote **poppler-utils**
  - Debian/Ubuntu: `sudo apt install poppler-utils`
  - macOS: `brew install poppler`

## Instalação como skill do Claude Code

```bash
git clone https://github.com/Itiho/margens-opcoes-btg.git ~/.claude/skills/margens-btg
```

Depois disso, basta pedir ao Claude algo como *"liste os ativos da tabela de margens de opções do BTG"*
ou *"quais vencimentos existem no margens.pdf?"* — a skill é acionada automaticamente.

## Uso direto do script

```bash
python3 scripts/listar_ativos.py                 # tabela: TICKER | NOME | nº de séries
python3 scripts/listar_ativos.py --vencimentos   # + calendário de vencimentos
python3 scripts/listar_ativos.py --csv           # CSV: ticker,nome,raiz_opcao,series
python3 scripts/listar_ativos.py --json          # saída JSON
python3 scripts/listar_ativos.py --pdf ARQ.pdf   # usa um PDF local (não baixa)
python3 scripts/listar_ativos.py --force         # ignora o cache e baixa de novo
```

O PDF é salvo em `~/.cache/margens-btg/margens.pdf` e reaproveitado por 6 horas. O servidor do BTG
é lento: o download (~8 MB) costuma levar cerca de 2 minutos.

## Como funciona

- A URL de margens **devolve o PDF diretamente** (`Content-Type: application/pdf`); não há HTML para raspar.
- Cada código de opção segue o formato `RAIZ(4) + LETRA + STRIKE [+ W<n>]`, por exemplo `PETRJ350`
  ou `BPACV516W4`. A raiz identifica o ativo-objeto, e o dicionário `ATIVOS` no script mapeia
  raiz → ticker + nome.
- A letra codifica mês e tipo: `A–L` = call de jan a dez, `M–X` = put de jan a dez. O ano não aparece
  no PDF; ele é inferido a partir da data "Atualizado em:" do próprio arquivo.
- Vencimento mensal = 3ª sexta-feira do mês. Séries semanais `W1/W2/W4/W5` vencem nas demais sextas
  (`W3` não existe). Se a sexta for feriado na B3, o vencimento passa para o dia útil seguinte.

## Estrutura

```
.
├── SKILL.md                 # definição da skill (lida pelo Claude Code)
├── README.md
└── scripts/
    └── listar_ativos.py     # download, parsing e saída
```

## Manutenção

Raízes novas (IPO, troca de nome, fusão) aparecem na saída como
`XXXX? (nao identificado - raiz nova no PDF)`. Para corrigir, acrescente a entrada correspondente
no dicionário `ATIVOS` em `scripts/listar_ativos.py`.

Casos particulares já tratados:

- Raiz diferente do ticker: `EMBJ` → EMBR3, `AXIA` → ex-ELET3/ELET6.
- Sufixos diferentes de 3/4/11: `CPLE6`, `USIM5`, `BRAP4`, `GGBR4`, `GOAU4`, `POMO4`, `CMIG4`, `ISAE4`.
- Raízes com duas classes com opções (PETR3/PETR4, BBDC3/BBDC4, CMIG3/CMIG4, ITSA3/ITSA4) usam
  a mesma raiz no PDF; o script mostra a classe mais líquida.

## Aviso

Projeto independente, sem vínculo com o BTG Pactual. Os dados vêm do PDF público da corretora e
podem mudar de formato sem aviso. Não é recomendação de investimento.
