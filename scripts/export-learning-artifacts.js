// Export the editable learning cards and noon cover as raster images.
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const ROOT = path.resolve(__dirname, '..');
const modules = process.env.ARTIFACT_NODE_MODULES;
const getModule = name => require(require.resolve(name, { paths: modules ? [modules] : [ROOT] }));
const { chromium } = getModule('playwright');
const sharp = getModule('sharp');

(async () => {
  const output = path.join(ROOT, 'out/learning-cards-v2');
  fs.mkdirSync(output, { recursive: true });
  const parchment = path.join(ROOT, 'web/img_hd/card_parchment.jpg');
  const { width, height } = await sharp(parchment).metadata();
  const cropped = await sharp(parchment).extract({ left: Math.round(width*.3), top: Math.round(height*.3),
    width: Math.round(width*.4), height: Math.round(height*.4) }).toBuffer();
  await sharp(cropped).resize(1440, 1920, { fit: 'fill' }).jpeg({ quality: 95 }).toFile(path.join(output, 'paper-texture.jpg'));
  const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true, args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1920 }, deviceScaleFactor: 1 });
  const checks=[];
  async function ready() {
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all([...document.images].map(image => image.decode()));
    });
  }
  for (let n=1;n<=4;n++) {
    await page.goto(pathToFileURL(path.join(ROOT,'web/learning-cards-viewer.html')).href+'?page='+n);
    await ready();
    const bounds=await page.evaluate(() => {
      const content=document.querySelector('.content'), footer=document.querySelector('.footer');
      const last=content.lastElementChild.getBoundingClientRect();
      return { bottom:last.bottom, footer:footer.getBoundingClientRect().top,
        widthOverflow:document.documentElement.scrollWidth>1440, heightOverflow:content.scrollHeight>content.clientHeight };
    });
    if(bounds.bottom>bounds.footer-10||bounds.widthOverflow||bounds.heightOverflow) throw new Error('Card overflow: '+n+' '+JSON.stringify(bounds));
    const png=path.join(output,`learning-card-${String(n).padStart(2,'0')}.png`);
    await page.screenshot({path:png});
    checks.push({page:n,...bounds,file:png});
  }
  await page.setViewportSize({width:1920,height:1080});
  await page.goto(pathToFileURL(path.join(ROOT,'web/cover-noon.html')).href);
  await ready();
  const cover=path.join(ROOT,'out/covers/cover-noon-ai-v2-169.png');
  await page.screenshot({path:cover});
  await sharp(cover).jpeg({quality:95}).toFile(cover.replace('.png','.jpg'));
  await sharp(cover).resize(480,270).jpeg({quality:90}).toFile(path.join(output,'cover-mobile-check.jpg'));
  await page.setViewportSize({width:1440,height:1080});
  await page.goto(pathToFileURL(path.join(ROOT,'web/cover-noon.html')).href+'?ratio=43');
  await ready();
  const cover43=path.join(ROOT,'out/covers/cover-noon-ai-v2-43.png');
  await page.screenshot({path:cover43});
  await sharp(cover43).jpeg({quality:95}).toFile(cover43.replace('.png','.jpg'));
  await sharp(cover43).resize(480,360).jpeg({quality:90}).toFile(path.join(output,'cover-43-mobile-check.jpg'));
  for(let n=1;n<=4;n++) await sharp(path.join(output,`learning-card-0${n}.png`))
    .resize(720,960).jpeg({quality:92}).toFile(path.join(output,`learning-card-0${n}-preview.jpg`));
  fs.writeFileSync(path.join(output,'layout-checks.json'),JSON.stringify({cards:checks,cover,cover43},null,2)+'\n');
  await browser.close();
  console.log('Exported four cards and cover:',output,cover);
})().catch(error=>{console.error(error);process.exit(1)});
