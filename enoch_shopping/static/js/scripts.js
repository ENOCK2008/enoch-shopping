const roomName = "{{ room_name }}"; // Ensure room_name is being passed correctly
const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + encodeURIComponent(roomName) + '/'
);
let reconnectAttempts = 0;

function updateStatus(message) {
    const statusElement = document.querySelector('#status');
    statusElement.textContent = message;
}

function connectWebSocket() {
    chatSocket.onopen = function(e) {
        console.log('WebSocket connection established');
        reconnectAttempts = 0;
        updateStatus('Connected');
    };

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const messageElement = document.createElement('div');
        const messageTime = new Date().toLocaleTimeString();

        // Assign class based on whether the message is from a bot or user
        messageElement.className = data.is_bot ? 'message bot' : 'message user';
        messageElement.innerHTML = `<strong>[${messageTime}]</strong> ${data.message}`;
        
        document.querySelector('#chat-log').appendChild(messageElement);
        document.querySelector('#chat-log').scrollTop = document.querySelector('#chat-log').scrollHeight;
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
