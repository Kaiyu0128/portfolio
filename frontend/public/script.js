document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('questionForm');
    const chatBox = document.getElementById('chatBox');

    form.addEventListener('submit', function(event) {
        event.preventDefault(); // フォームのデフォルト送信を防止

        const userQuestion = document.getElementById('userQuestion').value;

        // Append user's question to chat
        const userMessage = document.createElement('p');
        userMessage.textContent = "You: " + userQuestion;
        chatBox.appendChild(userMessage);

        // Show typing indicator
        const typingIndicator = document.createElement('p');
        typingIndicator.textContent = "Kai is typing...";
        typingIndicator.id = "typingIndicator";
        chatBox.appendChild(typingIndicator);
        chatBox.scrollTop = chatBox.scrollHeight;

        fetch('https://us-central1-focusing-416902.cloudfunctions.net/hello', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: userQuestion }), // ユーザーの質問をJSONとして送信
        })
        .then(response => response.json())
        .then(data => {
            if (document.getElementById('typingIndicator')) {
                document.getElementById('typingIndicator').remove();
            }
            const aiMessage = document.createElement('p');
            aiMessage.textContent = "Kai: " + data["Kai's AI"];
            chatBox.appendChild(aiMessage);
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch((error) => {
            console.error('Error:', error);
            if (document.getElementById('typingIndicator')) {
            document.getElementById('typingIndicator').remove();
            }
        });
    });
});
