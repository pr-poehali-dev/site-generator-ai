import json
import os
import urllib.request


def handler(event: dict, context) -> dict:
    '''
    Business: генерирует структуру и контент сайта по текстовому описанию пользователя через ИИ.
    Args: event с httpMethod, body (JSON {prompt: str}); context с request_id.
    Returns: HTTP-ответ с JSON {title, tagline, sections:[{heading, text}], cta, colors}.
    '''
    method = event.get('httpMethod', 'GET')

    cors = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '86400',
    }

    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': cors, 'body': ''}

    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {**cors, 'Content-Type': 'application/json'},
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
            'headers': {**cors, 'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Опишите, какой сайт вы хотите создать'}),
        }

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return {
            'statusCode': 500,
            'headers': {**cors, 'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'ИИ временно недоступен'}),
        }

    system = (
        'Ты — ИИ-конструктор сайтов. По описанию пользователя на любом языке '
        'сгенерируй контент для одностраничного сайта. Отвечай СТРОГО в JSON без markdown. '
        'Структура: {"title": str, "tagline": str, '
        '"sections": [{"heading": str, "text": str}] (4-5 блоков), '
        '"cta": str, "colors": {"primary": "#hex", "accent": "#hex"}}. '
        'Тексты живые, продающие, на языке запроса.'
    )

    payload = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.8,
        'response_format': {'type': 'json_object'},
    }

    req = urllib.request.Request(
        'https://api.openai.com/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))

    content = data['choices'][0]['message']['content']
    site = json.loads(content)

    return {
        'statusCode': 200,
        'headers': {**cors, 'Content-Type': 'application/json'},
        'body': json.dumps({'site': site}, ensure_ascii=False),
        'isBase64Encoded': False,
    }
