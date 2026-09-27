export const fields = ['name','email','company','need','budget','timeline'];
export const labels = {name:'姓名',email:'邮箱',company:'公司',need:'具体需求',budget:'预算',timeline:'期望时间'};
export const samples = [
 {title:'电商询盘', message:'您好，我是林悦，来自青禾生活电商。我们想把每天收到的客户询盘自动分类，把联系人和需求录入表格，再生成回复草稿。预算 5000 元，希望两周内完成。请联系 lin.yue@example.com。', result:{name:'林悦',email:'lin.yue@example.com',company:'青禾生活电商',need:'把每天收到的客户询盘自动分类，把联系人和需求录入表格，再生成回复草稿',budget:'5000 元',timeline:'两周内'}},
 {title:'English inquiry',message:'Hi, I am Alex Morgan from Northstar Studio. We need to automate weekly sales reports from Google Sheets. Our budget is EUR 800, and our timeline is three weeks. Please contact alex@example.com.',result:{name:'Alex Morgan',email:'alex@example.com',company:'Northstar Studio',need:'automate weekly sales reports from Google Sheets',budget:'EUR 800',timeline:'three weeks'}},
 {title:'信息不完整',message:'你好，我们团队每周都要花很多时间整理客户发来的 PDF 和表格，想做一个自动提取信息的工具。能否先聊聊怎么实现？',result:{name:'',email:'',company:'',need:'自动提取信息的工具',budget:'',timeline:''}}
];
export function validateMessage(text) {
 if(typeof text!=='string'||text.trim().length<20||text.trim().length>1800) throw new Error('请输入 20–1800 个字符。');
 return text.trim();
}
export function parseResult(text) {
 const start=text.indexOf('{'),end=text.lastIndexOf('}');
 if(start<0||end<=start) throw new Error('模型没有返回有效字段，请简化询盘后重试。');
 let value;try{value=JSON.parse(text.slice(start,end+1));}catch{throw new Error('模型输出格式不完整，请缩短询盘并重试。');}
 if(!value||Array.isArray(value)||typeof value!=='object'||fields.some(f=>typeof value[f]!=='string'))throw new Error('模型返回的字段格式不正确，请重试。');
 return value;
}
export function normalize(text){return text.trim().replace(/\s+/g,' ');}
export function verify(message, extracted, mode='ai') {
 message=validateMessage(message);const result={message,mode,warnings:[]};
 for(const f of fields){let value=typeof extracted[f]==='string'?extracted[f].trim():'';if(value&&!message.toLowerCase().includes(value.toLowerCase())){result.warnings.push(labels[f]+'无法在原文中核实，已留空。');value='';}result[f]=value;}
 const emails=[...new Set(message.match(/[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}/g)||[])];
 result.email=emails.length===1?emails[0]:'';
 if(emails.length>1)result.warnings.push('多个邮箱：请人工确认联系人。');
 result.missing=['name','email','need','budget','timeline'].filter(f=>!result[f]);
 const zh=/[\u4e00-\u9fff]/.test(message);
 result.draft=zh?'您好，感谢您的咨询！我们已收到您的需求。':'Hello, thank you for your inquiry. We have received your request.';
 if(result.missing.length) result.draft+=zh?'\n\n为便于评估，请补充：'+result.missing.map(f=>labels[f]).join('、')+'。':'\n\nCould you share the following: '+result.missing.join(', ')+'?';
 result.draft+=zh?'\n\n确认需求范围后，我们会进一步沟通方案、报价和交付时间。':'\n\nOnce the scope is clear, we can discuss an approach, a quote, and a delivery timeline.';
 return result;
}
export function toCSV(rows){const keys=[...fields,'mode','draft'];const quote=value=>'"'+String(value??'').replace(/^([\s]*[=+@-])/u,"'$1").replace(/"/g,'""')+'"';return '\ufeff'+[keys.map(quote).join(','),...rows.map(r=>keys.map(k=>quote(r[k])).join(','))].join('\r\n');}
