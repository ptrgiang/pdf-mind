document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const uploadForm = document.getElementById('upload-form');
    const uploadStatus = document.getElementById('upload-status');
    const fileInput = document.getElementById('file-input');
    const fileNameSpan = document.getElementById('file-name-span');
    const documentList = document.getElementById('document-list');

    const welcomeScreen = document.getElementById('welcome-screen');
    const chatArea = document.getElementById('chat-area');
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const questionInput = document.getElementById('question-input');
    const chatTargetTitle = document.getElementById('chat-target-title');

    // --- State ---
    let selectedDocIds = [];

    // --- Initialization ---
    loadDocumentList();

    // --- Event Listeners ---
    fileInput.addEventListener('change', () => {
        const numFiles = fileInput.files.length;
        fileNameSpan.textContent = numFiles > 0 ? `${numFiles} file(s) selected` : 'Choose PDFs';
    });

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (fileInput.files.length === 0) {
            showStatus('Please select one or more PDF files.', 'error');
            return;
        }
        
        const formData = new FormData(uploadForm);
        showStatus(`Ingesting ${fileInput.files.length} file(s)...`, 'loading');
        
        try {
            const response = await fetch('/ingest', { method: 'POST', body: formData });
            const result = await response.json();
            
            if (response.ok) {
                showStatus(result.success, 'success');
                await loadDocumentList(); // Refresh the list
            } else {
                showStatus(`Error: ${result.error}`, 'error');
            }
        } catch (error) {
            showStatus('An unexpected error occurred during upload.', 'error');
        } finally {
            fileInput.value = ''; // Reset file input
            fileNameSpan.textContent = 'Choose PDFs';
        }
    });

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const question = questionInput.value.trim();
        if (!question || selectedDocIds.length === 0) return;
        askQuestion(question);
    });

    questionInput.addEventListener('input', adjustTextareaHeight);
    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.requestSubmit();
        }
    });

    // --- Core Functions ---
    async function askQuestion(question) {
        clearFollowups();
        addMessage(question, 'user');
        questionInput.value = '';
        adjustTextareaHeight();
        addTypingIndicator();

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    question,
                    document_ids: selectedDocIds
                }),
            });
            
            const result = await response.json();
            removeTypingIndicator();

            if (response.ok) {
                addMessage(result.answer, 'bot', result.sources);
                displayFollowupQuestions(result.followup_questions);
            } else {
                addMessage(`Error: ${result.error}`, 'bot');
            }
        } catch (error) {
            removeTypingIndicator();
            addMessage('An unexpected error occurred while fetching the answer.', 'bot');
        }
    }

    async function loadDocumentList() {
        try {
            const response = await fetch('/documents');
            const docIds = await response.json();
            
            documentList.innerHTML = ''; // Clear existing list

            if (docIds.length > 0) {
                // Add the "Select All" checkbox
                const selectAllItem = document.createElement('li');
                selectAllItem.innerHTML = `
                    <input type="checkbox" id="select-all-checkbox">
                    <label for="select-all-checkbox">Select All</label>
                `;
                documentList.appendChild(selectAllItem);

                const selectAllCheckbox = document.getElementById('select-all-checkbox');
                selectAllCheckbox.addEventListener('change', (e) => {
                    document.querySelectorAll('.doc-checkbox').forEach(checkbox => {
                        checkbox.checked = e.target.checked;
                    });
                    updateSelectedDocs();
                });
            }

            // Add individual documents
            docIds.forEach(docId => {
                const item = document.createElement('li');
                item.innerHTML = `
                    <input type="checkbox" id="checkbox-${docId}" class="doc-checkbox" data-doc-id="${docId}">
                    <label for="checkbox-${docId}">${docId.replace(/_/g, ' ')}</label>
                `;
                documentList.appendChild(item);
            });

            // Add change listeners to all document checkboxes
            document.querySelectorAll('.doc-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', updateSelectedDocs);
            });

            // Restore previous selection
            if (selectedDocIds.length > 0) {
                selectedDocIds.forEach(docId => {
                    const checkbox = document.getElementById(`checkbox-${docId}`);
                    if (checkbox) checkbox.checked = true;
                });
            }
            updateSelectedDocs(); // Initial update

        } catch (error) {
            console.error('Failed to load document list:', error);
            showStatus('Could not load document list.', 'error');
        }
    }

    function updateSelectedDocs() {
        selectedDocIds = Array.from(document.querySelectorAll('.doc-checkbox:checked')).map(cb => cb.dataset.docId);
        updateChatUI();
    }

    // --- UI Functions ---
    function updateChatUI() {
        if (selectedDocIds.length === 0) {
            welcomeScreen.classList.remove('hidden');
            chatArea.classList.add('hidden');
        } else {
            welcomeScreen.classList.add('hidden');
            chatArea.classList.remove('hidden');
            
            let title;
            if (selectedDocIds.length === document.querySelectorAll('.doc-checkbox').length) {
                title = 'All Documents';
            } else if (selectedDocIds.length > 1) {
                title = `${selectedDocIds.length} Documents Selected`;
            } else {
                title = selectedDocIds[0].replace(/_/g, ' ');
            }
            chatTargetTitle.textContent = `Chatting with: ${title}`;
            questionInput.placeholder = `Ask a question about ${title}...`;
        }
    }

    function showStatus(message, type) {
        uploadStatus.textContent = message;
        uploadStatus.className = `upload-status ${type}`;
    }

    function displayFollowupQuestions(questions) {
        if (!questions || questions.length === 0) return;
        
        const followupContainer = document.createElement('div');
        followupContainer.className = 'followup-container';
        
        questions.forEach(q => {
            const button = document.createElement('button');
            button.textContent = q;
            button.onclick = () => {
                askQuestion(q);
            };
            followupContainer.appendChild(button);
        });
        
        chatBox.appendChild(followupContainer);
        scrollToBottom();
    }

    function clearFollowups() {
        const existingContainer = document.querySelector('.followup-container');
        if (existingContainer) {
            existingContainer.remove();
        }
    }

    function addMessage(text, sender, sources = null) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        messageElement.innerHTML = marked.parse(text);

        if (sources && sources.length > 0) {
            const sourcesContainer = document.createElement('div');
            sourcesContainer.className = 'sources-container';
            
            const toggleButton = document.createElement('button');
            toggleButton.className = 'sources-toggle';
            toggleButton.textContent = 'View Sources';
            
            const sourcesContent = document.createElement('div');
            sourcesContent.className = 'sources-content';
            sourcesContent.style.display = 'none';

            sources.forEach(source => {
                const card = document.createElement('div');
                card.className = 'source-card';
                const sourceName = source.metadata.source || 'N/A';
                const pageNum = source.metadata.page_number || 'N/A';
                card.innerHTML = `<h6>Source: ${sourceName} (Page ${pageNum})</h6><p>${source.page_content}</p>`;
                sourcesContent.appendChild(card);
            });

            toggleButton.onclick = () => {
                const isHidden = sourcesContent.style.display === 'none';
                sourcesContent.style.display = isHidden ? 'grid' : 'none';
                toggleButton.textContent = isHidden ? 'Hide Sources' : 'View Sources';
            };

            sourcesContainer.appendChild(toggleButton);
            sourcesContainer.appendChild(sourcesContent);
            messageElement.appendChild(sourcesContainer);
        }
        
        chatBox.appendChild(messageElement);
        scrollToBottom();
    }
    
    function addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.classList.add('message', 'bot-message');
        indicator.innerHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;
        chatBox.appendChild(indicator);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }

    function adjustTextareaHeight() {
        questionInput.style.height = 'auto';
        questionInput.style.height = `${questionInput.scrollHeight}px`;
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});