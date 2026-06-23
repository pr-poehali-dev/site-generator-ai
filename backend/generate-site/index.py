import json
import os
import re
import urllib.request


GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
MODEL = 'llama-3.3-70b-versatile'

CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
}

SYSTEM = (
    'You are a professional website content generator. '
    'Given any user description in any language, generate a complete one-page website structure. '
    'Respond ONLY with a valid JSON object, no markdown, no code blocks, no extra text. '
    'JSON schema: '
    '{"title": string, "tagline": string, '
    '"sections": [{"heading": string, "text": string}], '
    '"cta": string, "colors": {"primary": "#hex", "accent": "#hex"}}. '
    'Generate 4-6 sections. Make texts compelling, vivid, and in the same language as the user request. '
    'Choose colors that match the business theme.'
)


def extract_json(text: str) -> dict:
    text = text.strip()
    # убираем markdown-блоки если модель всё же добавила
    text = re.sub(r'^```[a-z]*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    return json.loads(text)


def handler(event: dict, context) -> dict:
    '''
    Генерирует структуру и контент сайта по описанию пользователя через Groq Llama 3.
    Принимает POST с телом {prompt: str}, возвращает {site: {...}}.
    Работает без ограничений — open-source модель Llama 3.3 70B.
    '''
    method = event.get('httpMethod', 'GET')

    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS, 'body': ''}

    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'}),
        }

    try:
        body = json.loads(event.get('body') or '{}')
    except Exception:
        body = {}

    prompt = (body.get('prompt') or '').strip()
    if not prompt:
        return {
            'statusCode': 400,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Опишите, какой сайт вы хотите создать'}),
        }

    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        return {
            'statusCode': 500,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'ИИ временно недоступен — добавьте GROQ_API_KEY'}),
        }

    payload = {
        'model': MODEL,
        'messages': [
            {'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.85,
        'max_tokens': 2048,
    }

    req = urllib.request.Request(
        GROQ_API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))

    raw = data['choices'][0]['message']['content']
    site = extract_json(raw)

    return {
        'statusCode': 200,
        'headers': {**CORS, 'Content-Type': 'application/json'},
        'body': json.dumps({'site': site}, ensure_ascii=False),
    }
