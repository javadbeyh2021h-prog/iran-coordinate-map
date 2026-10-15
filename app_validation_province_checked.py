from flask import Flask, render_template_string, request, jsonify
import requests
import math

app = Flask(__name__)
HEADERS = {"User-Agent": "Rahbar-Debirnet-Style/1.0 (route planning demo)"}

HTML = r"""
<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>مسیریابی هوشمند</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
:root{--blue:#1769aa;--red:#d93636;--bg:#f4f7fb;--card:#fff;--text:#17212b;--muted:#687787;--line:#dbe3ec}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font-family:Tahoma,Arial,sans-serif;color:var(--text)}
header{background:#fff;border-bottom:1px solid var(--line);padding:17px 22px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
h1{font-size:21px;margin:0 0 7px}header p{margin:0;color:var(--muted);font-size:13px;line-height:1.8}
.pill{background:#e8f3ff;color:#155a92;padding:7px 12px;border-radius:20px;font-size:12px}
main{max-width:1300px;margin:18px auto;padding:0 14px;display:grid;grid-template-columns:340px 1fr;gap:16px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:0 4px 18px #122b4409}
label{display:block;font-weight:bold;font-size:13px;margin:13px 0 7px}
input{width:100%;padding:11px;border:1px solid #cbd6e2;border-radius:9px;font:14px Tahoma;outline:none}
input:focus{border-color:var(--blue);box-shadow:0 0 0 3px #1769aa18}
.suggest{position:relative}.results{position:absolute;top:100%;right:0;left:0;background:white;border:1px solid var(--line);border-radius:9px;z-index:1000;max-height:220px;overflow:auto;box-shadow:0 8px 20px #0001}.results button{display:block;width:100%;text-align:right;border:0;background:white;padding:10px;font:13px Tahoma;cursor:pointer}.results button:hover{background:#edf6ff}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px}
button{cursor:pointer;border:0;border-radius:9px;padding:11px 10px;font:13px Tahoma;font-weight:bold}
.primary{background:var(--blue);color:white}.secondary{background:#edf2f7;color:#243447}.danger{background:#fff0f0;color:#a52626}
.hint{font-size:12px;line-height:1.9;color:var(--muted);margin:13px 0 0}
#map{height:calc(100vh - 155px);min-height:520px;border-radius:14px;border:1px solid var(--line);z-index:1}
.status{margin-top:14px;border:1px solid var(--line);background:#f8fafc;border-radius:10px;padding:12px;font-size:13px;line-height:1.9;white-space:pre-line}
.metric{display:flex;gap:8px;margin-top:9px}.metric div{flex:1;background:#f3f7fb;border-radius:9px;padding:10px;text-align:center}.metric small{display:block;color:var(--muted);margin-bottom:5px}.metric strong{font-size:17px}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-left:5px}.blue{background:var(--blue)}.red{background:var(--red)}
@media(max-width:850px){main{grid-template-columns:1fr}#map{height:55vh;min-height:390px}header{padding:14px}h1{font-size:18px}}
</style>
</head>
<body>
<header><div><h1>مسیریابی هوشمند</h1><p>مبدأ و مقصد را با جست‌وجو یا با دو کلیک روی نقشه انتخاب کنید.</p></div><span class="pill">نسخه مستقل مسیریابی</span></header>
<main>
<section class="panel">
<label><span class="dot blue"></span>مبدأ</label>
<div class="suggest"><input id="originSearch" placeholder="نام شهر یا مکان مبدأ را بنویسید" autocomplete="off"><div id="originResults" class="results" hidden></div></div>
<label><span class="dot red"></span>مقصد</label>
<div class="suggest"><input id="destSearch" placeholder="نام شهر یا مکان مقصد را بنویسید" autocomplete="off"><div id="destResults" class="results" hidden></div></div>
<div class="actions"><button class="primary" id="routeBtn">محاسبه مسیر</button><button class="secondary" id="clearBtn">شروع دوباره</button></div>
<p class="hint">روش انتخاب: ابتدا مبدأ و سپس مقصد را روی نقشه کلیک کنید؛ یا نام هر مکان را در کادر مربوط وارد کنید. فاصله و زمان مسیر تقریبی است.</p>
<div id="status" class="status">هنوز مبدأ و مقصد انتخاب نشده‌اند.</div>
<div id="metrics" class="metric" hidden><div><small>فاصله جاده‌ای</small><strong id="distance">—</strong></div><div><small>زمان تقریبی</small><strong id="duration">—</strong></div></div>
<div id="validation" class="status" hidden></div>
</section>
<div id="map"></div>
</main>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const map=L.map('map').setView([32.4,53.7],5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(map);
let origin=null,destination=null,originMarker=null,destMarker=null,routeLayer=null,clickMode=0;
const $=id=>document.getElementById(id);
function status(t){$('status').textContent=t}
function markerIcon(color){return L.divIcon({className:'',html:`<div style="width:20px;height:20px;background:${color};border:3px solid white;border-radius:50%;box-shadow:0 1px 7px #0008"></div>`,iconSize:[20,20],iconAnchor:[10,10]})}
function setPoint(which,lat,lon,name){
 const pt={lat:Number(lat),lon:Number(lon),name:name||`${lat}, ${lon}`};
 if(which==='origin'){origin=pt;if(originMarker)map.removeLayer(originMarker);originMarker=L.marker([pt.lat,pt.lon],{icon:markerIcon('#1769aa')}).addTo(map).bindPopup('مبدأ: '+pt.name);$('originSearch').value=pt.name}
 else{destination=pt;if(destMarker)map.removeLayer(destMarker);destMarker=L.marker([pt.lat,pt.lon],{icon:markerIcon('#d93636')}).addTo(map).bindPopup('مقصد: '+pt.name);$('destSearch').value=pt.name}
 $('metrics').hidden=true;$('validation').hidden=true;
 status((origin?'مبدأ: '+origin.name:'مبدأ انتخاب نشده')+'\n'+(destination?'مقصد: '+destination.name:'مقصد انتخاب نشده'));
 if(origin&&destination){map.fitBounds([[origin.lat,origin.lon],[destination.lat,destination.lon]],{padding:[45,45],maxZoom:13})}
}
map.on('click',e=>{if(!origin){setPoint('origin',e.latlng.lat,e.latlng.lng,'مبدأ انتخاب‌شده روی نقشه')}else if(!destination){setPoint('destination',e.latlng.lat,e.latlng.lng,'مقصد انتخاب‌شده روی نقشه')}else{setPoint('origin',e.latlng.lat,e.latlng.lng,'مبدأ انتخاب‌شده روی نقشه');destination=null;if(destMarker){map.removeLayer(destMarker);destMarker=null}}});
async function search(q){const u='https://nominatim.openstreetmap.org/search?format=jsonv2&limit=6&accept-language=fa&countrycodes=ir&q='+encodeURIComponent(q);const r=await fetch(u);if(!r.ok)throw Error('خطا در جست‌وجوی مکان');return await r.json()}
function attachSearch(inputId,resultsId,which){
 const input=$(inputId),box=$(resultsId);let timer=null;
 input.addEventListener('input',()=>{clearTimeout(timer);const q=input.value.trim();if(q.length<2){box.hidden=true;return}timer=setTimeout(async()=>{try{box.innerHTML='';const items=await search(q);if(!items.length){box.innerHTML='<button type="button">مکانی پیدا نشد</button>'}else items.forEach(item=>{const b=document.createElement('button');b.type='button';b.textContent=item.display_name;b.onclick=()=>{setPoint(which,item.lat,item.lon,item.display_name);map.setView([item.lat,item.lon],13);box.hidden=true};box.appendChild(b)});box.hidden=false}catch(e){box.innerHTML='<button type="button">جست‌وجو در دسترس نیست؛ دوباره تلاش کنید.</button>';box.hidden=false}},450)});
 document.addEventListener('click',e=>{if(!box.contains(e.target)&&e.target!==input)box.hidden=true});
}
attachSearch('originSearch','originResults','origin');attachSearch('destSearch','destResults','destination');
$('routeBtn').onclick=async()=>{
 if(!origin||!destination){status('ابتدا مبدأ و مقصد را انتخاب کنید.');return}
 $('routeBtn').disabled=true;$('routeBtn').textContent='در حال محاسبه…';
 try{
  const r=await fetch(`/route?ol=${origin.lon}&oa=${origin.lat}&dl=${destination.lon}&da=${destination.lat}`);
  const data=await r.json();if(!r.ok||data.error)throw Error(data.error||'مسیریابی انجام نشد');
  if(routeLayer)map.removeLayer(routeLayer);
  routeLayer=L.geoJSON(data.geometry,{style:{color:'#1769aa',weight:5,opacity:.85}}).addTo(map);map.fitBounds(routeLayer.getBounds(),{padding:[35,35]});
  $('distance').textContent=data.distance_km.toLocaleString('fa-IR')+' کیلومتر';$('duration').textContent=data.duration_text;$('metrics').hidden=false;
  status('مسیر جاده‌ای محاسبه شد.');
  const v=await fetch('/validate?olat='+origin.lat+'&olon='+origin.lon+'&dlat='+destination.lat+'&dlon='+destination.lon);
  const vd=await v.json();$('validation').textContent=vd.message||'بررسی محدوده انجام نشد.';$('validation').hidden=false;
 }catch(e){status('خطا: '+e.message+'\nاگر سرویس مسیریابی موقتاً در دسترس نیست، کمی بعد دوباره امتحان کنید.')}
 finally{$('routeBtn').disabled=false;$('routeBtn').textContent='محاسبه مسیر'}
};
$('clearBtn').onclick=()=>{origin=destination=null;[originMarker,destMarker,routeLayer].forEach(x=>{if(x)map.removeLayer(x)});originMarker=destMarker=routeLayer=null;$('originSearch').value='';$('destSearch').value='';$('metrics').hidden=true;$('validation').hidden=true;status('انتخاب‌ها پاک شد. ابتدا مبدأ و سپس مقصد را انتخاب کنید.');map.setView([32.4,53.7],5)};
</script>
</body></html>
"""

@app.get("/")
def index():
    return render_template_string(HTML)

@app.get("/route")
def route():
    try:
        ol=float(request.args["ol"]); oa=float(request.args["oa"])
        dl=float(request.args["dl"]); da=float(request.args["da"])
        if not all(map(math.isfinite,[ol,oa,dl,da])) or not(-90<=oa<=90 and -90<=da<=90 and -180<=ol<=180 and -180<=dl<=180):
            return jsonify(error="مختصات معتبر نیست."),400
        url=f"https://router.project-osrm.org/route/v1/driving/{ol},{oa};{dl},{da}"
        r=requests.get(url,params={"overview":"full","geometries":"geojson","steps":"false","alternatives":"false"},headers=HEADERS,timeout=18)
        r.raise_for_status()
        data=r.json()
        if data.get("code")!="Ok" or not data.get("routes"):
            return jsonify(error="برای این دو نقطه مسیر جاده‌ای پیدا نشد."),422
        route=data["routes"][0]
        seconds=int(route["duration"])
        hours,rem=divmod(seconds,3600);mins=rem//60
        duration=(f"{hours} ساعت و {mins} دقیقه" if hours else f"{mins} دقیقه")
        return jsonify(distance_km=round(route["distance"]/1000,1),duration_text=duration,geometry=route["geometry"])
    except requests.RequestException:
        return jsonify(error="سرویس مسیریابی پاسخ نداد؛ لطفاً دوباره تلاش کنید."),502
    except (ValueError,KeyError,TypeError):
        return jsonify(error="اطلاعات مبدأ یا مقصد ناقص یا نامعتبر است."),400

@app.get("/validate")
def validate():
    try:
        olat=float(request.args["olat"]);olon=float(request.args["olon"])
        dlat=float(request.args["dlat"]);dlon=float(request.args["dlon"])
        def reverse(lat,lon):
            r=requests.get("https://nominatim.openstreetmap.org/reverse",params={"format":"jsonv2","lat":lat,"lon":lon,"zoom":10,"addressdetails":1,"accept-language":"fa"},headers=HEADERS,timeout=10)
            r.raise_for_status()
            return r.json().get("address",{})
        a=reverse(olat,olon);b=reverse(dlat,dlon)
        def area(addr):
            return addr.get("city") or addr.get("town") or addr.get("municipality") or addr.get("county") or addr.get("village") or addr.get("state_district") or addr.get("state")
        aa,bb=area(a),area(b)
        if not aa or not bb:
            msg="نام محدوده یکی از نقاط از سرویس نقشه قابل تشخیص نبود. این نتیجه تأیید رسمی نیست."
        elif aa==bb:
            msg=f"هر دو نقطه در محدوده قابل تشخیص «{aa}» ثبت شده‌اند. این فقط بررسی تقریبی نقشه است و تأیید رسمی باربرگ نیست."
        else:
            msg=f"محدوده‌های برگشتی متفاوت‌اند: مبدأ «{aa}»، مقصد «{bb}». ممکن است نیاز به بررسی دستی باشد؛ این نتیجه تأیید رسمی نیست."
        return jsonify(message=msg,origin_area=aa,destination_area=bb)
    except requests.RequestException:
        return jsonify(message="سرویس تشخیص محدوده موقتاً پاسخ نداد. مسیر قابل محاسبه است، اما بررسی محدوده انجام نشد."),200
    except (ValueError,KeyError,TypeError):
        return jsonify(message="مختصات برای بررسی محدوده معتبر نیست."),400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
