# -*- coding: utf-8 -*-
"""Adaptador do NectarCRM — a implementação de referência do contrato de extração.

Serve a dois propósitos: atende os clientes que estão no NectarCRM e mostra, em
código que roda, o que um adaptador novo precisa entregar. Quando o
Flow passar a servir o CRM, este arquivo vira fallback.

  python3 extrair/crm_nectarcrm.py --cliente clientes/exemplo/cliente.json --saida bruto_crm.json

Fontes, nesta ordem:
  --bruto arquivo.json[.gz]   extrato salvo (`crm.bruto` no cliente.json) — roda offline
  --token / NECTAR_TOKEN      puxa da API (15 registros por página; leva minutos)

Pegadinhas do NectarCRM, aprendidas em campo:
  * sem `status=N` a API só devolve negócio aberto; 1=andamento 2=ganha 3=perdida 4=descartada 5=prorrogada;
  * `dataInicio`/`dataFim` mudam a ordenação e NÃO filtram — filtre localmente;
  * "Ganha" em funil de qualificação (pré-vendas, SDR) é passagem de etapa, não venda;
  * o campo `vendaBase` vem falso em todos os registros: recorrência é o funil, não o campo.
"""
import argparse, datetime, gzip, json, os, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extrair.base import Adaptador, Atribuicao, registrar  # noqa: E402
from transformar import canonico  # noqa: E402

BASE = "https://app.nectarcrm.com.br/crm/api/1"
GANHA, PERDIDA, DESCARTADA = 2, 3, 4


def abrir(caminho):
    f = gzip.open(caminho, "rt", encoding="utf-8") if str(caminho).endswith(".gz") else open(caminho, encoding="utf-8")
    with f:
        return json.load(f)


def data_local(iso):
    """A API devolve UTC; o cliente lê o dia em Brasília (UTC-3)."""
    if not iso:
        return None
    try:
        d = datetime.datetime.strptime(str(iso)[:19], "%Y-%m-%dT%H:%M:%S") - datetime.timedelta(hours=3)
        return d.date().isoformat()
    except ValueError:
        return None


@registrar("nectarcrm")
class NectarCRM(Adaptador):

    def extrair(self, cliente, janela=None):
        bruto = self.config.get("bruto_carregado") or self._obter(cliente)
        atrib = Atribuicao(cliente.get("atribuicao"))
        crm = cliente.get("crm") or {}
        funis_venda = set(crm.get("funis_venda") or [])
        funil_recorrencia = crm.get("funil_recorrencia")

        pacote = self.pacote(cliente, janela)
        pacote["extraido_em"] = bruto.get("puxado_em") or pacote["extraido_em"]
        contatos = {c["id"]: c for c in bruto.get("contatos", [])}

        if not funis_venda:
            pacote["avisos"].append("cliente.json sem crm.funis_venda: nenhum negócio foi classificado como venda.")

        for c in bruto.get("contatos", []):
            origem = c.get("origem")
            pacote["contatos"].append({
                "id": c["id"],
                "criado_em": data_local(c.get("criacao")),
                "origem": origem,
                "canal": atrib.canal(origem),
                "uf": c.get("uf"),
                "atribuicao": atrib.marcar(tags_contato=c.get("listas"), origem=origem),
            })

        for o in bruto.get("oportunidades", []):
            ct = contatos.get(o.get("cliente")) or {}
            origem = ct.get("origem")
            funil = o.get("pipeline")
            if funil not in funis_venda:
                continue          # funil de qualificação não é venda; entra como oportunidade, não como negócio
            status = {GANHA: "ganho", PERDIDA: "perdido", DESCARTADA: "perdido"}.get(o.get("status"), "aberto")
            pacote["negocios"].append({
                "id": o.get("codigo") or o.get("id"),
                "criado_em": data_local(o.get("criacao")),
                "fechado_em": data_local(o.get("conclusao")) if status != "aberto" else None,
                "status": status,
                "valor": float(o.get("valor") or 0.0),
                "funil": funil,
                "etapa": o.get("etapa"),
                "tipo": "recorrente" if funil == funil_recorrencia else "novo",
                "motivo_perda": (o.get("motivo") if status == "perdido" else None),
                "canal": atrib.canal(origem),
                "contato_id": o.get("cliente"),
                "atribuicao": atrib.marcar(tags_negocio=o.get("listas"), tags_contato=ct.get("listas"), origem=origem),
            })

        dias = [n["criado_em"] for n in pacote["negocios"] if n["criado_em"]]
        if dias and not pacote["periodo_bruto"]:
            pacote["periodo_bruto"] = {"de": min(dias), "ate": max(dias)}
        pacote["avisos"].append("NectarCRM não expõe histórico de mudança de etapa: tempo por etapa sai de "
                                "criação, entrada na etapa atual e conclusão.")
        return pacote

    # ------------------------------------------------------------- fontes

    def _obter(self, cliente):
        caminho = self.config.get("bruto")
        if caminho and os.path.exists(caminho):
            return abrir(caminho)
        token = self.config.get("token") or os.environ.get("NECTAR_TOKEN")
        if not token:
            raise SystemExit("NectarCRM sem fonte: passe --bruto com um extrato salvo ou --token/NECTAR_TOKEN.")
        return self._api(token)

    def _api(self, token):
        ops = self._paginar("oportunidades", token)
        for st in (2, 3, 4, 5):
            ops += self._paginar("oportunidades", token, status=st)
        vistos, unicas = set(), []
        for o in ops:
            if o["id"] not in vistos:
                vistos.add(o["id"])
                unicas.append(o)
        return self._normalizar(unicas, self._paginar("contatos", token))

    @staticmethod
    def _paginar(modulo, token, **filtros):
        itens, pagina, vistos, falhas = [], 1, set(), 0
        while pagina <= 3000:
            qs = "".join(f"&{k}={v}" for k, v in filtros.items())
            try:
                with urllib.request.urlopen(f"{BASE}/{modulo}/?api_token={token}&page={pagina}{qs}", timeout=60) as r:
                    lote = json.load(r)
            except Exception as e:
                falhas += 1
                if falhas > 5:
                    raise SystemExit(f"{modulo}: falhou 5 vezes seguidas na página {pagina} ({e}).")
                time.sleep(2)
                continue
            falhas = 0
            if not lote:
                break
            for reg in lote:
                if reg.get("id") not in vistos:
                    vistos.add(reg["id"])
                    itens.append(reg)
            pagina += 1
        return itens

    @staticmethod
    def _normalizar(ops, cts):
        def listas(x):
            return [(l.get("nome") if isinstance(l, dict) else l) for l in (x.get("listas") or [])]

        def motivo(o):
            for j in (o.get("justificativas") or []):
                t = (j.get("descricao") or j.get("nome") or j.get("motivo")) if isinstance(j, dict) else str(j)
                if t:
                    return t.strip()
            return None

        def nome_de(v):
            return v.get("nome") if isinstance(v, dict) else v

        return {
            "oportunidades": [dict(id=o["id"], codigo=o.get("codigo"), pipeline=o.get("pipeline"),
                                   etapa=o.get("etapaNome"), status=o.get("status"),
                                   valor=o.get("valorTotal") or 0.0, criacao=o.get("dataCriacao"),
                                   conclusao=o.get("dataConclusao"), listas=listas(o), motivo=motivo(o),
                                   cliente=(o.get("cliente") or {}).get("id")) for o in ops],
            "contatos": [dict(id=c["id"], nome=c.get("nome"), origem=nome_de(c.get("origem")),
                              listas=listas(c), criacao=c.get("dataCriacao"),
                              uf=((c.get("regiaoEstado") or {}).get("sigla")
                                  if isinstance(c.get("regiaoEstado"), dict) else None)) for c in cts],
            "puxado_em": datetime.date.today().isoformat(),
        }


def main():
    p = argparse.ArgumentParser(description="Extrai o NectarCRM no modelo canônico do check-in")
    p.add_argument("--cliente", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--bruto", help="extrato salvo (.json/.json.gz); sobrepõe o do cliente.json")
    p.add_argument("--token", default=os.environ.get("NECTAR_TOKEN"))
    a = p.parse_args()

    cliente = abrir(a.cliente)
    base = os.path.dirname(os.path.abspath(a.cliente))
    bruto = a.bruto or ((cliente.get("crm") or {}).get("bruto") and
                        os.path.join(base, cliente["crm"]["bruto"]))
    pacote = NectarCRM({"bruto": bruto, "token": a.token}).extrair(cliente)
    canonico.gravar(pacote, a.saida)
    print(f"{a.saida}: {len(pacote['negocios'])} negócios, {len(pacote['contatos'])} contatos "
          f"({sum(1 for n in pacote['negocios'] if n['atribuicao']['agencia'])} negócios da agência).")


if __name__ == "__main__":
    main()
