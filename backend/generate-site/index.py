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
    'Access-Control-Allow-Headers': 'Content-Type, X-Browser-Id',
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


def get_browser_id(event: dict) -> str | None:
    headers = event.get('headers') or {}
    bid = headers.get('X-Browser-Id') or headers.get('x-browser-id')
    if bid and len(bid) > 4:
        return bid[:128]
    return None


def get_credits(browser_id: str) -> int:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT used, reset_date FROM {SCHEMA}.ai_credits
                    WHERE ip = '{browser_id}'
                """)
                row = cur.fetchone()
                if not row:
                    return DAILY_LIMIT
                used, reset_date = row
                from datetime import date, timezone
                today = date.today()
                if reset_date < today:
                    return DAILY_LIMIT
                return max(0, DAILY_LIMIT - used)
    finally:
        conn.close()


def check_and_spend_credits(browser_id: str) -> tuple[bool, int]:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {SCHEMA}.ai_credits (ip, used, reset_date)
                    VALUES ('{browser_id}', 0, CURRENT_DATE)
                    ON CONFLICT (ip) DO UPDATE
                        SET used = CASE
                            WHEN {SCHEMA}.ai_credits.reset_date < CURRENT_DATE
                            THEN 0
                            ELSE {SCHEMA}.ai_credits.used
                        END,
                        reset_date = CASE
                            WHEN {SCHEMA}.ai_credits.reset_date < CURRENT_DATE
                            THEN CURRENT_DATE
                            ELSE {SCHEMA}.ai_credits.reset_date
                        END,
                        updated_at = NOW()
                    RETURNING used
                """)
                used = cur.fetchone()[0]
                remaining = DAILY_LIMIT - used
                if remaining < COST_PER_REQUEST:
                    return False, 0
                cur.execute(f"""
                    UPDATE {SCHEMA}.ai_credits
                    SET used = used + {COST_PER_REQUEST}, updated_at = NOW()
                    WHERE ip = '{browser_id}'
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
    GET  → возвращает текущий баланс кредитов {credits: int, limit: int}
    POST → генерирует сайт и списывает 1 кредит
    Идентификация по X-Browser-Id (уникальный ID браузера из localStorage).
    Лимит: 1000 кредитов в день, сброс в полночь UTC.
    '''
    method = event.get('httpMethod', 'GET')

    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS, 'body': ''}

    browser_id = get_browser_id(event)
    if not browser_id:
        return {
            'statusCode': 400,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Отсутствует X-Browser-Id'}),
        }

    if method == 'GET':
        remaining = get_credits(browser_id)
        return {
            'statusCode': 200,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({'credits': remaining, 'limit': DAILY_LIMIT}),
        }

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

    ok, remaining = check_and_spend_credits(browser_id)
    if not ok:
        return {
            'statusCode': 429,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Дневной лимит исчерпан. Кредиты обновятся в полночь по UTC.',
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
