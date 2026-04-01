// Aguarda o carregamento completo do HTML (DOM) antes de executar o script
document.addEventListener('DOMContentLoaded', () => {
    // Referências aos elementos da interface do Chat (Input, Botão Enviar, Lista de Mensagens)
    const userInput = document.getElementById('user-input'); // Campo onde o usuário digita
    const sendBtn = document.getElementById('send-btn'); // Botão com ícone de bolinha para enviar
    const chatMessages = document.getElementById('chat-messages'); // Área que exibe o histórico de conversa

    // Gerenciamento de sessão para manter contexto entre mensagens
    let sessionId = sessionStorage.getItem('tennis_session_id');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        sessionStorage.setItem('tennis_session_id', sessionId);
    }

    // Referências aos elementos do Console/Terminal (Painel técnico lateral)
    const consoleToggleBtn = document.getElementById('console-toggle-btn'); // Botão que abre o terminal
    const consolePanel = document.getElementById('console-panel'); // O painel principal do terminal
    const consoleBody = document.getElementById('console-body'); // Área interna onde os logs aparecem
    const closeConsole = document.getElementById('close-console'); // Botão de fechar (X)
    const clearConsole = document.getElementById('clear-console'); // Botão de limpar (lixeira)

    /**
     * Função: addMessage
     * Objetivo: Adiciona visualmente um novo balão de mensagem na tela do chat.
     * @param {string} text - O conteúdo da mensagem (pode conter HTML para destaques).
     * @param {string} sender - Quem enviou ('user' para o usuário azul, 'bot' para o robô escuro).
     */
    const addMessage = (text, sender) => {
        const messageDiv = document.createElement('div'); // Cria o container da mensagem
        messageDiv.classList.add('message', sender); // Adiciona as classes CSS correspondentes
        
        const bubble = document.createElement('div'); // Cria o balão (bubble) interno
        bubble.classList.add('bubble'); // Adiciona a classe de estilo do balão
        
        // Converte as quebras de linha '\n' vindas do Python em tags HTML '<br>'
        // Isso é necessário porque estamos usando innerHTML para suportar os destaques CSS
        const formattedText = text.replace(/\n/g, '<br>');
        bubble.innerHTML = formattedText; // Define o conteúdo formatado
        
        messageDiv.appendChild(bubble); // Coloca o balão dentro do container da mensagem
        chatMessages.appendChild(messageDiv); // Insere a mensagem completa na lista do chat
        
        // Faz o scroll automático para a última mensagem enviada
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // Helper: cria elemento com texto seguro
    const createEl = (tag, className, text) => {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (text) el.textContent = text;
        return el;
    };

    /**
     * Renderiza o pipeline visual de processamento no painel lateral.
     * Cada step é um card animado com ícone de status, nome, detalhe e dados extras.
     */
    const renderPipeline = (steps) => {
        if (!steps || steps.length === 0) return;

        const welcome = consoleBody.querySelector('.pipeline-welcome');
        if (welcome) welcome.remove();

        const block = createEl('div', 'pipeline-block');
        const label = createEl('div', 'pb-label', `Processamento #${document.querySelectorAll('.pipeline-block').length + 1}`);
        block.appendChild(label);

        const statusIcons = { success: '✓', skipped: '○', fail: '✗' };
        // Map step name → type class for colors
        const typeMap = {
            'Entrada do Usuário': 'input', 'Tokenização NLTK': 'token',
            'Filtro Off-Topic': 'filter', 'Árvore de Decisão': 'tree',
            'Query Parser': 'parser', 'Motor de Dados': 'engine',
            'Base de Conhecimento': 'engine', 'Resposta Final': 'response', 'Fallback': 'fail'
        };
        const typeIcons = {
            input: '📝', token: '🔤', filter: '🛡️', tree: '🌳',
            parser: '🔍', engine: '⚡', response: '✅', fail: '❌'
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

            // Token pills para tokenização
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

            // Helper: create tree node with colored dot
            const addTreeNode = (container, color, label, value) => {
                const node = createEl('div', 'tree-node');
                node.appendChild(createEl('span', `tn-dot ${color}`));
                node.appendChild(createEl('span', 'tn-label', label + ': '));
                node.appendChild(createEl('span', 'tn-val', value));
                container.appendChild(node);
            };

            // Árvore de decisão expandível com bolinhas
            if (step.data && step.data.turn !== undefined) {
                // Botão toggle
                const toggle = createEl('button', 'tree-toggle');
                toggle.appendChild(createEl('span', 'arrow', '▶'));
                toggle.appendChild(document.createTextNode(' Ver Decisões'));
                body.appendChild(toggle);

                // Painel expandível
                const detail = createEl('div', 'tree-detail');
                addTreeNode(detail, 'blue', 'Turno', String(step.data.turn));
                addTreeNode(detail, step.data.topic ? 'green' : 'gray', 'Tópico', step.data.topic || 'nenhum');
                addTreeNode(detail, step.data.pending ? 'yellow' : 'gray', 'Pendente', step.data.pending || 'nenhum');
                addTreeNode(detail, step.data.focus ? 'green' : 'gray', 'Jogador em Foco', step.data.focus || 'nenhum');

                // Decisões tomadas
                const decLabel = createEl('div', 'ps-detail');
                decLabel.style.cssText = 'margin-top:6px;font-weight:700;color:#64748b;font-size:0.65rem;text-transform:uppercase;letter-spacing:1px';
                decLabel.textContent = 'Caminho da Decisão:';
                detail.appendChild(decLabel);

                if (step.data.pending) {
                    addTreeNode(detail, 'green', 'Contexto ativo', 'Tentando resolver via sessão');
                    addTreeNode(detail, step.status === 'success' ? 'green' : 'red',
                        'Resolução', step.status === 'success' ? 'Resolvido no contexto' : 'Sem match → pipeline normal');
                } else {
                    addTreeNode(detail, 'gray', 'Contexto', 'Primeira mensagem ou sem pendência');
                    addTreeNode(detail, 'yellow', 'Decisão', 'Seguir pipeline normal');
                }

                body.appendChild(detail);

                toggle.addEventListener('click', () => {
                    toggle.classList.toggle('expanded');
                    detail.classList.toggle('visible');
                });
            }

            if (step.name === 'Resposta Final' && step.data) {
                const badges = [];
                if (step.data.follow_up) badges.push(['Próximo', step.data.follow_up]);
                if (step.data.focus) badges.push(['Foco', step.data.focus]);
                if (badges.length) addBadges(body, badges);
            }

            if (step.data && step.data.country) {
                const badges = [['País', step.data.country]];
                if (step.data.best) badges.push(['Melhor', '✓']);
                if (step.data.current) badges.push(['Atual', '✓']);
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

    /**
     * Função: handleSend
     * Objetivo: Processa o envio da mensagem, chama a API e gerencia os estados de carregamento.
     */
    const handleSend = async () => {
        const message = userInput.value.trim(); // Captura o texto do input sem espaços sobrando
        if (!message) return; // Se estiver vazio, não faz nada

        addMessage(message, 'user'); // Exibe a mensagem do usuário imediatamente no chat
        userInput.value = ''; // Limpa o campo de texto

        try {
            // Requisição assíncrona para o servidor Flask
            const response = await fetch('/predict', {
                method: 'POST', // Método de envio de dados
                headers: { 'Content-Type': 'application/json' }, // Indica que os dados são JSON
                body: JSON.stringify({ message, session_id: sessionId }) // Envia mensagem + ID da sessão
            });

            // Converte a resposta bruta do servidor para objeto JS
            const data = await response.json();
            
            // Exibe a resposta do robô
            addMessage(data.answer, 'bot');

            // Renderiza o pipeline visual no painel lateral
            if (data.pipeline && data.pipeline.length > 0) {
                renderPipeline(data.pipeline);
            }

        } catch (error) {
            // Tratamento de erro caso o servidor esteja offline ou ocorra falha na rede
            console.error('Erro:', error);
            addMessage('Ops, algo deu errado no servidor. Tente novamente.', 'bot');
        }
    };

    // --- Controle do Modal de Integrantes (Group Members) ---
    
    // Referências aos elementos do modal
    const groupBtn = document.getElementById('group-btn'); // Botão "Integrantes do Grupo" no footer
    const groupModal = document.getElementById('group-modal'); // Overlay do modal (fundo escuro)
    const closeModal = document.getElementById('close-modal'); // Botão X dentro do modal

    /**
     * Função: toggleModal
     * Objetivo: Abre ou fecha a tela de integrantes adicionando a classe 'active'.
     */
    const toggleModal = () => {
        groupModal.classList.toggle('active'); // Alterna a visibilidade suave via CSS
        
        // Modal aberto/fechado
    };

    // Listeners para abrir e fechar o modal
    groupBtn.addEventListener('click', toggleModal); // Abre ao clicar no botão do footer
    closeModal.addEventListener('click', toggleModal); // Fecha ao clicar no X

    // Fecha o modal se o usuário clicar fora da caixa central (no fundo escuro)
    window.addEventListener('click', (e) => {
        if (e.target === groupModal) toggleModal();
    });

    // --- Controle do Console (Abre/Fecha/Limpa) ---
    
    // Função para alternar a visibilidade do painel lateral
    const toggleConsole = () => {
        consolePanel.classList.toggle('active'); // Adiciona/Remove a classe que anima a abertura
        document.body.classList.toggle('console-open'); // Classe auxiliar para layouts responsivos
    };

    // Listeners de clique para os botões do terminal
    consoleToggleBtn.addEventListener('click', toggleConsole); // Abrir pelo botão superior
    closeConsole.addEventListener('click', toggleConsole); // Fechar pelo X interno
    
    // Botão para limpar o pipeline visual
    clearConsole.addEventListener('click', () => {
        consoleBody.textContent = '';
        const welcome = createEl('div', 'pipeline-welcome');
        const icon = createEl('div', 'pw-icon', '🧠');
        const text = createEl('div', 'pw-text', 'Pipeline limpo. Envie uma mensagem para começar.');
        welcome.appendChild(icon);
        welcome.appendChild(text);
        consoleBody.appendChild(welcome);
    });

    // --- Monitoramento de Eventos (Teclado e Clique) ---
    
    // Dispara o envio ao clicar no ícone da bolinha
    sendBtn.addEventListener('click', handleSend);
    
    // Dispara o envio ao pressionar "Enter" dentro do campo de texto
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });

    // Atalho de teclado rápido: Ctrl + ` (Crase) para abrir o painel técnico
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && (e.key === '`' || e.key === '\'')) toggleConsole();
    });

    // Foca o cursor no campo de texto assim que o site carrega para facilitar o uso
    userInput.focus();
    
    // Pipeline pronto
});
