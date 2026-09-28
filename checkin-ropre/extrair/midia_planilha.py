# -*- coding: utf-8 -*-
"""Adaptador de mídia paga a partir de planilha (Growth Pack e similares).

É o caminho enquanto a mídia não vier do Flow. Lê abas diárias — uma por canal —
e devolve `midia` no modelo canônico, um registro por dia e canal. Diário importa:
sem ele não dá para fechar quinzena, só mês.

  python3 extrair/midia_planilha.py --cliente clientes/<c>/cliente.json --saida bruto_midia.json

Configuração em `cliente.json`:

```json
"midia": {
  "arquivo": "growthpack.xlsx",
  "abas": [
    {"aba": "bd Meta Ads",    "canal": "meta",
     "colunas": {"dia": 0, "investimento": 1, "leads": 3, "impressoes": 4, "campanha": 5, "cliques": 9}},
    {"aba": "bd Google Ads ", "canal": "google",
     "colunas": {"dia": 0, "investimento": 1, "cliques": 2, "leads": 3, "impressoes": 5}}
  ]
}
```

As colunas são índices (0 = primeira), porque nome de coluna em planilha de
cliente muda sozinho. O adaptador avisa quando uma aba pára de receber dado —
é o erro mais comum, e o que mais estraga indicador de mídia.
"""
import argparse, datetime, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extrair.base import Adaptador, registrar  # noqa: E402
from transformar import canonico  # noqa: E402


def _num(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    txt = str(v).strip().replace("R$", "").replace(" ", "")
    if not txt:
        return None
    txt = txt.replace(".", "").replace(",", ".") if "," in txt else txt
    try:
        return float(txt)
    except ValueError:
        return None


def _dia(v):
    if isinstance(v, datetime.datetime):
        return v.date().isoformat()
    if isinstance(v, datetime.date):
        return v.isoformat()
    if not v:
        return None
    txt = str(v).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.datetime.strptime(txt[:10], formato).date().isoformat()
        except ValueError:
            continue
    return None


@registrar("midia_planilha")
class MidiaPlanilha(Adaptador):

    def extrair(self, cliente, janela=None):
        import openpyxl

        cfg = cliente.get("midia") or {}
        caminho = self.config.get("arquivo") or cfg.get("arquivo")
        pacote = self.pacote(cliente, janela)
        if not caminho or not os.path.exists(caminho):
            pacote["avisos"].append(f"Planilha de mídia não encontrada ({caminho!r}): bloco de mídia fica sem dado.")
            return pacote

        wb = openpyxl.load_workbook(caminho, data_only=True, read_only=True)
        fonte_por_canal = cfg.get("fonte_por_canal") or {}
        for aba_cfg in cfg.get("abas") or []:
            nome = aba_cfg["aba"]
            dono = fonte_por_canal.get(aba_cfg["canal"])
            if dono and dono != "planilha":
                continue
            if nome not in wb.sheetnames:
                pacote["avisos"].append(f"Aba {nome!r} não existe na planilha de mídia.")
                continue
            col = aba_cfg["colunas"]
            ultimo, linhas = None, 0
            for i, linha in enumerate(wb[nome].iter_rows(values_only=True)):
                if i == 0 or not linha:
                    continue
                dia = _dia(linha[col["dia"]] if col["dia"] < len(linha) else None)
                if not dia:
                    continue
                if janela and not (janela["de"] <= dia <= janela["ate"]):
                    ultimo = max(ultimo or dia, dia)
                    continue
                pega = lambda c: (_num(linha[col[c]]) if c in col and col[c] < len(linha) else None)  # noqa: E731
                pacote["midia"].append({
                    "dia": dia,
                    "canal": aba_cfg["canal"],
                    "campanha": (linha[col["campanha"]] if "campanha" in col and col["campanha"] < len(linha) else None),
                    "investimento": pega("investimento") or 0.0,
                    "impressoes": (int(pega("impressoes")) if pega("impressoes") is not None else None),
                    "cliques": (int(pega("cliques")) if pega("cliques") is not None else None),
                    "leads": (int(pega("leads")) if pega("leads") is not None else None),
                })
                linhas += 1
                ultimo = max(ultimo or dia, dia)
            if linhas == 0:
                pacote["avisos"].append(
                    f"Aba {nome!r} ({aba_cfg['canal']}) não tem linha no período" +
                    (f"; último dia com dado: {ultimo}." if ultimo else "."))
        return pacote


def main():
    p = argparse.ArgumentParser(description="Extrai mídia paga de planilha no modelo canônico")
    p.add_argument("--cliente", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--arquivo")
    p.add_argument("--de")
    p.add_argument("--ate")
    a = p.parse_args()
    with open(a.cliente, encoding="utf-8") as f:
        cliente = json.load(f)
    base = os.path.dirname(os.path.abspath(a.cliente))
    arquivo = a.arquivo or (cliente.get("midia", {}).get("arquivo") and
                            os.path.join(base, cliente["midia"]["arquivo"]))
    janela = {"de": a.de, "ate": a.ate} if a.de and a.ate else None
    pacote = MidiaPlanilha({"arquivo": arquivo}).extrair(cliente, janela)
    canonico.gravar(pacote, a.saida)
    total = sum(m["investimento"] for m in pacote["midia"])
    print(f"{a.saida}: {len(pacote['midia'])} dias de mídia, R$ {total:,.2f} investidos.")
    for aviso in pacote["avisos"]:
        print(f"  aviso: {aviso}")


if __name__ == "__main__":
    main()
