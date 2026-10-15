from flask import Flask, render_template_string, request, send_file, jsonify
from io import BytesIO
import random
import time
import re
import requests
from openpyxl import load_workbook

app = Flask(__name__)

HTML = r'''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>راه‌بر | نقشه مسیر و باربرگ</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    :root{--bg:#f3f6fb;--panel:#fff;--text:#172033;--muted:#64748b;--line:#dce4ef;--primary:#2457d6;--green:#13834b;--danger:#c52b3a;--soft:#edf3ff;--shadow:0 12px 35px #20365b12}
    body.dark{--bg:#101827;--panel:#182235;--text:#edf3ff;--muted:#a7b4ca;--line:#34435a;--primary:#7aa2ff;--green:#40cb87;--danger:#ff7581;--soft:#243450;--shadow:0 12px 35px #0003}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Tahoma,Arial,sans-serif;transition:background .2s,color .2s}header{background:linear-gradient(120deg,#143b9b,#2869e8);color:white;padding:22px 16px}header .head{max-width:1200px;margin:auto;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}h1{font-size:24px;margin:0 0 7px}header p{margin:0;color:#e3ebff;font-size:13px;line-height:1.8}.head-actions{display:flex;gap:8px;flex-wrap:wrap}.head-actions button{background:#ffffff20;border:1px solid #ffffff55}.wrap{max-width:1200px;width:calc(100% - 24px);margin:18px auto 35px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px;margin-bottom:15px;box-shadow:var(--shadow)}.section-title{font-size:16px;font-weight:bold;margin:0 0 13px}.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.field-card,.metric,.subpanel{background:var(--bg);border:1px solid var(--line);padding:14px;border-radius:12px;min-width:0}.field-card strong{display:block;margin-bottom:7px}.field-card input,.field-card select,.field-card textarea,.form-grid input,.form-grid select{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:9px;background:var(--panel);color:var(--text);font:inherit;font-size:13px;margin-top:7px}.buttons{display:flex;flex-wrap:wrap;gap:7px;margin-top:9px}button,.file-label{border:0;border-radius:9px;padding:10px 13px;background:var(--primary);color:white;font:inherit;font-size:13px;cursor:pointer;transition:filter .15s}button:hover,.file-label:hover{filter:brightness(.92)}button.green{background:var(--green)}button.gray{background:#596579}button.red{background:var(--danger)}button.outline{background:transparent;color:var(--text);border:1px solid var(--line)}button:disabled{opacity:.5;cursor:not-allowed}#map{height:54vh;min-height:360px;border-radius:13px;border:1px solid var(--line);overflow:hidden}.status{line-height:1.9;color:var(--muted);font-size:13px;margin:10px 0}.coords{direction:ltr;text-align:left;font-weight:bold;overflow-wrap:anywhere;margin:6px 0 10px;font-size:14px}.metric strong{display:block;font-size:13px;margin-bottom:9px}.big{font-size:22px;font-weight:bold;color:var(--primary)}.small{font-size:12px;line-height:1.8;color:var(--muted)}.tag{display:inline-block;padding:4px 8px;border-radius:30px;background:var(--soft);color:var(--primary);font-size:11px;margin-bottom:8px}.route-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.saved-item{padding:12px;border:1px solid var(--line);border-radius:11px;background:var(--bg);min-width:0}.saved-item .name{font-weight:bold;margin-bottom:7px}.saved-item .small{margin:4px 0}.saved-item .buttons button{padding:8px 10px}.form-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.empty{padding:18px;text-align:center;color:var(--muted);border:1px dashed var(--line);border-radius:10px;font-size:13px}.footer{text-align:center;color:var(--muted);font-size:11px;padding:12px}.hidden{display:none!important}
    @media(max-width:720px){h1{font-size:20px}.grid2,.grid3,.route-list,.form-grid{grid-template-columns:1fr}#map{height:50vh;min-height:320px}.panel{padding:12px}.wrap{width:calc(100% - 16px);margin-top:10px}.big{font-size:20px}}

    .iran-banner{display:block;width:100%;max-width:1200px;max-height:340px;object-fit:cover;object-position:center;margin:20px auto;border-radius:18px;box-shadow:0 8px 25px rgba(0,0,0,.2)}
    @media(max-width:650px){.iran-banner{max-height:220px;margin:12px auto;border-radius:12px}}
  </style>
</head>
<body>
<header><div class="head"><div><h1>🧭 راه‌بر | نقشه مسیر ایران</h1><p>انتخاب مبدأ و مقصد، محاسبه مسیر جاده‌ای، ذخیره مسیرها و آماده‌سازی اطلاعات باربرگ</p></div><div class="head-actions"><button onclick="toggleTheme()" id="themeBtn">🌙 حالت شب</button><button onclick="exportCSV()">⬇ خروجی اکسل (CSV)</button></div></div></header>
<div class="wrap"><img src="/iran-map.png" alt="نقشه سه‌بعدی ایران" class="iran-banner"></div>
<main class="wrap">
  <section class="panel">
    <div class="section-title">۱. انتخاب مبدأ و مقصد</div>
    <div class="grid2">
      <div class="field-card"><strong>📍 مبدأ</strong><input id="originSearch" placeholder="مثلاً لای‌بید، اصفهان" autocomplete="off"><div class="buttons"><button onclick="searchPlace('origin')">جست‌وجوی مبدأ</button><button class="gray" onclick="selectMode('origin')">انتخاب روی نقشه</button></div><div class="small">جست‌وجو با نام شهر، روستا یا مکان</div></div>
      <div class="field-card"><strong>🏁 مقصد</strong><input id="destinationSearch" placeholder="مثلاً اصفهان" autocomplete="off"><div class="buttons"><button class="green" onclick="searchPlace('destination')">جست‌وجوی مقصد</button><button class="gray" onclick="selectMode('destination')">انتخاب روی نقشه</button></div><div class="small">برای انتخاب دستی، دکمه را بزن و روی نقشه کلیک کن</div></div>
    </div>
    <p class="status" id="status">برای شروع، نام مکان را جست‌وجو کن یا حالت انتخاب روی نقشه را فعال کن.</p>
    <div id="map"></div><p class="small">نقشه و جست‌وجو به اینترنت نیاز دارند. مختصات و مسیرهای ذخیره‌شده در همین مرورگر نگهداری می‌شوند.</p>
  </section>
  <section class="panel"><div class="section-title">۲. مختصات و اطلاعات مسیر</div>
    <div class="grid2">
      <div class="field-card"><span class="tag">مبدأ</span><div>Latitude / عرض جغرافیایی</div><div class="coords" id="originLat">—</div><div>Longitude / طول جغرافیایی</div><div class="coords" id="originLng">—</div><button onclick="copyPoint('origin')">کپی مختصات مبدأ</button></div>
      <div class="field-card"><span class="tag">مقصد</span><div>Latitude / عرض جغرافیایی</div><div class="coords" id="destinationLat">—</div><div>Longitude / طول جغرافیایی</div><div class="coords" id="destinationLng">—</div><button class="green" onclick="copyPoint('destination')">کپی مختصات مقصد</button></div>
    </div>
    <div class="grid3" style="margin-top:12px"><div class="metric"><strong>🚗 فاصله جاده‌ای</strong><div class="big" id="routeDistance">—</div></div><div class="metric"><strong>⏱ زمان رانندگی تخمینی</strong><div class="big" id="routeDuration">—</div></div><div class="metric"><strong>🧭 وضعیت</strong><div id="routeStatus" class="small">هنوز مسیری محاسبه نشده است.</div></div></div>
    <div class="buttons"><button onclick="calculateRoute()">محاسبه مسیر جاده‌ای</button><button class="green" onclick="openGoogleMaps()">بازکردن در Google Maps</button><button class="gray" onclick="copyBoth()">کپی هر دو مختصات</button><button class="red" onclick="clearAll()">پاک‌کردن مبدأ و مقصد</button></div>
  </section>
  <section class="panel"><div class="section-title">۳. ذخیره مسیرهای پرتکرار</div><div class="grid2"><div class="field-card"><strong>نام دلخواه مسیر</strong><input id="routeName" placeholder="مثلاً لای‌بید به اصفهان"><div class="buttons"><button onclick="saveRoute()">ذخیره مسیر فعلی</button></div><div class="small">ابتدا مبدأ و مقصد را انتخاب کن؛ بعد مسیر را ذخیره کن.</div></div><div class="field-card"><strong>مدیریت مسیرها</strong><div class="buttons"><button class="outline" onclick="exportCSV()">خروجی CSV از مسیرهای ذخیره‌شده</button><button class="red" onclick="clearSavedRoutes()">حذف همه مسیرهای ذخیره‌شده</button></div><div class="small">مسیرها فقط در مرورگر همین دستگاه ذخیره می‌شوند؛ با پاک‌کردن داده‌های مرورگر ممکن است حذف شوند.</div></div></div><div id="savedRoutes" class="route-list" style="margin-top:12px"></div></section>

  <section class="panel">
    <div class="section-title">۵. ساخت مختصات باربرگ از روی پلاک اکسل</div>
    <p class="small">فایل Excel را انتخاب کن. برنامه کد دو رقمی ستون Q را می‌خواند، استان را تا جایی که در جدولش شناخته شده باشد تشخیص می‌دهد و مختصات را در ستون‌های I تا L می‌نویسد. برای هر ردیف فاصله جاده‌ای باید حداقل ۲۰ کیلومتر باشد. ردیف‌های ناشناخته یا بدون مسیر معتبر در گزارش مشخص می‌شوند.</p>
    <div class="field-card">
      <strong>فایل Excel باربرگ</strong>
      <input id="excelFile" type="file" accept=".xlsx,.xlsm">
      <div class="buttons"><button onclick="processExcel()">ساخت فایل مختصات</button></div>
      <p class="status" id="excelStatus">ستون Q: کد پلاک؛ ستون‌های I/J: مبدأ؛ ستون‌های K/L: مقصد.</p>
      <a id="excelDownload" class="hidden" style="display:inline-block;margin-top:8px;color:var(--primary);font-weight:bold" href="#">دانلود فایل آماده‌شده</a>
    </div>
  </section>
  <section class="panel"><div class="section-title">۴. اطلاعات کمکی باربرگ شهری</div><p class="small">این بخش برای مرتب‌کردن اطلاعات مسیر و خروجی گرفتن است؛ اطلاعات به سامانه رسمی باربرگ ارسال نمی‌شود.</p><div class="form-grid"><label class="small">نام راننده<input id="driverName" placeholder="نام راننده"></label><label class="small">شماره پلاک<input id="plate" placeholder="مثلاً ۱۲الف۳۴۵ ایران ۶۷"></label><label class="small">نوع بار<input id="cargo" placeholder="نوع بار"></label><label class="small">وزن بار (کیلوگرم)<input id="weight" type="number" min="0" placeholder="مثلاً ۱۲۰۰"></label><label class="small">شماره باربرگ (اختیاری)<input id="barbargNo" placeholder="شماره باربرگ"></label><label class="small">توضیحات<input id="notes" placeholder="توضیحات مسیر یا بار"></label></div><div class="buttons"><button onclick="copyBarbargSummary()">کپی خلاصه اطلاعات</button><button class="green" onclick="exportCSV()">خروجی اکسل (CSV)</button></div><p id="barbargStatus" class="status"></p></section>
  <div class="footer">نقشه با Leaflet و داده‌های OpenStreetMap نمایش داده می‌شود. فاصله و زمان جاده‌ای با سرویس عمومی OSRM محاسبه می‌شود و ممکن است موقتاً در دسترس نباشد.</div>
</main>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
let map, routeLayer=null, mode=null, routeRequestId=0;
const points={origin:{lat:null,lng:null,marker:null},destination:{lat:null,lng:null,marker:null}};
const STORAGE_KEY='iranCoordinateMapPoints_v2', ROUTES_KEY='iranCoordinateMapSavedRoutes_v1', THEME_KEY='iranCoordinateMapTheme';
function setStatus(text){document.getElementById('status').textContent=text}
function validPoint(p){return Number.isFinite(p.lat)&&Number.isFinite(p.lng)}
function initializeMap(){
  map=L.map('map').setView([32.4,53.7],5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
  map.on('click',e=>{if(!mode){setStatus('برای انتخاب نقطه، ابتدا دکمه انتخاب مبدأ یا مقصد روی نقشه را بزن.');return;}setPoint(mode,e.latlng.lat,e.latlng.lng,true);mode=null;});
  if(localStorage.getItem(THEME_KEY)==='dark')document.body.classList.add('dark'); updateThemeButton();
  restorePoints();renderSavedRoutes();
}
function selectMode(which){mode=which;setStatus(which==='origin'?'حالت انتخاب مبدأ فعال شد؛ روی نقشه کلیک کن.':'حالت انتخاب مقصد فعال شد؛ روی نقشه کلیک کن.');}
function setPoint(which,lat,lng,zoom){const p=points[which];if(p.marker)map.removeLayer(p.marker);p.lat=lat;p.lng=lng;p.marker=L.marker([lat,lng]).addTo(map).bindPopup(which==='origin'?'مبدأ':'مقصد');document.getElementById(which+'Lat').textContent=lat.toFixed(6);document.getElementById(which+'Lng').textContent=lng.toFixed(6);if(zoom)map.setView([lat,lng],Math.max(map.getZoom(),10));savePoints();clearRouteDisplay();if(validPoint(points.origin)&&validPoint(points.destination))calculateRoute();}
function savePoints(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify({origin:{lat:points.origin.lat,lng:points.origin.lng},destination:{lat:points.destination.lat,lng:points.destination.lng}}))}catch(e){}}
function restorePoints(){try{const data=JSON.parse(localStorage.getItem(STORAGE_KEY)||'null');if(!data)return;['origin','destination'].forEach(k=>{if(data[k]&&Number.isFinite(data[k].lat)&&Number.isFinite(data[k].lng))setPoint(k,data[k].lat,data[k].lng,false)});if(validPoint(points.origin)&&validPoint(points.destination)){const group=L.featureGroup([points.origin.marker,points.destination.marker]);map.fitBounds(group.getBounds().pad(.2));calculateRoute();}else if(validPoint(points.origin))map.setView([points.origin.lat,points.origin.lng],10);else if(validPoint(points.destination))map.setView([points.destination.lat,points.destination.lng],10);}catch(e){}}
async function searchPlace(which){const input=document.getElementById(which==='origin'?'originSearch':'destinationSearch');const query=input.value.trim();if(!query){setStatus('نام شهر، روستا یا مکان را وارد کن.');input.focus();return;}setStatus('در حال جست‌وجوی مکان...');try{const url='https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&countrycodes=ir&q='+encodeURIComponent(query);const response=await fetch(url,{headers:{'Accept-Language':'fa'}});if(!response.ok)throw Error('search failed');const results=await response.json();if(!results.length){setStatus('مکانی پیدا نشد؛ نام دیگری امتحان کن یا روی نقشه انتخاب کن.');return;}let result=results[0];if(results.length>1){const choices=results.map((r,i)=>(i+1)+'. '+r.display_name).join('\n');const answer=prompt('شماره مکان موردنظر را انتخاب کن:\n'+choices,'1');if(answer===null)return;const index=Number(answer)-1;if(!Number.isInteger(index)||index<0||index>=results.length){alert('شماره انتخابی معتبر نیست.');return;}result=results[index];}input.value=result.display_name;setPoint(which,Number(result.lat),Number(result.lon),true);setStatus((which==='origin'?'مبدأ':'مقصد')+' پیدا و روی نقشه ثبت شد.');}catch(e){setStatus('جست‌وجو ناموفق بود. اتصال اینترنت یا سرویس جست‌وجو را بررسی کن.');}}
function clearRouteDisplay(){routeRequestId++;if(routeLayer&&map){map.removeLayer(routeLayer);routeLayer=null;}document.getElementById('routeDistance').textContent='—';document.getElementById('routeDuration').textContent='—';document.getElementById('routeStatus').textContent='هنوز مسیری محاسبه نشده است.';}
async function calculateRoute(){if(!validPoint(points.origin)||!validPoint(points.destination)){setStatus('ابتدا مبدأ و مقصد را انتخاب کن.');return;}const requestId=++routeRequestId;document.getElementById('routeStatus').textContent='در حال محاسبه مسیر...';document.getElementById('routeDistance').textContent='...';document.getElementById('routeDuration').textContent='...';try{const start=points.origin.lng+','+points.origin.lat,end=points.destination.lng+','+points.destination.lat;const url='https://router.project-osrm.org/route/v1/driving/'+start+';'+end+'?overview=full&geometries=geojson&steps=false';const response=await fetch(url);if(!response.ok)throw Error('route failed');const data=await response.json();if(requestId!==routeRequestId)return;if(data.code!=='Ok'||!data.routes||!data.routes.length)throw Error('no route');const r=data.routes[0],km=r.distance/1000,mins=Math.round(r.duration/60);document.getElementById('routeDistance').textContent=km.toLocaleString('fa-IR',{maximumFractionDigits:1})+' کیلومتر';document.getElementById('routeDuration').textContent=mins<60?mins.toLocaleString('fa-IR')+' دقیقه':Math.floor(mins/60).toLocaleString('fa-IR')+' ساعت و '+(mins%60).toLocaleString('fa-IR')+' دقیقه';document.getElementById('routeStatus').textContent='مسیر جاده‌ای نمایش داده شد.';routeLayer=L.geoJSON(r.geometry,{style:{color:'#e43e61',weight:5,opacity:.88}}).addTo(map);map.fitBounds(routeLayer.getBounds(),{padding:[25,25]});setStatus('مسیر جاده‌ای محاسبه شد.');}catch(e){if(requestId!==routeRequestId)return;document.getElementById('routeDistance').textContent='در دسترس نیست';document.getElementById('routeDuration').textContent='—';document.getElementById('routeStatus').textContent='سرویس مسیریابی پاسخ نداد؛ دوباره تلاش کن یا Google Maps را باز کن.';setStatus('محاسبه مسیر ناموفق بود؛ ممکن است سرویس عمومی موقتاً در دسترس نباشد.');}}
function openGoogleMaps(){if(!validPoint(points.origin)||!validPoint(points.destination)){alert('ابتدا مبدأ و مقصد را انتخاب کن.');return;}window.open('https://www.google.com/maps/dir/?api=1&origin='+points.origin.lat+','+points.origin.lng+'&destination='+points.destination.lat+','+points.destination.lng+'&travelmode=driving','_blank','noopener');}
async function copyText(text){try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(text);alert('کپی شد.');}else throw Error('clipboard unavailable');}catch(e){prompt('متن زیر را انتخاب و کپی کن:',text)}}
function copyPoint(which){const p=points[which];if(!validPoint(p)){alert('ابتدا '+(which==='origin'?'مبدأ':'مقصد')+' را انتخاب کن.');return;}copyText(p.lat.toFixed(6)+', '+p.lng.toFixed(6));}
function copyBoth(){if(!validPoint(points.origin)||!validPoint(points.destination)){alert('ابتدا هر دو نقطه را انتخاب کن.');return;}copyText('مبدأ: '+points.origin.lat.toFixed(6)+', '+points.origin.lng.toFixed(6)+'\nمقصد: '+points.destination.lat.toFixed(6)+', '+points.destination.lng.toFixed(6));}
function clearAll(){if(!confirm('مبدأ و مقصد فعلی پاک شوند؟'))return;['origin','destination'].forEach(k=>{const p=points[k];if(p.marker)map.removeLayer(p.marker);p.marker=null;p.lat=null;p.lng=null;document.getElementById(k+'Lat').textContent='—';document.getElementById(k+'Lng').textContent='—';document.getElementById(k==='origin'?'originSearch':'destinationSearch').value='';});localStorage.removeItem(STORAGE_KEY);clearRouteDisplay();setStatus('مبدأ و مقصد پاک شدند.');}
function getSavedRoutes(){try{return JSON.parse(localStorage.getItem(ROUTES_KEY)||'[]')}catch(e){return []}}
function saveRoute(){if(!validPoint(points.origin)||!validPoint(points.destination)){alert('ابتدا مبدأ و مقصد را انتخاب کن.');return;}const name=document.getElementById('routeName').value.trim()||('مسیر '+(getSavedRoutes().length+1));const routes=getSavedRoutes();routes.unshift({id:Date.now(),name,origin:{lat:points.origin.lat,lng:points.origin.lng,label:document.getElementById('originSearch').value.trim()},destination:{lat:points.destination.lat,lng:points.destination.lng,label:document.getElementById('destinationSearch').value.trim()},created:new Date().toLocaleDateString('fa-IR')});localStorage.setItem(ROUTES_KEY,JSON.stringify(routes));document.getElementById('routeName').value='';renderSavedRoutes();setStatus('مسیر «'+name+'» ذخیره شد.');}
function renderSavedRoutes(){const box=document.getElementById('savedRoutes');if(!box)return;const routes=getSavedRoutes();if(!routes.length){box.innerHTML='<div class="empty" style="grid-column:1/-1">هنوز مسیری ذخیره نشده است.</div>';return;}box.innerHTML='';routes.forEach(r=>{const card=document.createElement('div');card.className='saved-item';const title=document.createElement('div');title.className='name';title.textContent=r.name;const desc=document.createElement('div');desc.className='small';desc.textContent=(r.origin.label||r.origin.lat.toFixed(4)+', '+r.origin.lng.toFixed(4))+' ← '+(r.destination.label||r.destination.lat.toFixed(4)+', '+r.destination.lng.toFixed(4));const date=document.createElement('div');date.className='small';date.textContent='تاریخ ذخیره: '+(r.created||'—');const actions=document.createElement('div');actions.className='buttons';const load=document.createElement('button');load.textContent='بارگذاری مسیر';load.onclick=()=>{document.getElementById('originSearch').value=r.origin.label||'';document.getElementById('destinationSearch').value=r.destination.label||'';setPoint('origin',r.origin.lat,r.origin.lng,false);setPoint('destination',r.destination.lat,r.destination.lng,false);map.fitBounds(L.featureGroup([points.origin.marker,points.destination.marker]).getBounds().pad(.2));calculateRoute();setStatus('مسیر ذخیره‌شده بارگذاری شد.');};const del=document.createElement('button');del.className='red';del.textContent='حذف';del.onclick=()=>{localStorage.setItem(ROUTES_KEY,JSON.stringify(getSavedRoutes().filter(x=>x.id!==r.id)));renderSavedRoutes();};actions.append(load,del);card.append(title,desc,date,actions);box.append(card);});}
function clearSavedRoutes(){if(!confirm('تمام مسیرهای ذخیره‌شده حذف شوند؟'))return;localStorage.removeItem(ROUTES_KEY);renderSavedRoutes();}
function csvEscape(value){const s=String(value==null?'':value);return '"'+s.replace(/"/g,'""')+'"';}
function exportCSV(){const routes=getSavedRoutes();const rows=[['نام مسیر','مبدأ','مبدأ Latitude','مبدأ Longitude','مقصد','مقصد Latitude','مقصد Longitude','فاصله جاده‌ای','نام راننده','پلاک','نوع بار','وزن کیلوگرم','شماره باربرگ','توضیحات','تاریخ ذخیره']];const dist=document.getElementById('routeDistance').textContent;const extra={driver:document.getElementById('driverName').value,plate:document.getElementById('plate').value,cargo:document.getElementById('cargo').value,weight:document.getElementById('weight').value,no:document.getElementById('barbargNo').value,notes:document.getElementById('notes').value};if(routes.length){routes.forEach(r=>rows.push([r.name,r.origin.label,r.origin.lat,r.origin.lng,r.destination.label,r.destination.lat,r.destination.lng,'',extra.driver,extra.plate,extra.cargo,extra.weight,extra.no,extra.notes,r.created]));}else if(validPoint(points.origin)&&validPoint(points.destination)){rows.push([document.getElementById('routeName').value||'مسیر فعلی',document.getElementById('originSearch').value,points.origin.lat,points.origin.lng,document.getElementById('destinationSearch').value,points.destination.lat,points.destination.lng,dist,extra.driver,extra.plate,extra.cargo,extra.weight,extra.no,extra.notes,new Date().toLocaleDateString('fa-IR')]);}else{alert('برای خروجی، ابتدا یک مسیر انتخاب کن یا مسیرهای ذخیره‌شده داشته باش.');return;}const csv='\uFEFF'+rows.map(row=>row.map(csvEscape).join(',')).join('\r\n');const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='iran-coordinate-routes.csv';document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);}
function copyBarbargSummary(){if(!validPoint(points.origin)||!validPoint(points.destination)){alert('ابتدا مبدأ و مقصد را انتخاب کن.');return;}const lines=['خلاصه اطلاعات مسیر','مبدأ: '+document.getElementById('originSearch').value,'مبدأ مختصات: '+points.origin.lat.toFixed(6)+', '+points.origin.lng.toFixed(6),'مقصد: '+document.getElementById('destinationSearch').value,'مقصد مختصات: '+points.destination.lat.toFixed(6)+', '+points.destination.lng.toFixed(6),'فاصله جاده‌ای: '+document.getElementById('routeDistance').textContent,'نام راننده: '+document.getElementById('driverName').value,'پلاک: '+document.getElementById('plate').value,'نوع بار: '+document.getElementById('cargo').value,'وزن کیلوگرم: '+document.getElementById('weight').value,'شماره باربرگ: '+document.getElementById('barbargNo').value,'توضیحات: '+document.getElementById('notes').value];copyText(lines.join('\n'));document.getElementById('barbargStatus').textContent='خلاصه اطلاعات آماده کپی است. این اطلاعات به سامانه رسمی ارسال نشده است.';}
function toggleTheme(){document.body.classList.toggle('dark');localStorage.setItem(THEME_KEY,document.body.classList.contains('dark')?'dark':'light');updateThemeButton()}
function updateThemeButton(){document.getElementById('themeBtn').textContent=document.body.classList.contains('dark')?'☀️ حالت روز':'🌙 حالت شب'}

async function processExcel(){
  const file=document.getElementById('excelFile').files[0];
  const status=document.getElementById('excelStatus'), link=document.getElementById('excelDownload');
  link.classList.add('hidden');
  if(!file){status.textContent='اول فایل اکسل را انتخاب کن.';return;}
  const form=new FormData();form.append('file',file);
  status.textContent='در حال پردازش فایل؛ ممکن است کمی طول بکشد...';
  try{
    const response=await fetch('/process_excel',{method:'POST',body:form});
    if(!response.ok){let msg='پردازش ناموفق بود.';try{const j=await response.json();msg=j.error||msg}catch(e){}throw Error(msg)}
    const blob=await response.blob(), url=URL.createObjectURL(blob);
    link.href=url;link.download='barbarg_with_coordinates.xlsx';link.classList.remove('hidden');
    status.textContent='آماده شد. روی «دانلود فایل آماده‌شده» بزن. ردیف‌های نامشخص در ستون وضعیت بررسی ثبت می‌شوند.';
  }catch(e){status.textContent='خطا: '+e.message;}
}

window.addEventListener('load',initializeMap);
</script>
</body></html>'''

@app.route('/')
def home():
    return render_template_string(HTML)


@app.route('/iran-map.png')
def iran_map_image():
    return send_file(
       
        app.root_path + '/iran-map.png.png',

        mimetype='image/png'
    )


# Approximate province mapping for common Iranian plate codes. Unknown codes are
# deliberately flagged instead of generating misleading coordinates.
PLATE_PROVINCES = {
    11:"تهران",12:"تهران",13:"تهران",14:"تهران",15:"تهران",16:"تهران",17:"تهران",18:"تهران",19:"تهران",
    21:"اصفهان",22:"اصفهان",23:"اصفهان",24:"اصفهان",25:"اصفهان",26:"اصفهان",
    31:"فارس",32:"فارس",33:"فارس",34:"فارس",35:"فارس",36:"فارس",
    41:"آذربایجان شرقی",42:"آذربایجان شرقی",43:"آذربایجان شرقی",44:"آذربایجان شرقی",
    51:"خراسان رضوی",52:"خراسان رضوی",53:"خراسان رضوی",54:"خراسان رضوی",55:"خراسان رضوی",56:"خراسان رضوی",57:"خراسان رضوی",58:"خراسان رضوی",
    61:"خوزستان",62:"خوزستان",63:"کرمان",64:"کرمان",65:"کرمان",
    71:"مازندران",72:"مازندران",73:"گیلان",74:"گیلان",75:"گیلان",
    81:"همدان",82:"همدان",83:"همدان",84:"همدان",
    91:"آذربایجان غربی",92:"آذربایجان غربی",93:"آذربایجان غربی",94:"آذربایجان غربی",
    29:"کرمانشاه"
}
# City centers and rough local search envelopes (lat, lon, radius in degrees).
# These are approximate seed points, not official city-boundary polygons.
PROVINCE_CITIES = {
    "تهران":[("تهران",35.6892,51.3890,.10),("شهریار",35.6590,51.0590,.08),("ورامین",35.3252,51.6457,.07)],
    "اصفهان":[("اصفهان",32.6546,51.6680,.10),("کاشان",33.9850,51.4100,.08),("نجف‌آباد",32.6324,51.3668,.07),("خمینی‌شهر",32.7000,51.5200,.07)],
    "فارس":[("شیراز",29.5918,52.5837,.10),("مرودشت",29.8742,52.8025,.07),("کازرون",29.6195,51.6541,.07)],
    "آذربایجان شرقی":[("تبریز",38.0962,46.2738,.10),("مراغه",37.3892,46.2374,.07),("میانه",37.4210,47.7150,.07)],
    "خراسان رضوی":[("مشهد",36.2972,59.6067,.10),("نیشابور",36.2133,58.7958,.07),("سبزوار",36.2126,57.6819,.07)],
    "خوزستان":[("اهواز",31.3183,48.6706,.10),("دزفول",32.3831,48.4236,.07),("آبادان",30.3473,48.2934,.07)],
    "کرمان":[("کرمان",30.2839,57.0834,.10),("رفسنجان",30.4067,55.9939,.07),("سیرجان",29.4514,55.6800,.07)],
    "مازندران":[("ساری",36.5659,53.0586,.08),("آمل",36.4696,52.3507,.07),("بابل",36.5387,52.6765,.07)],
    "گیلان":[("رشت",37.2808,49.5832,.08),("لاهیجان",37.2072,50.0039,.06),("انزلی",37.4727,49.4622,.06)],
    "همدان":[("همدان",34.7981,48.5150,.08),("ملایر",34.2969,48.8235,.07),("نهاوند",34.1885,48.3768,.06)],
    "آذربایجان غربی":[("ارومیه",37.5527,45.0761,.08),("خوی",38.5503,44.9521,.06),("مهاباد",36.7631,45.7222,.06)],
    "کرمانشاه":[("کرمانشاه",34.3142,47.0650,.10),("اسلام‌آباد غرب",34.1094,46.5275,.07),("کنگاور",34.5043,47.9653,.06),("پاوه",35.0434,46.3565,.05)]
}
def normalize_digits(value):
    return str(value or '').translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789')).strip()
def osrm_distance(a,b,timeout=12):
    url=f"https://router.project-osrm.org/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}?overview=false"
    r=requests.get(url,timeout=timeout)
    r.raise_for_status()
    data=r.json()
    if data.get('code')!='Ok' or not data.get('routes'): return None
    return float(data['routes'][0]['distance'])/1000
def make_pair(city):
    name,lat,lon,radius=city
    # Generate candidate points around the city center, then accept only a
    # real OSRM road route >=20 km. Coordinates remain approximate city-area points.
    for _ in range(10):
        a=(lat+random.uniform(-radius,radius),lon+random.uniform(-radius,radius))
        b=(lat+random.uniform(-radius,radius),lon+random.uniform(-radius,radius))
        try:
            km=osrm_distance(a,b)
            if km is not None and km >= 20:
                return a,b,km,name
        except Exception:
            time.sleep(.15)
    return None

@app.route('/process_excel', methods=['POST'])
def process_excel():
    if 'file' not in request.files or not request.files['file'].filename:
        return jsonify(error='فایل اکسل انتخاب نشده است.'),400
    file=request.files['file']
    if not file.filename.lower().endswith(('.xlsx','.xlsm')):
        return jsonify(error='لطفاً فایل xlsx یا xlsm انتخاب کن.'),400
    try:
        wb=load_workbook(file, data_only=False)
        ws=wb.active
        # Add a status column at the end, preserving existing columns.
        status_col=ws.max_column+1
        ws.cell(1,status_col).value='وضعیت تولید مختصات'
        ws.cell(1,status_col+1).value='استان تشخیص‌داده‌شده'
        for row in range(2,ws.max_row+1):
            raw=ws.cell(row,17).value # Q: first two digits of plate
            digits=normalize_digits(raw)
            match=re.search(r'(?<!\d)(\d{1,2})(?!\d)',digits)
            code=int(match.group(1)) if match else None
            province=PLATE_PROVINCES.get(code)
            ws.cell(row,status_col+1).value=province or ''
            if not province:
                ws.cell(row,status_col).value=f'بررسی لازم: کد پلاک {digits or "خالی"} در جدول موجود نیست'
                continue
            cities=PROVINCE_CITIES.get(province,[])
            if not cities:
                ws.cell(row,status_col).value='بررسی لازم: شهرهای استان تعریف نشده'
                continue
            city_order=cities[:]
            random.shuffle(city_order)
            pair=None
            for city in city_order:
                pair=make_pair(city)
                if pair: break
            if not pair:
                ws.cell(row,status_col).value='مسیر معتبر ۲۰ کیلومتر به بالا پیدا نشد؛ مختصات وارد نشد'
                continue
            a,b,km,city_name=pair
            # I=origin latitude, J=origin longitude, K=destination latitude, L=destination longitude
            ws.cell(row,9).value=round(a[0],6)
            ws.cell(row,10).value=round(a[1],6)
            ws.cell(row,11).value=round(b[0],6)
            ws.cell(row,12).value=round(b[1],6)
            ws.cell(row,status_col).value=f'ثبت شد؛ {city_name}؛ مسیر جاده‌ای حدود {km:.1f} کیلومتر'
        output=BytesIO()
        wb.save(output); output.seek(0)
        return send_file(output,as_attachment=True,download_name='barbarg_with_coordinates.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return jsonify(error='فایل پردازش نشد. مطمئن شو فایل Excel سالم است. جزئیات: '+str(e)),500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
