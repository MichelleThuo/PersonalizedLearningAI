// Chatbot interaction logic
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const chatContainer = document.getElementById('chat-container');
    const courseSelect = document.getElementById('course-select');
    let sessionId = null;
    let userId = chatContainer.dataset.userId || 1;
    
    // Function to add a message to the chat
    function addMessage(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user-message' : 'message assistant-message';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        // Process message text to handle markdown-like formatting
        let processedMessage = message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
            .replace(/\_(.*?)\_/g, '<em>$1</em>')  // Italic
            .replace(/`(.*?)`/g, '<code>$1</code>')  // Code
            .replace(/\n/g, '<br>');  // Line breaks
        
        // Handle links
        processedMessage = processedMessage.replace(
            /\[([^\]]+)\]\(([^)]+)\)/g, 
            '<a href="$2" target="_blank">$1</a>'
        );
        
        content.innerHTML = processedMessage;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to show loading state
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant-message loading';
        loadingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return loadingDiv;
    }
    
    // Function to hide loading state
    function hideLoading(loadingElement) {
        if (loadingElement && loadingElement.parentNode) {
            loadingElement.parentNode.removeChild(loadingElement);
        }
    }
    
    // Function to handle chat form submission
    function handleChatSubmit(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, true);
        
        // Clear input
        messageInput.value = '';
        
        // Show loading indicator
        const loadingIndicator = showLoading();
        
        // Get course ID if selected
        const courseId = courseSelect ? courseSelect.value : null;
        
        // Send message to backend
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
                user_id: userId,
                course_id: courseId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            hideLoading(loadingIndicator);
            
            // Add AI response to chat
            addMessage(data.response, false);
            
            // Store session ID for future messages
            sessionId = data.session_id;
        })
        .catch(error => {
            // Hide loading indicator
            hideLoading(loadingIndicator);
            
            // Show error message
            addMessage("I'm sorry, I encountered an error while processing your request. Please try again later.", false);
            console.error('Error sending message:', error);
        });
    }
    
    // Handle chat form submission
    if (chatForm) {
        chatForm.addEventListener('submit', handleChatSubmit);
    }
    
    // Add welcome message
    addMessage("Hello! I'm your AI learning assistant. How can I help you today?", false);
});
