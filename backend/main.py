from flask import request, jsonify
from flask_cors import cross_origin
import functions_framework
import anthropic

import tempfile
from google.cloud import storage
import firebase_admin
from firebase_admin import firestore, credentials
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma


@functions_framework.http
@cross_origin()
def hello(request):
    if request.content_type == 'application/json':
        request_json = request.get_json(silent=True)
        if request_json and 'content' in request_json:
            user_content = request_json['content']
        else:
            user_content = '何も聞かれていません。'
    else:
        return 'Invalid content type', 415

    client = anthropic.Anthropic(
        api_key = "",
    )
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.0,
        system="Act as a person who developed this website. Answer in the language that the user used. The website includes information about nomad visa, generative AI and hackathon. Be friendly to the user and only answer the quesiton that you can answer. The user can go to contact-me page to see the developer's SNS. Article page includes information about Digital Nomad Visa, Generative AI and hackathon.",
        messages=[
            {"role": "user", "content": user_content}
        ]
    )
    # 結果の処理
    if message.content and isinstance(message.content, list):
        # response.contentの最初の要素を取得し、辞書に変換する
        first_content_block = message.content[0]  # 最初のContentBlockオブジェクト
        text_response = first_content_block.text
    else:
            text_response = 'ライオン'
    return jsonify({"Kai's AI": text_response})



cred = credentials.Certificate('gs://portfolio-838bf.appspot.com/path/to/save/private.json')
firebase_admin.initialize_app(cred)
def process_pdf_file(request):
    """Cloud Function to process PDF files uploaded to Firebase Storage."""
    file_path = request.get_json().get('filePath')

    # Initialize the Cloud Storage cliente
    storage_client = storage.Client()
    bucket_name, file_name = file_path.split('/', 1)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Download the PDF file to a temporary file
    with tempfile.NamedTemporaryFile() as temp_pdf:
        blob.download_to_filename(temp_pdf.name)
        
        # Process the PDF file
        result = process_pdf_to_db(temp_pdf.name)

    return 'PDF file processed successfully.'

def process_pdf_to_db(pdf_file_path):
    """
    Process the uploaded PDF file, extract text, and store in a Chroma vector database.
    """
    # Load the PDF file
    loader = PyPDFLoader(pdf_file_path)
    documents = loader.load_and_split()

    # Split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)

    # Calculate embeddings
    embeddings = OpenAIEmbeddings()

    # Build the Chroma vector database
    db = Chroma.from_documents(texts, embeddings, persist_directory="./storage")
    db.persist()

    return "Process completed and data persisted to the database."