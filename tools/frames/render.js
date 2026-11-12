// node tools/frames/render.js <dir> [scale=2]: render every <dir>/*.svg to PNG at deviceScaleFactor=scale, transparent
const {chromium}=require('playwright');const fs=require('fs');
const dir=process.argv[2], sc=+(process.argv[3]||2);
(async()=>{const b=await chromium.launch();const ctx=await b.newContext({viewport:{width:800,height:600},deviceScaleFactor:sc});const p=await ctx.newPage();
for(const f of fs.readdirSync(dir).filter(f=>f.endsWith('.svg'))){const s=fs.readFileSync(dir+'/'+f,'utf8');
 const m=s.match(/width="([\d.]+)" height="([\d.]+)"/);const w=Math.ceil(+m[1]),h=Math.ceil(+m[2]);
 await p.setViewportSize({width:w,height:h});
 await p.setContent('<html><body style="margin:0;background:transparent"><img style="display:block" src="data:image/svg+xml;base64,'+Buffer.from(s).toString('base64')+'" width="'+w+'" height="'+h+'"></body></html>');
 await p.waitForTimeout(30);await p.screenshot({path:dir+'/'+f.replace('.svg',sc==2?'.png':'@'+sc+'.png'),omitBackground:true,clip:{x:0,y:0,width:w,height:h}});}
await b.close();})();
