// Núcleo da devolução CRM → plataformas (Kommo → n8n → sGTM/Meta e Google Ads).
// Funções puras, sem nada do n8n: o gerador (scripts/gerar_devolucao.py) cola este arquivo no começo dos nós
// Code do workflow, e tests/regressao.py roda as mesmas funções no JavaScript do macOS. Mudou aqui, muda nos dois.
// Sem require('crypto'): o n8n só libera módulo nativo com NODE_FUNCTION_ALLOW_BUILTIN, então o SHA-256 é daqui.

function sha256(ascii) {
  // SHA-256 em JS puro (texto em UTF-8), saída em hex minúsculo, como o Google Ads e o Meta pedem.
  var utf8 = unescape(encodeURIComponent(ascii));
  var K = [], H = [], i, j, primo = 0;
  for (var c = 2; primo < 64; c++) {
    var ok = true;
    for (j = 2; j * j <= c; j++) if (c % j === 0) { ok = false; break; }
    if (ok) {
      if (primo < 8) H[primo] = (Math.pow(c, 1 / 2) * 4294967296) | 0;
      K[primo++] = (Math.pow(c, 1 / 3) * 4294967296) | 0;
    }
  }
  var bytes = [];
  for (i = 0; i < utf8.length; i++) bytes.push(utf8.charCodeAt(i));
  var bits = bytes.length * 8;
  bytes.push(0x80);
  while (bytes.length % 64 !== 56) bytes.push(0);
  for (i = 7; i >= 0; i--) bytes.push(i >= 4 ? 0 : (bits >>> (i * 8)) & 0xff);
  var rot = function (x, n) { return (x >>> n) | (x << (32 - n)); };
  for (i = 0; i < bytes.length; i += 64) {
    var w = [], a = H[0], b = H[1], cc = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
    for (j = 0; j < 64; j++) {
      if (j < 16) w[j] = (bytes[i + j * 4] << 24) | (bytes[i + j * 4 + 1] << 16) | (bytes[i + j * 4 + 2] << 8) | bytes[i + j * 4 + 3];
      else {
        var s0 = rot(w[j - 15], 7) ^ rot(w[j - 15], 18) ^ (w[j - 15] >>> 3);
        var s1 = rot(w[j - 2], 17) ^ rot(w[j - 2], 19) ^ (w[j - 2] >>> 10);
        w[j] = (w[j - 16] + s0 + w[j - 7] + s1) | 0;
      }
      var t1 = (h + (rot(e, 6) ^ rot(e, 11) ^ rot(e, 25)) + ((e & f) ^ (~e & g)) + K[j] + w[j]) | 0;
      var t2 = ((rot(a, 2) ^ rot(a, 13) ^ rot(a, 22)) + ((a & b) ^ (a & cc) ^ (b & cc))) | 0;
      h = g; g = f; f = e; e = (d + t1) | 0; d = cc; cc = b; b = a; a = (t1 + t2) | 0;
    }
    H[0] = (H[0] + a) | 0; H[1] = (H[1] + b) | 0; H[2] = (H[2] + cc) | 0; H[3] = (H[3] + d) | 0;
    H[4] = (H[4] + e) | 0; H[5] = (H[5] + f) | 0; H[6] = (H[6] + g) | 0; H[7] = (H[7] + h) | 0;
  }
  var hex = '';
  for (i = 0; i < 8; i++) hex += ('00000000' + (H[i] >>> 0).toString(16)).slice(-8);
  return hex;
}

function lerWebhookKommo(body) {
  // Dois formatos de origem:
  //  - webhook da conta ("Lead stage changed"), x-www-form-urlencoded: leads[status][0][id]=…&…[status_id]=…
  //    (o n8n entrega aninhado, body.leads.status[0].id, ou achatado, "leads[status][0][id]", conforme o parser);
  //  - ação "Send webhook" do Digital Pipeline: {"lead":{"event":{id, status_id, pipeline_id, old_status_id…}}}.
  // Devolve [{lead_id, status_id, pipeline_id, old_status_id, quando}] só das mudanças de etapa.
  body = body || {};
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = {}; } }
  var linhas = [];
  var st = body.leads && body.leads.status;
  var dp = body.lead && body.lead.event;
  if (st) {
    var lista = Array.isArray(st) ? st : Object.keys(st).map(function (k) { return st[k]; });
    lista.forEach(function (l) { linhas.push(l); });
  } else if (dp) {
    (Array.isArray(dp) ? dp : [dp]).forEach(function (l) { linhas.push(l); });
  } else {
    var porIndice = {};
    Object.keys(body).forEach(function (k) {
      var m = k.match(/^leads\[status\]\[(\d+)\]\[([a-z_]+)\]$/) || k.match(/^lead\[event\]()\[([a-z_]+)\]$/);
      if (m) { (porIndice[m[1] || '0'] = porIndice[m[1] || '0'] || {})[m[2]] = body[k]; }
    });
    Object.keys(porIndice).sort().forEach(function (k) { linhas.push(porIndice[k]); });
  }
  return linhas.filter(function (l) { return l && l.id; }).map(function (l) {
    return {
      lead_id: String(l.id),
      status_id: String(l.status_id || ''),
      pipeline_id: String(l.pipeline_id || ''),
      old_status_id: String(l.old_status_id || ''),
      quando: Number(l.last_modified || l.updated_at || 0) || null,
    };
  });
}

function eventoDaEtapa(cfg, mudanca) {
  // cfg.etapas: {"<status_id>": "SQL", "142": "Purchase"}; cfg.funis (opcional): só esses pipelines.
  // 142 (ganho) e 143 (perdido) são iguais em todos os funis do Kommo, por isso a etapa sozinha basta.
  if (cfg.funis && cfg.funis.length && cfg.funis.map(String).indexOf(mudanca.pipeline_id) === -1) return null;
  return (cfg.etapas || {})[mudanca.status_id] || null;
}

function campo(entidade, id) {
  var cf = (entidade && entidade.custom_fields_values) || [];
  for (var i = 0; i < cf.length; i++) {
    if (String(cf[i].field_id) === String(id) || (cf[i].field_code && cf[i].field_code === id)) {
      var v = cf[i].values && cf[i].values[0] && cf[i].values[0].value;
      if (v !== undefined && v !== null && String(v).trim() !== '') return String(v).trim();
    }
  }
  return '';
}

function telefoneE164(bruto, ddi) {
  // Aceita com ou sem DDI, com máscara, com ".0" de planilha. Devolve "+5511999999999" ou "".
  ddi = ddi || '55';
  var d = String(bruto || '').split('.')[0].replace(/\D/g, '');
  if (!d) return '';
  if (d.indexOf('00') === 0) d = d.slice(2);
  if (ddi === '55') {
    if (d.length >= 12 && d.indexOf('55') === 0) return '+' + d;
    if (d.length === 10 || d.length === 11) return '+55' + d;
    return '';
  }
  return d.length >= 8 ? '+' + (d.indexOf(ddi) === 0 ? d : ddi + d) : '';
}

function emailNormalizado(bruto, paraGoogle) {
  var e = String(bruto || '').trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e)) return '';
  if (paraGoogle) {
    // Google Ads: em gmail.com e googlemail.com os pontos do usuário são ignorados antes do hash.
    var p = e.split('@');
    if (p[1] === 'gmail.com' || p[1] === 'googlemail.com') e = p[0].replace(/\./g, '') + '@' + p[1];
  }
  return e;
}

function dataGoogle(seg, fuso) {
  // ISO 8601 com o fuso da conta, como a Data Manager API pede: "2026-09-30T14:05:00-03:00".
  fuso = fuso || '-03:00';
  var m = fuso.match(/^([+-])(\d{2}):(\d{2})$/);
  var desloc = m ? (m[1] === '-' ? -1 : 1) * (Number(m[2]) * 60 + Number(m[3])) : -180;
  var d = new Date((seg + desloc * 60) * 1000);
  var z = function (n) { return ('0' + n).slice(-2); };
  return d.getUTCFullYear() + '-' + z(d.getUTCMonth() + 1) + '-' + z(d.getUTCDate()) + 'T' +
    z(d.getUTCHours()) + ':' + z(d.getUTCMinutes()) + ':' + z(d.getUTCSeconds()) + fuso;
}

function montarEvento(cfg, mudanca, lead, contato, agoraSeg) {
  // Devolve {pular, motivo} ou {event_id, event_name, meta, google, faltando}.
  var nome = eventoDaEtapa(cfg, mudanca);
  if (!nome) return { pular: true, motivo: 'etapa ' + mudanca.status_id + ' fora do mapa' };
  var c = cfg.campos || {};
  var quando = mudanca.quando && mudanca.quando <= agoraSeg ? mudanca.quando : agoraSeg;
  var eventId = 'kommo-' + mudanca.lead_id + '-' + nome.toLowerCase();

  var tel = telefoneE164(campo(contato, 'PHONE'), cfg.ddi);
  var email = emailNormalizado(campo(contato, 'EMAIL'));
  var nomeCompleto = String((contato && contato.name) || '').trim().split(/\s+/);
  var metaLeadId = c.meta_lead_id ? campo(lead, c.meta_lead_id).replace(/\D/g, '') : '';
  // lead_id do formulário instantâneo tem 15 a 17 dígitos; inválido faz o Meta recusar o evento inteiro.
  // Vai como texto: 17 dígitos passam do inteiro seguro do JavaScript e perderiam o final.
  var faltando = [];
  if (metaLeadId && !/^\d{15,17}$/.test(metaLeadId)) { faltando.push('meta: lead_id "' + metaLeadId + '" fora de 15-17 dígitos, ignorado'); metaLeadId = ''; }
  var fbc = c.fbc ? campo(lead, c.fbc) : '';
  var fbclid = c.fbclid ? campo(lead, c.fbclid) : '';
  if (!fbc && fbclid) fbc = 'fb.1.' + (quando * 1000) + '.' + fbclid;  // formato do _fbc a partir do fbclid
  var clique = { gclid: c.gclid ? campo(lead, c.gclid) : '', gbraid: c.gbraid ? campo(lead, c.gbraid) : '',
                 wbraid: c.wbraid ? campo(lead, c.wbraid) : '' };

  var valor = nome === 'Purchase' ? (Number(lead && lead.price) > 0 ? Number(lead.price) : Number(cfg.valor_venda_padrao || 0))
                                  : Number((cfg.valores || {})[nome] || 0);
  var moeda = cfg.moeda || 'BRL';

  if (!metaLeadId && !tel && !email && !fbc) faltando.push('meta: sem lead_id, telefone, e-mail nem fbc (o Meta não casa)');
  var maxDiasMeta = cfg.max_dias_meta || 7;
  var metaVelho = agoraSeg - quando > maxDiasMeta * 86400;
  if (metaVelho) faltando.push('meta: evento com mais de ' + maxDiasMeta + ' dias');

  var meta = metaVelho || (!metaLeadId && !tel && !email && !fbc) ? null : {
    event_name: nome,
    event_id: eventId,
    event_time: quando,
    lead_id: metaLeadId || undefined,
    external_id: c.external_id ? (campo(lead, c.external_id) || undefined) : undefined,
    fbc: fbc || undefined,
    fbp: c.fbp ? (campo(lead, c.fbp) || undefined) : undefined,
    user_data: {
      email_address: email || undefined,
      phone_number: tel || undefined,
      address: { first_name: nomeCompleto[0] || undefined,
                 last_name: nomeCompleto.length > 1 ? nomeCompleto[nomeCompleto.length - 1] : undefined,
                 country: cfg.pais || 'br' },
    },
    // IP e navegador do LEAD (quando o formulário gravou); vazio, a tag do sGTM não manda nada.
    // Sem isso o Data Client põe o IP do n8n no evento e o Meta recebe o servidor como se fosse a pessoa.
    lead_ip: c.ip ? (campo(lead, c.ip) || undefined) : undefined,
    lead_user_agent: c.user_agent ? (campo(lead, c.user_agent) || undefined) : undefined,
    value: valor,
    currency: moeda,
    crm: cfg.crm || 'Kommo',
    crm_lead_id: mudanca.lead_id,
  };

  // Google Ads pela Data Manager API (events:ingest). A Google Ads API (UploadClickConversions) não aceita
  // mais quem começou a importar offline depois de 15/06/2026: devolve CUSTOMER_NOT_ALLOWLISTED_FOR_THIS_FEATURE.
  var google = null;
  var g = cfg.google || {};
  var acao = (g.acoes || {})[nome];
  if (g.customer_id && acao) {
    var temClique = clique.gclid || clique.gbraid || clique.wbraid;
    var ids = [];
    var emailG = emailNormalizado(campo(contato, 'EMAIL'), true);
    if (emailG) ids.push({ emailAddress: sha256(emailG) });
    if (tel) ids.push({ phoneNumber: sha256(tel) });
    if (temClique || (g.sem_clique && ids.length)) {
      var ev = {
        eventTimestamp: dataGoogle(quando, g.fuso),
        transactionId: eventId,
        eventSource: g.event_source || 'WEB',
        conversionValue: valor,
        currency: moeda,
      };
      var ad = {};
      if (clique.gclid) ad.gclid = clique.gclid;
      if (clique.gbraid) ad.gbraid = clique.gbraid;   // o Google recomenda mandar gclid e gbraid juntos quando houver
      if (clique.wbraid && !clique.gclid && !clique.gbraid) ad.wbraid = clique.wbraid;
      if (temClique) ev.adIdentifiers = ad;
      if (ids.length) ev.userData = { userIdentifiers: ids };
      var cid = String(g.customer_id).replace(/\D/g, '');
      var destino = { operatingAccount: { accountType: 'GOOGLE_ADS', accountId: cid }, productDestinationId: String(acao) };
      if (g.login_customer_id) destino.loginAccount = { accountType: 'GOOGLE_ADS', accountId: String(g.login_customer_id).replace(/\D/g, '') };
      google = { destinations: [destino], encoding: 'HEX', events: [ev], validateOnly: !!g.validar_apenas };
    } else {
      faltando.push('google: sem gclid/gbraid/wbraid no lead');
    }
  }
  return { event_id: eventId, event_name: nome, meta: meta, google: google, faltando: faltando };
}

function variantesCelularBR(tel) {
  // Contato vindo do WhatsApp costuma estar sem o 9º dígito (55 DD 8 dígitos). O Meta aceita vários telefones por
  // evento: manda com e sem o 9 para casar com o cadastro da pessoa, seja qual for. Só celular (começa com 6-9).
  var d = String(tel || '').replace(/\D/g, '');
  if (d.indexOf('55') !== 0) return d ? [d] : [];
  var ddd = d.slice(2, 4), resto = d.slice(4);
  if (resto.length === 8 && /^[6-9]/.test(resto)) return [d, '55' + ddd + '9' + resto];
  if (resto.length === 9 && resto[0] === '9' && /^[6-9]/.test(resto.slice(1))) return [d, '55' + ddd + resto.slice(1)];
  return [d];
}

function metaGraph(meta, crm) {
  // Evento no formato da API de Conversões (POST graph.facebook.com/<versão>/<pixel>/events), para o modo
  // "direto" (n8n → Meta, sem sGTM). Aqui o hash é nosso: sem a tag da Stape no meio, ninguém faz por nós.
  // em/ph/fn/ln/country/external_id vão com SHA-256; lead_id, fbc, fbp, IP e navegador vão crus.
  if (!meta) return null;
  var ud = meta.user_data || {}, ad = ud.address || {}, u = {};
  var h = function (v) { return sha256(String(v).trim().toLowerCase()); };
  if (ud.email_address) u.em = [h(ud.email_address)];
  if (ud.phone_number) u.ph = variantesCelularBR(ud.phone_number).map(sha256);
  if (ad.first_name) u.fn = [h(ad.first_name)];
  if (ad.last_name) u.ln = [h(ad.last_name)];
  if (ad.country) u.country = [h(ad.country)];
  if (meta.external_id) u.external_id = [h(meta.external_id)];
  if (meta.lead_id) u.lead_id = meta.lead_id;
  if (meta.fbc) u.fbc = meta.fbc;
  if (meta.fbp) u.fbp = meta.fbp;
  if (meta.lead_ip) u.client_ip_address = meta.lead_ip;
  if (meta.lead_user_agent) u.client_user_agent = meta.lead_user_agent;
  return {
    event_name: meta.event_name,
    event_time: meta.event_time,
    event_id: meta.event_id,
    action_source: 'system_generated',
    user_data: u,
    custom_data: { value: meta.value, currency: meta.currency, event_source: 'crm', lead_event_source: crm || meta.crm || 'CRM' },
  };
}

function chaveTelefoneBR(tel) {
  // DDD + 8 últimos dígitos: imune ao DDI e ao 9º dígito (contato do WhatsApp costuma vir sem ele).
  var d = String(tel || '').replace(/\D/g, '');
  if (d.length < 10) return '';
  if (d.length >= 12 && d.indexOf('55') === 0) d = d.slice(2);
  return d.slice(0, 2) + '|' + d.slice(-8);
}

function acharLeadId(leadsMeta, telefone, antesDe) {
  // leadsMeta: leads da Graph API (/{form}/leads: id, created_time, field_data[{name, values}]).
  // Devolve o id (texto) do lead mais recente com o mesmo telefone criado até `antesDe` (segundos), ou ''.
  var alvo = chaveTelefoneBR(telefone);
  if (!alvo) return '';
  var melhor = null;
  (leadsMeta || []).forEach(function (l) {
    var fd = l.field_data || [];
    var tel = '';
    for (var i = 0; i < fd.length; i++) {
      if (/phone|telefone|whats|celular/i.test(fd[i].name || '')) { tel = (fd[i].values || [])[0] || ''; break; }
    }
    if (chaveTelefoneBR(tel) !== alvo) return;
    var t = Date.parse(l.created_time) / 1000;
    if (antesDe && t > antesDe) return;
    if (!melhor || t > melhor.t) melhor = { id: String(l.id), t: t };
  });
  return melhor && /^\d{15,17}$/.test(melhor.id) ? melhor.id : '';
}
