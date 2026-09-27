"""Generate a portable n8n workflow (no credentials)."""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
nodes = []
def node(name, kind, version, position, params, **extra):
    nodes.append(dict(id=str(uuid.uuid5(uuid.NAMESPACE_DNS, 'inquiry-desk/' + name)), name=name, type='n8n-nodes-base.'+kind, typeVersion=version, position=position, parameters=params, **extra))

def post(url, body, timeout=20000):
    return {'method':'POST', 'url':url, 'sendBody':True, 'specifyBody':'json', 'jsonBody':body, 'options':{'timeout':timeout}}

node('Receive inquiry', 'webhook', 2, [0,0], {'httpMethod':'POST', 'path':'portfolio-inquiry-desk-v1', 'responseMode':'responseNode', 'options':{}}, webhookId='portfolio-inquiry-desk-v1')
node('Validate & deduplicate', 'httpRequest', 4.2, [240,0], post('http://host.docker.internal:8769/internal/prepare', '={{ { message: $json.body.message } }}'), retryOnFail=True, maxTries=2, waitBetweenTries=1000)
node('New valid inquiry?', 'if', 2.2, [480,0], {'conditions':{'options':{'caseSensitive':True, 'leftValue':'', 'typeValidation':'strict', 'version':2}, 'conditions':[{'id':'needs-ai', 'leftValue':'={{ $json.needs_ai }}', 'rightValue':True, 'operator':{'type':'boolean','operation':'true','singleValue':True}}], 'combinator':'and'}, 'options':{}})
node('Extract with local Qwen', 'httpRequest', 4.2, [720,-100], post('http://ollama:11434/api/chat', '={{ $json.llm_request }}', 180000), onError='continueRegularOutput')
node('Verify fields & save draft', 'httpRequest', 4.2, [960,-100], post('http://host.docker.internal:8769/internal/finalize', "={{ { prepared: $('Validate & deduplicate').item.json, ai: $json } }}"), retryOnFail=True, maxTries=2, waitBetweenTries=1000)
node('Return result', 'respondToWebhook', 1.4, [1200,0], {'respondWith':'json', 'responseBody':'={{ $json }}', 'options':{'responseCode':'={{ $json.http_status || 200 }}'}})
node('About this portfolio', 'stickyNote', 1, [0,-330], {'content':'## Inquiry Desk · 询盘自动整理\n**n8n 编排 + 本地 Qwen + Python 校验与 SQLite**\n输入校验 → 去重 → AI 提取 → 原文核对 → 草稿与客户记录。\n回复采用校验模板；不会发送邮件。AI 异常时保存原文待人工整理。\n演示入口：http://127.0.0.1:8769\nPython 服务需运行；模型由 Python 服务配置，默认 qwen3-vl:2b。', 'height':250, 'width':620, 'color':4})
def edge(name): return {'node':name,'type':'main','index':0}
connections={
 'Receive inquiry':{'main':[[edge('Validate & deduplicate')]]},
 'Validate & deduplicate':{'main':[[edge('New valid inquiry?')]]},
 'New valid inquiry?':{'main':[[edge('Extract with local Qwen')],[edge('Return result')]]},
 'Extract with local Qwen':{'main':[[edge('Verify fields & save draft')]]},
 'Verify fields & save draft':{'main':[[edge('Return result')]]},
}
workflow={'id':'portfolioInquiryDeskV1','name':'Portfolio 01 | Inquiry Desk 询盘自动整理','active':False,'nodes':nodes,'connections':connections,'settings':{'executionOrder':'v1','executionTimeout':230,'saveDataSuccessExecution':'none','saveDataErrorExecution':'all','timezone':'Europe/Paris'},'pinData':{},'tags':[]}
(ROOT/'workflow.json').write_text(json.dumps(workflow,ensure_ascii=False,indent=2),encoding='utf-8')
print('Generated workflow.json')
