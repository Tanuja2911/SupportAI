(function () {
  'use strict';

  const SupportAI = {
    config: null,
    container: null,
    iframe: null,
    isOpen: false,

    init(options) {
      if (!options.apiKey) {
        console.error('SupportAI: apiKey is required');
        return;
      }

      this.config = {
        apiKey: options.apiKey,
        serverUrl: options.serverUrl || window.location.origin,
        position: options.position || 'bottom-right',
      };

      this.loadConfig().then(() => {
        this.createWidget();
      });
    },

    async loadConfig() {
      try {
        const res = await fetch(`${this.config.serverUrl}/api/widget/embed/${this.config.apiKey}`);
        if (res.ok) {
          const data = await res.json();
          Object.assign(this.config, data);
        }
      } catch (e) {
        console.error('SupportAI: Failed to load config', e);
      }
    },

    createWidget() {
      const primaryColor = this.config.primary_color || '#6366f1';
      const position = this.config.position || 'bottom-right';
      const isRight = position === 'bottom-right';

      // Floating button
      const btn = document.createElement('div');
      btn.id = 'supportai-btn';
      btn.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      `;
      Object.assign(btn.style, {
        position: 'fixed',
        bottom: '24px',
        [isRight ? 'right' : 'left']: '24px',
        width: '56px',
        height: '56px',
        borderRadius: '50%',
        backgroundColor: primaryColor,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        zIndex: '99999',
        transition: 'transform 0.2s',
      });
      btn.onmouseenter = () => (btn.style.transform = 'scale(1.1)');
      btn.onmouseleave = () => (btn.style.transform = 'scale(1)');
      btn.onclick = () => this.toggle();
      document.body.appendChild(btn);

      // Chat window
      const chat = document.createElement('div');
      chat.id = 'supportai-chat';
      Object.assign(chat.style, {
        position: 'fixed',
        bottom: '96px',
        [isRight ? 'right' : 'left']: '24px',
        width: '380px',
        height: '520px',
        borderRadius: '16px',
        overflow: 'hidden',
        boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
        zIndex: '99998',
        display: 'none',
        flexDirection: 'column',
        backgroundColor: '#fff',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      });

      // Header
      const header = document.createElement('div');
      Object.assign(header.style, {
        padding: '16px',
        backgroundColor: primaryColor,
        color: 'white',
        fontSize: '14px',
        fontWeight: '600',
      });
      header.textContent = this.config.bot_name || 'Support Assistant';
      chat.appendChild(header);

      // Messages area
      const msgs = document.createElement('div');
      msgs.id = 'supportai-messages';
      Object.assign(msgs.style, {
        flex: '1',
        overflowY: 'auto',
        padding: '16px',
        backgroundColor: '#f9fafb',
      });

      // Welcome message
      const welcome = document.createElement('div');
      Object.assign(welcome.style, {
        backgroundColor: '#fff',
        padding: '10px 14px',
        borderRadius: '12px',
        fontSize: '13px',
        color: '#374151',
        display: 'inline-block',
        boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
        marginBottom: '12px',
      });
      welcome.textContent = this.config.welcome_message || 'Hi! How can I help you today?';
      msgs.appendChild(welcome);
      chat.appendChild(msgs);

      // Input area
      const inputArea = document.createElement('div');
      Object.assign(inputArea.style, {
        padding: '12px',
        borderTop: '1px solid #e5e7eb',
        display: 'flex',
        gap: '8px',
      });

      const input = document.createElement('input');
      input.placeholder = this.config.placeholder_text || 'Type your question...';
      Object.assign(input.style, {
        flex: '1',
        padding: '8px 12px',
        border: '1px solid #d1d5db',
        borderRadius: '8px',
        fontSize: '13px',
        outline: 'none',
      });
      input.onfocus = () => (input.style.borderColor = primaryColor);
      input.onblur = () => (input.style.borderColor = '#d1d5db');

      const sendBtn = document.createElement('button');
      sendBtn.textContent = 'Send';
      Object.assign(sendBtn.style, {
        padding: '8px 16px',
        backgroundColor: primaryColor,
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        fontSize: '13px',
        cursor: 'pointer',
        fontWeight: '500',
      });

      let conversationId = null;

      const sendMessage = async () => {
        const text = input.value.trim();
        if (!text) return;

        this.addMessage(msgs, text, 'user', primaryColor);
        input.value = '';

        try {
          const res = await fetch(`${this.config.serverUrl}/api/chat/${this.config.apiKey}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: text,
              conversation_id: conversationId,
            }),
          });
          const data = await res.json();
          conversationId = data.conversation_id;
          this.addMessage(msgs, data.message, 'ai', primaryColor);
        } catch (e) {
          this.addMessage(msgs, 'Sorry, something went wrong. Please try again.', 'ai', primaryColor);
        }
      };

      sendBtn.onclick = sendMessage;
      input.onkeydown = (e) => { if (e.key === 'Enter') sendMessage(); };

      inputArea.appendChild(input);
      inputArea.appendChild(sendBtn);
      chat.appendChild(inputArea);

      // Branding
      if (this.config.show_branding !== false) {
        const brand = document.createElement('div');
        Object.assign(brand.style, {
          textAlign: 'center',
          padding: '6px',
          fontSize: '10px',
          color: '#9ca3af',
          borderTop: '1px solid #e5e7eb',
        });
        brand.textContent = 'Powered by SupportAI';
        chat.appendChild(brand);
      }

      document.body.appendChild(chat);
      this.container = chat;
    },

    addMessage(container, text, role, primaryColor) {
      const msg = document.createElement('div');
      Object.assign(msg.style, {
        marginBottom: '12px',
        display: 'flex',
        justifyContent: role === 'user' ? 'flex-end' : 'flex-start',
      });

      const bubble = document.createElement('div');
      Object.assign(bubble.style, {
        maxWidth: '75%',
        padding: '10px 14px',
        borderRadius: '12px',
        fontSize: '13px',
        lineHeight: '1.5',
        backgroundColor: role === 'user' ? primaryColor : '#fff',
        color: role === 'user' ? '#fff' : '#374151',
        boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
      });
      bubble.textContent = text;

      msg.appendChild(bubble);
      container.appendChild(msg);
      container.scrollTop = container.scrollHeight;
    },

    toggle() {
      this.isOpen = !this.isOpen;
      if (this.container) {
        this.container.style.display = this.isOpen ? 'flex' : 'none';
      }
    },
  };

  window.SupportAI = SupportAI;
})();
