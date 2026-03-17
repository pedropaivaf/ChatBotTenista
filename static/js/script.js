document.addEventListener('DOMContentLoaded', () => { // Aguarda todo o conteúdo da página carregar antes de rodar o script
    const userInput = document.getElementById('user-input'); // Seleciona o campo de texto onde o usuário digita
    const sendBtn = document.getElementById('send-btn'); // Seleciona o botão de enviar mensagem
    const chatMessages = document.getElementById('chat-messages'); // Seleciona a área onde as mensagens aparecem

    const addMessage = (text, sender) => { // Função para criar e adicionar uma mensagem na tela
        const messageDiv = document.createElement('div'); // Cria um novo elemento <div> para a mensagem
        messageDiv.classList.add('message', sender); // Adiciona as classes CSS conforme o autor (usuário ou robô)
        
        const bubble = document.createElement('div'); // Cria o balão de fala da mensagem
        bubble.classList.add('bubble'); // Adiciona a classe de estilo do balão
        bubble.textContent = text; // Insere o texto da mensagem dentro do balão
        
        messageDiv.appendChild(bubble); // Coloca o balão dentro do contêiner da mensagem
        chatMessages.appendChild(messageDiv); // Coloca a mensagem completa dentro da área de chat da página
        
        // Faz o chat rolar automaticamente para baixo sempre que uma nova mensagem chega
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const handleSend = async () => { // Função que envia a mensagem para o servidor Python
        const message = userInput.value.trim(); // Pega o texto digitado e remove espaços inúteis no início e fim
        if (!message) return; // Se o campo estiver vazio, não faz nada e interrompe o envio

        addMessage(message, 'user'); // Mostra a mensagem do usuário na tela imediatamente
        userInput.value = ''; // Limpa o campo de texto para a próxima mensagem

        try { // Bloco de tentativa de comunicação com o servidor
            const response = await fetch('/predict', { // Faz uma requisição para a rota /predict do nosso servidor Flask
                method: 'POST', // Define que estamos enviando dados (POST)
                headers: {
                    'Content-Type': 'application/json' // Avisa ao servidor que estamos enviando um arquivo JSON
                },
                body: JSON.stringify({ message }) // Converte o texto da mensagem para o formato JSON
            });

            const data = await response.json(); // Aguarda a resposta do servidor e converte de volta do JSON
            addMessage(data.answer, 'bot'); // Mostra a resposta do chatbot na tela
        } catch (error) { // Caso ocorra algum erro na comunicação (como o servidor estar desligado)
            console.error('Erro ao enviar mensagem:', error); // Mostra o erro no console do navegador para o desenvolvedor
            addMessage('Ops, algo deu errado. Tente novamente mais tarde.', 'bot'); // Avisa o usuário que houve um problema
        }
    };

    sendBtn.addEventListener('click', handleSend); // Configura o botão de enviar para rodar a função handleSend ao ser clicado

    userInput.addEventListener('keypress', (e) => { // Configura o campo de texto para ouvir as teclas pressionadas
        if (e.key === 'Enter') { // Se a tecla pressionada for o 'Enter'
            handleSend(); // Chama a função de enviar a mensagem automaticamente
        }
    });

    // Foca o cursor automaticamente na caixa de texto assim que a página abre, facilitando o início do chat
    userInput.focus();
});
