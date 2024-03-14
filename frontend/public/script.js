document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('questionForm');
    form.addEventListener('submit', function(event) {
        event.preventDefault(); // フォームのデフォルト送信を防止

        const userQuestion = document.getElementById('userQuestion').value;

        fetch('https://us-central1-focusing-416902.cloudfunctions.net/hello', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: userQuestion }), // ユーザーの質問をJSONとして送信
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            document.getElementById('response').textContent = data["Kai's AI"];
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    });
});
