import json, urllib.request, urllib.parse
BASE="https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/US_Electric_Power_Transmission_Lines/FeatureServer/0/query"
bbox="-85.7,30.3,-78.5,35.3"  # GA + SC
feats=[]; off=0
while True:
    q=dict(where="1=1",geometry=bbox,geometryType="esriGeometryEnvelope",inSR="4326",spatialRel="esriSpatialRelIntersects",
           outFields="OWNER,VOLTAGE,VOLT_CLASS,SUB_1,SUB_2,STATUS,TYPE",outSR="4326",f="geojson",resultOffset=off,resultRecordCount=2000)
    d=json.load(urllib.request.urlopen(BASE+"?"+urllib.parse.urlencode(q),timeout=120))
    fs=d.get("features",[]); feats+=fs; off+=len(fs)
    if not fs or not d.get("properties",{}).get("exceededTransferLimit",len(fs)==2000): break
json.dump({"type":"FeatureCollection","features":feats},open("hifld_lines_ga_sc.geojson","w"))
print("lines:",len(feats))
from collections import Counter
print(Counter(f["properties"]["OWNER"] for f in feats).most_common(12))
