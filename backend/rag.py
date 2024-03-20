
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import tempfile
from google.cloud import storage
from firebase_admin import credentials, initialize_app


cred = credentials.Certificate('firebase-adminsdk-75dfj@portfolio-838bf.iam.gserviceaccount.com')
initialize_app(cred, {'storageBucket': 'portfolio-838bf.appspot.com'})

def process_pdf_file(event, context):
    """Firebase Storageのトリガーで呼び出される関数。"""
    file_name = event['name']
    bucket_name = event['bucket']

    # Cloud Storageクライアントの初期化
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # 一時ファイルを作成してPDFファイルをダウンロード
    with tempfile.NamedTemporaryFile() as temp_pdf:
        blob.download_to_filename(temp_pdf.name)
        
        # PDFファイルを処理
        result = process_pdf_to_db(temp_pdf.name)
        print(result)
def process_pdf_to_db(pdf_file_path):
    """
    フロントエンドからアップロードされたPDFファイルを受け取り、
    テキストを抽出してChromaベクトルデータベースに保存する関数。
    """
    # PDFファイルのロード
    loader = PyPDFLoader(pdf_file_path)
    documents = loader.load_and_split()

    # テキストの分割
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)

    # Embeddingsの計算
    embeddings = OpenAIEmbeddings()

    # Chromaベクトルデータベースの構築
    db = Chroma.from_documents(texts, embeddings, persist_directory="./storage")
    db.persist()
    
    return "Process completed and data persisted to the database."

# フロントエンドからアップロードされたPDFファイルのパス
pdf_file_path = "path/to/your/uploaded/file.pdf"

# 関数の実行
result = process_pdf_to_db(pdf_file_path)
print(result)