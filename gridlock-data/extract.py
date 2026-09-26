import re, csv, pypdf
# --- SERTP (Southern BA = Georgia Power / Southern Co.) ---
t=open('sertp_2025_rtp.txt',encoding='utf-8').read()
pages=re.split(r'=====PAGE (\d+)\n',t)
rows=[]; ba=None
for i in range(1,len(pages),2):
    pno=int(pages[i]); body=pages[i+1]
    m=re.search(r'(\S[\w &/\-]+?) Balancing Authority Area',body)
    if m: ba=m.group(1).replace('SERTP TRANSMISSION PROJECTS (CEII)','').strip()
    for e in re.split(r'In-Service\s*\n\s*Year:\s*\n',body)[1:]:
        y=re.match(r'\s*(\d{4})',e)
        n=re.search(r'Project Name:\s*(.+?)\nDescription:',e,re.S)
        d=re.search(r'Description:\s*(.+?)(?:\n\s*\nSupporting|\nSupporting)',e,re.S)
        s=re.search(r'Statements:\s*(.+?)(?:\n\s*\n\s*\n|$)',e,re.S)
        if n:
            clean=lambda x:' '.join(x.split()) if x else ''
            rows.append(dict(utility_area=ba,in_service_year=y.group(1) if y else '',project_name=clean(n.group(1)),
              description=clean(d.group(1) if d else ''),need=clean(s.group(1) if s else '')[:300],source_page=pno,
              source='SERTP 2025 Regional Transmission Plan (Nov 26 2025)'))
with open('sertp_2025_projects.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
from collections import Counter
print('SERTP projects:',len(rows), Counter(r['utility_area'] for r in rows))
# --- DESC ---
t=open('../../../../.claude/projects/C--Users-lucia-OneDrive-Desktop-Shell-Hacks/15d39e86-3abe-46e2-ac62-5cbc7707d758/tool-results/scrtp_2026_2030.txt',encoding='utf-8').read() if False else '\n'.join(p.extract_text() or '' for p in pypdf.PdfReader('desc_scrtp_2026_2030.pdf').pages)
out=[]
for b in re.split(r'Project \d+ of \d+',t)[1:]:
    g=lambda k,nx: re.search(k+r'\s*\n(.+?)\n\s*'+nx,b,re.S)
    L=[l.strip() for l in b.splitlines() if l.strip()]
    i=L.index('5 Year Budget') if '5 Year Budget' in L else 2
    j=L.index('Project ID') if 'Project ID' in L else i+2
    clean=lambda m:' '.join(m.group(1).split()) if m else ''
    tot=re.findall(r'\$[\d,]+',b)
    out.append(dict(utility='Dominion Energy South Carolina',project_name=' '.join(L[i+1:j]).replace('\u2013','-'),
      project_id=clean(g('Project ID','Project Description')),description=clean(g('Project Description','Project Need')),
      need=clean(g('Project Need','Project Status')),status=clean(g('Project Status','Planned In-Service Date')),
      planned_in_service=clean(g('Planned In-Service Date','Estimated Project Cost')),total_cost=tot[-1] if tot else '',
      source='SCRTP Planned Facilities 2026-2030 $2M & Above'))
with open('desc_2026_2030_projects.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
print('DESC projects:',len(out))
