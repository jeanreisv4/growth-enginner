# -*- coding: utf-8 -*-
"""Adaptador do Flow pelos servidores MCP da V4 — a fonte principal do check-in.

Os servidores do Flow são endpoints HTTP que falam MCP (JSON-RPC + SSE), então este
adaptador fala MCP direto: o ETL roda em cron, em terminal ou dentro do Claude, sem
depender de qual deles está na frente.

  python3 extrair/flow_mcp.py --cliente clientes/exemplo/cliente.json \\
      --saida bruto_flow.json --de 2026-09-01 --ate 2026-09-22

O que ele traz hoje, por servidor:

  dados-flow         mídia paga por dia e canal (custo, impressões, cliques, leads),
                     metas do período (viram o bloco de Objetivos) e o CRM do projeto
                     quando houver conexão de CRM
  bigquery-whatsapp  atividade do grupo do cliente — vira pendência no bloco de Entregas
  bigquery-calls     calls do período — acordos viram Próximos Passos
  cockpit            health score e datas do projeto (churn, renovação) — contexto de risco

## Credenciais

Nunca no código e nunca no `cliente.json`. O adaptador lê, nesta ordem:

  1. `--mcp-config <arquivo>`
  2. `$FLOW_MCP_CONFIG`
  3. `~/.config/v4-flow/mcp.json`

no formato que o Flow distribui (`{"servidor": {"url": ..., "headers": {...}}}`). Guarde
o arquivo com `chmod 600`.

## Escopo

Tudo no Flow é escopado por `projectDocumentId`. Descubra o do cliente com
`localize_project` (bigquery-calls) ou `cockpit_list_projects`, e grave em
`cliente.json` → `flow.project_document_id`. Um mesmo cliente pode ter mais de um
projeto (assessoria e produtos adicionais entram como contratos separados): cada
projeto é um check-in.
"""
import argparse, collections, json, os, sys, urllib.request, uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extrair.base import Adaptador, registrar  # noqa: E402
from transformar import canonico  # noqa: E402

PADRAO_CONFIG = os.path.expanduser("~/.config/v4-flow/mcp.json")


# --------------------------------------------------------------- cliente MCP

class MCP:
    """Cliente MCP mínimo sobre HTTP. Aceita resposta JSON pura ou SSE."""

    def __init__(self, config):
        self.config = config
        self.sessoes = {}

    @staticmethod
    def carregar_config(caminho=None):
        alvo = caminho or os.environ.get("FLOW_MCP_CONFIG") or PADRAO_CONFIG
        if not os.path.exists(alvo):
            raise SystemExit(
                f"Configuração MCP do Flow não encontrada em {alvo}.\n"
                "Grave o JSON dos servidores (url + headers) nesse caminho, com chmod 600, "
                "ou aponte --mcp-config / $FLOW_MCP_CONFIG.")
        with open(alvo, encoding="utf-8") as f:
            dados = json.load(f)
        return dados.get("mcpServers", dados)

    def _post(self, servidor, corpo, timeout=120):
        srv = self.config[servidor]
        req = urllib.request.Request(srv["url"], data=json.dumps(corpo).encode())
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        for k, v in (srv.get("headers") or {}).items():
            req.add_header(k, v)
        if self.sessoes.get(servidor):
            req.add_header("Mcp-Session-Id", self.sessoes[servidor])
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.headers.get("Mcp-Session-Id"), r.read().decode("utf-8", "replace")

    @staticmethod
    def _eventos(bruto):
        bruto = (bruto or "").strip()
        if not bruto:
            return []
        if bruto.startswith("{"):
            return [json.loads(bruto)]
        saida = []
        for linha in bruto.splitlines():
            if linha.startswith("data:"):
                pedaco = linha[5:].strip()
                if pedaco and pedaco != "[DONE]":
                    try:
                        saida.append(json.loads(pedaco))
                    except json.JSONDecodeError:
                        pass
        return saida

    def abrir(self, servidor):
        if servidor in self.sessoes:
            return
        sid, bruto = self._post(servidor, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "checkin-ropre", "version": "1.0"}}})
        self.sessoes[servidor] = sid
        if sid:
            try:
                self._post(servidor, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            except Exception:
                pass

    def chamar(self, servidor, ferramenta, argumentos, timeout=120):
        """Devolve o conteúdo já decodificado, ou levanta RuntimeError com a mensagem do servidor."""
        if servidor not in self.config:
            raise RuntimeError(f"servidor {servidor!r} não está na configuração MCP")
        self.abrir(servidor)
        _, bruto = self._post(servidor, {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "tools/call",
                                         "params": {"name": ferramenta, "arguments": argumentos}}, timeout)
        for evento in self._eventos(bruto):
            if "error" in evento:
                raise RuntimeError(evento["error"].get("message", str(evento["error"])))
            if "result" in evento:
                return self._conteudo(evento["result"])
        raise RuntimeError(f"resposta vazia de {ferramenta}")

    @staticmethod
    def _conteudo(resultado):
        partes = resultado.get("content") or []
        for parte in partes:
            texto = parte.get("text")
            if texto is None:
                continue
            texto = texto.strip()
            if texto.startswith("Error:") or texto.startswith("Strapi HTTP"):
                raise RuntimeError(texto[:300])
            try:
                return json.loads(texto)
            except json.JSONDecodeError:
                return texto
        return resultado


# --------------------------------------------------------------- adaptador

@registrar("flow")
class Flow(Adaptador):

    def __init__(self, config=None):
        super().__init__(config)
        self.mcp = MCP(MCP.carregar_config((config or {}).get("mcp_config")))

    def extrair(self, cliente, janela=None):
        flow = cliente.get("flow") or {}
        projeto = flow.get("project_document_id")
        pacote = self.pacote(cliente, janela)
        if not projeto:
            raise SystemExit(
                "cliente.json sem flow.project_document_id. Descubra com:\n"
                "  bigquery-calls → localize_project(search_text='<cliente>')\n"
                "  cockpit        → cockpit_list_projects(filtersJson=...)")
        if not janela:
            raise SystemExit("flow_mcp precisa de janela (--de/--ate): as consultas do Flow são por período.")

        self._midia(pacote, projeto, flow, janela)
        self._metas(pacote, projeto, janela)
        self._whatsapp(pacote, flow, janela)
        self._calls(pacote, projeto, janela)
        return pacote

    # ------------------------------------------------------------- mídia

    def _midia(self, pacote, projeto, flow, janela):
        try:
            conexoes = (self.mcp.chamar("dados-flow", "flow_project_data_list_connections",
                                        {"projectDocumentId": projeto}) or {})
            conexoes = (conexoes.get("data") or {}).get("connections") or []
        except Exception as e:
            pacote["avisos"].append(f"Flow: não consegui listar as conexões do projeto ({e}).")
            return

        fonte_por_canal = ((flow.get("fonte_por_canal") or {}) or
                           ((self.config.get("cliente_midia") or {}).get("fonte_por_canal") or {}))
        for con in conexoes:
            if con.get("category") != "ads":
                continue
            plataforma = con.get("platform")
            dono = fonte_por_canal.get(_canal(plataforma))
            if dono and dono != "flow":
                pacote["avisos"].append(f"Flow: {plataforma} não foi extraído daqui — o cliente.json "
                                        f"aponta {dono} como fonte desse canal.")
                continue
            if not con.get("queryable") or not con.get("active"):
                pacote["avisos"].append(
                    f"Flow: conexão de {plataforma} não está consultável "
                    f"(último run {con.get('lastRunStatus')} em {(con.get('lastRunAt') or '')[:10]}). "
                    f"O canal fica sem medição no período.")
                continue
            try:
                self._midia_plataforma(pacote, projeto, plataforma, con.get("accountId"), janela)
            except Exception as e:
                pacote["avisos"].append(f"Flow: falha lendo mídia de {plataforma} ({e}).")

    def _midia_plataforma(self, pacote, projeto, plataforma, conta, janela):
        """Um registro por dia e canal.

        Custo, impressões e cliques saem de **um SQL** na tabela de insights: é exato e é
        uma chamada só. Leads saem de `flow_media_conversion_summary`, que desempacota as
        ações da Meta — essa devolve linha por anúncio e por dia, no máximo 100 por página,
        então tem teto de páginas e avisa quando bate no teto.
        """
        por_dia = {}
        tabela = self._tabela_insights(projeto, plataforma)
        conta_sql = (conta or "").replace("act_", "")
        if tabela and conta_sql:
            sql = (f"SELECT date_start AS dia, ROUND(SUM(CAST(spend AS FLOAT64)),2) AS investimento, "
                   f"SUM(CAST(impressions AS INT64)) AS impressoes, SUM(CAST(clicks AS INT64)) AS cliques "
                   f"FROM {tabela} WHERE account_id = '{conta_sql}' "
                   f"AND date_start >= '{janela['de']}' AND date_start <= '{janela['ate']}' "
                   f"GROUP BY dia ORDER BY dia")
            try:
                linhas = ((self.mcp.chamar("dados-flow", "flow_media_query",
                                           {"projectDocumentId": projeto, "platform": plataforma,
                                            "sql": sql}) or {}).get("data") or {}).get("rows") or []
                for linha in linhas:
                    por_dia[linha["dia"]] = {"investimento": float(linha.get("investimento") or 0),
                                             "impressoes": _int(linha.get("impressoes")),
                                             "cliques": _int(linha.get("cliques")), "leads": None}
            except Exception as e:
                pacote["avisos"].append(f"Flow: SQL de mídia de {plataforma} falhou ({e}); "
                                        f"custo do período fica sem medição.")

        leads, truncado = self._leads_por_dia(projeto, plataforma, janela)
        if truncado:
            # subcontagem silenciosa é pior que lacuna: some com o número e avisa
            pacote["avisos"].append(
                f"Flow: a contagem de leads de {plataforma} passou do teto de páginas e ficou incompleta, "
                f"então saiu sem medição. Custo, impressões e cliques do período seguem exatos (SQL).")
        else:
            for dia, n in leads.items():
                por_dia.setdefault(dia, {"investimento": 0.0, "impressoes": None, "cliques": None, "leads": None})
                por_dia[dia]["leads"] = n

        for dia, v in sorted(por_dia.items()):
            pacote["midia"].append({"dia": dia, "canal": _canal(plataforma), "campanha": None,
                                    "investimento": round(v["investimento"], 2),
                                    "impressoes": v["impressoes"], "cliques": v["cliques"],
                                    "leads": v["leads"]})
        if not por_dia:
            pacote["avisos"].append(f"Flow: {plataforma} sem linha no período {janela['de']} a {janela['ate']}.")

    def _tabela_insights(self, projeto, plataforma):
        """Descobre a tabela de insights da conexão (o nome muda por conta e por plataforma)."""
        try:
            tabelas = ((self.mcp.chamar("dados-flow", "flow_media_list_tables",
                                        {"projectDocumentId": projeto, "platform": plataforma}) or {})
                       .get("data") or {}).get("tables") or []
        except Exception:
            return None
        preferidos = ("adsinsights", "insights", "ad_performance_report", "campaign_insights")
        for alvo in preferidos:
            for t in tabelas:
                if t.get("stream") == alvo:
                    return t.get("qualifiedTable") or t.get("table")
        return None

    def _leads_por_dia(self, projeto, plataforma, janela, teto_paginas=12):
        por_dia, tamanho = collections.Counter(), 100
        pagina = 1
        while pagina <= teto_paginas:
            try:
                resposta = self.mcp.chamar("dados-flow", "flow_media_conversion_summary", {
                    "projectDocumentId": projeto, "platform": plataforma,
                    "period": {"startGte": janela["de"], "endLt": _dia_seguinte(janela["ate"])},
                    "pagination": {"page": pagina, "pageSize": tamanho}})
            except Exception:
                return dict(por_dia), False
            itens = ((resposta or {}).get("data") or {}).get("items") or []
            for item in itens:
                dia = ((item.get("period") or {}).get("startAt") or "")[:10]
                acoes = item.get("actions") or {}
                if dia:
                    por_dia[dia] += int(acoes.get("lead") or acoes.get("onsite_conversion.lead_grouped") or 0)
            if len(itens) < tamanho:
                return dict(por_dia), False
            pagina += 1
        return dict(por_dia), True

    # ------------------------------------------------------------- metas

    def _metas(self, pacote, projeto, janela):
        """As metas do Flow alimentam o bloco de Objetivos — OKR deixa de ser digitado à mão."""
        periodo = janela["ate"][:7]
        try:
            resposta = self.mcp.chamar("dados-flow", "flow_goals_list", {
                "subjectRef": projeto, "subjectType": "project",
                "periodKey": periodo, "granularity": "monthly"}) or {}
        except Exception as e:
            pacote["avisos"].append(f"Flow: não consegui ler as metas ({e}).")
            return
        itens = resposta.get("items") or []
        if not itens:
            pacote["avisos"].append(
                f"Flow: o projeto não tem meta cadastrada em {periodo} — o bloco de Objetivos "
                f"sai com as OKRs do cliente.json, e cadastrar a meta no Flow é próximo passo.")
            return
        for item in itens:
            pacote.setdefault("metas", []).append({
                "metrica": item.get("metricKey"),
                "rotulo": item.get("label") or item.get("metricKey"),
                "meta": item.get("target"),
                "realizado": item.get("actual"),
                "atingimento": item.get("attainment"),
                "ritmo": item.get("pace"),
                "periodo": periodo,
            })

    # ------------------------------------------------------------- conversas

    def _whatsapp(self, pacote, flow, janela):
        grupo = flow.get("whatsapp_group_id")
        if not grupo:
            return
        try:
            resumo = self.mcp.chamar("bigquery-whatsapp", "whatsapp_resumir_grupos_queryon", {
                "limit": "50", "mode": "list", "id_group": grupo, "client_documentid": "",
                "search_name": "", "start_date": janela["de"], "end_date": janela["ate"]})
        except Exception as e:
            pacote["avisos"].append(f"Flow: não consegui ler o grupo de WhatsApp ({e}).")
            return
        for linha in (resumo if isinstance(resumo, list) else []):
            texto = (linha.get("latest_resumo") or "").strip()
            risco = (linha.get("latest_status_risco") or "").strip()
            pacote["conversas"].append({
                "dia": (linha.get("last_created_at") or janela["ate"])[:10],
                "canal": "whatsapp",
                "status": risco or "sem status",
                "assunto": linha.get("name"),
                "pendencia": texto or None,
            })
        if not pacote["conversas"]:
            pacote["avisos"].append("Flow: grupo de WhatsApp sem resumo no período — sem pendência automática.")

    # ------------------------------------------------------------- calls

    def _calls(self, pacote, projeto, janela):
        try:
            calls = self.mcp.chamar("bigquery-calls", "consultar_calls_por_tipo", {
                "limit": "50", "call_type": "", "mode": "list",
                "project_document_id": projeto, "project_ticker": "", "project_tickers_csv": "",
                "start_date": janela["de"], "end_date": janela["ate"], "search_text": "",
                "require_transcription": "false", "require_url": "false",
                "include_transcription_excerpt": "true", "include_invitees": "false"})
        except Exception as e:
            pacote["avisos"].append(f"Flow: não consegui ler as calls ({e}).")
            return
        for c in (calls if isinstance(calls, list) else []):
            pacote["calls"].append({
                "dia": (c.get("start_time") or c.get("meeting_date") or janela["ate"])[:10],
                "titulo": c.get("title") or c.get("call_type") or "Call com o cliente",
                "acordos": [], "pendencias": [], "riscos": [],
                "_transcricao": (c.get("transcription_excerpt") or "")[:4000] or None,
            })
        if not pacote["calls"]:
            pacote["avisos"].append(
                f"Flow: nenhuma call registrada entre {janela['de']} e {janela['ate']}. "
                f"Acordo e próximo passo saem só do que a equipe registrou.")
        else:
            pacote["avisos"].append(
                "Flow: as calls vieram sem acordo extraído. Leia a transcrição (campo `_transcricao`) "
                "e preencha acordos, pendências e riscos antes de gerar o deck — a skill não infere "
                "compromisso de cliente a partir de texto corrido.")


def _int(v):
    return int(float(v)) if v not in (None, "") else None


def _canal(plataforma):
    return {"meta_ads": "meta", "google_ads": "google", "linkedin_ads": "linkedin",
            "tiktok_ads": "tiktok"}.get(plataforma, plataforma)


def _dia_seguinte(iso):
    import datetime
    return (datetime.date.fromisoformat(iso) + datetime.timedelta(days=1)).isoformat()


def main():
    ap = argparse.ArgumentParser(description="Extrai o Flow (MCP) no modelo canônico do check-in")
    ap.add_argument("--cliente", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--de", required=True)
    ap.add_argument("--ate", required=True)
    ap.add_argument("--mcp-config")
    a = ap.parse_args()
    with open(a.cliente, encoding="utf-8") as f:
        cliente = json.load(f)
    pacote = Flow({"mcp_config": a.mcp_config}).extrair(cliente, {"de": a.de, "ate": a.ate})
    canonico.gravar(pacote, a.saida)
    investido = sum(m["investimento"] for m in pacote["midia"])
    print(f"{a.saida}: {len(pacote['midia'])} dias de mídia (R$ {investido:,.2f}), "
          f"{len(pacote.get('metas') or [])} metas, {len(pacote['conversas'])} conversas, "
          f"{len(pacote['calls'])} calls.")
    for aviso in pacote["avisos"]:
        print(f"  aviso: {aviso}")


if __name__ == "__main__":
    main()
