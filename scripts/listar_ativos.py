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
    ap.add_argument("--pdf", help="usa um PDF local em vez de baixar")
    ap.add_argument("--force", action="store_true", help="ignora o cache e baixa de novo")
    ap.add_argument("--vencimentos", action="store_true", help="imprime tambem o calendario de vencimentos")
    ap.add_argument("--csv", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    pdf = a.pdf or baixar(a.force)
    por_ativo, por_venc, atualizado, total = analisar(extrair_texto(pdf))

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
