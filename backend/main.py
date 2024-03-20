from flask import request, jsonify
from flask_cors import cross_origin
import functions_framework
import anthropic

#get api key from .env file

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
