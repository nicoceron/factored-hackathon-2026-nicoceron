const icons = {
  arrow: '<path d="M5 12h14M12 5l7 7-7 7"/>', chevron: '<path d="m9 5 7 7-7 7"/>',
  home: '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>',
  chat: '<path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2v-10A8.5 8.5 0 0 1 10.5 3h2a8.5 8.5 0 0 1 8.5 8.5Z"/><path d="M7 10h9M7 14h6"/>',
  cases: '<rect x="3" y="6" width="18" height="15" rx="2"/><path d="M8 6V3h8v3M3 12h18M9 12v3h6v-3"/>',
  chart: '<path d="M4 3v18h17M8 16v-5M13 16V7M18 16V4"/>', shield: '<path d="m12 3 8 3v6c0 4-4 7-8 9-4-2-8-5-8-9V6z"/><path d="m8 12 3 3 5-6"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>', analyst: '<rect x="3" y="4" width="18" height="15" rx="2"/><path d="M7 9h4M7 13h2M15 9h2M15 13h2M8 22h8M12 19v3"/>',
  logout: '<path d="M9 4H4v16h5M9 12h12m-4-4 4 4-4 4"/>', calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18M8 15h2M14 15h2"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', card: '<rect x="2" y="5" width="20" height="14" rx="3"/><path d="M2 10h20M6 15h4"/>',
  refresh: '<path d="M20 7a9 9 0 1 0 1 8M20 3v5h-5"/>', sparkle: '<path d="m12 2 2.7 7.3L22 12l-7.3 2.7L12 22l-2.7-7.3L2 12l7.3-2.7z"/>',
  send: '<path d="m21 3-6 18-4-8-8-4zM11 13 21 3"/>', close: '<path d="m6 6 12 12M6 18 18 6"/>',
  check: '<path d="m5 12 4 4L19 6"/>', verified: '<path d="m12 2 3 2 3.5.5.5 3.5 2 4-2 3-.5 3.5-3.5.5-3 2-3-2-3.5-.5L4 15l-2-3 2-4 .5-3.5L8 4z"/><path d="m8 12 3 3 5-6"/>',
  lock: '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4M12 14v3"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v1"/>', globe: '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
  receipt: '<path d="M5 3h14v18l-3-2-4 2-4-2-3 2zM8 7h8M8 11h8M8 15h4"/>', file: '<path d="M14 2H5v20h14V7zM14 2v6h5M8 12h8M8 16h5"/>',
  alert: '<path d="m12 3 10 18H2zM12 9v5M12 17v1"/>', external: '<path d="M14 3h7v7M10 14 21 3M10 3H3v18h18v-7"/>', search: '<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>',
};
const icon = (name, cls = '') => `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name] || icons.file}</svg>`;
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const words = {
  es: {
    storyTitle: 'Tu banco.<br>Todo más <em>claro.</em>', storyDescription: 'Respuestas con contexto. Acciones con evidencia. Acompañamiento humano cuando más lo necesitas.', storyEyebrow: 'Asistencia bancaria, con criterio', understand: 'Entender lo que necesitas', verify: 'Consultar y verificar la evidencia', accompany: 'Resolver contigo, paso a paso', hackathon: 'Factored AI & Data Hackathon 2026', sandbox: 'Sandbox histórico', entry: 'CONOCE CLARO', welcome: 'La claridad empieza aquí.', entryDescription: 'Explora la experiencia como cliente o acompaña un caso desde el espacio de analistas.', esPersona: 'Cliente · Español', esPersonaDescription: 'Consulta movimientos y solicita ayuda', ptPersona: 'Cliente · Português', ptPersonaDescription: 'Consulte transações e solicite ajuda', analystPersona: 'Espacio de analistas', analystPersonaDescription: 'Revisa evidencia y da seguimiento a casos', enter: 'Entrar a la demostración', entering: 'Preparando tu espacio…', loginDisclaimer: 'Demostración pública con perfiles y datos ficticios creados por el equipo. No es un acceso bancario real. No ingreses datos personales ni credenciales.', privateWorkspace: 'Tu espacio está aislado. Las sesiones y los casos pueden borrarse al reiniciar el servicio.', workspace: 'TU ESPACIO', support: 'Asistencia', myCases: 'Mis casos', reviewQueue: 'Revisión de casos', evaluation: 'Evaluación', analytics: 'Operaciones', demoNoteTitle: 'Claridad, también en los límites.', demoNote: 'Datos ficticios. Ninguna acción mueve dinero ni modifica una cuenta bancaria.', workspaceFooter: 'DEMO · 2026', breadcrumb: 'Tu espacio', analystBreadcrumb: 'Espacio de analistas', customerRole: 'Cliente de demostración', analystRole: 'Analista de demostración', logout: 'Cambiar perfil', language: 'Idioma de la interfaz', hello: 'Hola', supportTitle: 'Hablemos de tus movimientos.', supportDescription: 'Entiende un cargo, revisa su estado o recibe ayuda para reportarlo.', protected: 'Espacio aislado', snapshot: 'Fecha de los datos', records: 'Movimientos disponibles', recordsSuffix: 'en tu perfil', channel: 'Canal de asistencia', channelValue: 'Español + Português', channelSuffix: 'Con contexto y evidencia', transactions: 'Tus movimientos', transactionHint: 'Selecciona uno para darle contexto a Claro.', historical: 'Registros ficticios · fotografía histórica', refresh: 'Actualizar', noTransactions: 'No hay movimientos disponibles', noTransactionsText: 'Cuando existan registros autorizados, aparecerán aquí.', asOf: 'Datos al', source: 'Fuente', sourceDemo: 'Fixture del equipo', unlistedMerchant: 'Comercio no registrado', posted: 'Completado', completed: 'Completado', approved: 'Aprobado', pending: 'Pendiente', declined: 'Rechazado', failed: 'Fallido', reversed: 'Revertido', trustTitle: 'Tus datos tienen un contexto.', trustText: 'Claro consulta solo los registros de este perfil. Una estimación de riesgo nunca es una prueba de fraude.', assistant: 'Claro, tu asistente', assistantSubtitle: 'Información verificada, decisiones cuidadosas', sessionActive: 'Sesión de demostración', greeting: 'Hola, soy Claro. Te ayudo a entender tus movimientos y a preparar un caso si necesitas revisión humana. ¿Qué quieres revisar?', greetingPrompt: 'Selecciona un movimiento o empieza con una pregunta.', promptStatus: 'Consultar un movimiento', promptDispute: 'No reconozco un cargo', promptHuman: 'Hablar con una persona', statusMessage: 'Quiero consultar el estado de este movimiento.', disputeMessage: 'No reconozco este cargo.', humanMessage: 'Quiero hablar con una persona.', chatLabel: 'Conversación con Claro', you: 'Tú', messagePlaceholder: 'Cuéntame, ¿en qué te ayudo?', send: 'Enviar mensaje', composerHint: 'No compartas claves ni datos personales. Enter para enviar · Shift + Enter para nueva línea.', selected: 'Movimiento seleccionado', clearSelection: 'Quitar movimiento seleccionado', thinking: 'Consultando la evidencia…', evidence: 'Ver evidencia', trace: 'Referencia de trazabilidad', proposalTitle: 'Un paso antes de crear el caso', proposalNotice: 'Se creará un caso de revisión en este sandbox. No se realizará un reembolso, bloqueo de tarjeta ni movimiento de dinero.', confirm: 'Revisar y confirmar', cancel: 'Cancelar', dismiss: 'Ahora no', cancelled: 'Acción cancelada. Puedes seguir conversando.', confirmed: 'Solicitud confirmada', confirmTitle: 'Confirmar caso de revisión', confirmAction: 'Confirmar creación', confirming: 'Verificando resultado…', receiptVerified: 'Caso guardado y verificado', receiptUnverified: 'Resultado sin verificar', receiptNotice: 'Registro leído después de guardarse. Un analista puede revisarlo aquí. Los casos y las sesiones pueden borrarse al reiniciar el servicio.', unverifiedNotice: 'No se ha verificado la escritura. Consulta tus casos antes de intentar de nuevo.', viewCase: 'Ver caso', casesTitle: 'Cada caso, con su contexto.', casesDescription: 'Consulta el estado y la evidencia de tus solicitudes de revisión.', queueTitle: 'El contexto para decidir mejor.', queueDescription: 'Revisa solicitudes, hechos verificados y preguntas pendientes de este espacio.', cases: 'Casos', all: 'Todos', open: 'Abiertos', closed: 'Cerrados', status_open: 'En revisión', status_pending: 'En revisión', status_needs_information: 'Requiere información', status_reviewed_closed: 'Revisión cerrada', status_closed: 'Cerrado', status_resolved: 'Resuelto', noCases: 'Todavía no hay casos', noCasesText: 'Los casos confirmados con Claro aparecerán aquí, junto con su evidencia.', noCasesFiltered: 'No hay casos en este filtro.', startConversation: 'Ir a asistencia', chooseCase: 'Selecciona un caso', chooseCaseText: 'Aquí encontrarás la solicitud, los hechos y la evidencia.', created: 'Creado', customerReport: 'Lo que reporta el cliente', verifiedFacts: 'Hechos verificados', transactionId: 'Movimiento', amount: 'Importe', status: 'Estado', merchant: 'Comercio', recordDate: 'Fecha del registro', risk: 'Señal de riesgo', riskUnavailable: 'No hay una estimación de riesgo disponible para este caso. El reporte del cliente conserva su prioridad de revisión.', riskDisclaimer: 'Estimación del modelo; no establece fraude, responsabilidad ni derecho a reembolso.', model: 'Modelo', pendingQuestions: 'Información pendiente', policy: 'Política de demostración', timeline: 'Historial del caso', caseCreated: 'Caso registrado', writeVerified: 'Escritura verificada', review: 'Registrar revisión', resolution: 'Resultado de la revisión', resolutionClosed: 'Revisión completada · cerrar caso', resolutionNeeds: 'Solicitar información adicional', resolutionDisclaimer: 'Este resultado solo actualiza el caso del sandbox. No confirma un fraude ni autoriza un reembolso.', saveReview: 'Guardar revisión', saving: 'Guardando…', reviewSaved: 'Revisión guardada.', analyticsTitle: 'La operación, a la vista.', analyticsDescription: 'Métricas reales de las sesiones de demostración de este espacio.', totalCases: 'Casos registrados', openCases: 'En revisión', verifiedActions: 'Casos creados y verificados', totalMessages: 'Mensajes procesados', activity: 'Actividad del sandbox', languages: 'Distribución por idioma', operationalBoundary: 'Estas métricas describen el uso del prototipo. No representan resultados de un banco, ahorro real ni una medición de satisfacción.', evaluationTitle: 'Evidencia antes que promesas.', evaluationDescription: 'Resultados reproducibles, comparaciones y límites explícitos del prototipo.', evaluationHeading: 'Evaluación del sistema', evaluationPending: 'Resultados aún no publicados', evaluationPendingText: 'La evaluación aparecerá aquí cuando exista un reporte medido y publicado por el servidor.', measure: 'Métrica', baseline: 'Baseline', candidate: 'Candidato', limitations: 'Cómo interpretar los resultados', limitation1: 'Escenarios, no producción', limitation1Text: 'Las pruebas del equipo no representan la distribución real de un banco.', limitation2: 'Español y portugués', limitation2Text: 'Los resultados por idioma deben evaluarse por separado. Los tamaños de muestra importan.', limitation3: 'Permisos fuera del modelo', limitation3Text: 'El servidor verifica la sesión, el acceso a registros y cada acción confirmada.', limitation4: 'Sin promesas de fraude', limitation4Text: 'Una señal estadística sirve para revisión; no prueba un fraude ni determina un reembolso.', viewReport: 'Abrir reporte JSON', reportDetails: 'Reporte publicado por el servidor', noData: 'No disponible', errorNetwork: 'No pudimos conectar. Tu solicitud no tiene un resultado confirmado. Intenta de nuevo con la misma solicitud.', errorGeneric: 'No pudimos completar la solicitud. Intenta de nuevo.', errorExpired: 'La sesión expiró. Ingresa otra vez para continuar.', retry: 'Reintentar', errorLoad: 'No pudimos cargar esta información.', footer: 'Claro · Asistencia bancaria con evidencia', footerDisclaimer: 'Prototipo independiente · datos ficticios · sin operaciones bancarias reales', resolutionRecorded: 'Revisión registrada', analystBoundary: 'Solo ves los casos del espacio privado de este navegador. Cambia al perfil de cliente para crear un caso de prueba.', customer: 'Cliente', languageEs: 'Español', languagePt: 'Português', unknown: 'Sin registro', tooLong: 'Escribe un mensaje de hasta 2.000 caracteres.', remaining: 'caracteres restantes', noEvidence: 'No hay evidencia adjunta.', refreshDone: 'Información actualizada.', title: 'Claro · Banca con claridad', cancelledProposal: 'Cancelada', confidence: 'Estimación', download: 'Descargar', sessionRestored: 'Sesión recuperada. Puedes continuar consultando tus movimientos y casos.'
  },
  pt: {
    storyTitle: 'Seu banco.<br>Tudo mais <em>claro.</em>', storyDescription: 'Respostas com contexto. Ações com evidências. Apoio humano quando você mais precisa.', storyEyebrow: 'Atendimento bancário, com critério', understand: 'Entender o que você precisa', verify: 'Consultar e verificar as evidências', accompany: 'Resolver com você, passo a passo', hackathon: 'Factored AI & Data Hackathon 2026', sandbox: 'Sandbox histórico', entry: 'CONHEÇA O CLARO', welcome: 'A clareza começa aqui.', entryDescription: 'Explore a experiência como cliente ou acompanhe um caso no espaço de analistas.', esPersona: 'Cliente · Español', esPersonaDescription: 'Consulta movimientos y solicita ayuda', ptPersona: 'Cliente · Português', ptPersonaDescription: 'Consulte transações e solicite ajuda', analystPersona: 'Espaço de analistas', analystPersonaDescription: 'Revise evidências e acompanhe casos', enter: 'Entrar na demonstração', entering: 'Preparando seu espaço…', loginDisclaimer: 'Demonstração pública com perfis e dados fictícios criados pela equipe. Não é um acesso bancário real. Não informe dados pessoais nem credenciais.', privateWorkspace: 'Seu espaço é isolado. Sessões e casos podem ser apagados ao reiniciar o serviço.', workspace: 'SEU ESPAÇO', support: 'Atendimento', myCases: 'Meus casos', reviewQueue: 'Revisão de casos', evaluation: 'Avaliação', analytics: 'Operações', demoNoteTitle: 'Clareza, também nos limites.', demoNote: 'Dados fictícios. Nenhuma ação movimenta dinheiro nem altera uma conta bancária.', workspaceFooter: 'DEMO · 2026', breadcrumb: 'Seu espaço', analystBreadcrumb: 'Espaço de analistas', customerRole: 'Cliente de demonstração', analystRole: 'Analista de demonstração', logout: 'Trocar perfil', language: 'Idioma da interface', hello: 'Olá', supportTitle: 'Vamos falar das suas transações.', supportDescription: 'Entenda uma cobrança, confira seu status ou receba ajuda para relatá-la.', protected: 'Espaço isolado', snapshot: 'Data dos dados', records: 'Transações disponíveis', recordsSuffix: 'no seu perfil', channel: 'Canal de atendimento', channelValue: 'Español + Português', channelSuffix: 'Com contexto e evidências', transactions: 'Suas transações', transactionHint: 'Selecione uma para dar contexto ao Claro.', historical: 'Registros fictícios · fotografia histórica', refresh: 'Atualizar', noTransactions: 'Nenhuma transação disponível', noTransactionsText: 'Os registros autorizados aparecerão aqui quando estiverem disponíveis.', asOf: 'Dados até', source: 'Fonte', sourceDemo: 'Fixture da equipe', unlistedMerchant: 'Estabelecimento não informado', posted: 'Concluída', completed: 'Concluída', approved: 'Aprovada', pending: 'Pendente', declined: 'Recusada', failed: 'Falhou', reversed: 'Estornada', trustTitle: 'Seus dados têm um contexto.', trustText: 'O Claro consulta apenas os registros deste perfil. Uma estimativa de risco nunca é uma prova de fraude.', assistant: 'Claro, seu assistente', assistantSubtitle: 'Informações verificadas, decisões cuidadosas', sessionActive: 'Sessão de demonstração', greeting: 'Olá, sou o Claro. Ajudo você a entender suas transações e preparar um caso quando precisar de revisão humana. O que você gostaria de revisar?', greetingPrompt: 'Selecione uma transação ou comece com uma pergunta.', promptStatus: 'Consultar uma transação', promptDispute: 'Não reconheço uma cobrança', promptHuman: 'Falar com uma pessoa', statusMessage: 'Quero consultar o status desta transação.', disputeMessage: 'Não reconheço esta cobrança.', humanMessage: 'Quero falar com uma pessoa.', chatLabel: 'Conversa com o Claro', you: 'Você', messagePlaceholder: 'Como posso ajudar você?', send: 'Enviar mensagem', composerHint: 'Não compartilhe senhas nem dados pessoais. Enter envia · Shift + Enter cria uma nova linha.', selected: 'Transação selecionada', clearSelection: 'Remover transação selecionada', thinking: 'Consultando as evidências…', evidence: 'Ver evidências', trace: 'Referência de rastreabilidade', proposalTitle: 'Um passo antes de criar o caso', proposalNotice: 'Será criado um caso para revisão neste sandbox. Nenhum reembolso, bloqueio de cartão ou transferência será realizado.', confirm: 'Revisar e confirmar', cancel: 'Cancelar', dismiss: 'Agora não', cancelled: 'Ação cancelada. Você pode continuar a conversa.', confirmed: 'Solicitação confirmada', confirmTitle: 'Confirmar caso para revisão', confirmAction: 'Confirmar criação', confirming: 'Verificando o resultado…', receiptVerified: 'Caso salvo e verificado', receiptUnverified: 'Resultado não verificado', receiptNotice: 'Registro consultado após ser salvo. Um analista pode revisá-lo aqui. Casos e sessões podem ser apagados ao reiniciar o serviço.', unverifiedNotice: 'A gravação ainda não foi verificada. Consulte seus casos antes de tentar novamente.', viewCase: 'Ver caso', casesTitle: 'Cada caso, com seu contexto.', casesDescription: 'Consulte o status e as evidências das suas solicitações de revisão.', queueTitle: 'O contexto para decidir melhor.', queueDescription: 'Revise solicitações, fatos verificados e perguntas pendentes deste espaço.', cases: 'Casos', all: 'Todos', open: 'Abertos', closed: 'Encerrados', status_open: 'Em revisão', status_pending: 'Em revisão', status_needs_information: 'Requer informações', status_reviewed_closed: 'Revisão encerrada', status_closed: 'Encerrado', status_resolved: 'Resolvido', noCases: 'Ainda não há casos', noCasesText: 'Os casos confirmados com o Claro aparecerão aqui, junto com suas evidências.', noCasesFiltered: 'Nenhum caso neste filtro.', startConversation: 'Ir para atendimento', chooseCase: 'Selecione um caso', chooseCaseText: 'Aqui você encontrará a solicitação, os fatos e as evidências.', created: 'Criado', customerReport: 'Relato do cliente', verifiedFacts: 'Fatos verificados', transactionId: 'Transação', amount: 'Valor', status: 'Status', merchant: 'Estabelecimento', recordDate: 'Data do registro', risk: 'Sinal de risco', riskUnavailable: 'Não há uma estimativa de risco disponível para este caso. O relato do cliente mantém sua prioridade de revisão.', riskDisclaimer: 'Estimativa do modelo; não determina fraude, responsabilidade nem direito a reembolso.', model: 'Modelo', pendingQuestions: 'Informações pendentes', policy: 'Política de demonstração', timeline: 'Histórico do caso', caseCreated: 'Caso registrado', writeVerified: 'Gravação verificada', review: 'Registrar revisão', resolution: 'Resultado da revisão', resolutionClosed: 'Revisão concluída · encerrar caso', resolutionNeeds: 'Solicitar informações adicionais', resolutionDisclaimer: 'Este resultado atualiza apenas o caso do sandbox. Não confirma uma fraude nem autoriza reembolso.', saveReview: 'Salvar revisão', saving: 'Salvando…', reviewSaved: 'Revisão salva.', analyticsTitle: 'A operação, à vista.', analyticsDescription: 'Métricas reais das sessões de demonstração deste espaço.', totalCases: 'Casos registrados', openCases: 'Em revisão', verifiedActions: 'Casos criados e verificados', totalMessages: 'Mensagens processadas', activity: 'Atividade do sandbox', languages: 'Distribuição por idioma', operationalBoundary: 'Estas métricas descrevem o uso do protótipo. Não representam resultados de um banco, economia real nem uma medição de satisfação.', evaluationTitle: 'Evidências antes de promessas.', evaluationDescription: 'Resultados reproduzíveis, comparações e limites explícitos do protótipo.', evaluationHeading: 'Avaliação do sistema', evaluationPending: 'Resultados ainda não publicados', evaluationPendingText: 'A avaliação aparecerá aqui quando houver um relatório medido e publicado pelo servidor.', measure: 'Métrica', baseline: 'Baseline', candidate: 'Candidato', limitations: 'Como interpretar os resultados', limitation1: 'Cenários, não produção', limitation1Text: 'Os testes da equipe não representam a distribuição real de um banco.', limitation2: 'Espanhol e português', limitation2Text: 'Os resultados por idioma precisam ser avaliados separadamente. O tamanho da amostra importa.', limitation3: 'Permissões fora do modelo', limitation3Text: 'O servidor verifica a sessão, o acesso aos registros e cada ação confirmada.', limitation4: 'Sem promessas de fraude', limitation4Text: 'Um sinal estatístico serve para revisão; não prova uma fraude nem determina reembolso.', viewReport: 'Abrir relatório JSON', reportDetails: 'Relatório publicado pelo servidor', noData: 'Não disponível', errorNetwork: 'Não foi possível conectar. Sua solicitação não tem um resultado confirmado. Tente novamente com a mesma solicitação.', errorGeneric: 'Não foi possível concluir a solicitação. Tente novamente.', errorExpired: 'A sessão expirou. Entre novamente para continuar.', retry: 'Tentar novamente', errorLoad: 'Não foi possível carregar estas informações.', footer: 'Claro · Atendimento bancário com evidências', footerDisclaimer: 'Protótipo independente · dados fictícios · sem operações bancárias reais', resolutionRecorded: 'Revisão registrada', analystBoundary: 'Você vê apenas os casos do espaço privado deste navegador. Troque para um perfil de cliente para criar um caso de teste.', customer: 'Cliente', languageEs: 'Español', languagePt: 'Português', unknown: 'Não informado', tooLong: 'Escreva uma mensagem com até 2.000 caracteres.', remaining: 'caracteres restantes', noEvidence: 'Não há evidências anexadas.', refreshDone: 'Informações atualizadas.', title: 'Claro · Seu banco, com clareza', cancelledProposal: 'Cancelada', confidence: 'Estimativa', download: 'Baixar', sessionRestored: 'Sessão recuperada. Você pode continuar consultando suas transações e casos.'
  }
};
Object.assign(words.es, { errorForbidden: 'Esta sesión no tiene permiso para realizar la acción. Vuelve a ingresar si cambiaste de perfil.', errorNotFound: 'El registro solicitado no está disponible en este perfil.', errorConflict: 'La solicitud está en curso o ya no es válida en este estado. Verifica el caso antes de intentar otra acción.', errorRateLimit: 'Has enviado muchas solicitudes. Espera un momento antes de reintentar.', errorUnavailable: 'El servicio no pudo verificar la operación. No se confirma ninguna acción. Reintenta con la misma solicitud.', errorValidation: 'La solicitud no es válida. Revisa el mensaje y vuelve a intentarlo.', misroutedReports: 'Reportes enrutados a otra intención', resetChat: 'Nueva conversación', resetSandbox: 'Borrar datos de prueba', resetTitle: 'Reiniciar este sandbox', resetNotice: 'Se borrarán las conversaciones, casos y sesiones de demostración de este navegador. Esta acción no se puede deshacer. No afecta a otros visitantes.', resetConfirm: 'Borrar mi sandbox', resetSuccess: 'Espacio de demostración reiniciado.', requests: 'Solicitudes procesadas', outcomes: 'Resultados del flujo', latency: 'Latencia del servicio', modelCost: 'Costo de API de modelos', latencyNote: 'Medición local del servidor; excluye red y tiempo humano.', languageReport: 'Comprensión del lenguaje', workflowReport: 'Flujo completo', fraudReport: 'Experimento de riesgo transaccional', comparisonNote: 'Mismo conjunto de 140 escenarios bilingües creados por el equipo. Sin revisión humana independiente ni revisión nativa de portugués. Es una prueba sintética, no una muestra de clientes reales.', languageNote: 'Clasificación de intención aislada. TF-IDF + regresión logística es el componente desplegado; Gemma es un comparador local. Estos resultados no miden resolución de casos.', workflowNote: 'Reproducción en TestClient, sin red ni carga concurrente. Las correcciones sobre este conjunto son regresiones; no prueban generalización a casos nuevos.', fraudNote: 'El conjunto temporal de prueba conserva la prevalencia original. Los candidatos no superaron el criterio de promoción en validación; se conserva el baseline constante. No hay un detector de fraude validado para el uso real.', macroF1: 'Macro-F1 de intención', accuracy: 'Exactitud', correctOutcomes: 'Resultados correctos', safeResolutions: 'Resoluciones automáticas seguras', missedHandoffs: 'Derivaciones necesarias omitidas', unnecessaryHandoffs: 'Propuestas humanas innecesarias', wrongOutcomes: 'Resultados materialmente incorrectos', unauthorized: 'Acceso o acción no autorizada', sample: 'Casos', modelLabel: 'Modelo', averagePrecision: 'Precisión promedio (AP)', selectedModel: 'Seleccionado', constant: 'Prevalencia constante', amount_history_rule: 'Regla de importe e historial', logistic: 'Regresión logística', catboost: 'CatBoost', disclosedLimits: 'Método y limitaciones del reporte', state_resolved: 'Respuesta completada', state_escalated: 'Derivación verificada', state_clarification: 'Aclaración solicitada', state_awaiting_confirmation: 'Confirmación pendiente', state_abstained: 'Abstención', state_blocked: 'Solicitud bloqueada', state_case_lookup: 'Consulta de caso', noProduction: 'Ninguna cifra representa desempeño de producción.', languageSlice: 'Resultados por idioma' });
Object.assign(words.pt, { errorForbidden: 'Esta sessão não tem permissão para realizar a ação. Entre novamente se você trocou de perfil.', errorNotFound: 'O registro solicitado não está disponível neste perfil.', errorConflict: 'A solicitação está em andamento ou não é mais válida neste estado. Verifique o caso antes de tentar outra ação.', errorRateLimit: 'Muitas solicitações foram enviadas. Aguarde um momento antes de tentar novamente.', errorUnavailable: 'O serviço não conseguiu verificar a operação. Nenhuma ação está confirmada. Tente novamente com a mesma solicitação.', errorValidation: 'A solicitação não é válida. Confira a mensagem e tente novamente.', misroutedReports: 'Relatos direcionados a outra intenção', resetChat: 'Nova conversa', resetSandbox: 'Apagar dados de teste', resetTitle: 'Reiniciar este sandbox', resetNotice: 'As conversas, os casos e as sessões de demonstração deste navegador serão apagados. Esta ação não pode ser desfeita. Outros visitantes não serão afetados.', resetConfirm: 'Apagar meu sandbox', resetSuccess: 'Espaço de demonstração reiniciado.', requests: 'Solicitações processadas', outcomes: 'Resultados do fluxo', latency: 'Latência do serviço', modelCost: 'Custo de API de modelos', latencyNote: 'Medição local do servidor; exclui rede e tempo humano.', languageReport: 'Compreensão de linguagem', workflowReport: 'Fluxo completo', fraudReport: 'Experimento de risco transacional', comparisonNote: 'Mesmo conjunto de 140 cenários bilíngues criados pela equipe. Sem revisão humana independente nem revisão nativa de português. É um teste sintético, não uma amostra de clientes reais.', languageNote: 'Classificação de intenção isolada. TF-IDF + regressão logística é o componente implantado; Gemma é um comparador local. Estes resultados não medem a resolução de casos.', workflowNote: 'Reprodução em TestClient, sem rede nem carga simultânea. As correções neste conjunto são regressões; não comprovam generalização para novos casos.', fraudNote: 'O conjunto temporal de teste mantém a prevalência original. Os candidatos não passaram pelo critério de promoção na validação; o baseline constante é mantido. Não há um detector de fraude validado para uso real.', macroF1: 'Macro-F1 de intenção', accuracy: 'Acurácia', correctOutcomes: 'Resultados corretos', safeResolutions: 'Resoluções automáticas seguras', missedHandoffs: 'Encaminhamentos necessários omitidos', unnecessaryHandoffs: 'Propostas humanas desnecessárias', wrongOutcomes: 'Resultados materialmente incorretos', unauthorized: 'Acesso ou ação não autorizada', sample: 'Casos', modelLabel: 'Modelo', averagePrecision: 'Precisão média (AP)', selectedModel: 'Selecionado', constant: 'Prevalência constante', amount_history_rule: 'Regra de valor e histórico', logistic: 'Regressão logística', catboost: 'CatBoost', disclosedLimits: 'Método e limitações do relatório', state_resolved: 'Resposta concluída', state_escalated: 'Encaminhamento verificado', state_clarification: 'Esclarecimento solicitado', state_awaiting_confirmation: 'Confirmação pendente', state_abstained: 'Abstenção', state_blocked: 'Solicitação bloqueada', state_case_lookup: 'Consulta de caso', noProduction: 'Nenhum número representa desempenho em produção.', languageSlice: 'Resultados por idioma' });
Object.assign(words.es, {"questionLabel": "Pregunta para el cliente", "questionHint": "Especifica qué falta para revisar el caso. No solicites claves, números completos ni otros datos sensibles.", "questionPlaceholder": "¿Qué información necesitas aclarar sobre este movimiento?", "requestedInformation": "Información solicitada", "replyLabel": "Tu respuesta al analista", "replyPlaceholder": "Responde con el contexto necesario, sin datos personales ni credenciales.", "sendReply": "Enviar respuesta", "replySaved": "Respuesta guardada y verificada.", "reviewSaved": "Revisión guardada y verificada.", "waitingReply": "Esperando respuesta del cliente", "replyHelp": "La respuesta se guardará en este caso y volverá a la cola de revisión.", "noPendingQuestion": "Este caso no tiene una pregunta pendiente para responder.", "historyUnavailable": "No hay eventos registrados en el historial de este caso.", "historyActor_customer": "Cliente", "historyActor_analyst": "Analista", "historyActor_system": "Sistema", "history_case_created": "Caso creado", "history_question_requested": "Información solicitada", "history_customer_reply": "Respuesta del cliente", "history_review_closed": "Revisión cerrada", "history_status_updated": "Estado actualizado", "historyEvent": "Evento registrado", "reconcileCase": "Actualizar y verificar el caso", "retryLimit": "Se alcanzaron 3 intentos. Verifica el estado del caso antes de iniciar otra acción; no asumimos que haya fallado o tenido éxito.", "retryCount": "Intentos", "uncertainAction": "La respuesta no está confirmada. Conservamos la misma solicitud para reintentar sin duplicarla.", "pendingOperation": "Hay una solicitud pendiente de verificar.", "caseChanged": "El estado del caso cambió. Actualízalo antes de continuar.", "caseVerified": "Cambio leído y verificado en el caso.", "providerNotice": "Los mensajes que escribas en este sandbox y el contexto ficticio mínimo pueden enviarse a los proveedores de IA habilitados. Nunca se envían datos de los organizadores. No ingreses datos personales ni credenciales.", "providerActiveNotice": "Esta sesión usa proveedores externos de IA para los mensajes del sandbox y contexto ficticio mínimo. No se envían datos de los organizadores.", "providerLocalNotice": "Esta sesión usa procesamiento local. Si un proveedor externo se habilita, se indicará en la respuesta.", "aiDetails": "Cómo se procesó esta respuesta", "aiConfig": "IA de esta sesión", "aiClassifier": "Comprensión", "aiResponse": "Redacción", "ai_used": "Proveedor utilizado", "ai_fallback": "Alternativa utilizada", "ai_configured": "Configurado", "ai_disabled": "Deshabilitado", "ai_unavailable": "No disponible", "ai_not_run": "No ejecutado", "ai_local": "Procesamiento local", "ai_not_configured": "Sin configurar", "aiFallbackNotice": "Se utilizó una alternativa; las acciones siguen sujetas a las verificaciones del servicio.", "aiStatusUnknown": "Estado no informado", "providerUnknown": "Proveedor no informado", "redactedReport": "Reporte que recibirá el analista", "reportPrivacy": "Revisa el texto antes de confirmar. Los datos sensibles identificados se ocultan.", "savedQuestion": "Pregunta guardada; pendiente de respuesta del cliente.", "replyRequestedBy": "Pregunta del analista", "historyNotice": "Eventos guardados por el servicio, en orden cronológico.", "actionUnverified": "El servidor no confirmó la verificación. Actualiza el caso antes de enviar otra acción.", "languageNote": "Comparación offline de TF-IDF + regresión logística, reglas y Gemma. El proveedor de cada interacción se muestra en su respuesta. Estos resultados no miden a todos los proveedores ni la resolución de casos."});
Object.assign(words.pt, {"questionLabel": "Pergunta para o cliente", "questionHint": "Especifique o que falta para analisar o caso. Não solicite senhas, números completos nem outros dados sensíveis.", "questionPlaceholder": "Que informação você precisa esclarecer sobre esta transação?", "requestedInformation": "Informação solicitada", "replyLabel": "Sua resposta ao analista", "replyPlaceholder": "Responda com o contexto necessário, sem dados pessoais nem credenciais.", "sendReply": "Enviar resposta", "replySaved": "Resposta salva e verificada.", "reviewSaved": "Análise salva e verificada.", "waitingReply": "Aguardando resposta do cliente", "replyHelp": "A resposta será salva neste caso, que voltará para a fila de análise.", "noPendingQuestion": "Este caso não tem uma pergunta pendente para responder.", "historyUnavailable": "Não há eventos registrados no histórico deste caso.", "historyActor_customer": "Cliente", "historyActor_analyst": "Analista", "historyActor_system": "Sistema", "history_case_created": "Caso criado", "history_question_requested": "Informação solicitada", "history_customer_reply": "Resposta do cliente", "history_review_closed": "Análise encerrada", "history_status_updated": "Status atualizado", "historyEvent": "Evento registrado", "reconcileCase": "Atualizar e verificar o caso", "retryLimit": "O limite de 3 tentativas foi atingido. Verifique o estado do caso antes de iniciar outra ação; não presumimos falha nem sucesso.", "retryCount": "Tentativas", "uncertainAction": "A resposta não está confirmada. Mantemos a mesma solicitação para tentar novamente sem duplicá-la.", "pendingOperation": "Há uma solicitação pendente de verificação.", "caseChanged": "O estado do caso mudou. Atualize-o antes de continuar.", "caseVerified": "Alteração consultada e verificada no caso.", "providerNotice": "As mensagens que você escrever neste sandbox e o contexto fictício mínimo podem ser enviados aos provedores de IA habilitados. Dados dos organizadores nunca são enviados. Não informe dados pessoais nem credenciais.", "providerActiveNotice": "Esta sessão usa provedores externos de IA para mensagens do sandbox e contexto fictício mínimo. Nenhum dado dos organizadores é enviado.", "providerLocalNotice": "Esta sessão usa processamento local. Se um provedor externo for habilitado, isso será indicado na resposta.", "aiDetails": "Como esta resposta foi processada", "aiConfig": "IA desta sessão", "aiClassifier": "Compreensão", "aiResponse": "Redação", "ai_used": "Provedor utilizado", "ai_fallback": "Alternativa utilizada", "ai_configured": "Configurado", "ai_disabled": "Desabilitado", "ai_unavailable": "Indisponível", "ai_not_run": "Não executado", "ai_local": "Processamento local", "ai_not_configured": "Não configurado", "aiFallbackNotice": "Uma alternativa foi usada; as ações continuam sujeitas às verificações do serviço.", "aiStatusUnknown": "Status não informado", "providerUnknown": "Provedor não informado", "redactedReport": "Relato que o analista receberá", "reportPrivacy": "Revise o texto antes de confirmar. Os dados sensíveis identificados são ocultados.", "savedQuestion": "Pergunta salva; aguardando resposta do cliente.", "replyRequestedBy": "Pergunta do analista", "historyNotice": "Eventos salvos pelo serviço, em ordem cronológica.", "actionUnverified": "O servidor não confirmou a verificação. Atualize o caso antes de enviar outra ação.", "languageNote": "Comparação offline de TF-IDF + regressão logística, regras e Gemma. O provedor de cada interação é mostrado na resposta. Estes resultados não medem todos os provedores nem a resolução de casos."});
Object.assign(words.es, {"providerActiveNotice": "Los proveedores externos de IA están habilitados para esta sesión. Solo pueden recibir mensajes del sandbox y contexto ficticio mínimo; nunca datos de los organizadores.", "ai_ok": "Proveedor utilizado", "ai_uncertain": "Resultado incierto", "ai_external_disabled": "Procesamiento local; proveedores externos deshabilitados", "ai_missing_key": "Proveedor sin configurar; no utilizado", "ai_budget_not_authorized": "Consumo no autorizado; proveedor no utilizado", "ai_budget_exhausted": "Límite de consumo alcanzado", "ai_invalid_input": "Solicitud no válida para el proveedor", "ai_input_too_large": "Solicitud demasiado extensa para el proveedor", "ai_response_limit": "Respuesta fuera de los límites permitidos", "ai_retryable_http": "Proveedor no disponible tras los intentos permitidos", "ai_rejected_http": "Solicitud rechazada por el proveedor", "ai_transport_unavailable": "No se pudo conectar con el proveedor", "ai_invalid_response": "Respuesta del proveedor descartada", "ai_usage_bound_exceeded": "Se superó el límite permitido de uso", "ai_budget_store_unavailable": "Control de consumo no disponible", "ai_deterministic_boundary": "Respuesta del servicio; no se requiere IA externa", "ai_unapproved_evidence": "Contexto no permitido para un proveedor externo", "ai_configured_not_probed": "Configurado; disponibilidad aún no comprobada", "ai_not_needed": "No se requirió clasificación", "aiRequestedModel": "Modelo solicitado", "aiResponseFallback": "Se utilizó la respuesta del servicio como alternativa.", "aiClassifierFallback": "La clasificación externa no se utilizó; el servicio conserva sus controles de seguridad.", "provider_local": "Modelo local", "provider_deterministic": "Servicio determinista"});
Object.assign(words.pt, {"providerActiveNotice": "Provedores externos de IA estão habilitados nesta sessão. Eles só podem receber mensagens do sandbox e contexto fictício mínimo; nunca dados dos organizadores.", "ai_ok": "Provedor utilizado", "ai_uncertain": "Resultado incerto", "ai_external_disabled": "Processamento local; provedores externos desabilitados", "ai_missing_key": "Provedor não configurado; não utilizado", "ai_budget_not_authorized": "Consumo não autorizado; provedor não utilizado", "ai_budget_exhausted": "Limite de consumo atingido", "ai_invalid_input": "Solicitação inválida para o provedor", "ai_input_too_large": "Solicitação extensa demais para o provedor", "ai_response_limit": "Resposta fora dos limites permitidos", "ai_retryable_http": "Provedor indisponível após as tentativas permitidas", "ai_rejected_http": "Solicitação rejeitada pelo provedor", "ai_transport_unavailable": "Não foi possível conectar ao provedor", "ai_invalid_response": "Resposta do provedor descartada", "ai_usage_bound_exceeded": "O limite de uso permitido foi excedido", "ai_budget_store_unavailable": "Controle de consumo indisponível", "ai_deterministic_boundary": "Resposta do serviço; IA externa não é necessária", "ai_unapproved_evidence": "Contexto não permitido para um provedor externo", "ai_configured_not_probed": "Configurado; disponibilidade ainda não verificada", "ai_not_needed": "Classificação não necessária", "aiRequestedModel": "Modelo solicitado", "aiResponseFallback": "A resposta do serviço foi usada como alternativa.", "aiClassifierFallback": "A classificação externa não foi usada; o serviço mantém seus controles de segurança.", "provider_local": "Modelo local", "provider_deterministic": "Serviço determinista"});
Object.assign(words.es, { intakeQuestions: 'Preguntas al crear el caso', ai_retry_deferred: 'Reintento del proveedor aplazado', rejectedAction: 'La solicitud fue rechazada. Verifica el caso o corrige los datos antes de continuar.' });
Object.assign(words.pt, { intakeQuestions: 'Perguntas ao criar o caso', ai_retry_deferred: 'Nova tentativa do provedor adiada', rejectedAction: 'A solicitação foi rejeitada. Verifique o caso ou corrija os dados antes de continuar.' });
Object.assign(words.es, { modelCost: 'Costo estimado de API de modelos', providerAttempts: 'Intentos con proveedores', unknownCostAttempts: 'Intentos con costo desconocido', providerCostNotice: 'Estimación según tarifas; no es una factura. Si falta información de uso, el costo se muestra como no disponible.' });
Object.assign(words.pt, { modelCost: 'Custo estimado de API de modelos', providerAttempts: 'Tentativas com provedores', unknownCostAttempts: 'Tentativas com custo desconhecido', providerCostNotice: 'Estimativa segundo tarifas; não é uma fatura. Se faltarem dados de uso, o custo aparece como indisponível.' });
Object.assign(words.es, { analystBoundary: 'Aquí se revisan los casos de este navegador. Vuelve al chat para crear una solicitud de prueba.', closedReadOnly: 'La revisión está cerrada. El historial se conserva para consulta.' });
Object.assign(words.pt, { analystBoundary: 'Aqui são analisados os casos deste navegador. Volte à conversa para criar uma solicitação de teste.', closedReadOnly: 'A análise está encerrada. O histórico é mantido para consulta.' });

Object.assign(words.es, {
  chatWelcome: '¿En qué te ayudo?', chatIntro: 'Consulta un movimiento, cuéntame qué pasó o pide ayuda. Seguimos la conversación en tu idioma.',
  chatGreeting: 'Hola, soy Claro. Puedo explicar un movimiento o preparar un caso para revisión humana. Cuéntame qué necesitas.',
  chatPrivacy: 'Datos ficticios. Sin acceso a cuentas reales. No compartas claves ni datos personales.', chatLimits: 'No se mueve dinero. Los casos pueden borrarse al reiniciar el servicio.',
  newChat: 'Nueva conversación', reviewDemo: 'Revisión humana', customerChat: 'Volver al chat', judgeEvidence: 'Evidencia del proyecto',
  languageAuto: 'Español y português, sin configurar nada', chatExample: 'Por ejemplo: «¿Qué pasó con el cargo de Tienda Demo?»',
  sessionRetry: 'Abrir conversación', yourCases: 'Seguimiento de tus casos', closeCase: 'Volver a la conversación',
  askQuestion: 'Enviar pregunta al cliente', closeReview: 'Cerrar revisión', sessionStarting: 'Preparando la conversación…',
  sourcesContext: 'Datos ficticios al', regressionProtocol: 'Regresión v3: exige respuestas de casos guardados con estado, fecha y evidencia. No es directamente comparable con v2; conserva los fallos de referencias inexistentes.', replyInChat: 'Responde aquí a la pregunta del analista.', jumpToLatest: 'Ver lo último', replyInComposer: 'Responder por chat', replyingTo: 'Respondiendo al analista', leaveReply: 'Seguir con otra consulta',
  attachedRecord: 'Movimiento adjunto al caso', noAttachedRecord: 'Solicitud general de revisión: no se adjuntará ningún movimiento.',
});
Object.assign(words.pt, {
  chatWelcome: 'Como posso ajudar?', chatIntro: 'Consulte uma transação, conte o que aconteceu ou peça ajuda. Seguimos a conversa no seu idioma.',
  chatGreeting: 'Olá, sou o Claro. Posso explicar uma transação ou preparar um caso para análise humana. Conte como posso ajudar.',
  chatPrivacy: 'Dados fictícios. Sem acesso a contas reais. Não compartilhe senhas nem dados pessoais.', chatLimits: 'Nenhum dinheiro é movimentado. Casos podem ser apagados ao reiniciar o serviço.',
  newChat: 'Nova conversa', reviewDemo: 'Análise humana', customerChat: 'Voltar à conversa', judgeEvidence: 'Evidências do projeto',
  languageAuto: 'Español e português, sem configurar nada', chatExample: 'Por exemplo: «O que aconteceu com a cobrança de Tienda Demo?»',
  sessionRetry: 'Abrir conversa', yourCases: 'Acompanhe seus casos', closeCase: 'Voltar à conversa',
  askQuestion: 'Enviar pergunta ao cliente', closeReview: 'Encerrar análise', sessionStarting: 'Preparando a conversa…',
  sourcesContext: 'Dados fictícios até', regressionProtocol: 'Regressão v3: exige respostas de casos salvos com estado, data e evidências. Não é diretamente comparável à v2; mantém as falhas de referências inexistentes.', replyInChat: 'Responda aqui à pergunta do analista.', jumpToLatest: 'Ver o mais recente', replyInComposer: 'Responder na conversa', replyingTo: 'Respondendo ao analista', leaveReply: 'Continuar com outra consulta',
  attachedRecord: 'Transação anexada ao caso', noAttachedRecord: 'Solicitação geral de análise: nenhuma transação será anexada.',
});

const MAX_ATTEMPTS = 3;
const browserLanguage = (navigator.languages || [navigator.language]).find(value => /^(es|pt)(-|$)/i.test(value)) || 'es';
const reviewMode = new URLSearchParams(location.search).has('review');
const state = { language: browserLanguage.toLowerCase().startsWith('pt') ? 'pt' : 'es', user: null, csrf: null, persona: null, view: 'support', session: null, transactions: [], transactionError: false, selected: null, messages: [], chatBusy: false, retry: null, cases: [], casesError: false, caseFilter: 'all', caseDetail: null, casesLoading: false, evaluation: null, evaluationError: false, analytics: null, analyticsError: false, loginBusy: false, loginError: '', generation: 0, chatAttempts: 0, caseDrafts: {}, caseOperations: {}, caseNotice: null, draft: '', replyCase: null, booting: true, scrollToEnd: true };
const t = key => words[state.language][key] || words.es[key] || key;
const root = document.querySelector('#app');
const date = value => { if (!value) return t('noData'); const d = new Date(typeof value === 'number' ? (value < 1e12 ? value * 1000 : value) : String(value).length === 10 ? `${value}T12:00:00Z` : value); return Number.isNaN(d.getTime()) ? String(value) : new Intl.DateTimeFormat(state.language === 'pt' ? 'pt-BR' : 'es-CO', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(d); };
const amount = tx => { if (tx?.amount == null || !tx?.currency) return t('noData'); const n = Number(tx.amount); if (!Number.isFinite(n)) return t('noData'); try { return new Intl.NumberFormat(state.language === 'pt' ? 'pt-BR' : 'es-CO', { style: 'currency', currency: tx.currency, currencyDisplay: 'code', maximumFractionDigits: 2 }).format(n); } catch { return `${n} ${tx.currency}`; } };
const statusLabel = value => (['posted', 'completed', 'approved', 'pending', 'declined', 'failed', 'reversed'].includes(value) ? words[state.language][value] : words[state.language][`status_${value}`]) || value || t('unknown');
const statusClass = value => ['posted', 'completed', 'approved', 'reviewed_closed', 'closed', 'resolved'].includes(value) ? 'green' : ['declined', 'failed'].includes(value) ? 'red' : 'amber';
const statusPill = value => `<span class="pill ${statusClass(value)}"><span class="dot"></span>${esc(statusLabel(value))}</span>`;
const initials = name => String(name || 'C').split(' ').slice(0, 2).map(part => part.charAt(0)).join('').toUpperCase();

const brand = (cls = '') => `<div class="brand ${cls}"><span class="brand-mark" aria-hidden="true">c.</span><span class="wordmark">claro</span></div>`;
const loading = () => `<span class="loading-dots" role="status" aria-label="${t('thinking')}"><i></i><i></i><i></i></span>`;
function announce(text) { document.querySelector('#announcer').textContent = text; }
let toastTimer;
function toast(message) { const el = document.querySelector('#toast'); el.textContent = message; el.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { el.hidden = true; }, 7000); }
class ApiError extends Error { constructor(message, status) { super(message); this.status = status; } }
async function api(path, { method = 'GET', body, anonymous = false } = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    // Select the route's authenticated session; the server still validates its role.
    const headers = { Accept: 'application/json', 'X-Claro-Role': reviewMode ? 'analyst' : 'customer' };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (method !== 'GET' && state.csrf && !anonymous) headers['X-CSRF-Token'] = state.csrf;
    const response = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), credentials: 'same-origin', cache: 'no-store', signal: controller.signal });
    let data = {};
    if (response.status !== 204) { try { data = await response.json(); } catch { throw new ApiError(t('errorGeneric'), response.status); } }
    if (!response.ok) {
      if (response.status === 401 && state.user) { clearSession(); state.loginError = t('errorExpired'); render(); throw new ApiError(t('errorExpired'), 401); }
      const localizedError = { 401: 'errorExpired', 403: 'errorForbidden', 404: 'errorNotFound', 409: 'errorConflict', 422: 'errorValidation', 429: 'errorRateLimit', 503: 'errorUnavailable' }[response.status];
      const detail = t(localizedError || 'errorGeneric');
      throw new ApiError(detail, response.status);
    }
    return data;
  } catch (error) { if (error instanceof ApiError) throw error; throw new ApiError(t('errorNetwork'), 0); }
  finally { clearTimeout(timeout); }
}
function clearSession() { announce(''); state.generation++; Object.assign(state, { user: null, csrf: null, session: null, transactions: [], messages: [], selected: null, cases: [], caseDetail: null, analytics: null, chatBusy: false, retry: null, chatAttempts: 0, caseDrafts: {}, caseOperations: {}, caseNotice: null, replyCase: null }); }
function syncLocale() { document.documentElement.lang = state.language; document.title = t('title'); }
function renderLogin() {
  root.innerHTML = `<div class="chat-shell">${chatHeader()}<main id="main" class="chat-main" tabindex="-1"><section class="conversation" aria-label="${t('chatLabel')}"><div class="chat-intro"><span class="intro-mark" aria-hidden="true">c.</span><p class="eyebrow">${t('languageAuto')}</p><h1>${t('chatWelcome')}</h1><p>${t('chatIntro')}</p></div><div class="session-state" role="status">${state.loginError ? `<p class="inline-error">${esc(state.loginError)}</p><button type="button" class="btn secondary" data-action="login">${t('sessionRetry')}${icon('arrow')}</button>` : `${loading()}<p>${t('sessionStarting')}</p>`}</div><p class="chat-disclosure">${icon('shield')}${t('chatPrivacy')}<span>${t('chatLimits')}</span></p></section></main></div>`;
}
function chatHeader() {
  return `<header class="chat-topbar">${brand()}<span class="chat-demo-label"><span class="dot"></span>Demo</span><div class="chat-topbar-actions">${state.user ? `<button type="button" class="icon-button" data-action="reset-chat" title="${t('newChat')}" aria-label="${t('newChat')}" ${state.chatBusy ? 'disabled' : ''}>${icon('refresh')}</button>` : ''}<a class="review-link" href="/?review=1">${t('reviewDemo')}${icon('external')}</a></div></header>`;
}

function navItems() { return state.user?.role === 'analyst' ? [{ id: 'cases', label: 'reviewQueue', symbol: 'cases' }, { id: 'analytics', label: 'analytics', symbol: 'chart' }, { id: 'evaluation', label: 'evaluation', symbol: 'shield' }] : [{ id: 'support', label: 'support', symbol: 'chat' }, { id: 'cases', label: 'myCases', symbol: 'cases' }, { id: 'evaluation', label: 'evaluation', symbol: 'chart' }]; }
function render() {
  const input = document.querySelector('#message-input');
  if (input) state.draft = input.value;
  const active = document.activeElement?.id;
  const selection = input && active === 'message-input' ? [input.selectionStart, input.selectionEnd] : null;
  const previousLog = document.querySelector('#chat-log');
  const scrollPosition = previousLog?.scrollTop;
  syncLocale();
  if (!state.user) return renderLogin();
  if (state.user.role === 'customer') {
    root.innerHTML = `<div class="chat-shell">${chatHeader()}<main id="main" class="chat-main" tabindex="-1">${renderSupport()}</main></div>`;
    updateChat();
  } else {
    const current = navItems().find(item => item.id === state.view) || navItems()[0];
    root.innerHTML = `<div class="shell"><aside class="sidebar" aria-label="${t('workspace')}">${brand()}<p class="workspace-label">${t('analystBreadcrumb')}</p><nav class="nav-list">${navItems().map(item => `<button type="button" class="nav-link" data-view="${item.id}" ${state.view === item.id ? 'aria-current="page"' : ''}>${icon(item.symbol)}<span>${t(item.label)}</span></button>`).join('')}</nav><div class="sidebar-note">${icon('shield')}<strong>${t('demoNoteTitle')}</strong><p>${t('demoNote')}</p></div><a class="sidebar-reset" href="/">${icon('chat')}<span>${t('customerChat')}</span></a><button type="button" class="sidebar-reset" data-action="reset-sandbox">${icon('refresh')}<span>${t('resetSandbox')}</span></button></aside><div class="workspace"><header class="topbar">${brand('mobile-brand')}<div class="breadcrumb"><span>${t('analystBreadcrumb')}</span>${icon('chevron')}<span>${t(current.label)}</span></div><a class="review-link" href="/">${t('customerChat')}${icon('arrow')}</a></header><main id="main" class="main" tabindex="-1">${renderView()}<footer class="footer-bar"><span>${icon('shield')}${t('footer')}</span><span>${t('footerDisclaimer')}</span></footer></main></div></div>`;
  }
  const fresh = document.querySelector('#message-input');
  if (fresh) { fresh.value = state.draft; resizeComposer(fresh); if (selection) { fresh.focus({ preventScroll: true }); fresh.setSelectionRange(...selection); } }
  const log = document.querySelector('#chat-log');
  if (log && scrollPosition != null && !state.scrollToEnd) log.scrollTop = scrollPosition;
}

function heading(eyebrow, title, description) { return `<div class="page-heading"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${description}</p></div><span class="pill">${icon('lock')}${t('protected')}</span></div>`; }
function stat(symbol, label, value, sub = '') { return `<div class="stat"><span class="stat-icon">${icon(symbol)}</span><div><p>${esc(label)}</p><strong>${esc(value)}</strong>${sub ? `<small>${esc(sub)}</small>` : ''}</div></div>`; }
function renderView() { if (state.view === 'cases') return renderCases(); if (state.view === 'analytics') return renderAnalytics(); if (state.view === 'evaluation') return renderEvaluation(); return renderSupport(); }
function renderSupport() {
  return `<section class="conversation ${state.messages.some(m => m.role === 'user') ? 'has-messages' : ''}" aria-label="${t('chatLabel')}"><div class="chat-intro"><span class="intro-mark" aria-hidden="true">c.</span><p class="eyebrow">${t('languageAuto')}</p><h1>${t('chatWelcome')}</h1><p>${t('chatIntro')}</p></div><div id="chat-log" class="chat-log" role="log" aria-label="${t('chatLabel')}" aria-live="polite" aria-relevant="additions text"></div>${state.caseDetail ? `<section class="inline-case panel" aria-label="${t('yourCases')}"><div class="panel-heading"><h2>${t('yourCases')}</h2><button type="button" class="icon-button" data-action="close-case" aria-label="${t('closeCase')}">${icon('close')}</button></div>${renderCaseDetail()}</section>` : ''}<div class="composer-dock"><div id="chat-context"></div><form class="composer" id="chat-form"><label class="sr-only" for="message-input">${t('messagePlaceholder')}</label><div class="composer-field"><textarea id="message-input" name="message" rows="1" maxlength="2000" placeholder="${t('messagePlaceholder')}" required></textarea><button type="submit" class="send-button" aria-label="${t('send')}" ${state.chatBusy ? 'disabled' : ''}>${icon('send')}</button></div><p class="composer-hint">${t('composerHint')}</p></form><p class="chat-disclosure">${icon('shield')}<span>${t('chatPrivacy')}<small>${t('chatLimits')}</small></span></p><details class="session-details"><summary>${t('sourcesContext')} ${esc(date(state.session?.as_of))}</summary>${renderProviderNotice()}<p>${t('chatExample')}</p><a href="/?review=1&view=evaluation">${t('judgeEvidence')}${icon('external')}</a></details></div></section>`;
}

function renderEvidence(evidence = []) {
  if (!Array.isArray(evidence) || !evidence.length) return '';
  return `<details class="evidence"><summary>${t('evidence')} · ${evidence.length}</summary>${evidence.map(item => `<div class="evidence-item"><strong>${esc(item.title || item.id || t('source'))}</strong>${esc(item.text || '')}<span>${esc(item.source || '')}${item.as_of ? ` · ${t('asOf')} ${esc(date(item.as_of))}` : ''}</span>${item.id ? `<span>${esc(item.id)}</span>` : ''}</div>`).join('')}</details>`;
}
function renderAI(ai, configured = false) {
  if (!ai || typeof ai !== 'object') return '';
  const items = [['classifier', 'aiClassifier'], ['response', 'aiResponse']].filter(([key]) => ai[key] && typeof ai[key] === 'object');
  if (!items.length) return '';
  const fallbackStatuses = ['fallback', 'missing_key', 'budget_not_authorized', 'budget_exhausted', 'invalid_input', 'input_too_large', 'response_limit', 'retryable_http', 'retry_deferred', 'rejected_http', 'transport_unavailable', 'invalid_response', 'usage_bound_exceeded', 'budget_store_unavailable', 'unapproved_evidence'];
  return `<details class="ai-details"><summary>${t(configured ? 'aiConfig' : 'aiDetails')}</summary><dl>${items.map(([key, label]) => {
    const item = ai[key];
    const status = item.status || (configured ? 'configured' : '');
    const statusText = configured && status === 'disabled' && ['local', 'deterministic'].includes(item.provider) ? t('ai_external_disabled') : words[state.language]['ai_' + status] || t('aiStatusUnknown');
    const provider = { jev: 'Jev', deepseek: 'DeepSeek', local: t('provider_local'), deterministic: t('provider_deterministic') }[item.provider] || item.provider || t('providerUnknown');
    const fallback = !configured && fallbackStatuses.includes(status);
    return `<div><dt>${t(label)}</dt><dd><strong>${esc(provider)}</strong>${item.model ? ` · ${esc(item.model)}` : item.requested_model ? `<small>${t('aiRequestedModel')}: ${esc(item.requested_model)}</small>` : ''}<span>${esc(statusText)}</span>${fallback ? `<small>${t(key === 'response' ? 'aiResponseFallback' : 'aiClassifierFallback')}</small>` : ''}</dd></div>`;
  }).join('')}</dl></details>`;
}
function renderProviderNotice() {
  const ai = state.session?.ai;
  return `<div class="provider-notice"><p>${t(ai?.external_enabled === true ? 'providerActiveNotice' : ai?.external_enabled === false ? 'providerLocalNotice' : 'providerNotice')}</p>${renderAI(ai, true)}</div>`;
}
function renderProposalSummary(proposal) {
  const tx = proposal.transaction;
  const attached = tx ? `<div class="proposal-transaction"><span class="label">${t('attachedRecord')}</span><dl class="detail-grid">${fact(t('transactionId'), tx.id)}${fact(t('merchant'), tx.merchant || t('unlistedMerchant'))}${fact(t('amount'), amount(tx))}${fact(t('status'), statusLabel(tx.status))}${fact(t('recordDate'), date(tx.date))}${fact(t('asOf'), date(tx.as_of))}</dl>${tx.source ? `<small>${t('source')}: ${esc(tx.source)}</small>` : ''}</div>` : `<p class="proposal-unattached">${t('noAttachedRecord')}</p>`;
  return `${attached}${proposal.customer_report ? `<div class="proposal-report"><span class="label">${t('redactedReport')}</span><p>${esc(proposal.customer_report)}</p><small>${t('reportPrivacy')}</small></div>` : ''}${Array.isArray(proposal.open_questions) && proposal.open_questions.length ? `<div class="proposal-questions"><span class="label">${t('pendingQuestions')}</span><ul>${proposal.open_questions.map(question => `<li>${esc(question)}</li>`).join('')}</ul></div>` : ''}`;
}
function renderProposal(proposal, index) {
  if (!proposal) return '';
  return `<div class="proposal"><strong>${icon('cases')}${t('proposalTitle')}</strong><p>${esc(proposal.summary || t('proposalNotice'))}</p>${renderProposalSummary(proposal)}<p>${t('proposalNotice')}</p><div class="proposal-actions">${proposal.done ? `<span class="pill green">${t('confirmed')}</span>` : proposal.cancelled ? `<span class="pill">${t('cancelledProposal')}</span>` : `<button type="button" class="btn primary compact" data-confirm="${index}" ${state.chatBusy || proposal.attempts >= MAX_ATTEMPTS ? 'disabled' : ''}>${t('confirm')}${icon('arrow')}</button><button type="button" class="btn secondary compact" data-dismiss="${index}" ${state.chatBusy ? 'disabled' : ''}>${t('dismiss')}</button>`}</div>${proposal.attempts >= MAX_ATTEMPTS && !proposal.done ? `<p class="retry-note">${t('retryLimit')}</p><button type="button" class="btn secondary compact" data-action="read-cases">${t('myCases')}</button>` : ''}</div>`;
}
function renderReceipt(receipt) {
  if (!receipt) return '';
  const verified = receipt.verified === true || receipt.read_back_verified === true || receipt.verification_status === 'verified';
  const id = receipt.case_id || receipt.action_id || receipt.id;
  return `<div class="receipt"><div class="receipt-label">${icon(verified ? 'verified' : 'alert')}${t(verified ? 'receiptVerified' : 'receiptUnverified')}</div>${id ? `<div class="receipt-code">${esc(id)}</div>` : ''}<p>${t(verified ? 'receiptNotice' : 'unverifiedNotice')}</p>${id ? `<button type="button" class="btn secondary compact" data-case-link="${esc(id)}">${t('viewCase')}${icon('arrow')}</button>` : ''}</div>`;
}
function messageMarkup(m, index) {
  if (m.kind === 'restored') return `<p class="session-restore-note">${t('sessionRestored')}</p>`;
  if (m.kind === 'welcome') return `<article class="chat-message welcome-message"><span class="message-avatar">${icon('sparkle')}</span><div class="message-body"><p class="message-name">Claro</p><div class="message-copy">${t('chatGreeting')}</div></div></article>`;
  const user = m.role === 'user';
  return `<article class="chat-message ${user ? 'user' : m.error ? 'system' : ''}">${user ? '' : `<span class="message-avatar">${icon(m.error ? 'alert' : 'sparkle')}</span>`}<div class="message-body"><p class="message-name">${user ? t('you') : 'Claro'}</p><div class="message-copy" ${m.language ? `lang="${esc(m.language)}"` : ''}>${esc(m.message)}</div>${renderEvidence(m.evidence)}${renderProposal(m.proposal, index)}${renderReceipt(m.receipt)}${Array.isArray(m.cases) && m.cases.length ? `<div class="chat-cases">${m.cases.map(c => `<div class="chat-case-card"><button type="button" class="chat-case-link" data-case="${esc(c.id)}"><span>${icon('cases')}${esc(c.id)}</span>${statusPill(c.status)}</button>${c.pending_question?.text ? `<p>${esc(c.pending_question.text)}</p><button type="button" class="btn primary compact" data-reply-chat="${esc(c.id)}">${icon('chat')}${t('replyInComposer')}</button>` : ''}</div>`).join('')}</div>` : ''}${renderAI(m.ai)}${m.caseOperationKey && state.caseOperations[m.caseOperationKey] ? operationNotice(state.caseOperations[m.caseOperationKey], { id: m.caseOperationKey.split(':')[0] }) : ''}${m.trace_id ? `<details class="trace-details"><summary>${t('trace')}</summary><code>${esc(m.trace_id)}</code></details>` : ''}${m.error && state.retry ? `<p class="retry-note">${t(state.chatAttempts >= MAX_ATTEMPTS ? 'retryLimit' : 'uncertainAction')} · ${t('retryCount')} ${state.chatAttempts}/${MAX_ATTEMPTS}</p><button type="button" class="btn secondary compact" data-action="retry-chat" ${state.chatAttempts >= MAX_ATTEMPTS ? 'disabled' : ''}>${icon('refresh')}${t('retry')}</button>` : ''}</div></article>`;
}

function updateChat() {
  const log = document.querySelector('#chat-log'); if (!log) return;
  const nearBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 90;
  const messages = state.messages.length ? state.messages : [{ kind: 'welcome' }];
  // Keep unchanged log entries in place so assistive technology announces new content once.
  log.querySelector('[data-thinking]')?.remove();
  const entries = [...log.children];
  messages.forEach((m, index) => {
    const markup = messageMarkup(m, index);
    if (entries[index]?.dataset.markup === markup) return;
    const template = document.createElement('template'); template.innerHTML = markup;
    const element = template.content.firstElementChild;
    element.dataset.markup = markup;
    if (entries[index]) entries[index].replaceWith(element); else log.append(element);
  });
  entries.slice(messages.length).forEach(element => element.remove());
  if (state.chatBusy) { const thinking = document.createElement('div'); thinking.className = 'chat-message thinking-message'; thinking.dataset.thinking = 'true'; thinking.innerHTML = `<span class="message-avatar">${icon('sparkle')}</span><div class="message-body"><span class="message-name">${t('thinking')}</span>${loading()}</div>`; log.append(thinking); }
  log.setAttribute('aria-busy', String(state.chatBusy));
  document.querySelector('.conversation')?.classList.toggle('has-messages', messages.some(m => m.role === 'user'));
  if (nearBottom || state.scrollToEnd) { log.scrollTop = log.scrollHeight; state.scrollToEnd = false; }
  const context = document.querySelector('#chat-context');
  if (context) context.innerHTML = state.replyCase ? `<div class="reply-context"><span>${icon('cases')}<strong>${t('replyingTo')} · ${esc(state.replyCase.id)}</strong><small>${esc(state.replyCase.question.text)}</small></span><button type="button" class="icon-button" data-action="leave-reply" aria-label="${t('leaveReply')}" ${state.chatBusy ? 'disabled' : ''}>${icon('close')}</button></div>` : '';
  const reset = document.querySelector('[data-action="reset-chat"]'); if (reset) reset.disabled = state.chatBusy;
  const input = document.querySelector('#message-input'); if (input) input.placeholder = t(state.replyCase ? 'replyPlaceholder' : 'messagePlaceholder');
  const send = document.querySelector('.send-button'); if (send) send.disabled = state.chatBusy;
}
function resizeComposer(input) { input.style.height = 'auto'; input.style.height = `${Math.min(input.scrollHeight, 144)}px`; }

function reportOf(c) { return c.customer_report || c.report || c.summary || c.request || ''; }
function renderCases() {
  const analyst = state.user.role === 'analyst';
  let visible = state.cases;
  if (state.caseFilter === 'open') visible = visible.filter(c => !['closed', 'resolved', 'reviewed_closed'].includes(c.status));
  if (state.caseFilter === 'closed') visible = visible.filter(c => ['closed', 'resolved', 'reviewed_closed'].includes(c.status));
  return `${heading(t(analyst ? 'analystBreadcrumb' : 'myCases'), t(analyst ? 'queueTitle' : 'casesTitle'), t(analyst ? 'queueDescription' : 'casesDescription'))}${analyst ? `<div class="annotation analyst-annotation">${icon('lock')}<span>${t('analystBoundary')}</span></div>` : ''}<div class="case-layout"><section class="panel" aria-labelledby="cases-title"><div class="panel-heading"><h2 id="cases-title">${t('cases')} <span class="muted">(${state.cases.length})</span></h2><button type="button" class="icon-button" data-action="refresh-cases" aria-label="${t('refresh')}">${icon('refresh')}</button></div><div class="case-filters" role="group" aria-label="${t('status')}">${['all', 'open', 'closed'].map(filter => `<button type="button" class="filter-btn" data-filter="${filter}" aria-pressed="${state.caseFilter === filter}">${t(filter)}</button>`).join('')}</div>${state.casesLoading ? `<div class="empty">${loading()}</div>` : state.casesError ? `<div class="retry-inline"><p>${t('errorLoad')}</p><button type="button" class="btn secondary compact" data-action="refresh-cases">${t('retry')}</button></div>` : visible.length ? `<div class="case-list">${visible.map(c => `<button type="button" class="case-item" data-case="${esc(c.id)}" aria-pressed="${state.caseDetail?.id === c.id}"><div class="case-item-top"><span>${esc(c.id)}</span>${statusPill(c.status)}</div><p>${esc(reportOf(c) || t('customerReport'))}</p><small>${esc(date(c.created_at))} · ${c.language === 'pt' ? 'PT' : 'ES'}</small></button>`).join('')}</div>` : `<div class="empty">${icon('cases')}<h3>${t(state.cases.length ? 'noCasesFiltered' : 'noCases')}</h3>${state.cases.length ? '' : `<p>${t('noCasesText')}</p>`}${!analyst ? `<button type="button" class="btn secondary compact" data-view="support">${t('startConversation')}${icon('arrow')}</button>` : ''}</div>`}</section><section class="panel" id="case-detail" aria-label="${t('verifiedFacts')}">${renderCaseDetail()}</section></div>`;
}
function fact(label, value) { return `<div class="detail-fact"><dt>${esc(label)}</dt><dd>${esc(value ?? t('unknown'))}</dd></div>`; }
function renderCaseDetail() {
  const c = state.caseDetail;
  if (!c) return `<div class="empty case-empty">${icon('cases')}<h3>${t('chooseCase')}</h3><p>${t('chooseCaseText')}</p></div>`;
  if (c.loading) return `<div class="empty case-empty">${loading()}</div>`;
  if (c.error) return `<div class="empty case-empty"><h3>${t('errorLoad')}</h3><button type="button" class="btn secondary compact" data-case="${esc(c.id)}">${t('retry')}</button></div>`;
  const tx = c.transaction || c.transaction_evidence;
  const risk = c.risk;
  const riskValue = risk?.probability ?? risk?.score;
  const questions = c.open_questions || c.missing_information || [];
  const history = Array.isArray(c.timeline) ? c.timeline : [];
  return `<div class="case-detail"><div class="case-detail-head"><div><div class="eyebrow">${t('cases')}</div><h2>${esc(c.id)}</h2><p>${t('created')} ${esc(date(c.created_at))} · ${c.language === 'pt' ? 'Português' : 'Español'}</p></div>${statusPill(c.status)}</div><section class="detail-section"><h3 class="label">${t('customerReport')}</h3><p class="quote">${esc(reportOf(c) || t('unknown'))}</p></section>${tx ? `<section class="detail-section"><h3 class="label">${t('verifiedFacts')}</h3><dl class="detail-grid">${fact(t('transactionId'), tx.id || c.transaction_id)}${fact(t('amount'), amount(tx))}${fact(t('merchant'), tx.merchant || t('unlistedMerchant'))}${fact(t('status'), statusLabel(tx.status))}${fact(t('recordDate'), date(tx.date || tx.transaction_date))}${fact(t('asOf'), date(tx.as_of || state.session?.as_of))}</dl></section>` : ''}<section class="detail-section"><h3 class="label">${t('risk')}</h3><div class="risk-note">${risk && riskValue != null && Number.isFinite(Number(riskValue)) ? `${t('confidence')}: <strong>${esc(new Intl.NumberFormat(state.language, { style: 'percent', maximumFractionDigits: 1 }).format(Number(riskValue)))}</strong><br>${t('model')}: ${esc(risk.model_version || risk.model || t('unknown'))}<br>${t('riskDisclaimer')}` : t('riskUnavailable')}</div></section>${Array.isArray(questions) && questions.length ? `<section class="detail-section"><h3 class="label">${t('intakeQuestions')}</h3><ul class="small muted">${questions.map(q => `<li>${esc(q)}</li>`).join('')}</ul></section>` : ''}<section class="detail-section"><h3 class="label">${t('evidence')}</h3>${renderEvidence(c.evidence) || `<p class="small muted">${t('noEvidence')}</p>`}</section>${c.receipt ? renderReceipt(c.receipt) : ''}${renderCaseHistory(history)}${renderCaseActions(c)}</div>`;
}
function eventTime(value) {
  if (!value) return t('noData');
  const d = new Date(typeof value === 'number' && value < 1e12 ? value * 1000 : value);
  return Number.isNaN(d.getTime()) ? t('noData') : new Intl.DateTimeFormat(state.language === 'pt' ? 'pt-BR' : 'es-CO', { dateStyle: 'medium', timeStyle: 'medium', timeZone: 'UTC' }).format(d) + ' UTC';
}
function renderCaseHistory(history) {
  return `<section class="detail-section"><h3 class="label">${t('timeline')}</h3><p class="resolution-note">${t('historyNotice')}</p>${history.length ? `<ol class="timeline">${history.map(event => `<li><div class="timeline-heading"><strong>${esc(words[state.language]['history_' + event.type] || t('historyEvent'))}</strong>${event.status ? statusPill(event.status) : ''}</div><small>${esc(words[state.language]['historyActor_' + event.actor_role] || t('historyActor_system'))} · ${esc(eventTime(event.created_at))}</small>${event.text ? `<p class="timeline-message">${esc(event.text)}</p>` : ''}</li>`).join('')}</ol>` : `<p class="small muted">${t('historyUnavailable')}</p>`}</section>`;
}
function caseDraft(c) { return state.caseDrafts[c.id] ||= { resolution: c.status === 'needs_information' ? 'needs_information' : 'reviewed_closed', question: '', reply: '' }; }
function operationNotice(op, c) {
  if (!op?.error) return '';
  return `<div class="case-operation-error" role="alert"><p>${esc(op.error)}</p><p>${t(op.rejected ? 'rejectedAction' : op.attempts >= MAX_ATTEMPTS ? 'retryLimit' : 'uncertainAction')} · ${t('retryCount')} ${op.attempts}/${MAX_ATTEMPTS}</p><div class="case-action-row">${op.retryable && op.attempts < MAX_ATTEMPTS ? `<button type="button" class="btn secondary compact" data-retry-case="${esc(op.kind)}" data-case-id="${esc(c.id)}" ${op.busy ? 'disabled' : ''}>${t('retry')}</button>` : ''}<button type="button" class="btn secondary compact" data-case="${esc(c.id)}" ${op.busy ? 'disabled' : ''}>${t('reconcileCase')}</button></div></div>`;
}
function renderCaseActions(c) {
  const analyst = state.user.role === 'analyst';
  const draft = caseDraft(c);
  const kind = analyst ? 'resolve' : 'reply';
  const op = state.caseOperations[c.id + ':' + kind];
  const locked = Boolean(op && !op.editable);
  const question = c.pending_question;
  const notice = state.caseNotice?.id === c.id ? `<p class="case-save-success" role="status">${t(state.caseNotice.kind === 'reply' ? 'replySaved' : 'reviewSaved')}</p>` : '';
  const pending = question?.text ? `<section class="pending-question"><div class="label">${t(analyst ? 'waitingReply' : 'replyRequestedBy')}</div><p>${esc(question.text)}</p></section>` : '';
  if (analyst && ['reviewed_closed', 'closed', 'resolved'].includes(c.status)) return `${notice}${operationNotice(op, c)}<p class="resolution-note closed-case-note">${t('closedReadOnly')}</p>`;
  if (analyst) return `${pending}<form class="detail-section case-action-form" id="resolution-form" data-case-id="${esc(c.id)}" aria-busy="${Boolean(op?.busy)}"><h3 class="label">${t('review')}</h3><fieldset ${locked ? 'disabled' : ''}><input type="hidden" name="resolution" value="needs_information"><label for="case-question">${t('questionLabel')}</label><textarea id="case-question" name="question" maxlength="1000" placeholder="${t('questionPlaceholder')}" aria-describedby="question-hint">${esc(draft.question)}</textarea><p class="resolution-note" id="question-hint">${t('questionHint')}</p><p class="resolution-note">${t('resolutionDisclaimer')}</p><div class="review-actions"><button type="submit" class="btn primary" name="review-action" value="needs_information">${icon('send')}${t(op?.busy ? 'saving' : 'askQuestion')}</button><button type="submit" class="btn secondary" name="review-action" value="reviewed_closed">${icon('check')}${t('closeReview')}</button></div></fieldset>${notice}${operationNotice(op, c)}</form>`;
  return `${pending}${c.status === 'needs_information' && question?.text ? `<div class="detail-section"><p class="resolution-note">${t('replyInChat')}</p><button type="button" class="btn primary" data-reply-chat="${esc(c.id)}" ${locked ? 'disabled' : ''}>${icon('chat')}${t('replyInComposer')}</button>${operationNotice(op, c)}</div>` : op ? operationNotice(op, c) : ''}${notice}`;
}
function metricValue(value) { if (value == null) return '—'; if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(3); return String(value); }
function estimatedCost(value) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) return t('noData');
  const format = new Intl.NumberFormat(state.language === 'pt' ? 'pt-BR' : 'es-CO', { style: 'currency', currency: 'USD', currencyDisplay: 'code', minimumFractionDigits: 2, maximumFractionDigits: 6 });
  return value > 0 && value < 0.000001 ? '< ' + format.format(0.000001) : format.format(value);
}
function renderAnalytics() {
  const a = state.analytics;
  const cases = a?.cases_by_status || {};
  const entries = Object.entries(a?.outcomes || {});
  const total = entries.reduce((sum, [, count]) => sum + count, 0);
  const caseCount = Object.values(cases).reduce((sum, count) => sum + count, 0);
  const openCount = Object.entries(cases).filter(([status]) => !['reviewed_closed', 'closed', 'resolved'].includes(status)).reduce((sum, [, count]) => sum + count, 0);
  return `${heading(t('analytics'), t('analyticsTitle'), t('analyticsDescription'))}${state.analyticsError ? `<div class="panel retry-inline"><p>${t('errorLoad')}</p><button class="btn secondary" data-action="refresh-analytics">${t('retry')}</button></div>` : !a ? `<div class="panel empty">${loading()}</div>` : `<div class="stats analytics-stats">${stat('cases', t('totalCases'), caseCount)}${stat('clock', t('openCases'), openCount)}${stat('verified', t('verifiedActions'), a.outcomes?.escalated || 0)}${stat('chat', t('requests'), a.total_requests ?? '—')}</div><div class="evaluation-grid"><section class="panel"><div class="panel-heading"><h2>${t('activity')}</h2><button type="button" class="icon-button" data-action="refresh-analytics" aria-label="${t('refresh')}">${icon('refresh')}</button></div><table class="metric-table"><thead><tr><th>${t('measure')}</th><th>${t('status')}</th></tr></thead><tbody><tr><td>${t('latency')} · p50</td><td><strong>${a.latency_ms?.p50 != null ? Number(a.latency_ms.p50).toFixed(1) + ' ms' : '—'}</strong></td></tr><tr><td>${t('latency')} · p95</td><td><strong>${a.latency_ms?.p95 != null ? Number(a.latency_ms.p95).toFixed(1) + ' ms' : '—'}</strong></td></tr><tr><td>${t('modelCost')}</td><td><strong>${esc(estimatedCost(a.estimated_model_api_cost_usd))}</strong></td></tr>${a.provider_attempts != null ? `<tr><td>${t('providerAttempts')}</td><td>${esc(metricValue(a.provider_attempts))}</td></tr>` : ''}${a.unknown_cost_attempts != null ? `<tr><td>${t('unknownCostAttempts')}</td><td>${esc(metricValue(a.unknown_cost_attempts))}</td></tr>` : ''}${Object.entries(cases).map(([key, value]) => `<tr><td>${esc(statusLabel(key))}</td><td>${value}</td></tr>`).join('')}</tbody></table><p class="report-notes">${t('latencyNote')} ${t('providerCostNotice')} ${t('operationalBoundary')}</p></section><section class="panel"><div class="panel-heading"><h2>${t('outcomes')}</h2></div><div class="analytics-language">${entries.length ? entries.map(([key, count]) => `<div><div class="language-row"><span>${esc(t('state_' + key))}</span><strong>${count}</strong></div><progress class="metric-bar" max="${total || 1}" value="${count}" aria-label="${esc(t('state_' + key))}">${count}/${total}</progress></div>`).join('') : `<p class="small muted">${t('noData')}</p>`}</div></section></div><div class="annotation">${icon('info')}<span>${t('operationalBoundary')}</span></div>`}`;
}
function metricName(key) {
  const map = { total_cases: 'totalCases', cases_total: 'totalCases', open_cases: 'openCases', cases_open: 'openCases', verified_actions: 'verifiedActions', verified_receipts: 'verifiedActions', total_messages: 'totalMessages', chat_turns: 'totalMessages' };
  return map[key] ? t(map[key]) : String(key).replace(/_/g, ' ');
}
function renderEvaluation() {
  const reports = state.evaluation?.reports || {};
  return `${heading(t('evaluation'), t('evaluationTitle'), t('evaluationDescription'))}<div class="evaluation-grid"><div class="report-stack">${state.evaluationError ? `<section class="panel retry-inline"><p>${t('errorLoad')}</p><button type="button" class="btn secondary compact" data-action="refresh-evaluation">${t('retry')}</button></section>` : Object.keys(reports).length ? renderEvaluationReport(reports) : `<section class="panel empty">${icon('chart')}<h3>${t('evaluationPending')}</h3><p>${t('evaluationPendingText')}</p></section>`}</div><section class="panel"><div class="panel-heading"><h2>${t('limitations')}</h2></div><div class="boundaries">${[1, 2, 3, 4].map(i => `<div class="boundary">${icon(i === 3 ? 'lock' : 'info')}<div><strong>${t(`limitation${i}`)}</strong><p>${t(`limitation${i}Text`)}</p></div></div>`).join('')}</div><p class="report-notes">${t('comparisonNote')}</p><a class="report-link" href="/api/evaluation" target="_blank" rel="noopener">${t('viewReport')}${icon('external')}</a></section></div>`;
}
const percent = value => value == null ? '—' : new Intl.NumberFormat(state.language, { style: 'percent', maximumFractionDigits: 1 }).format(value);
function comparisonTable(systems, columns, metrics) {
  const chosen = columns.filter(([key]) => systems[key]);
  return `<div class="table-scroll"><table class="metric-table"><thead><tr><th>${t('measure')}</th>${chosen.map(([, title]) => `<th>${esc(title)}</th>`).join('')}</tr></thead><tbody>${metrics.map(([key, label, format]) => `<tr><td>${t(label)}</td>${chosen.map(([id]) => `<td><strong>${esc(format ? format(systems[id][key]) : metricValue(systems[id][key]))}</strong></td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function reportDisclosure(report) { return `<details class="report-notes"><summary>${t('disclosedLimits')}</summary><pre class="report-json">${esc(JSON.stringify(report, null, 2))}</pre></details>`; }
function renderEvaluationReport(reports) {
  const language = reports['language-evaluation'];
  const system = reports['system-evaluation'];
  const fraud = reports['fraud-evaluation'];
  let html = '';
  if (language?.systems) {
    const columns = [['keyword_rules', 'Reglas / Regras'], ['tfidf_logistic', 'TF-IDF + LR'], ['gemma3_4b_local', 'Gemma 3 4B']];
    html += `<section class="panel"><div class="panel-heading"><h2>${t('languageReport')}</h2><span class="pill">ES + PT</span></div><p class="section-copy">${t('languageNote')}</p>${comparisonTable(language.systems, columns, [['cases', 'sample'], ['macro_f1', 'macroF1', percent], ['accuracy', 'accuracy', percent], ['customer_reports_misrouted_to_other_intent', 'misroutedReports']])}<div class="report-section"><h3>${t('languageSlice')}</h3>${comparisonTable(Object.fromEntries(Object.entries(language.systems).map(([key, item]) => [key, { es: item.language_slices?.es?.macro_f1, pt: item.language_slices?.pt?.macro_f1 }])), columns, [['es', 'languageEs', percent], ['pt', 'languagePt', percent]])}<p class="report-notes">Macro-F1 · ${t('comparisonNote')}</p></div>${reportDisclosure(language)}</section>`;
  }
  if (system?.systems) {
    html += `<section class="panel"><div class="panel-heading"><h2>${t('workflowReport')}</h2><span class="pill">${esc(system.cases_per_system)} ${t('sample').toLowerCase()}</span></div><p class="section-copy">${t('workflowNote')}</p>${system.version === 'system-grounded-case-lookup-v3' ? `<p class="report-notes">${t('regressionProtocol')}</p>` : ''}${comparisonTable(system.systems, [['keyword_rules', 'Reglas / Regras'], ['tfidf_logistic', 'TF-IDF + LR']], [['cases', 'sample'], ['correct_outcomes', 'correctOutcomes'], ['safe_automated_resolutions', 'safeResolutions'], ['missed_required_handoffs', 'missedHandoffs'], ['unnecessary_handoff_proposals', 'unnecessaryHandoffs'], ['materially_wrong_outcomes', 'wrongOutcomes'], ['unauthorized_disclosure_or_action', 'unauthorized']])}<p class="report-notes">${t('noProduction')} ${t('comparisonNote')}</p>${reportDisclosure(system)}</section>`;
  }
  if (fraud?.metrics?.test) {
    const models = ['constant', 'amount_history_rule', 'logistic', 'catboost'].filter(key => fraud.metrics.test[key]);
    html += `<section class="panel"><div class="panel-heading"><h2>${t('fraudReport')}</h2></div><p class="section-copy">${t('fraudNote')}</p><div class="table-scroll"><table class="metric-table"><thead><tr><th>${t('modelLabel')}</th><th>${t('averagePrecision')}</th><th>${t('sample')}</th></tr></thead><tbody>${models.map(key => `<tr class="${fraud.selected === key ? 'selected-model' : ''}"><td>${t(key)}${fraud.selected === key ? `<span class="report-subtitle">${t('selectedModel')}</span>` : ''}</td><td><strong>${Number(fraud.metrics.test[key].average_precision).toFixed(6)}</strong></td><td>${Number(fraud.metrics.test[key].rows).toLocaleString(state.language)}</td></tr>`).join('')}</tbody></table></div><p class="report-notes">${t('noProduction')}</p>${reportDisclosure(fraud)}</section>`;
  }
  return html;
}
async function login() {
  if (state.loginBusy) return;
  state.loginBusy = true; state.loginError = ''; render();
  try {
    const persona = reviewMode ? 'analyst' : state.persona && state.persona !== 'analyst' ? state.persona : state.language === 'pt' ? 'customer_pt' : 'customer_es';
    const data = await api('/api/session', { method: 'POST', body: { persona, language: state.language }, anonymous: true });
    applySession(data);
    await loadInitial();
    if (state.user.role === 'analyst' && new URLSearchParams(location.search).get('view') === 'evaluation') { state.view = 'evaluation'; await loadEvaluation(); }
  } catch (error) { state.loginError = error.message; }
  finally { state.loginBusy = false; state.booting = false; render(); }
}
function applySession(data) {
  state.session = data; state.user = data.user; state.csrf = data.csrf_token; state.persona = data.demo_persona || state.persona; state.language = data.user.language === 'pt' ? 'pt' : 'es';
  state.view = data.user.role === 'analyst' ? 'cases' : 'support'; state.selected = data.context?.transaction_id || null;
  const history = Array.isArray(data.context?.history) ? data.context.history : [];
  state.messages = [{ kind: 'welcome' }, ...history.filter(m => ['user', 'assistant'].includes(m.role) && typeof m.content === 'string').map(m => ({ role: m.role, message: m.content })), ...(history.length ? [{ kind: 'restored' }] : [])];
  if (data.proposal) state.messages.push({ role: 'assistant', message: data.proposal.summary, proposal: data.proposal, evidence: data.proposal_evidence || [] });
  state.scrollToEnd = true;
}

async function loadInitial() { if (state.user?.role === 'analyst') await loadCases(); else await loadTransactions(); }
async function loadTransactions() {
  const generation = state.generation;
  try { const data = await api('/api/transactions'); if (generation !== state.generation) return; state.transactions = data.transactions || []; state.asOf = data.as_of; state.transactionError = false; if (!state.transactions.some(tx => tx.id === state.selected)) state.selected = null; }
  catch (error) { if (error.status !== 401) state.transactionError = true; }
}
async function loadCases() {
  const generation = state.generation; state.casesLoading = true;
  try { const data = await api('/api/cases'); if (generation !== state.generation) return; state.cases = data.cases || []; state.casesError = false; }
  catch (error) { if (error.status !== 401) state.casesError = true; }
  finally { state.casesLoading = false; }
}
async function loadCase(id) {
  const generation = state.generation; state.caseDetail = { id, loading: true }; render();
  try { const data = await api(`/api/cases/${encodeURIComponent(id)}`); if (generation !== state.generation || state.caseDetail?.id !== id) return; state.caseDetail = data.case || data; syncCaseCards(state.caseDetail); reconcileCaseOperations(state.caseDetail); }
  catch (error) { if (error.status !== 401) state.caseDetail = { id, error: true }; }
  if (state.view === 'cases' || state.user?.role === 'customer') render();
}
async function navigate(view) {
  if (!navItems().some(item => item.id === view)) return;
  state.view = view; render();
  if (view === 'cases') await loadCases();
  if (view === 'analytics') await loadAnalytics();
  if (view === 'evaluation') await loadEvaluation();
  if (state.view === view) render();
}
async function loadAnalytics() { try { state.analytics = await api('/api/analytics'); state.analyticsError = false; } catch (error) { if (error.status !== 401) state.analyticsError = true; } }
async function loadEvaluation() { try { state.evaluation = await api('/api/evaluation'); state.evaluationError = false; } catch (error) { if (error.status === 404) { state.evaluation = null; state.evaluationError = false; } else state.evaluationError = true; } }
async function sendChat(message, retryBody) {
  if (state.chatBusy || !state.user || !message.trim()) return;
  if (message.length > 2000) { toast(t('tooLong')); return; }
  if (state.replyCase && !retryBody) { await sendChatReply(message.trim()); return; }
  const generation = state.generation;
  if (retryBody && state.chatAttempts >= MAX_ATTEMPTS) return;
  if (!retryBody) state.chatAttempts = 0;
  state.chatAttempts++;
  const body = retryBody || { message: message.trim(), idempotency_key: crypto.randomUUID() };
  if (!retryBody) { state.messages.push({ role: 'user', message: message.trim() }); }
  else state.messages = state.messages.filter(m => !m.error);
  state.chatBusy = true; state.retry = null; state.draft = ''; state.scrollToEnd = true;
  const input = document.querySelector('#message-input'); if (input) { input.value = ''; input.style.height = 'auto'; }
  updateChat();
  try { const data = await api('/api/chat', { method: 'POST', body }); if (generation !== state.generation) return; if (data.state === 'cancelled' || data.proposal) state.messages.forEach(m => { if (m.proposal && !m.proposal.done && m.proposal.id !== data.proposal?.id) m.proposal.cancelled = true; }); state.messages.push({ role: 'assistant', ...data }); if (data.transaction?.id) state.selected = data.transaction.id; if (data.language && data.language !== state.language) { state.language = data.language; render(); } }
  catch (error) { if (generation !== state.generation) return; state.messages.push({ role: 'assistant', message: error.message, error: true }); state.retry = body; }
  finally { if (generation === state.generation) { state.chatBusy = false; updateChat(); document.querySelector('#message-input')?.focus({ preventScroll: true }); } }
}
async function sendChatReply(message) {
  const reply = state.replyCase;
  if (!reply || state.caseOperations[reply.id + ':reply'] && !state.caseOperations[reply.id + ':reply'].editable) { toast(t('pendingOperation')); return; }
  const key = reply.id + ':reply';
  const body = { message, question_id: reply.question.id, idempotency_key: crypto.randomUUID() };
  state.caseOperations[key] = { kind: 'reply', body, attempts: 0, busy: false, error: '', retryable: true, chat: true };
  state.messages.push({ role: 'user', message }); state.draft = ''; state.scrollToEnd = true;
  const input = document.querySelector('#message-input'); if (input) input.value = '';
  state.caseDetail = null;
  await performCaseAction(reply.id, 'reply');
}
function syncCaseCards(c) { state.messages.forEach(message => { if (Array.isArray(message.cases)) message.cases = message.cases.map(value => value.id === c.id ? c : value); }); }
function finishChatReply(c, key) {
  syncCaseCards(c);
  state.messages = state.messages.filter(message => message.caseOperationKey !== key);
  state.messages.push({ role: 'assistant', message: t('replySaved'), cases: [c] });
  state.replyCase = null; state.caseDetail = null; state.scrollToEnd = true;
}

function openConfirm(index) {
  const message = state.messages[index]; if (!message?.proposal || message.proposal.done || message.proposal.cancelled || message.proposal.attempts >= MAX_ATTEMPTS || state.chatBusy) return;
  const proposal = message.proposal;
  const dialog = document.createElement('dialog'); dialog.id = 'confirm-dialog'; dialog.className = 'dialog'; dialog.setAttribute('aria-labelledby', 'confirm-title');
  dialog.innerHTML = `<div class="dialog-body"><h2 id="confirm-title">${t('confirmTitle')}</h2><p>${t('proposalNotice')}</p><div class="summary">${esc(proposal.summary || t('proposalTitle'))}${renderProposalSummary(proposal)}</div><div id="confirm-error"></div></div><div class="dialog-actions"><button type="button" class="btn secondary" id="close-confirm">${t('cancel')}</button><button type="button" class="btn primary" id="submit-confirm">${icon('check')}${t('confirmAction')}</button></div>`;
  document.body.append(dialog);
  let running = false;
  dialog.addEventListener('cancel', e => { if (running) e.preventDefault(); });
  dialog.addEventListener('close', () => dialog.remove());
  dialog.querySelector('#close-confirm').addEventListener('click', () => dialog.close());
  dialog.querySelector('#submit-confirm').addEventListener('click', async () => {
    if (running || proposal.attempts >= MAX_ATTEMPTS) return; running = true;
    proposal.attempts = (proposal.attempts || 0) + 1;
    proposal.idempotency_key ||= crypto.randomUUID();
    const confirmButton = dialog.querySelector('#submit-confirm'); confirmButton.disabled = true; confirmButton.textContent = t('confirming'); dialog.querySelector('#close-confirm').disabled = true;
    try {
      const data = await api('/api/actions/confirm', { method: 'POST', body: { proposal_id: proposal.id, idempotency_key: proposal.idempotency_key } });
      if (data.receipt?.verified !== true) throw new ApiError(t('actionUnverified'), 503);
      if (state.user) { proposal.done = true; state.messages.push({ role: 'assistant', ...data }); updateChat(); }
      dialog.close();
    } catch (error) { dialog.querySelector('#confirm-error').innerHTML = `<p class="inline-error" role="alert">${esc(error.message)}</p><p>${t(proposal.attempts >= MAX_ATTEMPTS ? 'retryLimit' : 'uncertainAction')} · ${t('retryCount')} ${proposal.attempts}/${MAX_ATTEMPTS}</p>`; confirmButton.disabled = proposal.attempts >= MAX_ATTEMPTS; confirmButton.textContent = t('retry'); dialog.querySelector('#close-confirm').disabled = false; if (error.status === 401) dialog.close(); }
    finally { running = false; updateChat(); }
  });
  dialog.showModal();
  dialog.querySelector('#close-confirm').focus();
}
function reconcileCaseOperations(c) {
  const events = Array.isArray(c.timeline) ? c.timeline : [];
  for (const kind of ['resolve', 'reply']) {
    const key = c.id + ':' + kind;
    const op = state.caseOperations[key];
    if (op && events.some(event => event.client_request_id === op.body.idempotency_key)) {
      if (op.chat) finishChatReply(c, key);
      delete state.caseOperations[key]; delete state.caseDrafts[c.id];
      state.caseNotice = { id: c.id, kind };
    } else if (op?.rejected) { delete state.caseOperations[key]; }
  }
}
async function submitCaseAction(form, kind) {
  if (!form.reportValidity()) return;
  const id = form.dataset.caseId;
  const previous = state.caseOperations[id + ':' + kind];
  if (previous && !previous.editable) return;
  const data = new FormData(form);
  const resolution = data.get('resolution');
  const text = String(data.get(kind === 'resolve' ? 'question' : 'message') || '').trim();
  const requiresText = kind === 'reply' || resolution === 'needs_information';
  if (requiresText && text.length < (kind === 'resolve' ? 5 : 1)) { const field = form.querySelector('textarea'); field.setCustomValidity(t('errorValidation')); field.reportValidity(); return; }
  const questionId = String(data.get('question_id') || '');
  if (kind === 'reply' && !questionId) { toast(t('caseChanged')); return; }
  const body = kind === 'resolve' ? { resolution, ...(resolution === 'needs_information' ? { question: text } : {}), idempotency_key: crypto.randomUUID() } : { message: text, question_id: questionId, idempotency_key: crypto.randomUUID() };
  state.caseOperations[id + ':' + kind] = { kind, body, attempts: 0, busy: false, error: '', retryable: true };
  state.caseNotice = null;
  await performCaseAction(id, kind);
}
async function performCaseAction(id, kind) {
  const key = id + ':' + kind;
  const op = state.caseOperations[key];
  if (!op || op.busy || !op.retryable || op.attempts >= MAX_ATTEMPTS || !state.user) return;
  const generation = state.generation;
  op.busy = true; op.attempts++; op.error = ''; if (op.chat) state.chatBusy = true; render();
  try {
    const data = await api(`/api/cases/${encodeURIComponent(id)}/${kind === 'resolve' ? 'resolve' : 'messages'}`, { method: 'POST', body: op.body });
    if (generation !== state.generation) return;
    const value = data.case || data;
    if (data.receipt?.verified !== true && value.receipt?.verified !== true) throw new ApiError(t('actionUnverified'), 503);
    if (state.caseDetail?.id === id) state.caseDetail = value;
    if (op.chat) finishChatReply(value, key);
    delete state.caseOperations[key]; delete state.caseDrafts[id];
    state.caseNotice = { id, kind };
    await loadCases();
    if (generation === state.generation) announce(t(kind === 'reply' ? 'replySaved' : 'reviewSaved'));
  } catch (error) {
    if (generation !== state.generation) return;
    op.error = error.status === 409 ? t('caseChanged') : error.message;
    op.retryable = [0, 408, 429, 500, 502, 503, 504].includes(error.status);
    op.rejected = [400, 403, 404, 409, 422].includes(error.status);
    op.editable = [400, 422].includes(error.status);
    if (op.chat) { state.messages = state.messages.filter(message => message.caseOperationKey !== key); state.messages.push({ role: 'assistant', message: op.error, caseOperationKey: key }); }
  } finally {
    if (generation === state.generation) { op.busy = false; if (op.chat) state.chatBusy = false; render(); document.querySelector('#message-input')?.focus({ preventScroll: true }); }
  }
}
async function cancelProposal(index) {
  const proposal = state.messages[index]?.proposal;
  if (!proposal || proposal.done || proposal.cancelled || state.chatBusy) return;
  const generation = state.generation;
  state.chatBusy = true; updateChat();
  try {
    await api('/api/conversation/reset', { method: 'POST' });
    if (generation !== state.generation) return;
    state.selected = null; state.retry = null; state.replyCase = null; state.caseDetail = null;
    state.messages.forEach(message => { if (message.proposal && !message.proposal.done) message.proposal.cancelled = true; });
    announce(t('cancelled'));
  } catch (error) { toast(error.message); }
  finally { if (generation === state.generation) { state.chatBusy = false; render(); } }
}
async function resetConversation(clearMessages = true) {
  if (state.chatBusy || !state.user) return;
  const generation = state.generation;
  state.chatBusy = true; updateChat();
  try {
    await api('/api/conversation/reset', { method: 'POST' });
    if (generation !== state.generation) return;
    state.selected = null; state.retry = null; state.replyCase = null; state.caseDetail = null;
    state.messages.forEach(message => { if (message.proposal && !message.proposal.done) message.proposal.cancelled = true; });
    if (clearMessages) state.messages = [{ kind: 'welcome' }];
  } catch (error) { if (generation === state.generation) toast(error.message); }
  finally { if (generation === state.generation) { state.chatBusy = false; render(); document.querySelector('#message-input')?.focus(); } }
}
function openResetSandbox() {
  const dialog = document.createElement('dialog'); dialog.className = 'dialog'; dialog.setAttribute('aria-labelledby', 'reset-title');
  dialog.innerHTML = `<h2 id="reset-title">${t('resetTitle')}</h2><p>${t('resetNotice')}</p><div id="reset-error"></div><div class="dialog-actions"><button type="button" class="btn secondary" id="cancel-reset">${t('cancel')}</button><button type="button" class="btn" id="submit-reset">${t('resetConfirm')}</button></div>`;
  document.body.append(dialog); dialog.addEventListener('close', () => dialog.remove()); dialog.querySelector('#cancel-reset').addEventListener('click', () => dialog.close());
  dialog.querySelector('#submit-reset').addEventListener('click', async () => { const button = dialog.querySelector('#submit-reset'); button.disabled = true; try { await api('/api/workspace', { method: 'DELETE' }); clearSession(); render(); dialog.close(); announce(t('resetSuccess')); } catch (error) { dialog.querySelector('#reset-error').innerHTML = `<p class="inline-error" role="alert">${esc(error.message)}</p>`; button.disabled = false; } });
  dialog.showModal(); dialog.querySelector('#cancel-reset').focus();
}
root.addEventListener('click', async event => {
  const button = event.target.closest('button'); if (!button || button.disabled) return;
  if (button.dataset.view) { await navigate(button.dataset.view); return; }
  if (button.dataset.prompt) { await sendChat(t(button.dataset.prompt)); return; }
  if (button.dataset.confirm) { openConfirm(Number(button.dataset.confirm)); return; }
  if (button.dataset.dismiss) { await cancelProposal(Number(button.dataset.dismiss)); return; }
  if (button.dataset.filter) { state.caseFilter = button.dataset.filter; render(); return; }
  if (button.dataset.retryCase) { await performCaseAction(button.dataset.caseId, button.dataset.retryCase); return; }
  if (button.dataset.replyChat) { const c = state.caseDetail?.id === button.dataset.replyChat ? state.caseDetail : state.messages.flatMap(m => m.cases || []).reverse().find(c => c.id === button.dataset.replyChat); if (c?.id === button.dataset.replyChat && c.pending_question?.id) { state.replyCase = { id: c.id, question: c.pending_question }; state.caseDetail = null; render(); document.querySelector('#message-input')?.focus(); } return; }
  if (button.dataset.case) { await loadCase(button.dataset.case); return; }
  if (button.dataset.caseLink) { await loadCases(); await loadCase(button.dataset.caseLink); return; }
  switch (button.dataset.action) {
    case 'login': await login(); break;
    case 'leave-reply': state.replyCase = null; render(); document.querySelector('#message-input')?.focus(); break;
    case 'close-case': state.caseDetail = null; render(); document.querySelector('#message-input')?.focus(); break;
    case 'logout': button.disabled = true; try { await api('/api/session', { method: 'DELETE' }); clearSession(); render(); } catch (error) { toast(error.message); button.disabled = false; } break;
    case 'clear-selection': await resetConversation(false); break;
    case 'reset-chat': await resetConversation(); break;
    case 'reset-sandbox': openResetSandbox(); break;
    case 'refresh-transactions': button.disabled = true; await loadTransactions(); render(); announce(t('refreshDone')); break;
    case 'refresh-cases': { const id = state.caseDetail?.id; await loadCases(); if (id && state.user) await loadCase(id); else render(); break; }
    case 'refresh-analytics': await loadAnalytics(); render(); break;
    case 'refresh-evaluation': await loadEvaluation(); render(); break;
    case 'read-cases': await sendChat(state.language === 'pt' ? 'Quero consultar meus casos.' : 'Quiero consultar mis casos.'); break;
    case 'retry-chat': if (state.retry) await sendChat(state.retry.message, state.retry); break;
  }
});
root.addEventListener('submit', event => { if (event.target.id === 'chat-form') { event.preventDefault(); sendChat(new FormData(event.target).get('message') || ''); } if (event.target.id === 'resolution-form') { event.preventDefault(); event.target.elements.resolution.value = event.submitter?.value || 'needs_information'; event.target.querySelector('textarea').setCustomValidity(''); submitCaseAction(event.target, 'resolve'); } if (event.target.id === 'case-reply-form') { event.preventDefault(); submitCaseAction(event.target, 'reply'); } });
root.addEventListener('keydown', event => { if (event.target.id === 'message-input' && event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); event.target.form.requestSubmit(); } });
root.addEventListener('input', event => {
  if (!['case-question', 'case-reply'].includes(event.target.id)) return;
  event.target.setCustomValidity('');
  const id = event.target.form.dataset.caseId;
  if (state.caseDrafts[id]) state.caseDrafts[id][event.target.id === 'case-question' ? 'question' : 'reply'] = event.target.value;
});
root.addEventListener('input', event => { if (event.target.id === 'message-input') { state.draft = event.target.value; resizeComposer(event.target); } });
async function boot() {
  render();
  try {
    const data = await api('/api/session', { anonymous: true });
    if (Boolean(data.user?.role === 'analyst') !== reviewMode) { await login(); return; }
    applySession(data); await loadInitial();
    if (reviewMode && new URLSearchParams(location.search).get('view') === 'evaluation') { state.view = 'evaluation'; await loadEvaluation(); }
    state.booting = false; render();
  } catch { await login(); }
}
boot();
