# CRM e integração: planilha, n8n, CRM, WhatsApp e a volta da venda

**Leitura:** API do CRM (`scripts/datacrazy.py` para DataCrazy; Kommo, RD CRM, NectarCRM e GoHighLevel pela API de
cada um), planilha de backup, execuções do n8n (API do n8n) e o backup de leads. **Escrita:** n8n (backup do fluxo
antes, modo automático pode negar), automações do CRM e Apps Script, com ok. A volta da venda para as plataformas é
implantada pela skill `tracking-web-and-capi`.

## Auditoria

| Id | Verificação | Frente | Como verificar | Sinal de problema | Gravidade |
| --- | --- | --- | --- | --- | --- |
| I1 | Todo lead do formulário chega ao destino (planilha, n8n, CRM, painel) | medicao | contagem formulário × destino por dia | 57 de 59 leads do formulário nativo fora do painel | crítica |
| I2 | O lead chega com origem gravada (UTM, gclid, fbclid, ctwaId) | medicao | campos de origem no CRM × backup | lead de mídia sem origem | alta |
| I3 | Formulário nativo do Meta integrado ao CRM | medicao | fluxo existente + contagem | leads baixados à mão ou esquecidos | alta |
| I4 | Duplicidade de pessoa no CRM | comercial | `leads.py` sobre o export do CRM | mesma pessoa em vários negócios | média |
| I5 | Fluxo com erro silencioso (n8n, Make, Apps Script) | medicao | execuções com erro nos últimos 30 dias | token 401, execução falhando sem alerta | alta |
| I6 | Etiqueta ou campo de origem automático, e com que atraso | comercial | histórico do lead (quem e quando etiquetou) | etiqueta manual com 7,8 dias de mediana | média |
| I7 | Pipelines e status: "Ganha" só no funil de venda | comercial | pipelines e etapas pela API | "Ganha" de pré-vendas com valor padrão | média |
| I8 | SQL e venda voltam para Meta (CAPI) e Google (offline) | medicao | eventos Purchase/SQL no conjunto de dados; conversões offline | plataformas otimizando só por lead | alta |
| I9 | Rastreio do clique para WhatsApp ligado no CRM | medicao | conversas com `sourceReferral`/ctwaId | conversa de anúncio sem origem | média |
| I10 | Credenciais fora de planilha, fluxo e arquivo | medicao | nós do n8n, abas da planilha, exports | token do WhatsApp ou do CRM em texto aberto | alta |
| I11 | Backup de leads com os campos padrão | fontes | colunas da planilha × padrão da skill `tracking-web-and-capi` | sem data, origem ou status | baixa |

## Correção

| Id | Correção | Corrige | Como aplicar | Validar antes | Risco | Voltar atrás | Verificar depois |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CX-I1 | Consertar o fluxo e reprocessar os leads perdidos a partir do backup | I1, I5 | API do n8n (backup do workflow antes) | lista dos leads a reprocessar; sem duplicar | R2 | restaurar o workflow do backup | contagem formulário × destino igual por 3 dias |
| CX-I2 | Mapear os campos de origem até o CRM | I2 | n8n + campo personalizado do CRM | lead real recente conferido campo a campo | R2 | mapeamento anterior | próximo lead com origem |
| CX-I3 | Integrar o formulário nativo (webhook do Meta → n8n → CRM) | I3 | n8n (fluxo novo) | fluxo ativo só depois do ok | R2 | desativar o fluxo | lead nativo chega em minutos |
| CX-I4 | Deduplicar por telefone e e-mail canônicos na entrada | I4 | n8n (busca antes de criar) com a regra de `leads.py` | casos de exemplo | R2 | versão anterior do fluxo | duplicados novos = 0 |
| CX-I5 | Alerta de erro no fluxo e renovação do token | I5 | n8n (Error Trigger → e-mail ou WhatsApp) | destino do alerta | R1 | desativar o alerta | erro de teste gera alerta |
| CX-I6 | Etiqueta de origem automática na criação do lead | I6 | automação do CRM ou n8n | regra de origem escrita | R2 | desligar a automação | atraso da etiqueta = 0 |
| CX-I7 | Filtrar os pipelines de venda e padronizar status | I7 | configuração do CRM + regra na memória | lista de pipelines e o que conta | R2 | — | venda do mês bate com o comercial |
| CX-I8 | Volta da venda: Apps Script ou webhook do CRM → servidor (Purchase, SQL) e upload offline | I8, A22 | skill `tracking-web-and-capi` + `google_ads.md` CX-A15 | gclid/fbclid gravados no lead | R2 | desativar o envio | Purchase e conversão offline chegando com valor |
| CX-I9 | Ligar a automação de rastreio do WhatsApp no CRM | I9, M17 | interface do CRM | instância do WhatsApp oficial | R1 | desligar | conversa nova com `sourceReferral` |
| CX-I10 | Tirar a credencial do lugar aberto e trocar | I10 | credenciais do n8n; revogar e gerar token novo | onde a credencial aparece | R2 | — | nenhuma credencial em texto aberto |
| CX-I11 | Backup de leads no padrão | I11 | planilha modelo da skill `tracking-web-and-capi` | colunas que faltam | R1 | planilha anterior | próximo lead com todos os campos |
