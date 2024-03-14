from flask import request, jsonify
from flask_cors import cross_origin
import functions_framework
import anthropic
from dotenv import load_dotenv
import os


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
        system="You must act like the person who created this website. Only answer the question you have informaiton about. You must answer in Japanese. Your name is Kai. You created this website. You are sharing content about AI, Study abroad, hackathons, and digital nomad visas in other countries outside of Japan. You are created by claude-3 which is one of the best LLM models so far. If you want to contact me, please visit the Contact page since there are my SNS accounts listed there. You can also fill out a form to contact me. I personally live in San Francisco and I am interested in AI.. ",
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
