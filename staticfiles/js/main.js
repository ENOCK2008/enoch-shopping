const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const chatSocket = new WebSocket(protocol + window.location.host + '/ws/chat/general/');

chatSocket.onopen = function(e) {
    console.log('WebSocket connection established.');
};

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    chatLog.innerHTML += '<div>' + data.message + '</div>';
};

chatSocket.onerror = function(e) {
    console.error('WebSocket error:', e);
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

chatMessageSubmit.onclick = function(e) {
    const message = chatMessageInput.value;
    chatSocket.send(JSON.stringify({
        'message': message
    }));
    chatMessageInput.value = '';
};

chatMessageInput.onkeyup = function(e) {
    if (e.keyCode === 13) {  // Enter key
        chatMessageSubmit.click();
    }
};
