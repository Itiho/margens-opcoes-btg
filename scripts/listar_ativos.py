#!/usr/bin/env python3
"""Baixa o PDF de margens de opcoes do BTG e imprime os ativos-objeto da lista.

Fonte: https://investimentos.btgpactual.com/opcoes/margens/  (a URL devolve o PDF direto)

Uso:
    python3 listar_ativos.py                 # tabela Ticker | Nome | nº de series
    python3 listar_ativos.py --vencimentos   # tambem o calendario de vencimentos
    python3 listar_ativos.py --csv           # saida CSV (ticker,nome,series)
    python3 listar_ativos.py --json
    python3 listar_ativos.py --pdf ARQ.pdf   # usa um PDF local em vez de baixar
    python3 listar_ativos.py --force         # ignora o cache e baixa de novo
    python3 listar_ativos.py PETR4           # series de opcoes de um ativo, com vencimento e margem
    python3 listar_ativos.py PETR4 --tipo put --venc 11/2026
    python3 listar_ativos.py PETR4 --venc 11/2026 --semana W1,M   # W1, W2, W4, W5 ou M (mensal)
"""
import argparse, collections, csv, datetime as dt, json, os, re, shutil, subprocess, sys, tempfile
import urllib.request

URL = "https://investimentos.btgpactual.com/opcoes/margens/"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "margens-btg")

# raiz de 4 caracteres da serie de opcoes -> (ticker do ativo-objeto, nome)
ATIVOS = {
    "ABEV": ("ABEV3", "Ambev"),
    "ALOS": ("ALOS3", "Allos"),
    "ASAI": ("ASAI3", "Assai (Sendas Distribuidora)"),
    "AURE": ("AURE3", "Auren Energia"),
    "AXIA": ("AXIA3", "Axia Energia (ex-Eletrobras)"),
    "AZZA": ("AZZA3", "Azzas 2154"),
    "B3SA": ("B3SA3", "B3 - Brasil, Bolsa, Balcao"),
    "BBAS": ("BBAS3", "Banco do Brasil"),
    "BBDC": ("BBDC4", "Bradesco PN"),
    "BBSE": ("BBSE3", "BB Seguridade"),
    "BEEF": ("BEEF3", "Minerva Foods"),
    "BOVA": ("BOVA11", "ETF iShares Ibovespa (nao e acao)"),
    "BOVV": ("BOVV11", "ETF It Now Ibovespa (nao e acao)"),
    "BPAC": ("BPAC11", "BTG Pactual (unit)"),
    "BRAP": ("BRAP4", "Bradespar PN"),
    "BRAV": ("BRAV3", "Brava Energia"),
    "CEAB": ("CEAB3", "C&A Modas"),
    "CMIG": ("CMIG4", "Cemig PN"),
    "COGN": ("COGN3", "Cogna Educacao"),
    "CPFE": ("CPFE3", "CPFL Energia"),
    "CPLE": ("CPLE6", "Copel PNB"),
    "CSAN": ("CSAN3", "Cosan"),
    "CSMG": ("CSMG3", "Copasa"),
    "CSNA": ("CSNA3", "CSN - Cia Siderurgica Nacional"),
    "CURY": ("CURY3", "Cury Construtora"),
    "CXSE": ("CXSE3", "Caixa Seguridade"),
    "CYRE": ("CYRE3", "Cyrela Brazil Realty"),
    "DIRR": ("DIRR3", "Direcional Engenharia"),
    "ECOR": ("ECOR3", "EcoRodovias"),
    "EGIE": ("EGIE3", "Engie Brasil Energia"),
    "EMBJ": ("EMBR3", "Embraer"),
    "ENEV": ("ENEV3", "Eneva"),
    "ENGI": ("ENGI11", "Energisa (unit)"),
    "EQTL": ("EQTL3", "Equatorial Energia"),
    "FLRY": ("FLRY3", "Fleury"),
    "GGBR": ("GGBR4", "Gerdau PN"),
    "GOAU": ("GOAU4", "Metalurgica Gerdau PN"),
    "HYPE": ("HYPE3", "Hypera Pharma"),
    "IGTI": ("IGTI11", "Iguatemi (unit)"),
    "ISAE": ("ISAE4", "ISA Energia Brasil (ex-ISA Cteep) PN"),
    "ITSA": ("ITSA4", "Itausa PN"),
    "ITUB": ("ITUB4", "Itau Unibanco PN"),
    "JBSS": ("JBSS3", "JBS"),
    "JHSF": ("JHSF3", "JHSF Participacoes"),
    "KLBN": ("KLBN11", "Klabin (unit)"),
    "LREN": ("LREN3", "Lojas Renner"),
    "MBRF": ("MBRF3", "MBRF Global Foods (BRF + Marfrig)"),
    "MGLU": ("MGLU3", "Magazine Luiza"),
    "MOTV": ("MOTV3", "Motiva (ex-CCR)"),
    "MRVE": ("MRVE3", "MRV Engenharia"),
    "MULT": ("MULT3", "Multiplan"),
    "MYPK": ("MYPK3", "Iochpe-Maxion"),
    "NATU": ("NATU3", "Natura &Co"),
    "PETR": ("PETR4", "Petrobras PN"),
    "POMO": ("POMO4", "Marcopolo PN"),
    "PRIO": ("PRIO3", "PRIO (ex-PetroRio)"),
    "PSSA": ("PSSA3", "Porto Seguro"),
    "RADL": ("RADL3", "Raia Drogasil"),
    "RAIL": ("RAIL3", "Rumo"),
    "RDOR": ("RDOR3", "Rede D'Or Sao Luiz"),
    "RENT": ("RENT3", "Localiza Rent a Car"),
    "SANB": ("SANB11", "Santander Brasil (unit)"),
    "SBSP": ("SBSP3", "Sabesp"),
    "SMAL": ("SMAL11", "ETF iShares Small Cap (nao e acao)"),
    "SMFT": ("SMFT3", "Smart Fit"),
    "SUZB": ("SUZB3", "Suzano"),
    "TAEE": ("TAEE11", "Taesa (unit)"),
    "TEND": ("TEND3", "Construtora Tenda"),
    "TIMS": ("TIMS3", "TIM Brasil"),
    "TOTS": ("TOTS3", "Totvs"),
    "UGPA": ("UGPA3", "Ultrapar"),
    "USIM": ("USIM5", "Usiminas PNA"),
    "VALE": ("VALE3", "Vale"),
    "VAMO": ("VAMO3", "Vamos Locacao"),
    "VBBR": ("VBBR3", "Vibra Energia"),
    "VIVA": ("VIVA3", "Vivara"),
    "VIVT": ("VIVT3", "Telefonica Brasil / Vivo"),
    "WEGE": ("WEGE3", "WEG"),
    "YDUQ": ("YDUQ3", "Yduqs"),
}

SERIE_RE = re.compile(r"\b([A-Z0-9]{4})([A-Z])([0-9]{1,3})(W[0-9])?\b")
MARGEM_RE = re.compile(r"\b(([A-Z0-9]{4})([A-Z])([0-9]{1,3})(W[0-9])?)\s+R\$\s*([0-9.,]+)")
CALL, PUT = "ABCDEFGHIJKL", "MNOPQRSTUVWX"   # A=jan..L=dez (call), M=jan..X=dez (put)
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def baixar(force=False):
    os.makedirs(CACHE, exist_ok=True)
    destino = os.path.join(CACHE, "margens.pdf")
    if os.path.exists(destino) and not force:
        idade = dt.datetime.now() - dt.datetime.fromtimestamp(os.path.getmtime(destino))
        if idade < dt.timedelta(hours=6):
            print(f"# usando cache ({destino}, {int(idade.total_seconds()//60)} min)", file=sys.stderr)
            return destino
    print(f"# baixando {URL}", file=sys.stderr)
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        if "pdf" not in r.headers.get("Content-Type", ""):
            sys.exit(f"erro: a URL respondeu {r.headers.get('Content-Type')}, esperava application/pdf")
        tmp = destino + ".part"
        with open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
    os.replace(tmp, destino)
    print(f"# salvo em {destino} ({os.path.getsize(destino)/1e6:.1f} MB)", file=sys.stderr)
    return destino


def extrair_texto(pdf):
    if not shutil.which("pdftotext"):
        sys.exit("erro: pdftotext nao encontrado. Instale com: sudo apt install poppler-utils")
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as t:
        saida = t.name
    subprocess.run(["pdftotext", "-layout", pdf, saida], check=True)
    texto = open(saida, encoding="utf-8", errors="replace").read()
    os.unlink(saida)
    return texto


def analisar(texto):
    series = set(SERIE_RE.findall(texto))
    por_ativo = collections.Counter()
    por_venc = collections.Counter()
    for raiz, letra, _strike, wk in series:
        por_ativo[raiz] += 1
        por_venc[(letra, wk or "M")] += 1
    m = re.search(r"Atualizado em:\s*(\d{2}/\d{2}/\d{4})", texto)
    atualizado = dt.datetime.strptime(m.group(1), "%d/%m/%Y").date() if m else None
    return por_ativo, por_venc, atualizado, len(series)


def sextas(ano, mes):
    d = dt.date(ano, mes, 1)
    d += dt.timedelta(days=(4 - d.weekday()) % 7)
    out = []
    while d.month == mes:
        out.append(d)
        d += dt.timedelta(days=7)
    return out


def data_vencimento(letra, wk, atualizado):
    """(letra, 'W1'|'W2'|'M'|'W4'|'W5') -> date, pela escada de 12 meses a partir do arquivo."""
    base = atualizado or dt.date.today()
    mes = (CALL + PUT).index(letra) % 12 + 1
    ano = base.year + (1 if mes < base.month else 0)
    fr = sextas(ano, mes)
    n = 3 if wk == "M" else int(wk[1])
    return fr[n - 1] if n <= len(fr) else None


def raiz_do_ativo(ativo):
    ativo = ativo.upper()
    if ativo in ATIVOS:
        return ativo
    for raiz, (ticker, _nome) in ATIVOS.items():
        if ticker == ativo:
            return raiz
    # PETR3, BBDC3 etc.: mesma raiz da classe liquida; EMBR3 -> EMBJ
    for raiz, (ticker, _nome) in ATIVOS.items():
        if ticker.rstrip("0123456789") == ativo.rstrip("0123456789"):
            return raiz
    return ativo[:4]


def opcoes_do_ativo(texto, raiz, atualizado):
    out = {}
    for codigo, r, letra, num, wk, valor in MARGEM_RE.findall(texto):
        if r != raiz or letra not in CALL + PUT:
            continue
        venc = data_vencimento(letra, wk or "M", atualizado)
        out[codigo] = {
            "codigo": codigo,
            "tipo": "CALL" if letra in CALL else "PUT",
            "vencimento": venc,
            "semanal": wk or "",
            "margem": float(valor.replace(",", "")),
            "_num": num.ljust(3, "0"),  # 44 ~ 44,0 e 423 ~ 42,3: compara como decimal
        }
    ops = sorted(out.values(), key=lambda o: (o["vencimento"] or dt.date.max, o["tipo"], o["_num"], o["codigo"]))
    for o in ops:
        del o["_num"]
    return ops


def imprimir_opcoes(a, texto, atualizado):
    raiz = raiz_do_ativo(a.ativo)
    ticker, nome = ATIVOS.get(raiz, (a.ativo.upper(), "(raiz nao cadastrada)"))
    ops = opcoes_do_ativo(texto, raiz, atualizado)
    if a.tipo:
        ops = [o for o in ops if o["tipo"] == a.tipo.upper()]
    if a.semana:
        sem = {x.strip().upper() for x in a.semana.split(",")}
        sem = {"" if x in ("M", "MENSAL") else x for x in sem}
        invalidas = sem - {"", "W1", "W2", "W4", "W5"}
        if invalidas:
            sys.exit(f"erro: --semana invalida: {', '.join(sorted(invalidas))} (use W1, W2, W4, W5 ou M)")
        ops = [o for o in ops if o["semanal"] in sem]
    if a.venc:
        m = re.fullmatch(r"(\d{1,2})/(\d{4})|(\d{2})/(\d{2})/(\d{4})", a.venc)
        if not m:
            sys.exit("erro: --venc deve ser MM/AAAA ou DD/MM/AAAA")
        if m.group(1):
            mes, ano = int(m.group(1)), int(m.group(2))
            ops = [o for o in ops if o["vencimento"] and (o["vencimento"].month, o["vencimento"].year) == (mes, ano)]
        else:
            alvo = dt.date(int(m.group(5)), int(m.group(4)), int(m.group(3)))
            ops = [o for o in ops if o["vencimento"] == alvo]
    if not ops:
        sys.exit(f"nenhuma opcao encontrada para {a.ativo.upper()} (raiz {raiz}) com esses filtros")

    fmt = lambda d: d.strftime("%d/%m/%Y") if d else "-"
    if a.json:
        print(json.dumps({"atualizado": fmt(atualizado), "ativo": ticker, "nome": nome, "raiz": raiz,
                          "opcoes": [{**o, "vencimento": fmt(o["vencimento"])} for o in ops]},
                         ensure_ascii=False, indent=2))
        return
    if a.csv:
        w = csv.writer(sys.stdout)
        w.writerow(["codigo", "tipo", "vencimento", "semanal", "margem"])
        for o in ops:
            w.writerow([o["codigo"], o["tipo"], fmt(o["vencimento"]), o["semanal"], f"{o['margem']:.2f}"])
        return

    print(f"\n{ticker} - {nome} | raiz {raiz} | atualizado em: {fmt(atualizado)} | {len(ops)} series")
    print("-" * 52)
    print(f"{'CODIGO':<12} {'TIPO':<5} {'VENCIMENTO':<11} {'SEM':<4} {'MARGEM (R$)':>14}")
    print("-" * 52)
    anterior = None
    for o in ops:
        if anterior and o["vencimento"] != anterior:
            print()
        anterior = o["vencimento"]
        print(f"{o['codigo']:<12} {o['tipo']:<5} {fmt(o['vencimento']):<11} {o['semanal']:<4} "
              f"{o['margem']:>14,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print("-" * 52)
    print("MARGEM = margem exigida por opcao vendida (R$). O PDF nao traz o strike; o numero no\n"
          "codigo so lembra o strike (VALEK353 ~ 35,30) e nao acompanha ajustes por proventos.")


def calendario(por_venc, atualizado):
    """Escada de 12 meses a partir do mes do arquivo; mensal = 3a sexta, semanais = as outras."""
    base = atualizado or dt.date.today()
    linhas = []
    for k in range(12):
        mes = (base.month - 1 + k) % 12 + 1
        ano = base.year + (base.month - 1 + k) // 12
        for slot in ("W1", "W2", "M", "W4", "W5"):
            qtd = por_venc.get((CALL[mes - 1], slot), 0) + por_venc.get((PUT[mes - 1], slot), 0)
            if not qtd:
                continue
            fr = sextas(ano, mes)
            data = fr[2] if slot == "M" else (fr[int(slot[1]) - 1] if int(slot[1]) <= len(fr) else None)
            linhas.append({
                "mes": f"{MESES[mes-1]}/{str(ano)[2:]}",
                "tipo": "Mensal (3a sexta)" if slot == "M" else f"Semanal {slot}",
                "call": CALL[mes - 1], "put": PUT[mes - 1],
                "data": data.strftime("%d/%m/%Y") if data else "-",
                "series": qtd,
            })
    return linhas


def main():
    ap = argparse.ArgumentParser(description="Lista os ativos-objeto do PDF de margens de opcoes do BTG.")
    ap.add_argument("ativo", nargs="?", help="ticker ou raiz (ex.: PETR4, VALE3, BOVA11, PETR) - lista as series dele")
    ap.add_argument("--tipo", choices=["call", "put"], help="com ATIVO: filtra calls ou puts")
    ap.add_argument("--semana", help="com ATIVO: W1, W2, W4, W5 ou M (mensal); aceita lista, ex.: W1,M")
    ap.add_argument("--venc", help="com ATIVO: filtra pelo vencimento (MM/AAAA ou DD/MM/AAAA)")
    ap.add_argument("--pdf", help="usa um PDF local em vez de baixar")
    ap.add_argument("--force", action="store_true", help="ignora o cache e baixa de novo")
    ap.add_argument("--vencimentos", action="store_true", help="imprime tambem o calendario de vencimentos")
    ap.add_argument("--csv", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if (a.tipo or a.venc or a.semana) and not a.ativo:
        ap.error("--tipo, --semana e --venc exigem um ATIVO (ex.: PETR4)")

    pdf = a.pdf or baixar(a.force)
    texto = extrair_texto(pdf)
    por_ativo, por_venc, atualizado, total = analisar(texto)
    if a.ativo:
        imprimir_opcoes(a, texto, atualizado)
        return

    itens = []
    for raiz in sorted(por_ativo):
        ticker, nome = ATIVOS.get(raiz, (raiz + "?", "(nao identificado - raiz nova no PDF)"))
        itens.append({"raiz": raiz, "ticker": ticker, "nome": nome, "series": por_ativo[raiz]})
    itens.sort(key=lambda x: x["ticker"])
    vencs = calendario(por_venc, atualizado)

    if a.json:
        print(json.dumps({"atualizado": atualizado.strftime("%d/%m/%Y") if atualizado else None,
                          "total_series": total, "ativos": itens, "vencimentos": vencs},
                         ensure_ascii=False, indent=2))
        return
    if a.csv:
        w = csv.writer(sys.stdout)
        w.writerow(["ticker", "nome", "raiz_opcao", "series"])
        for i in itens:
            w.writerow([i["ticker"], i["nome"], i["raiz"], i["series"]])
        return

    print(f"\nMargem Exigida - Opcoes (BTG) | atualizado em: "
          f"{atualizado.strftime('%d/%m/%Y') if atualizado else '?'} | "
          f"{len(itens)} ativos-objeto | {total:,} series".replace(",", "."))
    print("-" * 78)
    print(f"{'TICKER':<8} {'NOME':<52} {'SERIES':>7}")
    print("-" * 78)
    for i in itens:
        print(f"{i['ticker']:<8} {i['nome']:<52} {i['series']:>7}")
    print("-" * 78)
    print(f"{'TOTAL':<8} {'':<52} {total:>7}")

    if a.vencimentos:
        print("\nVencimentos presentes no arquivo")
        print("-" * 78)
        print(f"{'MES':<8} {'TIPO':<20} {'CALL':<5} {'PUT':<5} {'VENCIMENTO':<12} {'SERIES':>7}")
        print("-" * 78)
        for v in vencs:
            print(f"{v['mes']:<8} {v['tipo']:<20} {v['call']:<5} {v['put']:<5} {v['data']:<12} {v['series']:>7}")
        print("-" * 78)
        print("Mensal = 3a sexta-feira; semanais = as demais sextas (W3 nao existe: e a semana do mensal).")
        print("Se a sexta nao for dia util na B3, o vencimento passa para o 1o dia util seguinte.")
        print("O ano nao esta no PDF - inferido pela escada de 12 meses a partir da data do arquivo.")


if __name__ == "__main__":
    main()
