/**
 * WebSocket Client for Real-Time Messaging
 * Handles communication between the browser and Django Channels consumers
 */

class ChatWebSocketClient {
    constructor(options = {}) {
        this.options = {
            protocol: options.protocol || (window.location.protocol === 'https:' ? 'wss' : 'ws'),
            host: options.host || window.location.host,
            reconnectInterval: options.reconnectInterval || 3000,
            maxReconnectAttempts: options.maxReconnectAttempts || 10,
            ...options
        };
        
        this.socket = null;
        this.reconnectAttempts = 0;
        this.messageHandlers = {};
        this.isConnecting = false;
    }
    
    /**
     * Connect to WebSocket server
     * @param {string} path - The path to connect to (e.g., '/ws/chat/direct/5/')
     * @param {Function} onOpen - Callback when connection opens
     * @param {Function} onClose - Callback when connection closes
     */
    connect(path, onOpen, onClose) {
        if (this.socket) {
            console.warn('WebSocket already connected');
            return;
        }
        
        this.isConnecting = true;
        const url = `${this.options.protocol}://${this.options.host}${path}`;
        
        try {
            this.socket = new WebSocket(url);
            
            this.socket.onopen = () => {
                console.log('WebSocket connected to', url);
                this.reconnectAttempts = 0;
                this.isConnecting = false;
                if (onOpen) onOpen();
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            this.socket.onclose = () => {
                console.log('WebSocket closed');
                this.socket = null;
                this.isConnecting = false;
                
                // Attempt to reconnect
                if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Reconnecting... (Attempt ${this.reconnectAttempts})`);
                    setTimeout(() => this.connect(path, onOpen, onClose), this.options.reconnectInterval);
                } else {
                    console.error('Max reconnection attempts reached');
                    if (onClose) onClose();
                }
            };
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.isConnecting = false;
        }
    }
    
    /**
     * Send a message through the WebSocket
     * @param {string} type - The message type
     * @param {Object} data - The message data
     */
    send(type, data = {}) {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket is not connected');
            return false;
        }
        
        try {
            this.socket.send(JSON.stringify({
                type,
                ...data
            }));
            return true;
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
            return false;
        }
    }
    
    /**
     * Register a handler for a specific message type
     * @param {string} type - The message type to handle
     * @param {Function} callback - The callback function
     */
    on(type, callback) {
        if (!this.messageHandlers[type]) {
            this.messageHandlers[type] = [];
        }
        this.messageHandlers[type].push(callback);
    }
    
    /**
     * Remove a handler for a specific message type
     * @param {string} type - The message type
     * @param {Function} callback - The callback function to remove
     */
    off(type, callback) {
        if (this.messageHandlers[type]) {
            this.messageHandlers[type] = this.messageHandlers[type].filter(cb => cb !== callback);
        }
    }
    
    /**
     * Handle incoming messages from WebSocket
     * @param {Object} data - The message data
     */
    handleMessage(data) {
        const type = data.type;
        if (this.messageHandlers[type]) {
            this.messageHandlers[type].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in handler for ${type}:`, error);
                }
            });
        }
    }
    
    /**
     * Check if WebSocket is connected
     */
    isConnected() {
        return this.socket && this.socket.readyState === WebSocket.OPEN;
    }
    
    /**
     * Disconnect the WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}


/**
 * Typing Indicator Manager
 * Handles typing status for real-time chat feedback
 */
class TypingIndicatorManager {
    constructor(websocketClient) {
        this.websocketClient = websocketClient;
        this.typingUsers = new Set();
        this.typingTimeout = null;
        this.typingDelay = 1000;  // Milliseconds before sending stop typing
    }
    
    /**
     * Notify that user is typing
     */
    startTyping() {
        if (this.websocketClient.isConnected()) {
            this.websocketClient.send('typing', { state: 'start' });
        }
        
        // Reset timeout to send stop typing
        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.stopTyping();
        }, this.typingDelay);
    }
    
    /**
     * Notify that user stopped typing
     */
    stopTyping() {
        if (this.websocketClient.isConnected()) {
            this.websocketClient.send('typing', { state: 'stop' });
        }
    }
    
    /**
     * Update typing indicator display
     * @param {string} userName - Name of user typing
     */
    addTypingUser(userId, userName) {
        this.typingUsers.add(userId);
        this.updateDisplay();
    }
    
    /**
     * Remove typing user from display
     * @param {number} userId - ID of user
     */
    removeTypingUser(userId) {
        this.typingUsers.delete(userId);
        this.updateDisplay();
    }
    
    /**
     * Update the typing indicator display
     */
    updateDisplay() {
        const indicator = document.getElementById('typing-indicator');
        if (!indicator) return;
        
        if (this.typingUsers.size > 0) {
            const userNames = Array.from(this.typingUsers).join(', ');
            indicator.innerHTML = `<em>${userNames} ${this.typingUsers.size === 1 ? 'is' : 'are'} typing...</em>`;
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    }
}


/**
 * Message Manager
 * Handles message rendering and DOM updates
 */
class MessageManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.messageMap = new Map();
    }
    
    /**
     * Add a new message to the container
     * @param {Object} messageData - Message data from WebSocket
     * @param {string} senderId - ID of the sender
     * @param {string} currentUserId - ID of current user
     */
    addMessage(messageData, senderId, currentUserId) {
        const isOwnMessage = senderId === currentUserId;
        const messageHTML = this.createMessageHTML(messageData, isOwnMessage);
        
        // Create wrapper div
        const wrapper = document.createElement('div');
        wrapper.id = `message-${messageData.message_id}`;
        wrapper.innerHTML = messageHTML;
        
        // Add to container
        if (this.container) {
            this.container.appendChild(wrapper.firstElementChild);
            this.scrollToBottom();
        }
        
        // Store message reference
        this.messageMap.set(messageData.message_id, messageData);
    }
    
    /**
     * Create HTML for a message
     * @param {Object} data - Message data
     * @param {boolean} isOwnMessage - Whether this is the sender's message
     */
    createMessageHTML(data, isOwnMessage) {
        const direction = isOwnMessage ? 'end' : 'start';
        const alignment = isOwnMessage ? 'flex-row-reverse' : '';
        const bubbleClass = isOwnMessage 
            ? 'bg-primary text-white rounded-br-none'
            : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-bl-none border border-gray-200 dark:border-gray-700';
        
        const senderName = !isOwnMessage ? `<p class="text-xs font-bold text-gray-800 dark:text-gray-200 mb-1">${data.sender_name}</p>` : '';
        const avatar = !isOwnMessage ? `
            <div class="flex-shrink-0">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center text-white font-bold text-xs">
                    ${data.sender_name.substring(0, 1).toUpperCase()}
                </div>
            </div>
        ` : '';
        
        // Convert ISO timestamp to local time
        let displayTime = data.timestamp;  // fallback to provided timestamp
        if (data.iso_timestamp) {
            try {
                const date = new Date(data.iso_timestamp);
                displayTime = date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false });
            } catch (e) {
                console.error('Error parsing timestamp:', e);
            }
        }
        
        // Handle attachment if present
        let attachmentHtml = '';
        if (data.attachment_url) {
            const url = data.attachment_url;
            const urlLower = url.toLowerCase();
            
            // Check file type and render accordingly
            if (urlLower.match(/\.(jpg|jpeg|png|gif|webp)$/i)) {
                // Image
                attachmentHtml = `
                    <div class="mb-2">
                        <img src="${url}" alt="Attachment" class="max-w-xs rounded-lg cursor-pointer hover:opacity-80 transition" 
                             onclick="openImageModal('${url}')">
                    </div>
                `;
            } else if (urlLower.match(/\.(mp4|webm|mov|avi|mkv)$/i)) {
                // Video
                attachmentHtml = `
                    <div class="mb-2">
                        <video class="max-w-xs rounded-lg" controls>
                            <source src="${url}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                `;
            } else if (urlLower.match(/\.(mp3|wav|ogg|m4a|flac)$/i)) {
                // Audio
                attachmentHtml = `
                    <div class="mb-2">
                        <audio class="max-w-xs" controls>
                            <source src="${url}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                `;
            } else {
                // Generic file
                const fileName = url.split('/').pop().split('?')[0];
                attachmentHtml = `
                    <div class="mb-2">
                        <a href="${url}" download class="inline-flex items-center gap-2 bg-opacity-20 ${isOwnMessage ? 'bg-white' : 'bg-gray-200'} px-3 py-2 rounded-lg hover:opacity-80 transition">
                            <i class="fas fa-file"></i>
                            <span class="text-xs sm:text-sm">${this.escapeHtml(fileName)}</span>
                        </a>
                    </div>
                `;
            }
        }
        
        return `
            <div class="flex justify-${direction} animate-fadeIn mb-3">
                <div class="flex gap-3 max-w-lg ${alignment}">
                    ${avatar}
                    <div class="flex flex-col ${isOwnMessage ? 'items-end' : 'items-start'}">
                        ${senderName}
                        <div class="px-4 py-2 rounded-2xl ${bubbleClass} shadow-sm break-words text-sm">
                            ${attachmentHtml}
                            <p class="leading-relaxed">${this.escapeHtml(data.message)}</p>
                        </div>
                        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 px-2">${displayTime}</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Scroll to the bottom of the message container
     */
    scrollToBottom() {
        if (this.container) {
            setTimeout(() => {
                this.container.scrollTop = this.container.scrollHeight;
            }, 0);
        }
    }
    
    /**
     * Escape HTML special characters
     */
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}


/**
 * File Upload Manager
 * Handles file attachment uploads via HTMX
 */
class FileUploadManager {
    constructor(options = {}) {
        this.maxFileSize = options.maxFileSize || 50 * 1024 * 1024;  // 50 MB
        this.uploadEndpoint = options.uploadEndpoint || '/community/upload/';
    }
    
    /**
     * Handle file selection and upload
     * @param {File} file - The file to upload
     * @param {Function} onSuccess - Callback on successful upload
     * @param {Function} onError - Callback on error
     */
    uploadFile(file, onSuccess, onError) {
        // Validate file size
        if (file.size > this.maxFileSize) {
            onError(`File size exceeds ${this.maxFileSize / 1024 / 1024}MB limit`);
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch(this.uploadEndpoint, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (onSuccess) onSuccess(data);
        })
        .catch(error => {
            console.error('Upload error:', error);
            if (onError) onError(error.message);
        });
    }
    
    /**
     * Get CSRF token from cookie
     */
    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}
