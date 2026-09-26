import json
proj = open("projects.geojson", encoding="utf-8").read()
ov = json.load(open("overlaps.json", encoding="utf-8"))[:40]
html = """<!doctype html><html><head><meta charset="utf-8"><title>GridLock preview</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
 body{margin:0;font:13px/1.4 system-ui,sans-serif;display:flex;height:100vh}
 #map{flex:1} #side{width:380px;overflow:auto;border-left:1px solid #ccc;padding:10px;background:#fafafa}
 @media(max-width:800px){body{flex-direction:column}#map{flex:none;height:62vh}#side{width:auto;border-left:0;border-top:1px solid #ccc}}
 h2{margin:4px 0 8px;font-size:16px} .ov{padding:6px;border-bottom:1px solid #e3e3e3;cursor:pointer} .ov:hover{background:#eef}
 .tag{display:inline-block;padding:0 5px;border-radius:3px;font-size:11px;color:#fff} .x{background:#c0392b} .g{background:#7f8c8d}
 .legend{background:#fff;padding:6px 8px;border-radius:4px;box-shadow:0 1px 4px #0003;line-height:1.6}
 .sw{display:inline-block;width:18px;height:4px;margin-right:6px;vertical-align:middle}
</style></head><body><div id="map"></div><div id="side"><h2>Top coordination opportunities</h2>
<div style="color:#666;margin-bottom:6px">Preview built from projects.geojson + overlaps.json. Dashed = approximate location. Click a row to zoom.</div>
<div id="list"></div></div>
<script>
const P=__PROJ__, O=__OV__;
const COL={"Dominion Energy SC":"#d35400","Georgia Power":"#2471a3","Georgia Transmission Corp.":"#17a589","MEAG Power":"#8e44ad","Dalton Utilities":"#7f8c8d","Georgia ITS (joint)":"#34495e"};
const map=L.map('map').setView([32.6,-81.8],7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'&copy; OpenStreetMap'}).addTo(map);
const byId={};
const layer=L.geoJSON(P,{
 style:f=>({color:COL[f.properties.utility]||'#555',weight:3,dashArray:f.properties.accuracy==='exact'?null:'6 5'}),
 pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:6,color:COL[f.properties.utility]||'#555',weight:2,fillOpacity:f.properties.accuracy==='exact'?0.9:0.3,dashArray:f.properties.accuracy==='exact'?null:'3 3'}),
 onEachFeature:(f,l)=>{const p=f.properties;byId[p.id]=l;
  l.bindPopup(`<b>${p.name}</b><br>${p.utility} &middot; in service ${p.in_service||'?'}${p.cost?' &middot; '+p.cost:''}<br><i>${p.description||''}</i><br><br>
  <b>Location:</b> ${p.accuracy} &ndash; ${p.location_source}<br><b>Source:</b> ${p.source_doc}, page ${p.source_page}`);}
}).addTo(map);
const lg=L.control({position:'bottomleft'});lg.onAdd=()=>{const d=L.DomUtil.create('div','legend');
 d.innerHTML=Object.entries(COL).map(([k,v])=>`<span class="sw" style="background:${v}"></span>${k}`).join('<br>')+'<br><span class="sw" style="border-top:3px dashed #555;height:0"></span>approximate location';return d};lg.addTo(map);
document.getElementById('list').innerHTML=O.map((o,i)=>`<div class="ov" data-i="${i}"><b>#${o.rank}</b> <span class="tag ${o.cross_state?'x':'g'}">${o.cross_state?'cross-state':'GA utilities'}</span>
 ${o.distance_km} km &middot; ${o.band_label} &middot; ${o.timeline}<br>${o.a_name}<br>&harr; ${o.b_name}<br><span style="color:#666">${o.can_share}</span></div>`).join('');
document.querySelectorAll('.ov').forEach(el=>el.onclick=()=>{const o=O[+el.dataset.i];
 const g=L.featureGroup([byId[o.a],byId[o.b]].filter(Boolean));map.fitBounds(g.getBounds().pad(1.5),{maxZoom:11});});
</script></body></html>"""
open("preview.html", "w", encoding="utf-8").write(html.replace("__PROJ__", proj).replace("__OV__", json.dumps(ov, ensure_ascii=False)))
print("wrote preview.html")
