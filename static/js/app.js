document.documentElement.classList.add('js-ready');

document.querySelectorAll('[data-onboarding]').forEach((root) => {
    const steps = Array.from(root.querySelectorAll('.wizard-step'));
    const previousButton = root.querySelector('[data-prev]');
    const nextButton = root.querySelector('[data-next]');
    const submitButton = root.querySelector('[data-submit]');
    const currentLabel = root.querySelector('[data-step-current]');
    const progressBar = root.querySelector('[data-progress-bar]');
    const birthDateInput = root.querySelector('[data-birth-date]');
    const birthSummary = root.querySelector('[data-birth-summary]');
    const initialStep = Math.max(1, Number(root.dataset.initialStep || 1));
    let currentStep = initialStep - 1;

    function getHoroscopeSign(month, day) {
        const signs = [
            [[1, 20], 'Capricornio'], [[2, 19], 'Acuario'], [[3, 21], 'Piscis'],
            [[4, 20], 'Aries'], [[5, 21], 'Tauro'], [[6, 21], 'Geminis'],
            [[7, 23], 'Cancer'], [[8, 23], 'Leo'], [[9, 23], 'Virgo'],
            [[10, 23], 'Libra'], [[11, 22], 'Escorpio'], [[12, 22], 'Sagitario'],
            [[12, 32], 'Capricornio'],
        ];
        return signs.find(([[limitMonth, limitDay]]) => month < limitMonth || (month === limitMonth && day < limitDay))?.[1] || 'Capricornio';
    }

    function refreshBirthSummary() {
        if (!birthDateInput || !birthSummary || !birthDateInput.value) {
            return;
        }
        const [year, month, day] = birthDateInput.value.split('-').map(Number);
        if (!year || !month || !day) {
            return;
        }
        const today = new Date();
        let age = today.getFullYear() - year;
        const birthdayPassed = today.getMonth() + 1 > month || (today.getMonth() + 1 === month && today.getDate() >= day);
        if (!birthdayPassed) {
            age -= 1;
        }
        const sign = getHoroscopeSign(month, day);
        birthSummary.textContent = age >= 0 ? `${age} años - ${sign}` : 'Revisa la fecha indicada.';
    }

    function refreshChoiceState() {
        root.querySelectorAll('.choice-card').forEach((card) => {
            const input = card.querySelector('input');
            card.classList.toggle('is-selected', Boolean(input && input.checked));
        });
    }

    function showStep(index) {
        currentStep = Math.max(0, Math.min(index, steps.length - 1));
        steps.forEach((step, stepIndex) => {
            step.classList.toggle('is-active', stepIndex === currentStep);
        });
        previousButton.disabled = currentStep === 0;
        nextButton.hidden = currentStep === steps.length - 1;
        submitButton.hidden = currentStep !== steps.length - 1;
        currentLabel.textContent = String(currentStep + 1);
        progressBar.style.width = `${((currentStep + 1) / steps.length) * 100}%`;
        steps[currentStep].querySelector('input, textarea, select')?.focus({ preventScroll: true });
    }

    root.querySelectorAll('.choice-card input').forEach((input) => {
        input.addEventListener('change', refreshChoiceState);
    });

    birthDateInput?.addEventListener('change', refreshBirthSummary);
    birthDateInput?.addEventListener('input', refreshBirthSummary);
    previousButton.addEventListener('click', () => showStep(currentStep - 1));
    nextButton.addEventListener('click', () => showStep(currentStep + 1));

    refreshChoiceState();
    refreshBirthSummary();
    showStep(initialStep - 1);
});

document.querySelectorAll('.choice-card').forEach((card) => {
    const input = card.querySelector('input');
    if (!input || card.closest('[data-onboarding]')) {
        return;
    }
    const refresh = () => card.classList.toggle('is-selected', input.checked);
    input.addEventListener('change', refresh);
    refresh();
});

document.querySelectorAll('[data-birth-widget]').forEach((root) => {
    const birthDateInput = root.querySelector('[data-birth-date]');
    const birthSummary = root.querySelector('[data-birth-summary]');
    if (!birthDateInput || !birthSummary) {
        return;
    }

    function getHoroscopeSign(month, day) {
        const signs = [
            [[1, 20], 'Capricornio'], [[2, 19], 'Acuario'], [[3, 21], 'Piscis'],
            [[4, 20], 'Aries'], [[5, 21], 'Tauro'], [[6, 21], 'Geminis'],
            [[7, 23], 'Cancer'], [[8, 23], 'Leo'], [[9, 23], 'Virgo'],
            [[10, 23], 'Libra'], [[11, 22], 'Escorpio'], [[12, 22], 'Sagitario'],
            [[12, 32], 'Capricornio'],
        ];
        return signs.find(([[limitMonth, limitDay]]) => month < limitMonth || (month === limitMonth && day < limitDay))?.[1] || 'Capricornio';
    }

    function refreshBirthSummary() {
        if (!birthDateInput.value) {
            return;
        }
        const [year, month, day] = birthDateInput.value.split('-').map(Number);
        if (!year || !month || !day) {
            return;
        }
        const today = new Date();
        let age = today.getFullYear() - year;
        const birthdayPassed = today.getMonth() + 1 > month || (today.getMonth() + 1 === month && today.getDate() >= day);
        if (!birthdayPassed) {
            age -= 1;
        }
        const sign = getHoroscopeSign(month, day);
        birthSummary.textContent = age >= 0 ? `${age} años - ${sign}` : 'Revisa la fecha indicada.';
    }

    birthDateInput.addEventListener('change', refreshBirthSummary);
    birthDateInput.addEventListener('input', refreshBirthSummary);
    refreshBirthSummary();
});

document.querySelectorAll('[data-location-country]').forEach((countrySelect) => {
    const form = countrySelect.closest('form');
    const cityInput = form?.querySelector('[data-location-city]');
    const datalistId = cityInput?.getAttribute('list');
    const datalist = datalistId ? document.getElementById(datalistId) : null;
    if (!cityInput || !datalist) {
        return;
    }

    const citySuggestions = {
        ES: ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Zaragoza', 'Málaga', 'Murcia', 'Palma', 'Las Palmas de Gran Canaria', 'Bilbao', 'Alicante', 'Córdoba', 'Valladolid', 'Vigo', 'Gijón', 'A Coruña'],
        MX: ['Ciudad de México', 'Guadalajara', 'Monterrey', 'Puebla', 'Tijuana', 'León', 'Mérida', 'Querétaro', 'Cancún', 'Toluca'],
        AR: ['Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'La Plata', 'Mar del Plata', 'San Miguel de Tucumán', 'Salta'],
        CO: ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena', 'Bucaramanga', 'Pereira', 'Manizales'],
        CL: ['Santiago', 'Valparaíso', 'Concepción', 'La Serena', 'Antofagasta', 'Temuco', 'Viña del Mar'],
        PE: ['Lima', 'Arequipa', 'Trujillo', 'Chiclayo', 'Cusco', 'Piura', 'Iquitos'],
        VE: ['Caracas', 'Maracaibo', 'Valencia', 'Barquisimeto', 'Maracay', 'Mérida'],
        EC: ['Quito', 'Guayaquil', 'Cuenca', 'Manta', 'Ambato', 'Loja'],
        UY: ['Montevideo', 'Salto', 'Paysandú', 'Maldonado', 'Rivera'],
        PY: ['Asunción', 'Ciudad del Este', 'San Lorenzo', 'Luque', 'Encarnación'],
        BO: ['La Paz', 'Santa Cruz de la Sierra', 'Cochabamba', 'Sucre', 'Tarija'],
        CR: ['San José', 'Alajuela', 'Cartago', 'Heredia', 'Liberia'],
        DO: ['Santo Domingo', 'Santiago de los Caballeros', 'La Romana', 'San Pedro de Macorís'],
        GT: ['Ciudad de Guatemala', 'Quetzaltenango', 'Escuintla', 'Mixco', 'Villa Nueva'],
        HN: ['Tegucigalpa', 'San Pedro Sula', 'La Ceiba', 'Choloma'],
        SV: ['San Salvador', 'Santa Ana', 'San Miguel', 'Soyapango'],
        NI: ['Managua', 'León', 'Granada', 'Masaya'],
        PA: ['Ciudad de Panamá', 'San Miguelito', 'David', 'Colón'],
        CU: ['La Habana', 'Santiago de Cuba', 'Camagüey', 'Holguín'],
        PR: ['San Juan', 'Bayamón', 'Carolina', 'Ponce', 'Mayagüez'],
        US: ['Miami', 'Nueva York', 'Los Ángeles', 'Chicago', 'Houston', 'San Antonio'],
    };

    function refreshCitySuggestions() {
        datalist.innerHTML = '';
        (citySuggestions[countrySelect.value] || []).forEach((city) => {
            const option = document.createElement('option');
            option.value = city;
            datalist.append(option);
        });
    }

    countrySelect.addEventListener('change', refreshCitySuggestions);
    refreshCitySuggestions();
});

document.querySelectorAll('[data-notifications]').forEach(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/notificaciones/`);

    function updateBadge(name, value) {
        const badge = document.querySelector(`[data-badge="${name}"]`);
        if (!badge) {
            return;
        }
        const count = Number(value || 0);
        badge.textContent = count > 99 ? '99+' : String(count);
        badge.classList.toggle('is-hidden', count <= 0);
        badge.setAttribute('aria-label', count === 1 ? '1 aviso pendiente' : `${count} avisos pendientes`);
    }

    function applyConversationRow(row) {
        const inbox = document.querySelector('[data-inbox]');
        const list = inbox?.querySelector('.conversation-list');
        if (!list || !row) {
            return;
        }

        const existing = list.querySelector(`[data-conversation-row="${row.dataset.conversationRow}"]`);
        if (existing) {
            existing.replaceWith(row);
        } else {
            list.querySelector('.empty-state')?.remove();
            list.prepend(row);
        }
        list.prepend(row);
    }

    function updateConversationRow(conversation) {
        if (!conversation) {
            return;
        }

        const inbox = document.querySelector('[data-inbox]');
        const list = inbox?.querySelector('.conversation-list');
        if (!list) {
            return;
        }

        fetch(conversation.row_url || `/mensajes/${conversation.id}/fila/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
            .then((response) => response.text())
            .then((html) => {
                const template = document.createElement('template');
                template.innerHTML = html.trim();
                applyConversationRow(template.content.firstElementChild);
            })
            .catch(() => {
                updateConversationRowFallback(conversation, list);
            });
    }

    function updateConversationRowFallback(conversation, list) {
        const row = list?.querySelector(`[data-conversation-row="${conversation.id}"]`);
        if (!row) {
            return;
        }

        row.querySelector('[data-conversation-title]').textContent = conversation.title;
        row.querySelector('[data-conversation-subtitle]').textContent = conversation.subtitle;
        row.querySelector('[data-conversation-preview]').textContent = conversation.last_message;
        row.querySelector('[data-conversation-time]').textContent = conversation.time_label;

        const unread = row.querySelector('[data-conversation-unread]');
        const unreadCount = Number(conversation.unread_count || 0);
        unread.textContent = unreadCount > 99 ? '99+' : String(unreadCount);
        unread.classList.toggle('is-hidden', unreadCount <= 0);
        row.classList.toggle('is-unread', unreadCount > 0);

        list.prepend(row);
    }

    socket.addEventListener('message', (event) => {
        const counts = JSON.parse(event.data);
        updateBadge('panel', counts.panel);
        updateBadge('messages', counts.messages);
        updateBadge('connections', counts.connections);
        updateConversationRow(counts.conversation);
    });
});

document.querySelectorAll('[data-chat]').forEach((chat) => {
    const conversationId = chat.dataset.conversationId;
    const currentUserId = Number(chat.dataset.currentUserId);
    const isPublicChat = chat.dataset.publicChat === 'true';
    const isParticipantChat = chat.dataset.participantChat === 'true';
    const messages = chat.querySelector('[data-chat-messages]');
    const form = chat.querySelector('[data-chat-form]');
    const participantsList = chat.querySelector('[data-chat-participants]');
    const textarea = form?.querySelector('textarea[name="body"]');
    const imageInput = form?.querySelector('input[name="image"]');
    const csrfToken = form?.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
    const status = chat.querySelector('[data-chat-status]');
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socketUrl = `${protocol}://${window.location.host}/ws/mensajes/${conversationId}/`;
    let socket;

    if (isParticipantChat) {
        chat.querySelectorAll('.message-actions, .message-ticks').forEach((element) => element.remove());
        chat.querySelectorAll('.image-upload-button, [data-image-name]').forEach((element) => element.remove());
    }

    function setStatus(text, connected = false) {
        status.textContent = text;
        status.classList.toggle('is-connected', connected);
    }

    function addOrUpdateParticipant(participant) {
        if (!isParticipantChat || !participantsList || !participant?.id) {
            return;
        }
        chat.querySelector('[data-empty-participants]')?.remove();
        let row = participantsList.querySelector(`[data-participant-id="${participant.id}"]`);
        if (!row) {
            row = document.createElement(participant.profile_url ? 'a' : 'div');
            row.className = 'chat-participant';
            row.dataset.participantId = participant.id;
            participantsList.append(row);
        }
        if (participant.profile_url && row.tagName !== 'A') {
            const link = document.createElement('a');
            link.className = row.className;
            link.dataset.participantId = participant.id;
            row.replaceWith(link);
            row = link;
        }
        if (participant.profile_url) {
            row.href = participant.profile_url;
        }

        const avatar = document.createElement('span');
        avatar.className = 'chat-avatar small';
        if (participant.avatar_url) {
            const img = document.createElement('img');
            img.src = participant.avatar_url;
            img.alt = '';
            avatar.append(img);
        } else {
            const initial = document.createElement('span');
            initial.textContent = participant.initial || participant.username?.charAt(0)?.toUpperCase() || '?';
            avatar.append(initial);
        }

        const text = document.createElement('span');
        const name = document.createElement('strong');
        name.textContent = participant.username || 'Usuario';
        const details = document.createElement('small');
        const status = participant.is_online === false ? 'Offline' : 'Online';
        details.textContent = isPublicChat ? (participant.details || 'Sin datos de perfil') : `${participant.details || 'Sin datos de perfil'} · ${status}`;
        text.append(name, details);

        row.replaceChildren(avatar, text);
    }

    function removeParticipant(participantId) {
        if (!isParticipantChat || !participantsList || !participantId) {
            return;
        }
        const row = participantsList.querySelector(`[data-participant-id="${participantId}"]`);
        if (!row) {
            return;
        }
        if (!isPublicChat) {
            const details = row.querySelector('small');
            if (details) {
                details.textContent = details.textContent.replace('Online', 'Offline');
            }
            return;
        }
        row.remove();
        if (!participantsList.querySelector('[data-participant-id]')) {
            const empty = document.createElement('p');
            empty.className = 'muted';
            empty.dataset.emptyParticipants = '';
            empty.textContent = 'Todavía no hay usuarios en esta sala.';
            participantsList.append(empty);
        }
    }

    function appendMessage(message) {
        chat.querySelector('[data-empty-chat]')?.remove();
        if (message.id && messages.querySelector(`[data-message-id="${message.id}"]`)) {
            return;
        }

        const article = document.createElement('article');
        article.className = `message ${Number(message.sender_id) === currentUserId ? 'mine' : ''} ${isPublicChat ? 'message--public' : ''}`;
        if (message.id) {
            article.dataset.messageId = message.id;
        }

        if (isPublicChat) {
            const avatar = document.createElement('span');
            avatar.className = 'message-author-avatar';
            if (message.sender_avatar_url) {
                const img = document.createElement('img');
                img.src = message.sender_avatar_url;
                img.alt = '';
                avatar.append(img);
            } else {
                const initial = document.createElement('span');
                initial.textContent = message.sender_initial || message.sender_name?.charAt(0)?.toUpperCase() || '?';
                avatar.append(initial);
            }
            article.append(avatar);
        }

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        const sender = document.createElement('strong');
        sender.textContent = message.sender_name;
        if (isPublicChat) {
            sender.className = 'message-author-name';
        }
        const body = document.createElement('p');
        body.textContent = message.body;
        const createdAt = document.createElement('span');
        createdAt.textContent = message.created_at;
        const meta = document.createElement('span');
        meta.className = 'message-meta';
        meta.append(createdAt);

        if (Number(message.sender_id) === currentUserId && !isPublicChat) {
            const ticks = document.createElement('span');
            ticks.className = 'message-ticks';
            ticks.textContent = '✓✓';
            ticks.title = 'Recibido';
            meta.append(ticks);
        }

        if (isPublicChat || Number(message.sender_id) !== currentUserId) {
            bubble.append(sender);
        }
        if (message.body) {
            bubble.append(body);
        }
        bubble.append(meta);

        if (Number(message.sender_id) === currentUserId && message.id && !isPublicChat) {
            const actions = document.createElement('div');
            actions.className = 'message-actions';

            if (message.body) {
                const details = document.createElement('details');
                const summary = document.createElement('summary');
                summary.textContent = 'Editar';
                const editForm = document.createElement('form');
                editForm.method = 'post';
                editForm.action = `/mensajes/mensaje/${message.id}/editar/`;
                editForm.className = 'message-edit-form';
                editForm.innerHTML = `
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                    <textarea name="body" rows="3" maxlength="2000"></textarea>
                    <button class="button small" type="submit">Guardar</button>
                `;
                editForm.querySelector('textarea').value = message.body;
                details.append(summary, editForm);
                actions.append(details);
            }

            const deleteForm = document.createElement('form');
            deleteForm.method = 'post';
            deleteForm.action = `/mensajes/mensaje/${message.id}/eliminar/`;
            deleteForm.innerHTML = `
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                <button class="link-button danger-link" type="submit">Eliminar</button>
            `;
            actions.append(deleteForm);
            bubble.append(actions);
        }

        article.append(bubble);
        messages.append(article);
        article.scrollIntoView({ block: 'nearest' });
    }

    function applyReadReceipt(payload) {
        if (!payload || Number(payload.reader_id) === currentUserId) {
            return;
        }
        (payload.message_ids || []).forEach((messageId) => {
            const ticks = messages.querySelector(`[data-message-id="${messageId}"] .message-ticks`);
            if (!ticks) {
                return;
            }
            ticks.classList.add('is-read');
            ticks.title = 'Leído';
            ticks.setAttribute('aria-label', 'Leído');
        });
    }

    function connect() {
        socket = new WebSocket(socketUrl);

        socket.addEventListener('open', () => {
            setStatus('Chat en tiempo real activo', true);
        });

        socket.addEventListener('message', (event) => {
            const payload = JSON.parse(event.data);
            if (payload.type === 'read_receipt') {
                applyReadReceipt(payload);
                return;
            }
            if (payload.type === 'presence') {
                addOrUpdateParticipant(payload.participant);
                return;
            }
            if (payload.type === 'presence_leave') {
                removeParticipant(payload.participant_id);
                return;
            }
            appendMessage(payload);
        });

        socket.addEventListener('close', () => {
            setStatus('Chat en modo clásico. Recarga si no ves mensajes nuevos.');
        });

        socket.addEventListener('error', () => {
            setStatus('No se pudo conectar el chat en tiempo real.');
        });
    }

    form.addEventListener('submit', (event) => {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            return;
        }
        if (imageInput?.files?.length) {
            return;
        }

        event.preventDefault();
        const body = textarea.value.trim();
        if (!body) {
            return;
        }

        socket.send(JSON.stringify({ body }));
        textarea.value = '';
        textarea.focus();
    });

    connect();
});

document.querySelectorAll('input[name="image"]').forEach((input) => {
    const form = input.closest('form');
    const fileName = form?.querySelector('[data-image-name]');
    if (!fileName) {
        return;
    }

    input.addEventListener('change', () => {
        fileName.textContent = input.files?.[0]?.name ? `Adjunto: ${input.files[0].name}` : '';
    });
});

document.querySelectorAll('.profile-photo-field input[type="file"]').forEach((input) => {
    const field = input.closest('.profile-photo-field');
    const preview = field?.querySelector('[data-photo-preview]');
    if (!preview) {
        return;
    }

    input.addEventListener('change', () => {
        const file = input.files?.[0];
        if (!file || !file.type.startsWith('image/')) {
            preview.hidden = true;
            preview.removeAttribute('src');
            return;
        }
        preview.src = URL.createObjectURL(file);
        preview.hidden = false;
    });
});

document.querySelectorAll('[data-emoji-picker]').forEach((picker) => {
    const form = picker.closest('form');
    const targetName = picker.dataset.emojiTarget || 'body';
    const textarea = form?.querySelector(`textarea[name="${targetName}"]`);
    const toggle = picker.querySelector('[data-emoji-toggle]');
    const panel = picker.querySelector('[data-emoji-panel]');
    const search = picker.querySelector('[data-emoji-search]');
    const tabs = picker.querySelector('[data-emoji-tabs]');
    const grid = picker.querySelector('[data-emoji-grid]');
    if (!textarea || !toggle || !panel || !search || !tabs || !grid) {
        return;
    }

    const emojiCategories = [
        {
            id: 'caras',
            label: '\uD83D\uDE00',
            name: 'Caras',
            keywords: 'caras emociones feliz triste amor risa saludo',
            emojis: [
                '\uD83D\uDE00', '\uD83D\uDE03', '\uD83D\uDE04', '\uD83D\uDE01', '\uD83D\uDE06', '\uD83D\uDE05', '\uD83E\uDD23', '\uD83D\uDE02',
                '\uD83D\uDE42', '\uD83D\uDE43', '\uD83D\uDE09', '\uD83D\uDE0A', '\uD83D\uDE07', '\uD83E\uDD70', '\uD83D\uDE0D', '\uD83E\uDD29',
                '\uD83D\uDE18', '\uD83D\uDE17', '\uD83D\uDE19', '\uD83D\uDE1A', '\uD83D\uDE0B', '\uD83D\uDE1B', '\uD83D\uDE1C', '\uD83E\uDD2A',
                '\uD83D\uDE0E', '\uD83E\uDD13', '\uD83E\uDD17', '\uD83E\uDD14', '\uD83E\uDD2D', '\uD83E\uDD2B', '\uD83D\uDE10', '\uD83D\uDE11',
                '\uD83D\uDE36', '\uD83D\uDE0F', '\uD83D\uDE44', '\uD83D\uDE2C', '\uD83E\uDD25', '\uD83D\uDE0C', '\uD83D\uDE14', '\uD83D\uDE2A',
                '\uD83E\uDD24', '\uD83D\uDE34', '\uD83D\uDE37', '\uD83E\uDD12', '\uD83E\uDD15', '\uD83E\uDD22', '\uD83E\uDD27', '\uD83E\uDD75',
                '\uD83E\uDD76', '\uD83D\uDE35', '\uD83E\uDD2F', '\uD83E\uDD20', '\uD83E\uDD73', '\uD83D\uDE0A', '\uD83E\uDD79', '\uD83D\uDE22',
                '\uD83D\uDE2D', '\uD83D\uDE31', '\uD83D\uDE28', '\uD83D\uDE30', '\uD83D\uDE21', '\uD83D\uDE24', '\uD83D\uDE08', '\uD83D\uDC4B'
            ],
        },
        {
            id: 'gestos',
            label: '\uD83D\uDC4D',
            name: 'Gestos',
            keywords: 'manos gestos ok aplauso abrazo fuerza',
            emojis: [
                '\uD83D\uDC4D', '\uD83D\uDC4E', '\uD83D\uDC4C', '\uD83E\uDD0C', '\uD83E\uDD0F', '\u270C\uFE0F', '\uD83E\uDD1E', '\uD83E\uDEF0',
                '\uD83E\uDD19', '\uD83E\uDD18', '\uD83D\uDC48', '\uD83D\uDC49', '\uD83D\uDC46', '\uD83D\uDC47', '\u261D\uFE0F', '\u270B',
                '\uD83E\uDD1A', '\uD83D\uDD90\uFE0F', '\uD83D\uDD96', '\uD83D\uDC4B', '\uD83E\uDD1D', '\uD83D\uDE4F', '\uD83D\uDC4F', '\uD83D\uDCAA',
                '\uD83E\uDEC2', '\uD83E\uDEC1', '\uD83E\uDEF6', '\uD83D\uDC85', '\uD83E\uDD33', '\u270D\uFE0F'
            ],
        },
        {
            id: 'corazones',
            label: '\u2764\uFE0F',
            name: 'Corazones',
            keywords: 'amor corazones amistad apoyo flores',
            emojis: [
                '\u2764\uFE0F', '\uD83E\uDDE1', '\uD83D\uDC9B', '\uD83D\uDC9A', '\uD83D\uDC99', '\uD83D\uDC9C', '\uD83E\uDD0E', '\uD83D\uDDA4',
                '\uD83E\uDD0D', '\uD83D\uDC94', '\u2763\uFE0F', '\uD83D\uDC95', '\uD83D\uDC9E', '\uD83D\uDC93', '\uD83D\uDC97', '\uD83D\uDC96',
                '\uD83D\uDC98', '\uD83D\uDC9D', '\uD83D\uDC90', '\uD83C\uDF39', '\uD83C\uDF37', '\uD83C\uDF38', '\uD83C\uDF3B', '\uD83C\uDF3C',
                '\uD83C\uDF40', '\u2728', '\uD83C\uDF1F', '\uD83D\uDCAB'
            ],
        },
        {
            id: 'planes',
            label: '\u2615',
            name: 'Planes',
            keywords: 'planes cafe cine musica juegos lectura comida deporte',
            emojis: [
                '\u2615', '\uD83E\uDD64', '\uD83C\uDF75', '\uD83C\uDF7D\uFE0F', '\uD83C\uDF55', '\uD83C\uDF54', '\uD83C\uDF5F', '\uD83C\uDF5D',
                '\uD83C\uDF5C', '\uD83C\uDF5A', '\uD83C\uDF63', '\uD83C\uDF70', '\uD83C\uDF82', '\uD83C\uDF6B', '\uD83C\uDF6A', '\uD83C\uDF7F',
                '\uD83C\uDFAC', '\uD83C\uDFA7', '\uD83C\uDFB5', '\uD83C\uDFA4', '\uD83C\uDFAE', '\uD83C\uDFB2', '\uD83D\uDCDA', '\uD83D\uDCD6',
                '\uD83C\uDFA8', '\uD83C\uDFAD', '\uD83C\uDFC3', '\uD83D\uDEB6', '\uD83E\uDDD8', '\u26BD', '\uD83C\uDFC0', '\uD83C\uDFD3'
            ],
        },
        {
            id: 'viajes',
            label: '\uD83D\uDE97',
            name: 'Lugares',
            keywords: 'lugares viajes ciudad casa tiempo transporte naturaleza',
            emojis: [
                '\uD83C\uDFE0', '\uD83C\uDFE1', '\uD83C\uDFD9\uFE0F', '\uD83C\uDFE5', '\uD83C\uDFEB', '\uD83C\uDFDB\uFE0F', '\uD83C\uDFDE\uFE0F', '\uD83C\uDFD6\uFE0F',
                '\uD83C\uDF33', '\uD83C\uDF32', '\uD83C\uDF3F', '\u2600\uFE0F', '\uD83C\uDF24\uFE0F', '\u2601\uFE0F', '\uD83C\uDF27\uFE0F', '\u26C4',
                '\uD83C\uDF08', '\uD83D\uDE97', '\uD83D\uDE95', '\uD83D\uDE8C', '\uD83D\uDE86', '\u2708\uFE0F', '\uD83D\uDEB2', '\u267F',
                '\uD83D\uDCCD', '\uD83D\uDDFA\uFE0F', '\u23F0', '\uD83D\uDCC5'
            ],
        },
        {
            id: 'objetos',
            label: '\uD83D\uDCA1',
            name: 'Objetos',
            keywords: 'objetos ideas trabajo salud mensajes',
            emojis: [
                '\uD83D\uDCA1', '\uD83D\uDCF1', '\uD83D\uDCBB', '\u2328\uFE0F', '\uD83D\uDCE7', '\uD83D\uDCAC', '\uD83D\uDCDD', '\uD83D\uDCCC',
                '\uD83D\uDD12', '\uD83D\uDD11', '\uD83D\uDC8A', '\uD83E\uDE79', '\uD83E\uDE7A', '\uD83E\uDEBC', '\uD83E\uDDAF', '\uD83E\uDDBD',
                '\uD83C\uDFA7', '\uD83D\uDCF7', '\uD83D\uDCB0', '\uD83C\uDF81', '\uD83D\uDCE6', '\u2705', '\u274C', '\u26A0\uFE0F'
            ],
        },
    ];

    let activeCategory = emojiCategories[0].id;

    function insertEmoji(emoji) {
        const start = textarea.selectionStart || textarea.value.length;
        const end = textarea.selectionEnd || textarea.value.length;
        textarea.value = `${textarea.value.slice(0, start)}${emoji}${textarea.value.slice(end)}`;
        textarea.focus();
        textarea.selectionStart = start + emoji.length;
        textarea.selectionEnd = start + emoji.length;
    }

    function matchingEmojis(query) {
        const normalizedQuery = query.trim().toLowerCase();
        if (!normalizedQuery) {
            return emojiCategories.find((category) => category.id === activeCategory)?.emojis || [];
        }
        return emojiCategories
            .filter((category) => `${category.name} ${category.keywords}`.toLowerCase().includes(normalizedQuery))
            .flatMap((category) => category.emojis);
    }

    function renderTabs() {
        tabs.innerHTML = '';
        emojiCategories.forEach((category) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = category.label;
            button.title = category.name;
            button.dataset.emojiCategory = category.id;
            button.classList.toggle('is-active', category.id === activeCategory);
            tabs.append(button);
        });
    }

    function renderGrid() {
        grid.innerHTML = '';
        matchingEmojis(search.value).forEach((emoji) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = emoji;
            button.dataset.emojiValue = emoji;
            grid.append(button);
        });
    }

    toggle.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        panel.hidden = !panel.hidden;
        if (!panel.hidden) {
            search.focus({ preventScroll: true });
        }
    });

    search.addEventListener('input', renderGrid);

    panel.addEventListener('click', (event) => {
        const categoryButton = event.target.closest('[data-emoji-category]');
        const emojiButton = event.target.closest('[data-emoji-value]');
        if (!categoryButton && !emojiButton) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();

        if (categoryButton) {
            activeCategory = categoryButton.dataset.emojiCategory;
            search.value = '';
            renderTabs();
            renderGrid();
            return;
        }

        insertEmoji(emojiButton.dataset.emojiValue || '');
    });

    document.addEventListener('click', (event) => {
        if (!picker.contains(event.target)) {
            panel.hidden = true;
        }
    });

    renderTabs();
    renderGrid();
});
