/**
 * SETUP AUTOMATICO - Planilha de Leads WK
 *
 * Como usar:
 * 1. Crie uma nova planilha em branco no Google Sheets
 * 2. Va em Extensoes -> Apps Script
 * 3. Apague o codigo padrao
 * 4. Cole TODO este codigo
 * 5. Salve (icone do disquete)
 * 6. Selecione a funcao "setupPlanilha" no menu suspenso
 * 7. Clique em "Executar"
 * 8. Autorize as permissoes
 * 9. Aguarde alguns segundos
 *
 * Resultado: planilha 100% configurada (abas, dropdowns, cores, fórmulas).
 */

function setupPlanilha() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // ============================================================
  // 1) CRIAR ABA "Leads"
  // ============================================================
  let sheetLeads = ss.getSheetByName('Leads');
  if (!sheetLeads) {
    // Renomeia a primeira aba se ela estiver vazia
    const firstSheet = ss.getSheets()[0];
    if (firstSheet.getLastRow() <= 1) {
      firstSheet.setName('Leads');
      sheetLeads = firstSheet;
    } else {
      sheetLeads = ss.insertSheet('Leads', 0);
    }
  }

  // Cabecalhos da aba Leads
  const headers = [
    'lead_id', 'data_lead', 'origem', 'nome', 'email', 'whatsapp',
    'ambiente', 'metragem', 'utm_source', 'utm_medium', 'utm_campaign',
    'utm_term', 'utm_content', 'gclid', 'fbclid', 'status',
    'data_mql', 'data_sql', 'data_venda', 'motivo_perdido',
    'vendedor', 'faturamento', 'observacao', 'sincronizado_capi'
  ];

  sheetLeads.getRange(1, 1, 1, headers.length).setValues([headers]);

  // Formatacao do cabecalho
  const headerRange = sheetLeads.getRange(1, 1, 1, headers.length);
  headerRange.setBackground('#274e13')
             .setFontColor('#ffffff')
             .setFontWeight('bold')
             .setHorizontalAlignment('center');

  // Larguras de coluna sugeridas
  const colWidths = [120, 140, 200, 150, 200, 130, 180, 160, 100, 100, 130, 130, 130, 120, 120, 100, 130, 130, 130, 180, 130, 110, 250, 130];
  colWidths.forEach((w, i) => sheetLeads.setColumnWidth(i + 1, w));

  // Congelar primeira linha
  sheetLeads.setFrozenRows(1);

  // ============================================================
  // 2) CRIAR ABA "Configuracao"
  // ============================================================
  let sheetConfig = ss.getSheetByName('Configuracao');
  if (!sheetConfig) {
    sheetConfig = ss.insertSheet('Configuracao');
  }
  sheetConfig.clear();

  // Conteudo da aba Configuracao
  const configData = [
    ['origem', 'ambiente', 'metragem', 'status', 'motivo_perdido', 'vendedor'],
    ['LP - Carpete em Placas', 'corporativo/escritório', 'até 25m²', 'Lead', 'Fora do perfil', 'Vendedor 1'],
    ['Meta Lead Ads - Pegasus', 'hotelaria/flats', 'entre 25 e 50m²', 'MQL', 'Sem orçamento', 'Vendedor 2'],
    ['WhatsApp Direto - LP', 'institucional (cinemas, teatros)', 'entre 50 e 75m²', 'SQL', 'Foi pra concorrente', 'Vendedor 3'],
    ['WhatsApp Direto - Ads', 'residencial (quarto, sala, home office)', 'entre 75 e 100m²', 'Cliente', 'Sem retorno do cliente', ''],
    ['WhatsApp Direto - Outros', '', 'acima de 100m²', 'Perdido', 'Projeto cancelado', ''],
    ['Indicação', '', '', '', 'Timing errado (volta depois)', ''],
    ['Outros', '', '', '', 'Outro', '']
  ];

  sheetConfig.getRange(1, 1, configData.length, configData[0].length).setValues(configData);

  // Formatacao do cabecalho da Configuracao
  sheetConfig.getRange(1, 1, 1, configData[0].length)
             .setBackground('#1c4587')
             .setFontColor('#ffffff')
             .setFontWeight('bold');

  // ============================================================
  // 3) DROPDOWNS (Validacao de Dados)
  // ============================================================

  // Helper pra criar dropdown
  function setDropdown(col, configCol) {
    const range = sheetLeads.getRange(2, col, 1000, 1);
    const sourceRange = sheetConfig.getRange('Configuracao!' + configCol + '2:' + configCol);
    const rule = SpreadsheetApp.newDataValidation()
      .requireValueInRange(sourceRange, true)
      .setAllowInvalid(false)
      .build();
    range.setDataValidation(rule);
  }

  setDropdown(3, 'A');   // origem
  setDropdown(7, 'B');   // ambiente
  setDropdown(8, 'C');   // metragem
  setDropdown(16, 'D');  // status
  setDropdown(20, 'E');  // motivo_perdido
  setDropdown(21, 'F');  // vendedor

  // Checkbox em sincronizado_capi
  sheetLeads.getRange(2, 24, 1000, 1).insertCheckboxes();

  // ============================================================
  // 4) FORMATACAO CONDICIONAL (cores por status)
  // ============================================================
  const fcRange = sheetLeads.getRange('A2:X1000');
  const statusColors = [
    ['Lead', '#f3f3f3'],
    ['MQL', '#fff2cc'],
    ['SQL', '#fce5cd'],
    ['Cliente', '#d9ead3'],
    ['Perdido', '#f4cccc']
  ];

  const rules = sheetLeads.getConditionalFormatRules();
  statusColors.forEach(([status, color]) => {
    const rule = SpreadsheetApp.newConditionalFormatRule()
      .whenFormulaSatisfied('=$P2="' + status + '"')
      .setBackground(color)
      .setRanges([fcRange])
      .build();
    rules.push(rule);
  });
  sheetLeads.setConditionalFormatRules(rules);

  // ============================================================
  // 5) FORMATACAO DAS COLUNAS DE DATA E MOEDA
  // ============================================================
  sheetLeads.getRange('B2:B1000').setNumberFormat('dd/mm/yyyy hh:mm');  // data_lead
  sheetLeads.getRange('Q2:S1000').setNumberFormat('dd/mm/yyyy hh:mm');  // data_mql/sql/venda
  sheetLeads.getRange('V2:V1000').setNumberFormat('R$ #,##0.00');       // faturamento

  // ============================================================
  // 6) GATILHO ONEDIT (datas automaticas) - aviso pro usuario
  // ============================================================

  // Nao instala onEdit aqui (precisa ser feito manualmente OU via PropertiesService)
  // O codigo onEdit ja foi colado neste arquivo - basta salvar e funcionar

  // ============================================================
  // 7) MENSAGEM FINAL
  // ============================================================
  SpreadsheetApp.getUi().alert(
    '✅ SETUP COMPLETO!',
    'A planilha foi configurada com:\n\n' +
    '• Aba Leads com 24 colunas\n' +
    '• Aba Configuracao com dropdowns\n' +
    '• Validacao de dados em 6 colunas\n' +
    '• Formatacao condicional (5 cores)\n' +
    '• Formatacao de datas e moeda\n' +
    '• Checkbox em sincronizado_capi\n\n' +
    'O Apps Script onEdit (datas automaticas) ja esta neste arquivo. Salve para ativar.\n\n' +
    'Proximo passo: editar a aba Configuracao com os vendedores reais (coluna F).',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}


/**
 * ONEDIT - Preenche automaticamente data_mql, data_sql, data_venda
 * quando o status muda.
 *
 * Esta funcao roda automaticamente sempre que voce edita a planilha.
 * NAO precisa executar manualmente.
 */
function onEdit(e) {
  const sheet = e.range.getSheet();
  if (sheet.getName() !== 'Leads') return;

  const col = e.range.getColumn();
  const row = e.range.getRow();
  if (row < 2) return;

  // Coluna P = status (16)
  if (col !== 16) return;

  const status = e.value;
  const now = new Date();

  const dateCols = {
    'MQL': 17,      // Q
    'SQL': 18,      // R
    'Cliente': 19   // S
  };

  if (dateCols[status]) {
    const dateCol = dateCols[status];
    const existingDate = sheet.getRange(row, dateCol).getValue();
    if (!existingDate) {
      sheet.getRange(row, dateCol).setValue(now);
    }
  }
}
