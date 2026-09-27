"""Exercise the running app through the real n8n webhook and local AI."""
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

SAMPLES = [
    ('zh_complete', '您好，我是林悦，来自青禾生活电商。我们想把每天收到的客户询盘自动分类，把联系人和需求录入表格，再生成回复草稿。现在每天大概有 40 封邮件。预算 5000 元，希望两周内完成。请联系 lin.yue@example.com。'),
    ('en_complete', 'Hi, I am Alex Morgan from Northstar Studio. We need to automate our weekly sales reports from Google Sheets and prepare a summary for review. Our budget is EUR 800, and we would like a first version within three weeks. Please contact alex@example.com.'),
    ('missing_fields', '你好，我们团队每周都要花很多时间整理客户发来的 PDF 和表格，想做一个自动提取信息的工具。能否先聊聊怎么实现？'),
]

def submit(message):
    req = urllib.request.Request('http://127.0.0.1:8769/api/intake', json.dumps({'message':message}).encode(), {'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=245) as response:
        return json.load(response)

if __name__ == '__main__':
    results = []
    for name, message in SAMPLES:
        started = time.monotonic()
        result = submit(message)
        lead = result['lead']
        assert lead['ai_status'] == 'extracted', (name, lead['warnings'])
        assert lead['human_review_required'] is True
        assert lead['message'] == message
        if name == 'zh_complete':
            assert lead['name'] == '林悦', lead
            assert lead['email'] == 'lin.yue@example.com', lead
            assert '5000' in lead['budget'], lead
        if name == 'en_complete':
            assert lead['name'] == 'Alex Morgan', lead
            assert lead['email'] == 'alex@example.com', lead
            assert '800' in lead['budget'], lead
        if name == 'missing_fields':
            assert not lead['email'] and not lead['budget'] and not lead['timeline'], lead
            assert lead['status'] == 'needs_info', lead
        row = {'case':name,'passed':True,'seconds':round(time.monotonic()-started,1),'duplicate':result['duplicate'],'model':lead['model'],'lead_id':lead['id']}
        results.append(row)
        print(json.dumps(row,ensure_ascii=False),flush=True)
    repeated = submit(SAMPLES[0][1])
    assert repeated['duplicate'] is True
    assert repeated['lead']['id'] == results[0]['lead_id']
    results.append({'case':'duplicate_submission','passed':True})
    try:
        submit('short')
        raise AssertionError('Invalid input was accepted')
    except urllib.error.HTTPError as error:
        assert error.code == 400
    results.append({'case':'invalid_input','passed':True})
    with urllib.request.urlopen('http://127.0.0.1:8769/api/export.csv') as response:
        export = response.read().decode('utf-8-sig')
    assert 'lin.yue@example.com' in export and 'alex@example.com' in export
    results.append({'case':'csv_export','passed':True})
    target = Path(__file__).resolve().parent / 'verification.json'
    target.write_text(json.dumps({'tested_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
    print('All six end-to-end checks passed.',flush=True)
