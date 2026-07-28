const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatHistory = document.getElementById('chat-history');
const logContainer = document.getElementById('log-container');
const statusIndicator = document.getElementById('status-indicator');

let isGenerating = false;

function appendMessage(content, isUser = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Convert newlines to br for simple formatting
    bubble.innerHTML = content.replace(/\n/g, '<br>');
    
    msgDiv.appendChild(bubble);
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function appendLog(content, type) {
    const logDiv = document.createElement('div');
    logDiv.className = `log-entry ${type}`;
    logDiv.innerText = content;
    logContainer.appendChild(logDiv);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function showTypingIndicator() {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai-message';
    msgDiv.id = 'typing-indicator-msg';
    
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.style.display = 'flex';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    
    msgDiv.appendChild(indicator);
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator-msg');
    if (indicator) {
        indicator.remove();
    }
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (isGenerating) return;
    
    const query = userInput.value.trim();
    if (!query) return;
    
    // UI Updates
    userInput.value = '';
    appendMessage(query, true);
    appendLog(`[USER]: ${query}`, 'system-msg');
    showTypingIndicator();
    
    isGenerating = true;
    statusIndicator.classList.add('thinking');
    
    try {
        // SSE Connection
        const url = `/api/chat?q=${encodeURIComponent(query)}`;
        const eventSource = new EventSource(url);
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            switch(data.type) {
                case 'step_start':
                    appendLog(data.content, 'step-start');
                    break;
                case 'llm_output':
                    appendLog(data.content, 'thought');
                    break;
                case 'tool_call':
                    appendLog(`Action: ${data.tool_name} [${data.args}]`, 'tool-call');
                    break;
                case 'observation':
                    appendLog(data.content, 'observation');
                    break;
                case 'error':
                    appendLog(data.content, 'error');
                    break;
                case 'crisis':
                    appendLog(data.content, 'error');
                    break;
                case 'final_answer':
                    removeTypingIndicator();
                    appendMessage(data.content, false);
                    appendLog("✅ Agent đã đưa ra câu trả lời.", "system-msg");
                    eventSource.close();
                    isGenerating = false;
                    statusIndicator.classList.remove('thinking');
                    break;
            }
        };
        
        eventSource.onerror = function(err) {
            console.error("EventSource failed:", err);
            removeTypingIndicator();
            appendLog("Lỗi kết nối đứt gãy.", "error");
            eventSource.close();
            isGenerating = false;
            statusIndicator.classList.remove('thinking');
        };
        
    } catch (error) {
        removeTypingIndicator();
        appendMessage("Đã có lỗi xảy ra khi kết nối máy chủ.", false);
        isGenerating = false;
        statusIndicator.classList.remove('thinking');
    }
});
