#!/usr/bin/env python3
"""Inspect paired, locally built sites; capture real compositor frames, never ship a script."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import time

from portal_preview import serve
from handbook_toolkit import design

SITES = {
    'template': ('site', 'figures.html', 'manuscript/chapters/01-example.html'),
    'sample': ('site', 'manuscript/chapters/ch01-why-handbooks-fail.html', 'manuscript/chapters/ch02-editorial-contract.html'),
    'portal': ('', 'how-it-works.html', 'create.html'),
}
# Inspection only: records the browser's real native transition, not a replacement animation.
OBSERVER = """addEventListener('pagereveal', event => {
  window.motionProbe = {hasTransition: !!event.viewTransition};
  if (event.viewTransition) {
    event.viewTransition.ready.then(() => {
      motionProbe.start = Date.now();
      motionProbe.animations = [];
      const observe = () => {
        for (const a of document.getAnimations()) {
          const item = {name:a.animationName, duration:a.effect.getTiming().duration,
                        delay:a.effect.getTiming().delay};
          if (!motionProbe.animations.some(x => x.name === item.name)) motionProbe.animations.push(item);
        }
        if (!motionProbe.finish) requestAnimationFrame(observe);
      };
      observe();
    }).catch(error => motionProbe.error = String(error));
    event.viewTransition.finished.then(() => motionProbe.finish = Date.now());
  }
});"""


def regions(page) -> dict[str, int]:
    result = page.evaluate("""() => {
      const names={}; for (const e of document.querySelectorAll('*')) {
        const name=getComputedStyle(e).viewTransitionName;
        if(name && name!=='none') names[name]=(names[name]||0)+1;
      } return names;
    }""")
    if any(value != 1 for value in result.values()):
        raise ValueError('duplicate view-transition-name: ' + str(result))
    return result


def pixel_difference(page, before: bytes, after: bytes) -> dict[str, object]:
    encoded = [base64.b64encode(data).decode() for data in (before, after)]
    return page.evaluate("""async ([a,b]) => {
      const load=async s=>createImageBitmap(await(await fetch('data:image/png;base64,'+s)).blob());
      const [x,y]=await Promise.all([load(a),load(b)]);
      if(x.width!==y.width||x.height!==y.height) throw Error('image dimensions changed');
      const c=document.createElement('canvas');c.width=x.width;c.height=x.height;
      const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(x,0,0);
      const first=ctx.getImageData(0,0,c.width,c.height).data;ctx.clearRect(0,0,c.width,c.height);
      ctx.drawImage(y,0,0);const second=ctx.getImageData(0,0,c.width,c.height).data;
      let changed=0,minX=c.width,minY=c.height,maxX=-1,maxY=-1;for(let i=0;i<first.length;i+=4)
        if(first[i]!==second[i]||first[i+1]!==second[i+1]||first[i+2]!==second[i+2]||first[i+3]!==second[i+3]){changed++;let x=(i/4)%c.width,y=Math.floor(i/4/c.width);minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
      return {width:c.width,height:c.height,changed,bounds:changed?[minX,minY,maxX,maxY]:null};
    }""", encoded)


def sheet(page, frames: list[tuple[str, bytes]], path: Path, width: int) -> None:
    colors = design.load_tokens()['color']
    payload = {'frames':[(label,base64.b64encode(data).decode()) for label,data in frames],
               'width':width, 'canvas':colors['canvas']['light'], 'text':colors['text']['light']}
    result = page.evaluate("""async data => {
      const images=await Promise.all(data.frames.map(async([label,s])=>[label,
        await createImageBitmap(await(await fetch('data:image/png;base64,'+s)).blob())]));
      const w=data.width,h=Math.round(images[0][1].height*w/images[0][1].width),label=28,cols=4;
      const c=document.createElement('canvas');c.width=cols*w;c.height=Math.ceil(images.length/cols)*(h+label);
      const x=c.getContext('2d');x.fillStyle=data.canvas;x.fillRect(0,0,c.width,c.height);
      x.fillStyle=data.text;x.font='14px sans-serif';
      images.forEach(([text,image],i)=>{const left=i%cols*w,top=Math.floor(i/cols)*(h+label);
        x.fillText(text,left+8,top+19);x.drawImage(image,left,top+label,w,h);});
      return c.toDataURL('image/png').split(',')[1];
    }""", payload)
    path.write_bytes(base64.b64decode(result))


def navigation(context, source: str, target: str, output: Path, compositor, reduced: bool) -> dict:
    page = context.new_page()
    page.bring_to_front()
    page.goto(source, wait_until='networkidle');page.evaluate('document.fonts.ready')
    page.wait_for_timeout(500)
    initial = page.screenshot()
    frames: list[tuple[float, bytes]] = []
    cdp = context.new_cdp_session(page)
    def receive(event):
        frames.append((event['metadata'].get('timestamp', time.time()) * 1000,
                       base64.b64decode(event['data'])))
        cdp.send('Page.screencastFrameAck', {'sessionId':event['sessionId']})
    cdp.on('Page.screencastFrame', receive)
    page.bring_to_front()
    cdp.send('Page.startScreencast', {'format':'png','everyNthFrame':1})
    clicked = time.time() * 1000
    # Follow an existing native link without Playwright auto-scrolling to an offscreen Next button.
    page.locator('a').evaluate_all("""(nodes,target)=>{
      const link=nodes.find(n=>n.hasAttribute('href') && new URL(n.getAttribute('href'),location.href).href===target);
      if(!link)throw Error('No native navigation link to '+target);link.click();
    }""", target)
    page.wait_for_url(target);page.wait_for_load_state('networkidle');page.wait_for_timeout(500)
    cdp.send('Page.stopScreencast')
    probe = page.evaluate('window.motionProbe') or {}
    page.evaluate('document.fonts.ready')
    geometry=page.evaluate('({scrollY, width:innerWidth, height:innerHeight})')
    final = page.screenshot()
    if probe.get('hasTransition'):
        raise ValueError('navigation unexpectedly created a view transition')
    start = probe.get('start', clicked)
    chosen = [('before', initial)]
    for milliseconds in range(0, 401, 40):
        eligible = [(stamp,data) for stamp,data in frames if stamp <= start+milliseconds]
        chosen.append((f'{milliseconds} ms', eligible[-1][1] if eligible else initial))
    chosen.append(('settled', final))
    sheet(compositor, chosen, output, 300 if context.pages[0].viewport_size['width']>400 else 195)
    page.close()
    return {'probe':probe, 'settled_geometry':geometry, 'compositor_frames':len(frames), 'sheet':output.name,
            'timestamps_ms':[round(stamp-start,1) for stamp,_data in frames]}


def inspect(root: Path, output: Path, *, software_at_rest: bool = False) -> dict:
    from playwright.sync_api import sync_playwright
    output.mkdir(parents=True)
    (output/'screenshots').mkdir();(output/'contact-sheets').mkdir()
    report = {'at_rest':{}, 'navigation':{}, 'page_contracts':{}, 'network':[]}
    with serve(root) as base, sync_playwright() as p:
        static_args=[
            '--disable-gpu','--disable-gpu-compositing','--disable-gpu-rasterization','--force-color-profile=srgb'] if software_at_rest else []
        browser=p.chromium.launch(args=static_args)
        native_browser=p.chromium.launch()
        report['chromium']=browser.version
        report['renderer']={'at_rest_args':static_args,'navigation_args':[],'device_scale_factor':1}
        compositor=browser.new_page()
        for name,(subfolder,source,target) in SITES.items():
            roots = {phase:root/(name+'-'+phase)/subfolder for phase in ('before','after')}
            copies=list(roots['after'].rglob('reading.css'))
            if len(copies)!=1 or copies[0].read_text()!=design.reading_css():
                raise ValueError(f'{name}: built motion CSS does not match the current toolkit')
            # Every generated page must retain exactly the same script inventory.
            for relative in sorted(path.relative_to(roots['after']) for path in roots['after'].rglob('*.html')):
                from html_support import Document
                markup=(roots['after']/relative).read_text()
                if 'view-transition' in design.reading_css():
                    raise ValueError('page transition CSS remains')
                document=Document(markup).root
                if document.find('link', rel='expect'):
                    raise ValueError(f'unexpected render-blocking capture link: {name}/{relative}')
                if sum(node.attrs.get('id')=='quarto-html-after-body' for node in document.walk())!=1:
                    raise ValueError(f'missing/ambiguous Quarto body completion marker: {name}/{relative}')
                def inventory(path):
                    doc=Document(path.read_text()).root
                    return [(node.attrs.get('src'),hashlib.sha256(node.text().encode()).hexdigest()) for node in doc.find('script')]
                if inventory(roots['before']/relative)!=inventory(roots['after']/relative):
                    raise ValueError(f'added/changed script: {name}/{relative}')
            for width in (1440,390):
                for scheme in ('light','dark'):
                    for preference in ('no-preference','reduce'):
                        key=f'{name}.{width}.{scheme}.{preference}'
                        scenario_browser=p.chromium.launch(args=static_args)
                        context=scenario_browser.new_context(viewport={'width':width,'height':1000},color_scheme=scheme,reduced_motion=preference)
                        def observe_request(request):
                            if not request.url.startswith(base):report['network'].append(request.url)
                        context.on('request',observe_request)
                        for relative in ('index.html',source,target):
                            images=[]; computed=[]
                            for phase in ('before','after'):
                                # At-rest comparisons are independent first loads, not a cross-build navigation.
                                page=context.new_page()
                                url=base+(roots[phase]/relative).relative_to(root).as_posix()
                                page.goto(url,wait_until='networkidle');page.mouse.move(0,0)
                                page.evaluate('document.fonts.ready');page.wait_for_timeout(600)
                                if phase=='after':report['page_contracts'][key+'/'+relative]=regions(page)
                                computed.append(page.locator('#quarto-header, #quarto-sidebar, #quarto-margin-sidebar, main, #title-block-header, footer.footer, .callout, figure, table, caption').evaluate_all('''nodes=>nodes.map(e=>{
                                  const s=getComputedStyle(e),r=e.getBoundingClientRect();
                                  if(r.bottom<=0||r.top>=innerHeight||r.width===0||r.height===0)return null;
                                  return {tag:e.tagName,id:e.id,rect:[r.x,r.y,r.width,r.height],color:s.color,
                                    background:s.backgroundColor,font:s.font,border:s.border};}).filter(Boolean)'''))
                                path=output/'screenshots'/f'{key}.{relative.replace("/","--")}.{phase}.png'
                                images.append(page.screenshot(path=str(path)))
                                page.close()
                            diff=pixel_difference(compositor,*images)
                            diff['computed_equal'] = computed[0] == computed[1]
                            report['at_rest'][key+'/'+relative]=diff
                            (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
                        native_context=native_browser.new_context(viewport={'width':width,'height':1000},
                            color_scheme=scheme,reduced_motion=preference)
                        native_context.add_init_script(OBSERVER)
                        native_context.on('request',observe_request)
                        source_url=base+(roots['after']/source).relative_to(root).as_posix()
                        target_url=base+(roots['after']/target).relative_to(root).as_posix()
                        skipped=[]
                        for attempt in range(3):
                            try:
                                result=navigation(native_context,source_url,target_url,
                                    output/'contact-sheets'/(key+'.png'),compositor,preference=='reduce')
                                report['navigation'][key]={**result,'browser_skips':skipped}
                                break
                            except RuntimeError as error:
                                skipped.append(str(error))
                                if attempt==2:raise
                        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
                        native_context.close()
                        context.close()
                        scenario_browser.close()
                        print(key, 'captured',flush=True)
        native_browser.close()
        browser.close()
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    changed={key:value for key,value in report['at_rest'].items() if value['changed']}
    if changed:raise ValueError('at-rest pixel differences: '+str(changed))
    if report['network']:raise ValueError('external browser requests: '+str(report['network']))
    return report


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--software-at-rest',action='store_true',
                        help='Diagnostic: use software compositing for the static pixel comparison.')
    args=parser.parse_args()
    if args.output.exists():parser.error('output must be new')
    inspect(args.root.resolve(),args.output.resolve(),software_at_rest=args.software_at_rest)


if __name__=='__main__':
    # Reuse the repository's parsed HTML helper, not regexes over markup.
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
    main()
