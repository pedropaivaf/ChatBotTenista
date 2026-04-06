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
    const addMessage = (text, sender) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        const bubble = document.createElement('div');
        bubble.classList.add('bubble');
        const formattedText = text.replace(/\n/g, '<br>');
        bubble.innerHTML = formattedText;
        messageDiv.appendChild(bubble);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // Helper: cria elemento com texto seguro
    const createEl = (tag, className, text) => {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (text) el.textContent = text;
        return el;
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
            parser: '\uD83D\uDD0E', engine: '\u26A1', response: '\u2705', fail: '\u274C'
        };
        const delay = 130;

        steps.forEach((step, i) => {
            if (i > 0) {
                const conn = createEl('div', 'pipe-connector');
                conn.style.opacity = '0';
                setTimeout(() => { conn.style.opacity = '1'; conn.style.transition = 'opacity 0.3s'; }, i * delay);
                block.appendChild(conn);
            }

            const stepType = typeMap[step.name] || '';
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

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, session_id: sessionId })
            });

            const data = await response.json();
            addMessage(data.answer, 'bot');

            if (data.pipeline && data.pipeline.length > 0) {
                renderPipeline(data.pipeline);
            }

        } catch (error) {
            console.error('Erro:', error);
            addMessage('Ops, algo deu errado no servidor. Tente novamente.', 'bot');
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
