(focusOnly, belowMinimum) => {
  const out = {contrast: [], graphics: [], targets: [], fonts: [], motion: [], structure: [], reduced: [], names: []};
  const controls = 'button,input:not([type="hidden"]),select,textarea,a[href],summary,[role="button"]';
  const inactiveControl = el => {
    const control=el.closest(controls);
    return control && (control.matches(':disabled') || control.getAttribute('aria-disabled')==='true');
  };
  const id = el => el.id ? `#${el.id}` : el.dataset.projectId ? `[data-project-id="${el.dataset.projectId}"]` : `${el.tagName.toLowerCase()}.${String(el.className.baseVal ?? el.className).trim().replace(/\s+/g, '.')}`;
  const rendered = el => {
    if (!el.getClientRects().length || el.closest('[hidden],[inert],script,style')) return false;
    for (let p = el; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.display === 'none' || s.visibility === 'hidden') return false;
      if (p.tagName === 'DETAILS' && !p.open && !p.querySelector('summary')?.contains(el)) return false;
    }
    return true;
  };
  // Canvas resolves OKLCH, named colours and alpha without assuming a white page.
  const ctx = document.createElement('canvas').getContext('2d', {willReadFrequently:true});
  const rgba = color => { ctx.clearRect(0,0,1,1); ctx.fillStyle=color; ctx.fillRect(0,0,1,1); return [...ctx.getImageData(0,0,1,1).data].map((v,i)=>i===3?v/255:v); };
  const blend = (fg,bg) => fg.slice(0,3).map((v,i)=>v*fg[3]+bg[i]*(1-fg[3])).concat(1);
  const background = el => {
    const chain=[];
    for(let p=el;p;p=p.parentElement) chain.unshift(p);
    let color=[255,255,255,1];
    for(const p of chain) color=blend(rgba(getComputedStyle(p).backgroundColor),color);
    return color;
  };
  const lum = rgb => rgb.slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
  const ratio = (a,b) => (Math.max(lum(a),lum(b))+.05)/(Math.min(lum(a),lum(b))+.05);
  const opacity = el => {let n=1;for(let p=el;p;p=p.parentElement)n*=Number(getComputedStyle(p).opacity);return n;};
  const checkRing = active => {
    const s=getComputedStyle(active);
    if(s.outlineStyle!=='none' && parseFloat(s.outlineWidth)>0) {
      const bg=background(active.parentElement), c=rgba(s.outlineColor), value=ratio(blend(c,bg),bg);
      if(belowMinimum(value,3))out.graphics.push(`${id(active)} focus ${value.toFixed(2)} < 3`);
    }
  };
  if(focusOnly === 'all') {
    for(const el of document.querySelectorAll(controls+', [tabindex]:not([tabindex="-1"])'))if(rendered(el) && !el.disabled && el.getAttribute('aria-disabled')!=='true') {
      el.focus({preventScroll:true});
      if(document.activeElement===el)checkRing(el);
    }
    return out;
  }
  const active=document.activeElement;
  if(active && rendered(active))checkRing(active);
  if(focusOnly)return out;
  const textElements = [...document.querySelectorAll('body *')].filter(el=>rendered(el) && [...el.childNodes].some(n=>n.nodeType===3 && n.textContent.trim()));
  for(const el of textElements) {
    const s=getComputedStyle(el), size=parseFloat(s.fontSize), bold=Number(s.fontWeight)>=700;
    const bg=background(el), color=rgba(s.color); color[3]*=opacity(el);
    const value=ratio(blend(color,bg),bg), minimum=size>=24 || (size>=18.66 && bold)?3:4.5;
    // WCAG contrast excludes inactive controls, including Leaflet's disabled zoom.
    // An aria-disabled attribute on ordinary prose does not create that exemption.
    if(!inactiveControl(el) && belowMinimum(value,minimum)) out.contrast.push(`${id(el)} ${value.toFixed(2)} < ${minimum}`);
    const mapLabel=el.closest('.state-label,.city-label-icon,[data-map-label]');
    const functional=el.closest(controls+',label,output,[role="status"],.count,.row-rank,.leaflet-control-attribution');
    const floor=mapLabel?9:functional?11:12;
    let scale=1;
    for(let p=el;p;p=p.parentElement) {const m=getComputedStyle(p).transform;if(m!=='none'){const matrix=new DOMMatrix(m);scale*=Math.hypot(matrix.a,matrix.b);}}
    if(belowMinimum(size*scale,floor)) out.fonts.push(`${id(el)} ${size*scale} < ${floor}`);
    if(matchMedia('(prefers-reduced-motion: reduce)').matches && opacity(el)<.01) out.reduced.push(`${id(el)} hidden text`);
  }
  for(const el of document.querySelectorAll(controls)) {
    if(!rendered(el)) continue;
    const s=getComputedStyle(el), r=el.getBoundingClientRect();
    // The label is part of the native checkbox/radio hit target.
    const label=el.matches('input[type="checkbox"],input[type="radio"]') ? el.labels?.[0] : null;
    const hit=label?.getBoundingClientRect() ?? r;
    if(innerWidth<=390 && (belowMinimum(hit.width,44) || belowMinimum(hit.height,44))) out.targets.push(`${id(el)} ${hit.width.toFixed(3)} x ${hit.height.toFixed(3)}`);
    if(innerWidth<=390 && el.matches('input:not([type="checkbox"]):not([type="radio"]):not([type="range"]),select,textarea') && belowMinimum(parseFloat(s.fontSize),16)) out.fonts.push(`${id(el)} phone input ${s.fontSize} < 16`);
    if(!el.disabled) for(const side of ['Top','Right','Bottom','Left']) {
      const border=rgba(s[`border${side}Color`]);
      if(parseFloat(s[`border${side}Width`])>0 && s[`border${side}Style`]!=='none' && border[3]>0) {
        const bg=background(el.parentElement), value=ratio(blend(border,bg),bg);
        if(belowMinimum(value,3)) {out.graphics.push(`${id(el)} border ${value.toFixed(2)} < 3`);break;}
      }
    }
    const name=el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')?.split(/\s+/).map(key=>document.getElementById(key)?.textContent||'').join(' ') || [...(el.labels||[])].map(n=>n.textContent).join(' ') || el.textContent || el.getAttribute('title');
    if(!name?.trim()) out.structure.push(`${id(el)} unlabelled control`);
  }
  for(const el of document.querySelectorAll('.sample,[data-testid="project-feature"],.project-line')) {
    if(!rendered(el))continue;
    const s=getComputedStyle(el), color=rgba(el.matches('.sample')?s.borderTopColor:s.stroke);
    color[3]*=opacity(el)*(el.matches('.sample')?1:Number(s.strokeOpacity));
    if(color[3]===0)continue;
    const land=getComputedStyle(document.documentElement).getPropertyValue('--map-land').trim();
    const bg=el.closest('#map') && land?rgba(land):background(el.parentElement), value=ratio(blend(color,bg),bg);
    if(belowMinimum(value,3))out.graphics.push(`${id(el)} line ${value.toFixed(2)} < 3`);
  }
  for(const el of document.querySelectorAll('body *')) {
    if(!rendered(el))continue;
    const s=getComputedStyle(el), props=s.transitionProperty.split(',').map(x=>x.trim()), durations=s.transitionDuration.split(',').map(x=>parseFloat(x)*1000);
    for(let i=0;i<props.length;i++) if(durations[i%durations.length]>0) {
      if(!['transform','opacity','none'].includes(props[i]))out.motion.push(`${id(el)} transition ${props[i]}`);
      const cap=el.matches('.panel,[data-sheet]')?500:300;
      if(durations[i%durations.length]>cap)out.motion.push(`${id(el)} duration > ${cap}`);
    }
    if(durations.some(n=>n>0) && /(^|,\s*)ease-in(,|$)/.test(s.transitionTimingFunction))out.motion.push(`${id(el)} ease-in`);
    if(matchMedia('(prefers-reduced-motion: reduce)').matches && s.animationName!=='none' && s.animationIterationCount.split(',').some(x=>x.trim()==='infinite'))out.reduced.push(`${id(el)} endless animation`);
  }
  if(document.querySelectorAll('h1').length!==1)out.structure.push('expected one h1');
  if(!document.documentElement.lang.trim())out.structure.push('missing lang');
  if(!document.title.trim())out.structure.push('missing title');
  if(![...document.querySelectorAll('[role="region"]')].some(el=>/map/i.test(el.getAttribute('aria-label')||document.getElementById(el.getAttribute('aria-labelledby'))?.textContent||'')))out.structure.push('missing named map region');
  let previous=0;
  for(const h of document.querySelectorAll('h1,h2,h3,h4,h5,h6'))if(rendered(h)){const level=Number(h.tagName[1]);if(level>previous+1)out.structure.push(`${id(h)} skipped heading ${previous} to ${level}`);previous=level;}
  for(const el of document.querySelectorAll('[data-src="name"],[data-src="a_name"],[data-src="b_name"],[data-src="label"]')) {
    if(!rendered(el))continue;
    const s=getComputedStyle(el);
    if((el.scrollWidth>el.clientWidth+1 || el.scrollHeight>el.clientHeight+1) && ['hidden','clip'].includes(s.overflow) && el.getAttribute('title')!==el.textContent)out.names.push(`${id(el)} clipped source name`);
  }
  for(const category of Object.keys(out))out[category]=[...new Set(out[category])];
  return out;
}
