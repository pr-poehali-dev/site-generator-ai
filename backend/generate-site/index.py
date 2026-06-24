import json
import os
import re
import urllib.request
import psycopg2

DAILY_LIMIT = 1000
COST_PER_REQUEST = 1

API_URL = 'https://openrouter.ai/api/v1/chat/completions'
MODEL = 'meta-llama/llama-3.3-70b-instruct:free'

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

SCHEMA = 't_p63123944_site_generator_ai'


def get_ip(event: dict) -> str:
    return (
        event.get('requestContext', {}).get('identity', {}).get('sourceIp')
        or event.get('headers', {}).get('X-Forwarded-For', 'unknown').split(',')[0].strip()
    )


def check_and_spend_credits(ip: str) -> tuple[bool, int]:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {SCHEMA}.ai_credits (ip, used, reset_date)
                    VALUES ('{ip}', 0, CURRENT_DATE AT TIME ZONE 'UTC')
                    ON CONFLICT (ip) DO UPDATE
                        SET used = CASE
                            WHEN {SCHEMA}.ai_credits.reset_date < (CURRENT_DATE AT TIME ZONE 'UTC')
                            THEN 0
                            ELSE {SCHEMA}.ai_credits.used
                        END,
                        reset_date = CASE
                            WHEN {SCHEMA}.ai_credits.reset_date < (CURRENT_DATE AT TIME ZONE 'UTC')
                            THEN CURRENT_DATE AT TIME ZONE 'UTC'
                            ELSE {SCHEMA}.ai_credits.reset_date
                        END,
                        updated_at = NOW()
                    RETURNING used
                """)
                used = cur.fetchone()[0]
                remaining = DAILY_LIMIT - used
                if remaining < COST_PER_REQUEST:
                    return False, remaining
                cur.execute(f"""
                    UPDATE {SCHEMA}.ai_credits
                    SET used = used + {COST_PER_REQUEST}, updated_at = NOW()
                    WHERE ip = '{ip}'
                """)
                return True, remaining - COST_PER_REQUEST
    finally:
        conn.close()


def extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r'^```[a-z]*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'```$', '', text, flags=re.MULTILINE)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def handler(event: dict, context) -> dict:
    '''
    Генерирует структуру сайта через OpenRouter Llama 3.3 70B.
    Лимит: 1000 кредитов в день на IP, сброс в полночь UTC.
    POST {prompt: str} → {site: {...}, credits_remaining: int}
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

    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        return {
            'statusCode': 500,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'ИИ временно недоступен'}),
        }

    ip = get_ip(event)
    ok, remaining = check_and_spend_credits(ip)
    if not ok:
        return {
            'statusCode': 429,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': f'Дневной лимит исчерпан. Кредиты обновятся в полночь по UTC.',
                'credits_remaining': 0,
            }),
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
        API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://poehali.dev',
            'X-Title': 'NebulaAI Site Generator',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f'OpenRouter HTTP {e.code}: {err_body}')
        return {
            'statusCode': 502,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'OpenRouter {e.code}: {err_body}'}),
        }

    print('OpenRouter response:', json.dumps(data)[:500])

    raw = data['choices'][0]['message']['content']
    site = extract_json(raw)

    return {
        'statusCode': 200,
        'headers': {**CORS, 'Content-Type': 'application/json'},
        'body': json.dumps({'site': site, 'credits_remaining': remaining}, ensure_ascii=False),
    }
