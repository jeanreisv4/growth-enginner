#!/bin/zsh
# Roda o ETL inteiro e entrega o check-in em deck e documento.
#
#   ./gerar.sh exemplo mensal 2026-08-15
#   ./gerar.sh exemplo quinzenal 2026-09-21
#
# Argumentos: <cliente> <cadência: quinzenal|mensal|quarter> [referência YYYY-MM-DD]
set -e
cd "$(dirname "$0")"

CLIENTE=${1:?informe o cliente (pasta em clientes/)}
CADENCIA=${2:-mensal}
REFERENCIA=${3:-$(date +%Y-%m-%d)}

DIR="clientes/$CLIENTE"
CFG="$DIR/cliente.json"
OUT="saida/$CLIENTE"
[ -f "$CFG" ] || { echo "não achei $CFG"; exit 1; }
mkdir -p "$OUT"

# A extração cobre o período do check-in INTEIRO mais o histórico que as tabelas
# de safra e de série mensal precisam. Cortar a extração na data de referência
# faz um mês fechado parecer incompleto — e some com ROAS e CPL do período.
eval "$(python3 - "$REFERENCIA" "$CADENCIA" <<'PY'
import sys, datetime
sys.path.insert(0, ".")
from transformar import canonico
p = canonico.periodo(sys.argv[1], sys.argv[2])
inicio_hist = (datetime.date.fromisoformat(p["ate"]) - datetime.timedelta(days=760)).isoformat()
print(f"PERIODO_ATE={p['ate']}")
print(f"HIST_DE={inicio_hist}")
print(f"ROTULO='{p['rotulo']}'")
PY
)"

echo "── E: extraindo ($HIST_DE → $PERIODO_ATE)"
PACOTES=()

# CRM: do Flow quando houver conexão de CRM lá; do adaptador direto quando não.
python3 extrair/crm_nectarcrm.py --cliente "$CFG" --saida "$OUT/crm.json" && PACOTES+=("$OUT/crm.json")

# Flow (MCP): mídia, metas, WhatsApp e calls.
if python3 -c "import json,sys; c=json.load(open('$CFG')); sys.exit(0 if (c.get('flow') or {}).get('project_document_id') else 1)"; then
  python3 extrair/flow_mcp.py --cliente "$CFG" --saida "$OUT/flow.json" \
    --de "$HIST_DE" --ate "$PERIODO_ATE" && PACOTES+=("$OUT/flow.json")
fi

# Planilha: só os canais que o cliente.json atribui a ela.
python3 extrair/midia_planilha.py --cliente "$CFG" --saida "$OUT/midia.json" \
  --de "$HIST_DE" --ate "$PERIODO_ATE" && PACOTES+=("$OUT/midia.json")

python3 extrair/conversas_mcp.py --cliente "$CFG" --saida "$OUT/conversas.json" \
  --calls "$DIR/entradas/calls.json" --conversas "$DIR/entradas/conversas.json" && PACOTES+=("$OUT/conversas.json")

echo "── T + L: montando o ROPRE ($ROTULO)"
python3 carregar/blocos.py --cliente "$CFG" --dados "${PACOTES[@]}" \
  --cadencia "$CADENCIA" --referencia "$REFERENCIA" --entradas "$DIR/entradas/entregas.json" \
  --saida "$OUT/checkin.json"

echo "── saída"
python3 carregar/documento.py --checkin "$OUT/checkin.json" --saida "$OUT/checkin.md"
python3 carregar/deck.py --checkin "$OUT/checkin.json" --saida "$OUT/checkin.pptx"
echo
echo "pronto:"
echo "  $OUT/checkin.json   (números, para conferir)"
echo "  $OUT/checkin.md     (documento de revisão)"
echo "  $OUT/checkin.pptx   (deck; o Google Slides abre e converte)"
