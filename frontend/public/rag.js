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
        // バックエンドへの通知やファイル処理のトリガーをここに実装
    });
});
