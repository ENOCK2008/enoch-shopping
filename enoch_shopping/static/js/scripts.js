// Register the service worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/js/serviceworker.js')
    .then(function(registration) {
        console.log('Service Worker registered with scope:', registration.scope);
    })
    .catch(function(error) {
        console.error('Service Worker registration failed:', error);
    });
}

// Ensure room_name is being passed correctly
const roomName = "{{ room_name }}"; 
const socket = new WebSocket('ws://' + window.location.host + '/ws/chat/general/');
let reconnectAttempts = 0;

function updateStatus(message) {
    const statusElement = document.querySelector('#status');
    if (statusElement) {
        statusElement.textContent = message;
    } else {
        console.warn('Status element not found');
    }
}

function connectWebSocket() {
    chatSocket.onopen = function(e) {
        console.log('WebSocket connection established');
        reconnectAttempts = 0;
        updateStatus('Connected');
    };

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log('Message received:', data); // Log received messages

        const messageElement = document.createElement('div');
        const messageTime = new Date().toLocaleTimeString();

        // Assign class based on whether the message is from a bot or user
        messageElement.className = data.is_bot ? 'message bot' : 'message user';
        messageElement.innerHTML = `<strong>[${messageTime}]</strong> ${data.message}`;
        
        const chatLog = document.querySelector('#chat-log');
        if (chatLog) {
            chatLog.appendChild(messageElement);
            chatLog.scrollTop = chatLog.scrollHeight; // Scroll to bottom
        } else {
            console.warn('#chat-log element not found');
        }
    };

    chatSocket.onerror = function(e) {
        console.error('WebSocket error:', e);
        updateStatus('Connection error. Attempting to reconnect...');
    };

    chatSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly', e);
        reconnectAttempts++;
        const waitTime = Math.min(10000, 1000 * Math.pow(2, reconnectAttempts)); // Exponential backoff for reconnecting
        updateStatus(`Disconnected. Reconnecting in ${waitTime / 1000} seconds...`);
        setTimeout(connectWebSocket, waitTime); // Reconnect after waitTime
    };
}

// Initial connection
connectWebSocket();

// Send a message when the form is submitted
document.querySelector('#chat-message-submit').onclick = function(e) {
    const messageInput = document.querySelector('#chat-message-input');
    const message = messageInput.value.trim();

    const MAX_MESSAGE_LENGTH = 200; // Set your desired max message length

    if (message && message.length <= MAX_MESSAGE_LENGTH) {
        if (chatSocket.readyState === WebSocket.OPEN) {
            console.log('Sending message:', message); // Log the message being sent
            chatSocket.send(JSON.stringify({ 'message': message }));
            messageInput.value = ''; // Clear input after sending
        } else {
            console.error('WebSocket is not open. Current state:', chatSocket.readyState);
        }
    } else {
        alert(`Message must be under ${MAX_MESSAGE_LENGTH} characters.`);
    }
};

// Send message on 'Enter' key press
document.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        document.querySelector('#chat-message-submit').click();
    }
});
