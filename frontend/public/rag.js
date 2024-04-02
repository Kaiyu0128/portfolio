document.getElementById('fileDropArea').addEventListener('dragover', function(e) {
    e.preventDefault(); // デフォルトの処理をキャンセル
    e.stopPropagation();
    this.style.backgroundColor = "#e9e9e9"; // 視覚的フィードバック
});

document.getElementById('fileDropArea').addEventListener('drop', function(e) {
    e.preventDefault();
    e.stopPropagation();
    this.style.backgroundColor = ""; // 背景色を元に戻す

    const file = e.dataTransfer.files[0]; // ドロップされたファイルを取得

    const storageRef = firebase.storage().ref();
    const fileRef = storageRef.child('path/to/save/' + file.name);
    fileRef.put(file).then(function(snapshot) {
        console.log('Uploaded a file!');
        window.uploadedFilePath = 'gs://portfolio-838bf.appspot.com/path/to/save/' + file.name;
        // バックエンドへの通知やファイル処理のトリガーをここに実装
        const functionUrl = 'https://us-central1-focusing-416902.cloudfunctions.net/process_pdf_file';
            fetch(functionUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filePath: snapshot.ref.fullPath })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Cloud Function response:', data);
                // Handle the response from the Cloud Function as needed
            })
            .catch(error => {
                console.error('Error calling Cloud Function:', error);
    });
}); 
}
);

/*
document.getElementById('generateChatbot').addEventListener('click', function() {
    // アップロードされたファイルのフルパスを使う
    const uploadedFilePath = window.uploadedFilePath; // これはファイルをアップロードした後に設定する必要があります

    const functionUrl = 'https://REGION-PROJECT_ID.cloudfunctions.net/process_pdf_file';
    fetch(functionUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filePath: uploadedFilePath })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Cloud Function response:', data);
    })
    .catch(error => {
        console.error('Error calling Cloud Function:', error);
    });
});


// Google Cloud FunctionのURL
// Chat Bot (RAG)
/*
document.addEventListener('DOMContentLoaded', function() {
    // フォームの送信イベントリスナーを設定
    document.getElementById('chatForm').addEventListener('submit', function(event) {
        event.preventDefault(); // フォームのデフォルト送信動作をキャンセル
        sendChat();
    });
});

//google cloud functionのURLをパスに設定するべき。
const cloudFunctionUrl = 'YOUR_CLOUD_FUNCTION_URL';

function sendChat() {
    var inputElement = document.getElementById("chatInput");
    var message = inputElement.value;
    if (message.trim() === "") {
        return; // メッセージが空の場合は何もしない
    }
    displayMessage("user", message); // ユーザーメッセージを表示
    inputElement.value = ""; // 入力欄をクリア
    displayTypingIndicator(); // タイピングインジケーターを表示

    // ユーザーのメッセージをバックエンドに送信
    fetch(cloudFunctionUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        // 応答メッセージを表示
        removeTypingIndicator(); // タイピングインジケーターを削除
        displayMessage("RAG + LLM", data.response);
    })
    .catch(error => {
        console.error('Error:', error);
        removeTypingIndicator(); // タイピングインジケーターを削除
        displayMessage("RAG + LLM", "エラーが発生しました。");
    });
}

function displayMessage(sender, message) {
    var chatHistory = document.getElementById("chatHistory");
    var messageElement = document.createElement("div");
    if (sender === "user") {
        messageElement.style.textAlign = "right";
    } else {
        messageElement.style.textAlign = "left";
    }
    messageElement.textContent = message;
    chatHistory.appendChild(messageElement);
    chatHistory.scrollTop = chatHistory.scrollHeight; // スクロールを最下部に
}
*/