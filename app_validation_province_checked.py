from flask import Flask, render_template_string, request, jsonify
import requests
import math

app = Flask(__name__)
HEADERS = {"User-Agent": "DebirnetRouteDemo/1.0 (Iran route planner)"}
HTML = r"""
<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>سرویس هوشمند مسیریابی دبیرنت</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
:root{--primary:#2563eb;--success:#10b981;--danger:#ef4444;--bg:#f8fafc;--card:#fff;--text:#0f172a;--muted:#64748b;--border:#e2e8f0}
*{box-sizing:border-box;font-family:Vazirmatn,Tahoma,sans-serif}body{margin:0;background:var(--bg);color:var(--text)}
header{background:#fff;padding:16px 20px;text-align:center;box-shadow:0 4px 20px #00000008;border-bottom:1px solid var(--border);position:relative}
h1{font-size:20px;margin:0;color:var(--primary);font-weight:900}.subtitle{font-size:13px;color:var(--muted);margin:6px 0 0}
.live{position:absolute;left:20px;top:50%;transform:translateY(-50%);font-size:12px;color:#059669;background:#ecfdf5;padding:5px 10px;border-radius:20px;border:1px solid #a7f3d0}
main{max-width:1400px;margin:20px auto;padding:0 15px;display:grid;grid-template-columns:420px minmax(0,1fr);gap:20px;align-items:start}
.card{background:var(--card);border-radius:18px;padding:20px;box-shadow:0 10px 25px -5px #0000000d;border:1px solid var(--border)}
.section-title{font-size:15px;font-weight:800;margin:0 0 12px}.search-wrap{position:relative;margin-bottom:5px}
input{width:100%;padding:13px 14px;font-size:14px;border:2px solid var(--border);border-radius:12px;outline:none;background:#f8fafc}
input:focus{border-color:var(--primary);background:#fff;box-shadow:0 4px 14px #2563eb18}
.suggestions{position:absolute;top:calc(100% + 5px);right:0;left:0;background:#fff;border:1px solid var(--border);border-radius:12px;box-shadow:0 10px 25px #0001;max-height:220px;overflow:auto;z-index:2000;display:none}
.suggestions button{display:block;width:100%;border:0;border-bottom:1px solid var(--border);padding:11px;text-align:right;background:white;font-size:13px;cursor:pointer}
.suggestions button:hover{background:#eff6ff;color:var(--primary)}
.help{font-size:12px;line-height:1.9;margin:12px 0 17px;background:#f0f9ff;padding:12px;border-radius:10px;color:#0369a1;border:1px solid #bae6fd;border-right:4px solid #38bdf8}
.info{display:none;border-radius:14px;padding:15px;margin-bottom:14px;border:1px solid var(--border);border-right:5px solid #cbd5e1;line-height:1.8;overflow-wrap:anywhere}
.info.origin{background:#f0fdf4;border-right-color:var(--success)}.info.dest{background:#eff6ff;border-right-color:#3b82f6}
.info-title{font-weight:800;font-size:14px;margin-bottom:8px}.info.origin .info-title{color:#059669}.info.dest .info-title{color:#1d4ed8}
.small{font-size:11px;color:var(--muted);font-weight:800;display:block;margin-top:8px}.coords{direction:ltr;display:inline-block;background:#e2e8f0;padding:3px 7px;border-radius:6px;font-family:monospace;font-weight:bold}
.result{display:none;border-radius:14px;padding:16px;margin-top:10px;gap:13px;flex-direction:column}.result.success{background:#f0fdf4;border:2px solid #34d399;color:#065f46}.result.danger{background:#fef2f2;border:2px solid #f87171;color:#991b1b}.result.warn{background:#fff7ed;border:2px solid #fdba74;color:#9a3412}
.result-status{text-align:center;font-weight:800;line-height:1.8;padding-bottom:10px;border-bottom:1px solid #0001}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;text-align:center}.stat{background:#ffffffb5;border:1px solid #0000000a;border-radius:10px;padding:12px}.stat strong{font-size:20px;display:block}.stat span{font-size:12px}
button{cursor:pointer;font-weight:800;font-size:14px;border:0;border-radius:11px;padding:13px}
.reset{width:100%;margin-top:15px;background:#475569;color:white}.reset:hover{background:#0f172a}
.map-card{padding:12px;height:calc(100vh - 120px);min-height:530px;position:sticky;top:20px}#map{width:100%;height:100%;min-height:500px;border-radius:14px}
.legend{font-size:12px;color:var(--muted);margin:8px 4px 0}
@media(max-width:991px){main{grid-template-columns:1fr}.map-card{position:static;height:55vh;min-height:400px}#map{min-height:375px}.live{position:static;transform:none;display:inline-block;margin-top:10px}}
</style>
</head>
<body>
<header><span class="live">● سرویس مسیریابی</span><h1>سرویس هوشمند مسیریابی دبیرنت</h1><p class="subtitle">انتخاب مبدأ و مقصد، محاسبه فاصله جاده‌ای و بررسی تقریبی محدوده</p></header>
<main>
<section class="card">
 <div class="section-title">🏙️ ۱. شهر خود را پیدا کنید</div>
 <div class="search-wrap"><input id="city-search" placeholder="نام شهر را تایپ کنید؛ مثال: شیراز" autocomplete="off"><div id="city-list" class="suggestions"></div></div>
 <div class="help">💡 ابتدا شهر را جست‌وجو کنید، سپس روی نقشه کلیک کنید.<br>• کلیک اول: مبدأ 📍<br>• کلیک دوم: مقصد 🏁<br><b style="color:#ef4444">توجه: بررسی شهرستان تقریبی است و تأیید رسمی باربرگ محسوب نمی‌شود.</b></div>
 <div class="info origin" id="origin-info"><div class="info-title">📍 مشخصات مبدأ</div><div id="origin-address"></div><span class="small">مختصات (Lat/Lon)</span><span class="coords" id="origin-coords"></span></div>
 <div class="info dest" id="dest-info"><div class="info-title">🏁 مشخصات مقصد</div><div id="dest-address"></div><span class="small">مختصات (Lat/Lon)</span><span class="coords" id="dest-coords"></span></div>
 <div class="result" id="result"><div class="result-status" id="result-status"></div><div class="stats"><div class="stat"><strong><span id="dist">—</span> <span>کیلومتر</span></strong><span>مسافت جاده‌ای تقریبی</span></div><div class="stat"><strong><span id="time">—</span></strong><span>زمان تقریبی حمل</span></div></div></div>
 <button class="reset" id="reset">🔄 پاک کردن نقشه و شروع مجدد</button>
 <div class="legend">مبدأ با نشان سبز و مقصد با نشان قرمز مشخص می‌شود.</div>
</section>
<section class="card map-card"><div id="map"></div></section>
</main>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const map=L.map('map').setView([35.6892,51.3890],7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(map);
let origin=null,dest=null,originMarker=null,destMarker=null,routeLayer=null,cityCenter=null;
const $=id=>document.getElementById(id);
const green=L.divIcon({className:'',html:'<div style="width:20px;height:20px;background:#10b981;border:3px solid white;border-radius:50%;box-shadow:0 0 0 5px #10b98133"></div>',iconSize:[20,20],iconAnchor:[10,10]});
const red=L.divIcon({className:'',html:'<div style="width:20px;height:20px;background:#ef4444;border:3px solid white;border-radius:50%;box-shadow:0 0 7px #0005"></div>',iconSize:[20,20],iconAnchor:[10,10]});
async function nominatimSearch(q){const r=await fetch('https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=8&countrycodes=ir&accept-language=fa&q='+encodeURIComponent(q));if(!r.ok)throw Error('جست‌وجوی مکان در دسترس نیست');return r.json()}
async function reverse(lat,lon){const r=await fetch('https://nominatim.openstreetmap.org/reverse?format=jsonv2&addressdetails=1&zoom=10&accept-language=fa&lat='+lat+'&lon='+lon);if(!r.ok)throw Error('آدرس قابل تشخیص نیست');return r.json()}
function countyOf(a){return a.county||a.city_district||a.municipality||a.city||a.town||a.village||a.state_district||null}
function addressOf(x){return x.display_name||'آدرس نامشخص روی نقشه'}
function setPoint(which,lat,lon,data){
 const point={lat:+lat,lon:+lon,address:addressOf(data),county:countyOf(data.address||{})};
 if(which==='origin'){origin=point;if(originMarker)map.removeLayer(originMarker);originMarker=L.marker([point.lat,point.lon],{icon:green}).addTo(map);$('origin-info').style.display='block';$('origin-address').textContent=(point.county?'شهرستان '+point.county+' — ':'')+point.address;$('origin-coords').textContent=point.lat.toFixed(5)+' , '+point.lon.toFixed(5)}
 else{dest=point;if(destMarker)map.removeLayer(destMarker);destMarker=L.marker([point.lat,point.lon],{icon:red}).addTo(map);$('dest-info').style.display='block';$('dest-address').textContent=(point.county?'شهرستان '+point.county+' — ':'')+point.address;$('dest-coords').textContent=point.lat.toFixed(5)+' , '+point.lon.toFixed(5)}
 $('result').style.display='none';
 if(origin&&dest)calculateRoute();
}
map.on('click',async e=>{
 if(origin&&dest){alert('مبدأ و مقصد قبلاً انتخاب شده‌اند. برای انتخاب دوباره، «شروع مجدد» را بزنید.');return}
 const which=origin?'dest':'origin';
 try{const d=await reverse(e.latlng.lat,e.latlng.lng);setPoint(which,e.latlng.lat,e.latlng.lng,d)}
 catch(err){setPoint(which,e.latlng.lat,e.latlng.lng,{display_name:'مختصات انتخاب‌شده روی نقشه',address:{}})}
});
let searchTimer;
$('city-search').addEventListener('input',()=>{
 clearTimeout(searchTimer);const q=$('city-search').value.trim();const box=$('city-list');box.style.display='none';if(q.length<2)return;
 searchTimer=setTimeout(async()=>{try{const data=await nominatimSearch(q);box.innerHTML='';data.forEach(item=>{const b=document.createElement('button');b.type='button';const a=item.address||{};const province=a.state?' (استان '+a.state+')':'';b.textContent=(item.name||item.display_name)+province;b.onclick=()=>{$('city-search').value=item.name||item.display_name;box.style.display='none';cityCenter=[+item.lat,+item.lon];map.flyTo(cityCenter,11,{duration:1.2})};box.appendChild(b)});if(!data.length){const b=document.createElement('button');b.textContent='مکانی پیدا نشد';box.appendChild(b)}box.style.display='block'}catch(e){box.innerHTML='<button type="button">جست‌وجو موقتاً در دسترس نیست</button>';box.style.display='block'}},450);
});
document.addEventListener('click',e=>{if(e.target!==$('city-search')&&!$('city-list').contains(e.target))$('city-list').style.display='none'});
async function calculateRoute(){
 $('result').style.display='flex';$('result').className='result warn';$('result-status').textContent='در حال محاسبه مسیر جاده‌ای…';
 try{
 const r=await fetch(`/route?olat=${origin.lat}&olon=${origin.lon}&dlat=${dest.lat}&dlon=${dest.lon}`);const d=await r.json();if(!r.ok||d.error)throw Error(d.error||'مسیریابی انجام نشد');
 $('dist').textContent=d.distance_km.toLocaleString('fa-IR');$('time').textContent=d.duration_text;
 if(routeLayer)map.removeLayer(routeLayer);routeLayer=L.geoJSON(d.geometry,{style:{color:'#3b82f6',weight:6,opacity:.9}}).addTo(map);map.fitBounds(routeLayer.getBounds(),{padding:[55,55],maxZoom:14});
 const a=origin.county,b=dest.county;let cls='success',msg='';
 if(a&&b&&a!==b){cls='danger';msg=`❌ محدوده‌های شهرستان متفاوت تشخیص داده شدند: مبدأ «${a}»، مقصد «${b}». این مسیر ممکن است برای باربرگ شهری مناسب نباشد.`}
 else if(!a||!b){cls='warn';msg='⚠️ مسیر پیدا شد، اما شهرستان یکی از نقاط با اطمینان تشخیص داده نشد؛ نتیجه نیازمند بررسی دستی است.'}
 else if(d.distance_km<10){cls='danger';msg='⚠️ فاصله مسیر کمتر از ۱۰ کیلومتر است؛ مناسب‌بودن آن را بررسی کنید.'}
 else{cls='success';msg=`✅ هر دو نقطه در محدوده شهرستان «${a}» تشخیص داده شدند و مسیر محاسبه شد. این نتیجه تأیید رسمی باربرگ نیست.`}
 $('result').className='result '+cls;$('result-status').textContent=msg;
 }catch(e){$('result').className='result danger';$('result-status').textContent='خطا در محاسبه مسیر: '+e.message}
}
$('reset').onclick=()=>{origin=dest=null;cityCenter=null;[originMarker,destMarker,routeLayer].forEach(x=>{if(x)map.removeLayer(x)});originMarker=destMarker=routeLayer=null;$('city-search').value='';$('origin-info').style.display='none';$('dest-info').style.display='none';$('result').style.display='none';map.flyTo([35.6892,51.3890],7,{duration:1.2})};
</script>
</body></html>
"""
@app.get("/")
def index():
    return render_template_string(HTML)

@app.get("/route")
def route():
    try:
        olat=float(request.args["olat"]); olon=float(request.args["olon"])
        dlat=float(request.args["dlat"]); dlon=float(request.args["dlon"])
        vals=[olat,olon,dlat,dlon]
        if not all(math.isfinite(v) for v in vals) or not(-90<=olat<=90 and -90<=dlat<=90 and -180<=olon<=180 and -180<=dlon<=180):
            return jsonify(error="مختصات نامعتبر است."),400
        url=f"https://router.project-osrm.org/route/v1/driving/{olon},{olat};{dlon},{dlat}"
        r=requests.get(url,params={"overview":"full","geometries":"geojson","steps":"false","alternatives":"false"},headers=HEADERS,timeout=20)
        r.raise_for_status(); data=r.json()
        if data.get("code")!="Ok" or not data.get("routes"):return jsonify(error="برای این دو نقطه مسیر جاده‌ای پیدا نشد."),422
        route=data["routes"][0]; sec=int(route["duration"]); h,m=divmod(sec,3600); mins=m//60
        duration=f"{h} ساعت و {mins} دقیقه" if h else f"{mins} دقیقه"
        return jsonify(distance_km=round(route["distance"]/1000,1),duration_text=duration,geometry=route["geometry"])
    except requests.RequestException:return jsonify(error="سرویس مسیریابی پاسخ نداد؛ کمی بعد دوباره تلاش کنید."),502
    except (ValueError,KeyError,TypeError):return jsonify(error="اطلاعات مبدأ یا مقصد ناقص است."),400

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000,debug=False)
