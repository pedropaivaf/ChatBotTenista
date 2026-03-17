// Aguarda o carregamento completo do HTML (DOM) antes de executar o script
document.addEventListener('DOMContentLoaded', () => {
    // Referências aos elementos da interface do Chat (Input, Botão Enviar, Lista de Mensagens)
    const userInput = document.getElementById('user-input'); // Campo onde o usuário digita
    const sendBtn = document.getElementById('send-btn'); // Botão com ícone de bolinha para enviar
    const chatMessages = document.getElementById('chat-messages'); // Área que exibe o histórico de conversa
    
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
        bubble.innerHTML = text; // Define o conteúdo (innerHTML permite renderizar os spans de destaque)
        
        messageDiv.appendChild(bubble); // Coloca o balão dentro do container da mensagem
        chatMessages.appendChild(messageDiv); // Insere a mensagem completa na lista do chat
        
        // Faz o scroll automático para a última mensagem enviada
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    /**
     * Função: addLog
     * Objetivo: Adiciona uma linha de registro técnico no console/terminal.
     * @param {string} message - O texto bruto recebido do backend/frontend.
     */
    const addLog = (message) => {
        const logEntry = document.createElement('div'); // Cria o elemento da linha de log
        logEntry.classList.add('log-entry'); // Adiciona a classe base de log
        
        // Lógica de coloração baseada em níveis de severidade/tipo
        if (message.includes('[SYSTEM]')) logEntry.classList.add('system'); // Status do sistema (Azul)
        else if (message.includes('[DEBUG]')) logEntry.classList.add('DEBUG'); // Informação técnica (Cinza)
        else if (message.includes('[WARNING]')) logEntry.classList.add('WARNING'); // Alertas de contexto (Amarelo)
        else if (message.includes('[ERROR]')) logEntry.classList.add('ERROR'); // Erros críticos (Vermelho)
        else if (message.includes('[SUCCESS]')) logEntry.classList.add('SUCCESS'); // Identificações positivas (Verde)
        else logEntry.classList.add('INFO'); // Informação geral (Padrão)

        // Processamento visual do texto do log para destacar porcentagens e nomes técnicos
        let processedMessage = message;

        // 1. Regex para identificar porcentagens (Ex: 88.9%) e aplicar cores dinâmicas
        processedMessage = processedMessage.replace(/(\d+(\.\d+)?%)/g, (match) => {
            const percentage = parseFloat(match);
            let className = 'match-low'; // Padrão: Baixa confiança
            if (percentage >= 80) className = 'match-high'; // Alta confiança (Verde)
            else if (percentage >= 50) className = 'match-mid'; // Média confiança (Amarelo)
            return `<span class="${className}">${match}</span>`;
        });

        // 2. Regex para identificar tags identificadas pelo NLTK (Ex: tag: djokovic)
        processedMessage = processedMessage.replace(/(tag:\s+)(\w+)/gi, (match, p1, p2) => {
            return `${p1}<span class="match-tag">${p2}</span>`; // Aplica fundo azul e bordas arredondadas
        });

        logEntry.innerHTML = processedMessage; // Aplica o texto formatado no elemento
        consoleBody.appendChild(logEntry); // Insere o log no corpo do terminal
        
        // Scroll automático para o final dos logs
        consoleBody.scrollTop = consoleBody.scrollHeight;
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
        addLog(`>> Comando enviado: ${message}`); // Registra a ação no terminal

        try {
            // Requisição assíncrona para o servidor Flask
            const response = await fetch('/predict', {
                method: 'POST', // Método de envio de dados
                headers: { 'Content-Type': 'application/json' }, // Indica que os dados são JSON
                body: JSON.stringify({ message }) // Converte o objeto JS para string JSON
            });

            // Converte a resposta bruta do servidor para objeto JS
            const data = await response.json();
            
            // Exibe a resposta do robô (com os novos destaques CSS .msg-highlight)
            addMessage(data.answer, 'bot');

            // Percorre a lista de logs técnicos enviados pelo backend e os exibe no terminal
            if (data.logs && data.logs.length > 0) {
                data.logs.forEach(log => addLog(log));
            }

        } catch (error) {
            // Tratamento de erro caso o servidor esteja offline ou ocorra falha na rede
            console.error('Erro:', error);
            addLog(`[ERROR] Falha na comunicação com o servidor: ${error.message}`);
            addMessage('Ops, algo deu errado no servidor. Tente novamente.', 'bot');
        }
    };

    // --- Controle do Console (Abre/Fecha/Limpa) ---
    
    // Função para alternar a visibilidade do painel lateral
    const toggleConsole = () => {
        consolePanel.classList.toggle('active'); // Adiciona/Remove a classe que anima a abertura
        document.body.classList.toggle('console-open'); // Classe auxiliar para layouts responsivos
    };

    // Listeners de clique para os botões do terminal
    consoleToggleBtn.addEventListener('click', toggleConsole); // Abrir pelo botão superior
    closeConsole.addEventListener('click', toggleConsole); // Fechar pelo X interno
    
    // Botão de "Lixo" para limpar o histórico de logs
    clearConsole.addEventListener('click', () => {
        consoleBody.innerHTML = '<div class="log-entry system">> Console limpo. Pronto para novos logs...</div>';
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
    
    // Log inicial para confirmar que o sistema está em prontidão
    addLog("[SYSTEM] Frontend conectado ao backend com sucesso.");
});
