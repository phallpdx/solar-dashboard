const {chromium}=require('playwright');const fs=require('fs');const {execFileSync}=require('child_process');
const dir=__dirname+'/out/'+process.argv[2];
(async()=>{const b=await chromium.launch();const p=await (await b.newContext({viewport:{width:600,height:600},deviceScaleFactor:2})).newPage();
for(const f of fs.readdirSync(dir).filter(f=>f.endsWith('.svg'))){const [w,h]=f.match(/(\d+)x(\d+)/).slice(1).map(Number);
 await p.setViewportSize({width:w+20,height:h+20});await p.setContent('<body style="margin:10px;background:#fff"><img src="data:image/svg+xml;base64,'+fs.readFileSync(dir+'/'+f).toString('base64')+'" width="'+w+'" height="'+h+'"></body>');
 await p.waitForTimeout(100);const o=dir+'/'+f.replace('.svg','.png');await p.screenshot({path:o});try{execFileSync('python3',[__dirname+'/simulate.py',o,o.replace('.png','-eink.png')]);}catch(e){}}
await b.close();})();
