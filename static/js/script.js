document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    // Gerenciamento de sessao para manter contexto entre mensagens
    let sessionId = sessionStorage.getItem('tennis_session_id');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        sessionStorage.setItem('tennis_session_id', sessionId);
    }

    // Referencias aos elementos do Console/Terminal
    const consoleToggleBtn = document.getElementById('console-toggle-btn');
    const consolePanel = document.getElementById('console-panel');
    const consoleBody = document.getElementById('console-body');
    const closeConsole = document.getElementById('close-console');
    const clearConsole = document.getElementById('clear-console');

    // Adiciona mensagem ao chat
    // Nota: innerHTML usado intencionalmente para renderizar destaques HTML do backend (msg-highlight, attr-label, etc.)
    // O conteudo vem exclusivamente do servidor Flask (nao do usuario), portanto e seguro.
    const addMessage = (text, sender, meta = {}) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        const bubble = document.createElement('div');
        bubble.classList.add('bubble');

        // Resposta gerada pelo LLM (LM Studio) -> badge + identidade violeta
        if (meta.fromLLM) {
            bubble.classList.add('from-llm');
            const badge = document.createElement('div');
            badge.className = 'llm-badge';
            badge.appendChild(createEl('span', 'llm-core'));
            badge.appendChild(document.createTextNode('Gerado por IA · LM Studio'));
            if (meta.latency) badge.appendChild(createEl('span', 'llm-latency', meta.latency));
            bubble.appendChild(badge);
        }

        // Painel "modo pesquisa" (Claude/DeepSeek): acima da resposta, se a IA pesquisou.
        if (meta.search && meta.search.sources && meta.search.sources.length) {
            bubble.appendChild(buildSearchChatPanel(meta.search));
        }

        const content = document.createElement('div');
        if (sender === 'bot') {
            // Respostas do bot trazem HTML confiável do servidor (destaques, badges de jogador)
            content.innerHTML = text.replace(/\n/g, '<br>');
        } else {
            // Entrada do usuário -> texto puro (evita XSS de auto-injeção)
            content.textContent = text;
        }
        bubble.appendChild(content);

        messageDiv.appendChild(bubble);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    };

    // Helper: cria elemento com texto seguro
    const createEl = (tag, className, text) => {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (text) el.textContent = text;
        return el;
    };

    // Indicador de "pensando" enquanto o servidor responde. A base responde em
    // milissegundos; se passar de ~0,9s, é o LLM -> revela "consultando o modelo de IA".
    const showTyping = () => {
        const messageDiv = createEl('div', 'message bot');
        const bubble = createEl('div', 'bubble');
        const ind = createEl('div', 'typing-indicator');
        const dots = createEl('div', 'typing-dots');
        dots.appendChild(createEl('span'));
        dots.appendChild(createEl('span'));
        dots.appendChild(createEl('span'));
        ind.appendChild(dots);
        ind.appendChild(createEl('span', 'typing-label', 'consultando o modelo de IA…'));
        bubble.appendChild(ind);
        messageDiv.appendChild(bubble);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        const timer = setTimeout(() => ind.classList.add('consulting'), 900);
        return { messageDiv, timer };
    };

    // Constrói o "inspetor de API" da chamada ao LLM: requisição -> resposta -> métricas
    const buildLlmInspector = (llm) => {
        const card = createEl('div', 'llm-card');

        const head = createEl('div', 'llm-card-head');
        head.appendChild(createEl('span', 'llm-chip', 'LM Studio'));
        if (llm.request && llm.request.model) head.appendChild(createEl('span', 'llm-model', llm.request.model));
        card.appendChild(head);

        // Métricas (latência, tokens, tok/s)
        const stats = createEl('div', 'llm-stats');
        const addStat = (val, lbl) => {
            if (val === null || val === undefined || val === '') return;
            const s = createEl('div', 'llm-stat');
            s.appendChild(createEl('span', 'lst-val', String(val)));
            s.appendChild(createEl('span', 'lst-lbl', lbl));
            stats.appendChild(s);
        };
        if (llm.latency != null) addStat(llm.latency + 's', 'latência');
        const u = llm.usage || {};
        addStat(u.prompt_tokens, 'tokens in');
        addStat(u.completion_tokens, 'tokens out');
        if (llm.tokens_per_s != null) addStat(llm.tokens_per_s, 'tok/s');
        if (stats.children.length) card.appendChild(stats);

        // Requisição enviada (colapsável)
        if (llm.request) {
            const det = createEl('details', 'llm-details');
            const sum = createEl('summary', 'llm-sec-title');
            sum.textContent = '📤 Requisição enviada';
            det.appendChild(sum);
            det.appendChild(createEl('div', 'llm-endpoint',
                (llm.request.method || 'POST') + ' ' + (llm.request.endpoint || '')));
            const params = createEl('div', 'llm-params');
            if (llm.request.temperature != null) params.appendChild(createEl('span', 'llm-param', 'temperature ' + llm.request.temperature));
            if (llm.request.max_tokens != null) params.appendChild(createEl('span', 'llm-param', 'max_tokens ' + llm.request.max_tokens));
            params.appendChild(createEl('span', 'llm-param', 'stream false'));
            det.appendChild(params);
            (llm.request.messages || []).forEach((m) => {
                const msg = createEl('div', 'llm-msg');
                msg.appendChild(createEl('span', 'llm-role llm-role-' + m.role, m.role));
                msg.appendChild(createEl('div', 'llm-msg-text', m.content || ''));
                det.appendChild(msg);
            });
            card.appendChild(det);
        }

        // Resposta retornada
        const resp = createEl('div', 'llm-resp');
        resp.appendChild(createEl('div', 'llm-sec-title', '📥 Resposta retornada'));
        resp.appendChild(createEl('div', 'llm-resp-text', llm.answer || ''));
        if (llm.finish_reason) resp.appendChild(createEl('div', 'llm-finish', 'finish_reason: ' + llm.finish_reason));
        card.appendChild(resp);

        return card;
    };

    // Constrói o painel "MODO PESQUISA": mostra o que a IA buscou e as fontes que leu
    // (Wikipedia/DuckDuckGo), com título clicável e o trecho lido — estilo Claude/DeepSeek.
    const buildSearchInspector = (search) => {
        const card = createEl('div', 'search-card');

        const head = createEl('div', 'search-card-head');
        const chip = createEl('span', 'search-chip');
        chip.appendChild(createEl('span', 'search-spin'));      // anel girando (efeito "pesquisando")
        chip.appendChild(createEl('span', null, '🔎 Pesquisa na web'));
        head.appendChild(chip);
        const n = (search.sources || []).length;
        head.appendChild(createEl('span', 'search-count', n + (n === 1 ? ' fonte' : ' fontes')));
        card.appendChild(head);

        if (search.query) {
            const q = createEl('div', 'search-query');
            q.appendChild(createEl('span', 'search-query-label', 'buscou por'));
            q.appendChild(createEl('span', 'search-query-text', '“' + search.query + '”'));
            card.appendChild(q);
        }

        const det = createEl('details', 'search-details');
        det.open = true;
        const sum = createEl('summary', 'search-sec-title');
        sum.textContent = '📄 Fontes consultadas';
        det.appendChild(sum);

        (search.sources || []).forEach((s, i) => {
            const row = createEl('a', 'search-source');
            if (s.url) { row.href = s.url; row.target = '_blank'; row.rel = 'noopener noreferrer'; }
            const eng = (s.engine || '').toLowerCase().indexOf('wiki') >= 0 ? 'wiki' : 'ddg';
            const top = createEl('div', 'search-source-top');
            top.appendChild(createEl('span', 'search-engine se-' + eng, s.engine || 'web'));
            top.appendChild(createEl('span', 'search-source-title', s.title || s.url || ''));
            row.appendChild(top);
            if (s.snippet) row.appendChild(createEl('div', 'search-snippet', s.snippet));
            // Revela as fontes em cascata (sensação de "lendo as fontes")
            row.style.opacity = '0'; row.style.transform = 'translateY(4px)';
            setTimeout(() => {
                row.style.transition = 'all 0.3s ease';
                row.style.opacity = '1'; row.style.transform = 'translateY(0)';
            }, 140 + i * 120);
            det.appendChild(row);
        });
        card.appendChild(det);
        return card;
    };

    // Painel "modo pesquisa" DENTRO DO CHAT (estilo Claude/DeepSeek): colapsável acima da
    // resposta — "🔎 Pesquisou na web · N fontes ▾" que expande para ver o que a IA leu.
    const buildSearchChatPanel = (search) => {
        const det = createEl('details', 'search-chat');
        const sum = createEl('summary', 'search-chat-sum');
        sum.appendChild(createEl('span', 'search-chat-title', '🔎 Pesquisou na web'));
        const n = (search.sources || []).length;
        sum.appendChild(createEl('span', 'search-chat-count', '· ' + n + (n === 1 ? ' fonte' : ' fontes')));
        det.appendChild(sum);

        const wrap = createEl('div', 'search-chat-body');
        if (search.query) {
            const q = createEl('div', 'search-query');
            q.appendChild(createEl('span', 'search-query-label', 'buscou por'));
            q.appendChild(createEl('span', 'search-query-text', '“' + search.query + '”'));
            wrap.appendChild(q);
        }
        (search.sources || []).forEach((s) => {
            const row = createEl('a', 'search-source');
            if (s.url) { row.href = s.url; row.target = '_blank'; row.rel = 'noopener noreferrer'; }
            const eng = (s.engine || '').toLowerCase().indexOf('wiki') >= 0 ? 'wiki' : 'ddg';
            const top = createEl('div', 'search-source-top');
            top.appendChild(createEl('span', 'search-engine se-' + eng, s.engine || 'web'));
            top.appendChild(createEl('span', 'search-source-title', s.title || s.url || ''));
            row.appendChild(top);
            if (s.snippet) row.appendChild(createEl('div', 'search-snippet', s.snippet));
            wrap.appendChild(row);
        });
        det.appendChild(wrap);
        return det;
    };

    // Renderiza o pipeline visual de processamento no painel lateral
    const renderPipeline = (steps) => {
        if (!steps || steps.length === 0) return;

        const welcome = consoleBody.querySelector('.pipeline-welcome');
        if (welcome) welcome.remove();

        const block = createEl('div', 'pipeline-block');
        const label = createEl('div', 'pb-label', `Processamento #${document.querySelectorAll('.pipeline-block').length + 1}`);
        block.appendChild(label);

        const statusIcons = { success: '\u2714', skipped: '\u25CB', fail: '\u2718' };
        const typeMap = {
            'Entrada do Usu\u00E1rio': 'input', 'Tokeniza\u00E7\u00E3o NLTK': 'token',
            'Filtro Off-Topic': 'filter', '\u00C1rvore de Decis\u00E3o': 'tree',
            'Query Parser': 'parser', 'Motor de Dados': 'engine',
            'Base de Conhecimento': 'engine', 'Resposta Final': 'response', 'Fallback': 'fail'
        };
        const typeIcons = {
            input: '\uD83D\uDD0D', token: '\uD83D\uDD24', filter: '\uD83D\uDEE1\uFE0F', tree: '\uD83C\uDF33',
            parser: '\uD83D\uDD0E', engine: '\u26A1', response: '\u2705', fail: '\u274C',
            llm: '\uD83E\uDD16'
        };
        const delay = 130;

        steps.forEach((step, i) => {
            if (i > 0) {
                const conn = createEl('div', 'pipe-connector');
                conn.style.opacity = '0';
                setTimeout(() => { conn.style.opacity = '1'; conn.style.transition = 'opacity 0.3s'; }, i * delay);
                block.appendChild(conn);
            }

            const stepType = typeMap[step.name] || (/LLM/i.test(step.name) ? 'llm' : '');
            const el = createEl('div', `pipeline-step ps-${step.status} ps-type-${stepType}`);
            el.style.opacity = '0';
            el.style.transform = 'translateX(-10px)';

            const iconText = typeIcons[stepType] || statusIcons[step.status] || '?';
            const icon = createEl('div', 'ps-icon', iconText);
            const body = createEl('div', 'ps-body');
            body.appendChild(createEl('div', 'ps-name', step.name));
            if (step.detail) body.appendChild(createEl('div', 'ps-detail', step.detail));

            // Token pills
            if (step.data && step.data.tokens && step.data.stems) {
                const row = createEl('div', 'token-row');
                step.data.tokens.forEach((tok, j) => {
                    const pill = createEl('span', 'token-pill');
                    pill.appendChild(createEl('span', 'tp-word', tok));
                    pill.appendChild(createEl('span', 'tp-stem', step.data.stems[j] || tok));
                    row.appendChild(pill);
                });
                body.appendChild(row);
            }

            // Helper: add badge row
            const addBadges = (container, badges) => {
                const wrap = createEl('div');
                wrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px;margin-top:4px';
                badges.forEach(([lbl, val]) => {
                    const badge = createEl('span', 'session-badge', lbl + ' ');
                    badge.appendChild(createEl('span', 'sb-val', val));
                    wrap.appendChild(badge);
                });
                container.appendChild(wrap);
            };

            // Arvore de decisao - fluxograma visual com branches
            if (step.data && step.data.turn !== undefined) {
                const stateBadges = [['Turno', String(step.data.turn)]];
                if (step.data.pending) stateBadges.push(['Pendente', step.data.pending]);
                if (step.data.focus) stateBadges.push(['Foco', step.data.focus]);
                if (step.data.topic) stateBadges.push(['T\u00F3pico', step.data.topic]);
                addBadges(body, stateBadges);

                if (step.data.trace && step.data.trace.length > 0) {
                    const flowChart = createEl('div', 'tree-flow');
                    step.data.trace.forEach((node, ni) => {
                        const branch = createEl('div', `tree-branch ${node.matched ? 'tb-matched' : 'tb-missed'}`);
                        const header = createEl('div', 'tb-header');
                        header.appendChild(createEl('span', 'tb-icon', node.icon || ''));
                        header.appendChild(createEl('span', 'tb-name', node.branch));
                        header.appendChild(createEl('span', `tb-status ${node.matched ? 'tb-yes' : 'tb-no'}`, node.matched ? '\u2714' : '\u2718'));
                        branch.appendChild(header);
                        if (node.detail) {
                            branch.appendChild(createEl('div', 'tb-detail', node.detail));
                        }
                        flowChart.appendChild(branch);
                        if (ni < step.data.trace.length - 1) {
                            flowChart.appendChild(createEl('div', 'tb-connector'));
                        }
                    });
                    body.appendChild(flowChart);
                }
            }

            if (step.name === 'Resposta Final' && step.data) {
                const badges = [];
                if (step.data.follow_up) badges.push(['Pr\u00F3ximo', step.data.follow_up]);
                if (step.data.focus) badges.push(['Foco', step.data.focus]);
                if (badges.length) addBadges(body, badges);
            }

            if (step.data && step.data.country) {
                const badges = [['Pa\u00EDs', step.data.country]];
                if (step.data.best) badges.push(['Melhor', '\u2714']);
                if (step.data.current) badges.push(['Atual', '\u2714']);
                if (step.data.circuit) badges.push(['Circuito', step.data.circuit]);
                addBadges(body, badges);
            }

            // Painel "modo pesquisa": fontes que a IA consultou (Wikipedia/DuckDuckGo)
            if (step.data && step.data.search) {
                body.appendChild(buildSearchInspector(step.data.search));
            }

            // Inspetor do LLM: requisi\u00E7\u00E3o enviada -> resposta -> m\u00E9tricas do LM Studio
            if (step.data && step.data.llm) {
                body.appendChild(buildLlmInspector(step.data.llm));
            }

            el.appendChild(icon);
            el.appendChild(body);

            setTimeout(() => {
                el.style.transition = 'all 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                el.style.opacity = '1';
                el.style.transform = 'translateX(0)';
            }, i * delay);

            block.appendChild(el);
        });

        consoleBody.appendChild(block);
        const sep = createEl('div');
        sep.style.cssText = 'height:1px;background:#1e293b;margin:12px 0';
        consoleBody.appendChild(sep);
        setTimeout(() => { consoleBody.scrollTop = consoleBody.scrollHeight; }, steps.length * delay + 100);
    };

    // Envia mensagem e processa resposta
    const handleSend = async () => {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        userInput.value = '';
        userInput.disabled = true;
        sendBtn.disabled = true;

        // Animação de "saque" na bolinha de envio
        sendBtn.classList.add('serving');
        setTimeout(() => sendBtn.classList.remove('serving'), 500);

        const typing = showTyping();

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, session_id: sessionId })
            });

            const data = await response.json();

            clearTimeout(typing.timer);
            typing.messageDiv.remove();

            // Detecta se a resposta veio do LLM (passo "LLM · LM Studio" com sucesso)
            const llmStep = Array.isArray(data.pipeline)
                ? data.pipeline.find(s => /LLM/i.test(s.name) && s.status === 'success')
                : null;
            let latency = '';
            if (llmStep && llmStep.detail) {
                const m = llmStep.detail.match(/([\d]+[.,]?[\d]*)\s*s/);
                if (m) latency = m[1].replace(',', '.') + 's';
            }

            // Fontes da pesquisa web (para o painel "modo pesquisa" no chat)
            const searchStep = Array.isArray(data.pipeline)
                ? data.pipeline.find(s => s.data && s.data.search)
                : null;
            const searchMeta = searchStep ? searchStep.data.search : null;

            addMessage(data.answer, 'bot', { fromLLM: !!llmStep, latency, search: searchMeta });

            if (data.pipeline && data.pipeline.length > 0) {
                renderPipeline(data.pipeline);
            }

        } catch (error) {
            console.error('Erro:', error);
            clearTimeout(typing.timer);
            typing.messageDiv.remove();
            addMessage('Ops, algo deu errado no servidor. Tente novamente.', 'bot');
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
        }
    };

    // --- Controle do Modal de Integrantes ---
    const groupBtn = document.getElementById('group-btn');
    const groupModal = document.getElementById('group-modal');
    const closeModal = document.getElementById('close-modal');

    const toggleModal = () => {
        groupModal.classList.toggle('active');
    };

    groupBtn.addEventListener('click', toggleModal);
    closeModal.addEventListener('click', toggleModal);

    window.addEventListener('click', (e) => {
        if (e.target === groupModal) toggleModal();
    });

    // --- Controle do Console (Abre/Fecha/Limpa) ---
    const toggleConsole = () => {
        consolePanel.classList.toggle('active');
        document.body.classList.toggle('console-open');
    };

    consoleToggleBtn.addEventListener('click', toggleConsole);
    closeConsole.addEventListener('click', toggleConsole);

    clearConsole.addEventListener('click', () => {
        consoleBody.textContent = '';
        const welcome = createEl('div', 'pipeline-welcome');
        const icon = createEl('div', 'pw-icon', '\uD83E\uDDE0');
        const text = createEl('div', 'pw-text', 'Pipeline limpo. Envie uma mensagem para come\u00E7ar.');
        welcome.appendChild(icon);
        welcome.appendChild(text);
        consoleBody.appendChild(welcome);
    });

    // --- Eventos de Envio ---
    sendBtn.addEventListener('click', handleSend);

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });

    // Atalho: Ctrl + ` para abrir o painel
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && (e.key === '`' || e.key === '\'')) toggleConsole();
    });

    // --- Modo Apresentacao (Fullscreen + Fontes Grandes) ---
    const fullscreenBtn = document.getElementById('fullscreen-btn');

    const togglePresentation = () => {
        document.body.classList.toggle('presentation-mode');

        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(() => {});
        } else {
            document.exitFullscreen().catch(() => {});
        }
    };

    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', togglePresentation);
    }

    // F11 tambem ativa o modo apresentacao
    document.addEventListener('keydown', (e) => {
        if (e.key === 'F11') {
            e.preventDefault();
            togglePresentation();
        }
    });

    // Sincroniza quando o usuario sai do fullscreen pelo ESC
    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement && document.body.classList.contains('presentation-mode')) {
            document.body.classList.remove('presentation-mode');
        }
    });

    userInput.focus();
});
