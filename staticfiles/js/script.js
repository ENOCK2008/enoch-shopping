let chatSocket; // Ensure this is declared only once.
        let roomName = "{{ room_name }}"; 
        let userTypingTimeout;

        function registerServiceWorker() {
            if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                    navigator.serviceWorker.register('{% static "js/serviceworker.js" %}').then(function(registration) {
                        console.log('Service Worker registered with scope:', registration.scope);
                    }).catch(function(error) {
                        console.error('Service Worker registration failed:', error);
                    });
                });
            }
        }

        function updateStatus(message) {
            const statusElement = document.querySelector('#status');
            if (statusElement) {
                statusElement.textContent = message;
            }
        }

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            chatSocket = new WebSocket(protocol + '127.0.0.1:8001/ws/chat/' + encodeURIComponent(roomName) + '/');

            chatSocket.onopen = function() {
                console.log('WebSocket connection established');
                updateStatus('Connected to room: ' + roomName);
            };

            chatSocket.onmessage = function(e) {
                const data = JSON.parse(e.data);
                handleIncomingMessage(data);
            };

            chatSocket.onerror = function(e) {
                console.error('WebSocket error:', e);
                updateStatus('Connection error. Attempting to reconnect...');
            };

            chatSocket.onclose = function(e) {
                console.error('Chat socket closed unexpectedly', e);
                updateStatus('Disconnected. Attempting to reconnect...');
                setTimeout(connectWebSocket, 2000); 
            };
        }

        function handleIncomingMessage(data) {
            if (data.is_typing !== undefined) {
                updateTypingStatus(data);
            } else {
                const messageElement = document.createElement('div');
                const messageTime = new Date().toLocaleTimeString();
                messageElement.className = data.is_bot ? 'message bot' : 'message user';
                messageElement.innerHTML = `<strong>[${messageTime}]</strong> ${data.message}`;

                const chatLog = document.querySelector('#chat-log');
                if (chatLog) {
                    chatLog.appendChild(messageElement);
                    chatLog.scrollTop = chatLog.scrollHeight; 
                }
            }
        }

        function updateTypingStatus(data) {
            const typingStatus = document.querySelector('#typing-status');
            typingStatus.textContent = data.is_typing ? `${data.users.join(', ')} is typing...` : ''; 
        }

        document.addEventListener('DOMContentLoaded', function() {
            registerServiceWorker();
            connectWebSocket();

            const roomSelectorForm = document.getElementById('room-selector-form');
            roomSelectorForm.onsubmit = function(e) {
                e.preventDefault();
                const newRoomName = document.getElementById('room-name-input').value.trim();
                if (newRoomName && newRoomName !== roomName) {
                    roomName = newRoomName;
                    chatSocket.close();
                    connectWebSocket();
                }
            };

            document.querySelector('#chat-message-submit').onclick = function() {
                sendMessage();
            };

            document.addEventListener('keypress', function(event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    document.querySelector('#chat-message-submit').click();
                }
            });

            document.querySelector('#chat-message-input').addEventListener('input', function() {
                handleTypingIndication();
            });
        });

        function sendMessage() {
            const messageInput = document.querySelector('#chat-message-input');
            const message = messageInput.value.trim();
            const MAX_MESSAGE_LENGTH = 200;

            if (message && message.length <= MAX_MESSAGE_LENGTH) {
                if (chatSocket.readyState === WebSocket.OPEN) {
                    chatSocket.send(JSON.stringify({ 'message': message, 'is_bot': false }));
                    messageInput.value = ''; 
                } else {
                    console.error('WebSocket is not open. Current state:', chatSocket.readyState);
                }
            } else {
                alert(`Message must be under ${MAX_MESSAGE_LENGTH} characters.`);
            }
        }

        function handleTypingIndication() {
            clearTimeout(userTypingTimeout);
            chatSocket.send(JSON.stringify({ 'is_typing': true })); 
            userTypingTimeout = setTimeout(() => {
                chatSocket.send(JSON.stringify({ 'is_typing': false })); 
            }, 1000);
        }