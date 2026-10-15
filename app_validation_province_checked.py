from flask import Flask, render_template_string, request, jsonify, send_file
import requests
import math
from pathlib import Path

app = Flask(__name__)
HEADERS = {"User-Agent": "DebirnetRouteDemo/1.0 (Iran route planner)"}
HTML = r"""
<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>دالاهو</title>
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
.copy-btn{font-size:12px;padding:9px 11px;margin-top:10px;background:#e0f2fe;color:#075985;border:1px solid #7dd3fc}
.copy-btn:hover:not(:disabled){background:#bae6fd}
.copy-btn:disabled{opacity:.45;cursor:not-allowed}
.copy-all{width:100%;margin-top:6px;background:#dbeafe;color:#1d4ed8;border:1px solid #93c5fd}
.reset{width:100%;margin-top:15px;background:#475569;color:white}.reset:hover{background:#0f172a}
.map-card{padding:12px;height:calc(100vh - 120px);min-height:530px;position:sticky;top:20px}#map{width:100%;height:100%;min-height:500px;border-radius:14px}
.legend{font-size:12px;color:var(--muted);margin:8px 4px 0}
.poster-wrap{max-width:1000px;margin:20px auto 0;padding:0 15px;text-align:center}.poster-card{background:#fff;border:1px solid var(--border);border-radius:18px;padding:14px;box-shadow:0 10px 25px -5px #0000000d}.poster-title{font-weight:900;color:var(--primary);margin:0 0 12px;font-size:18px}.poster-image{display:block;width:100%;max-width:520px;height:auto;margin:0 auto;border-radius:12px;box-shadow:0 8px 24px #0002}.poster-caption{font-size:12px;color:var(--muted);margin:10px 0 0}
.hidden{display:none!important}.dash-wrap{max-width:1100px;margin:28px auto;padding:0 16px 35px}.dash-welcome{padding:26px;border-radius:22px;background:linear-gradient(135deg,#1d4ed8,#0f766e);color:#fff;box-shadow:0 14px 32px #1e40af20}.dash-welcome h2{margin:0 0 8px;font-size:26px}.dash-welcome p{margin:0;line-height:1.9;color:#e0f2fe}.dash-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px;margin-top:22px}.dash-tile{display:block;text-align:right;background:#fff;border:1px solid var(--border);border-radius:20px;padding:22px;min-height:190px;box-shadow:0 10px 25px -8px #0000000d;transition:transform .15s,box-shadow .15s}.dash-tile:hover{transform:translateY(-3px);box-shadow:0 16px 30px -8px #0002}.tile-icon{font-size:38px;display:block;margin-bottom:12px}.dash-tile strong{display:block;font-size:18px;margin-bottom:7px;color:#0f172a}.dash-tile span:last-child{display:block;color:#64748b;font-size:13px;line-height:1.8}.top-actions{max-width:1400px;margin:14px auto 0;padding:0 15px}.back-btn{background:#e2e8f0;color:#0f172a;padding:10px 15px}.page-heading{display:flex;align-items:center;gap:12px;margin:0 0 14px}.page-heading h2{font-size:18px;margin:0}.game-wrap{max-width:900px;margin:20px auto;padding:0 15px 30px}.game-card{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:18px;box-shadow:0 10px 25px -5px #0000000d}.game-head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.game-title{font-size:17px;font-weight:900;margin:0}.game-tools{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.game-score{background:#f1f5f9;border-radius:9px;padding:8px 12px;font-weight:900}.game-btn{background:#2563eb;color:white;padding:10px 15px}.game-board-wrap{margin-top:14px;background:#0f172a;border-radius:14px;padding:8px;overflow:hidden}#snake-board{display:block;width:100%;max-width:640px;margin:auto;background:#111827;border-radius:8px;touch-action:none}.game-help{font-size:12px;color:var(--muted);line-height:1.9;margin:10px 0 0}.game-pad{display:grid;grid-template-columns:repeat(3,54px);gap:6px;justify-content:center;margin-top:12px}.game-pad button{background:#e2e8f0;color:#0f172a;padding:12px 0;font-size:18px}.game-pad button:nth-child(1){grid-column:2}.game-pad button:nth-child(2){grid-column:1;grid-row:2}.game-pad button:nth-child(3){grid-column:2;grid-row:2}.game-pad button:nth-child(4){grid-column:3;grid-row:2}
@media(max-width:991px){main{grid-template-columns:1fr}.map-card{position:static;height:55vh;min-height:400px}#map{min-height:375px}.live{position:static;transform:none;display:inline-block;margin-top:10px}}
 
.pasoor-area{margin-top:20px;padding:16px;border:1px solid var(--border);border-radius:16px;background:#f8fafc}.pasoor-area h3{margin:0 0 12px}.pasoor-cards{display:flex;flex-wrap:wrap;gap:9px;min-height:80px;align-items:center}.playing-card{width:64px;height:92px;border:1px solid #cbd5e1;background:#fff;color:#0f172a;border-radius:10px;box-shadow:0 4px 10px #0f172a14;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;font-size:19px;padding:5px}.playing-card b{font-size:25px}.playing-card.red-card{color:#dc2626}.playing-card:hover{transform:translateY(-4px);box-shadow:0 8px 16px #0f172a22}.game-board-wrap canvas{max-width:100%;height:auto;border-radius:16px}
 
/* Polished Hokm table and mobile-friendly controls */
.hokm-table{margin-top:18px;padding:18px;border-radius:22px;background:radial-gradient(ellipse at center,#18734f 0%,#10553d 55%,#073b2b 100%);color:#fff;box-shadow:inset 0 0 0 5px #c6a15b, inset 0 0 0 8px #6b4b21;min-height:300px;display:flex;flex-direction:column;align-items:center;justify-content:space-between;gap:14px}
.hokm-seat{display:flex;flex-direction:column;align-items:center;gap:5px;font-weight:800;font-size:13px;text-align:center}.hokm-seat span{font-size:11px;color:#d1fae5;font-weight:500}.hokm-middle{width:100%;display:grid;grid-template-columns:minmax(64px,1fr) minmax(130px,2fr) minmax(64px,1fr);gap:8px;align-items:center}.hokm-trick{min-height:135px;border:1px dashed #a7f3d055;border-radius:15px;display:flex;flex-wrap:wrap;align-content:center;align-items:center;justify-content:center;gap:6px;padding:8px}.hokm-trick .playing-card{width:48px;height:69px;font-size:14px}.hokm-trick .playing-card b{font-size:20px}.user-seat{background:#ffffff18;border-radius:12px;padding:8px 22px}.hokm-select{margin-top:15px;padding:14px;border-radius:14px;background:#fff7ed;border:1px solid #fdba74;display:flex;flex-direction:column;gap:10px;color:#7c2d12}.hokm-select.hidden{display:none}.hokm-suits{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.hokm-suits button{padding:12px 5px;border-radius:12px;background:#fff;border:1px solid #fed7aa;color:#7c2d12;font-size:15px;font-weight:900}.hokm-suits button:nth-child(2),.hokm-suits button:nth-child(3){color:#dc2626}.pasoor-area{background:#eefbf4}.playing-card{flex-shrink:0;width:58px;height:86px;font-weight:900}.playing-card:disabled{opacity:.45;cursor:not-allowed}.game-pad button{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;min-height:54px;border-radius:12px;box-shadow:0 3px 0 #94a3b8;font-weight:900}.game-pad button small{font-size:10px;font-weight:700}.game-pad button:active{transform:translateY(2px);box-shadow:0 1px 0 #94a3b8}.game-pad{grid-template-columns:repeat(3,minmax(56px,72px));gap:8px}.game-pad button:nth-child(1){grid-column:2;grid-row:1}.game-pad button:nth-child(2){grid-column:1;grid-row:2}.game-pad button:nth-child(3){grid-column:2;grid-row:2}.game-pad button:nth-child(4){grid-column:3;grid-row:2}
@media(max-width:600px){.hokm-table{padding:12px;min-height:260px}.hokm-middle{grid-template-columns:56px minmax(105px,1fr) 56px;gap:4px}.hokm-seat{font-size:11px}.hokm-trick{min-height:115px;padding:4px}.hokm-trick .playing-card{width:40px;height:60px}.playing-card{width:48px;height:74px}.pasoor-cards{gap:5px}.hokm-suits{gap:5px}.hokm-suits button{font-size:13px;padding:10px 2px}}
</style>
</head>
<body>
<header><span class="live">● دالاهو</span><h1>دالاهو</h1><p class="subtitle" id="site-subtitle">داشبورد ابزارها و سرگرمی‌های دالاهو</p></header>
<section id="dashboard" class="dash-wrap">
 <div class="dash-welcome"><h2>به دالاهو خوش آمدید 👋</h2><p>از این داشبورد ابزار موردنظرتان را انتخاب کنید. نقشه و بازی‌ها هرکدام در صفحه جداگانه باز می‌شوند.</p></div>
 <div class="dash-grid">
  <button class="dash-tile" type="button" data-open="route-page"><span class="tile-icon">🗺️</span><strong>نقشه مسیر ایران</strong><span>انتخاب مبدأ و مقصد، محاسبه مسیر و کپی مختصات</span></button>
  <button class="dash-tile" type="button" data-open="games-page"><span class="tile-icon">🎮</span><strong>بخش بازی‌ها</strong><span>ورود به بازی مار و پاسور</span></button>
 </div>
</section>
<div id="page-actions" class="top-actions hidden"><button type="button" class="back-btn" id="back-dashboard">← بازگشت به داشبورد</button></div>
<div id="route-page" class="page hidden">
<div class="top-actions"><div class="page-heading"><h2>🗺️ نقشه مسیر ایران</h2></div></div>
<main>
<section class="card">
 <div class="section-title">🏙️ ۱. شهر خود را پیدا کنید</div>
 <div class="search-wrap"><input id="city-search" placeholder="نام شهر را تایپ کنید؛ مثال: شیراز" autocomplete="off"><div id="city-list" class="suggestions"></div></div>
 <div class="help">💡 ابتدا شهر را جست‌وجو کنید، سپس روی نقشه کلیک کنید.<br>• کلیک اول: مبدأ 📍<br>• کلیک دوم: مقصد 🏁<br><b style="color:#ef4444">توجه: بررسی شهرستان تقریبی است و تأیید رسمی باربرگ محسوب نمی‌شود.</b></div>
 <div class="info origin" id="origin-info"><div class="info-title">📍 مشخصات مبدأ</div><div id="origin-address"></div><span class="small">مختصات (Lat/Lon)</span><span class="coords" id="origin-coords"></span><button type="button" class="copy-btn copy-origin" id="copy-origin" disabled>📋 کپی مختصات مبدأ</button></div>
 <div class="info dest" id="dest-info"><div class="info-title">🏁 مشخصات مقصد</div><div id="dest-address"></div><span class="small">مختصات (Lat/Lon)</span><span class="coords" id="dest-coords"></span><button type="button" class="copy-btn copy-dest" id="copy-dest" disabled>📋 کپی مختصات مقصد</button></div>
 <button type="button" class="copy-btn copy-all" id="copy-all" disabled>📋 کپی هر چهار مختصات</button>
 <div id="copy-message" role="status" aria-live="polite" style="font-size:12px;margin-top:8px;color:#059669"></div>
 <div class="result" id="result"><div class="result-status" id="result-status"></div><div class="stats"><div class="stat"><strong><span id="dist">—</span> <span>کیلومتر</span></strong><span>مسافت جاده‌ای تقریبی</span></div><div class="stat"><strong><span id="time">—</span></strong><span>زمان تقریبی حمل</span></div></div></div>
 <button class="reset" id="reset">🔄 پاک کردن نقشه و شروع مجدد</button>
 <div class="legend">مبدأ با نشان سبز و مقصد با نشان قرمز مشخص می‌شود.</div>
</section>
<section class="card map-card"><div id="map"></div></section>
</main>
</div>
<div id="games-page" class="page hidden">
 <section class="game-wrap">
  <div class="game-card">
   <div class="game-head"><h2 class="game-title">🎮 بازی‌های دالاهو</h2></div>
   <p class="game-help">یکی از بازی‌ها را انتخاب کن تا در صفحه جداگانه باز شود.</p>
   <div class="dash-grid">
    <button class="dash-tile" type="button" data-open="game-page"><span class="tile-icon">🐍</span><strong>مار کلاسیک</strong><span>سرعت، امتیاز و رکوردگیری</span></button>
    <button class="dash-tile" type="button" data-open="pasoor-page"><span class="tile-icon">🂡</span><strong>حکم چهار نفره</strong><span>حکم انتخاب کن، کارت بازی کن و دست‌ها را ببر</span></button>
   </div>
  </div>
 </section>
</div>
<div id="pasoor-page" class="page hidden">
 <section class="game-wrap"><div class="game-card">
  <div class="game-head"><h2 class="game-title">🂡 حکم چهار نفره دالاهو</h2><div class="game-tools"><span class="game-score">تیم شما: <span id="pasoor-player-score">۰</span></span><span class="game-score">حریف: <span id="pasoor-ai-score">۰</span></span><button class="game-btn" id="pasoor-new">بازی جدید</button></div></div>
  <p class="game-help" id="pasoor-message">۵ کارت اول را ببین و خال حکم را انتخاب کن. سپس با هم‌تیمی‌ات مقابل دو حریف بازی کن؛ اگر از خال شروع‌شده کارت داری، باید همان خال را بازی کنی.</p>
  <div id="hokm-select" class="hokm-select hidden"><strong>خال حکم را انتخاب کن:</strong><div class="hokm-suits"><button type="button" data-trump="♠">♠ پیک</button><button type="button" data-trump="♥">♥ دل</button><button type="button" data-trump="♦">♦ خشت</button><button type="button" data-trump="♣">♣ گشنیز</button></div></div>
  <div class="hokm-table"><div class="hokm-seat">حریف روبه‌رو <span id="hokm-top-count">۱۳ کارت</span></div><div class="hokm-middle"><div class="hokm-seat">حریف چپ <span id="hokm-left-count">۱۳ کارت</span></div><div id="pasoor-table" class="hokm-trick"><span class="game-help">کارت‌های هر دور اینجا نمایش داده می‌شوند</span></div><div class="hokm-seat">هم‌تیمی <span id="hokm-right-count">۱۳ کارت</span></div></div><div class="hokm-seat user-seat">شما <span id="hokm-user-count">۵ کارت</span></div></div>
  <div class="pasoor-area"><h3>دست شما — برای بازی روی کارت بزن</h3><div id="pasoor-hand" class="pasoor-cards"></div></div>
 </div></section>
</div>
<div id="game-page" class="page hidden">
<section class="game-wrap">
 <div class="game-card">
  <div class="game-head"><h2 class="game-title">🐍 بازی مار دالاهو</h2><div class="game-tools"><span class="game-score">امتیاز: <span id="snake-score">۰</span></span><button class="game-btn" id="snake-start">شروع / بازی دوباره</button></div></div>
  <div class="game-board-wrap"><canvas id="snake-board" width="600" height="400" aria-label="بازی مار"></canvas></div>
  <p class="game-help" id="snake-message">برای شروع دکمه «شروع» یا کلید Enter را بزن. حرکت با جهت‌ها یا W A S D؛ گوشی: از دکمه‌های جهت‌دار زیر صفحه استفاده کن.</p>
  <div class="game-pad" aria-label="کنترل لمسی بازی"><button type="button" data-dir="up" aria-label="حرکت به بالا">▲<small>بالا</small></button><button type="button" data-dir="left" aria-label="حرکت به چپ">◀<small>چپ</small></button><button type="button" data-dir="down" aria-label="حرکت به پایین">▼<small>پایین</small></button><button type="button" data-dir="right" aria-label="حرکت به راست">▶<small>راست</small></button></div>
 </div>
</section>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const $=id=>document.getElementById(id);
const dashboard=$('dashboard'), routePage=$('route-page'), gamePage=$('game-page'), gamesPage=$('games-page'), pasoorPage=$('pasoor-page'), pageActions=$('page-actions');
const appPages=[routePage,gamePage,gamesPage,pasoorPage];
function openPage(id){dashboard.classList.add('hidden');appPages.forEach(p=>p.classList.toggle('hidden',p.id!==id));pageActions.classList.remove('hidden');const labels={'route-page':'نقشه مسیر ایران','games-page':'انتخاب بازی','game-page':'بازی مار کلاسیک','pasoor-page':'پاسور دالاهو'};$('site-subtitle').textContent=labels[id]||'دالاهو';if(id==='route-page'){setTimeout(()=>map.invalidateSize(),80)}if(id==='game-page'){snakeDraw()}if(id==='pasoor-page'&&!pasoorStarted){pasoorNewGame()}}
document.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',()=>openPage(b.dataset.open)));
$('back-dashboard').addEventListener('click',()=>{appPages.forEach(p=>p.classList.add('hidden'));pageActions.classList.add('hidden');dashboard.classList.remove('hidden');$('site-subtitle').textContent='داشبورد ابزارها و سرگرمی‌های دالاهو'});
const map=L.map('map').setView([35.6892,51.3890],7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(map);
let origin=null,dest=null,originMarker=null,destMarker=null,routeLayer=null,cityCenter=null;
const green=L.divIcon({className:'',html:'<div style="width:20px;height:20px;background:#10b981;border:3px solid white;border-radius:50%;box-shadow:0 0 0 5px #10b98133"></div>',iconSize:[20,20],iconAnchor:[10,10]});
const red=L.divIcon({className:'',html:'<div style="width:20px;height:20px;background:#ef4444;border:3px solid white;border-radius:50%;box-shadow:0 0 7px #0005"></div>',iconSize:[20,20],iconAnchor:[10,10]});
async function nominatimSearch(q){const r=await fetch('https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=8&countrycodes=ir&accept-language=fa&q='+encodeURIComponent(q));if(!r.ok)throw Error('جست‌وجوی مکان در دسترس نیست');return r.json()}
async function reverse(lat,lon){const r=await fetch('https://nominatim.openstreetmap.org/reverse?format=jsonv2&addressdetails=1&zoom=10&accept-language=fa&lat='+lat+'&lon='+lon);if(!r.ok)throw Error('آدرس قابل تشخیص نیست');return r.json()}
function countyOf(a){return a.county||a.city_district||a.municipality||a.city||a.town||a.village||a.state_district||null}
function addressOf(x){return x.display_name||'آدرس نامشخص روی نقشه'}
function updateCopyButtons(){
 $('copy-origin').disabled=!origin;
 $('copy-dest').disabled=!dest;
 $('copy-all').disabled=!(origin&&dest);
}
async function copyText(text){
 const message=$('copy-message');
 try{
   if(navigator.clipboard && window.isSecureContext){await navigator.clipboard.writeText(text)}
   else{
     const temp=document.createElement('textarea');temp.value=text;temp.style.position='fixed';temp.style.opacity='0';
     document.body.appendChild(temp);temp.focus();temp.select();
     const ok=document.execCommand('copy');temp.remove();if(!ok)throw Error('کپی خودکار انجام نشد');
   }
   message.textContent='✅ مختصات کپی شد؛ حالا می‌توانید در اکسل جای‌گذاری کنید.';
 }catch(e){message.textContent='کپی خودکار ممکن نشد؛ مختصات را از کادر بالا انتخاب و کپی کنید.'}
}
function setPoint(which,lat,lon,data){
 const point={lat:+lat,lon:+lon,address:addressOf(data),county:countyOf(data.address||{})};
 if(which==='origin'){origin=point;if(originMarker)map.removeLayer(originMarker);originMarker=L.marker([point.lat,point.lon],{icon:green}).addTo(map);$('origin-info').style.display='block';$('origin-address').textContent=(point.county?'شهرستان '+point.county+' — ':'')+point.address;$('origin-coords').textContent=point.lat.toFixed(5)+' , '+point.lon.toFixed(5)}
 else{dest=point;if(destMarker)map.removeLayer(destMarker);destMarker=L.marker([point.lat,point.lon],{icon:red}).addTo(map);$('dest-info').style.display='block';$('dest-address').textContent=(point.county?'شهرستان '+point.county+' — ':'')+point.address;$('dest-coords').textContent=point.lat.toFixed(5)+' , '+point.lon.toFixed(5)}
 $('result').style.display='none';
 updateCopyButtons();
 $('copy-message').textContent='';
 if(origin&&dest)calculateRoute();
}
let nextPoint='origin';
map.on('click',async e=>{
 const which=nextPoint;
 // شروع یک جفت تازه با کلیک سوم: مبدأ قبلی جایگزین می‌شود و مقصد قبلی پاک می‌شود.
 if(which==='origin'){
   dest=null;
   if(destMarker){map.removeLayer(destMarker);destMarker=null}
   if(routeLayer){map.removeLayer(routeLayer);routeLayer=null}
   $('dest-info').style.display='none';
   $('result').style.display='none';
   updateCopyButtons();
 }
 try{const d=await reverse(e.latlng.lat,e.latlng.lng);setPoint(which,e.latlng.lat,e.latlng.lng,d)}
 catch(err){setPoint(which,e.latlng.lat,e.latlng.lng,{display_name:'مختصات انتخاب‌شده روی نقشه',address:{}})}
 nextPoint=which==='origin'?'dest':'origin';
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
$('copy-origin').onclick=()=>{if(origin)copyText(origin.lat.toFixed(6)+' , '+origin.lon.toFixed(6))};
$('copy-dest').onclick=()=>{if(dest)copyText(dest.lat.toFixed(6)+' , '+dest.lon.toFixed(6))};
$('copy-all').onclick=()=>{if(origin&&dest)copyText([origin.lat.toFixed(6),origin.lon.toFixed(6),dest.lat.toFixed(6),dest.lon.toFixed(6)].join('\\t'))};
$('reset').onclick=()=>{origin=dest=null;nextPoint='origin';cityCenter=null;[originMarker,destMarker,routeLayer].forEach(x=>{if(x)map.removeLayer(x)});originMarker=destMarker=routeLayer=null;$('city-search').value='';$('origin-info').style.display='none';$('dest-info').style.display='none';$('result').style.display='none';$('copy-message').textContent='';updateCopyButtons();map.invalidateSize()};
updateCopyButtons();

// حکم چهار نفره: شما و بازیکن روبه‌رو در یک تیم هستید
let pasoorStarted=false, hDeck=[], hHands=[[],[],[],[]], hTrick=[], hTrump=null, hLeader=0, hTurn=0, hTeamTricks=[0,0], hPhase='trump', hGameOver=false;
const hSuits=['♠','♥','♦','♣'], hRanks=[{v:2,t:'۲'},{v:3,t:'۳'},{v:4,t:'۴'},{v:5,t:'۵'},{v:6,t:'۶'},{v:7,t:'۷'},{v:8,t:'۸'},{v:9,t:'۹'},{v:10,t:'۱۰'},{v:11,t:'سرباز'},{v:12,t:'بی‌بی'},{v:13,t:'شاه'},{v:14,t:'آس'}];
function hShuffle(){hDeck=[];for(const su of hSuits)for(const r of hRanks)hDeck.push({s:su,v:r.v,t:r.t,id:su+r.v});for(let i=hDeck.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[hDeck[i],hDeck[j]]=[hDeck[j],hDeck[i]]}}
function hCard(c,disabled=false){return `<button type="button" class="playing-card ${c.s==='♥'||c.s==='♦'?'red-card':''}" data-card="${c.id}" ${disabled?'disabled':''}><span>${c.t}</span><b>${c.s}</b></button>`}
function hRender(){
 $('pasoor-table').innerHTML=hTrick.length?hTrick.map(x=>`<div class="hokm-play"><small>${['شما','حریف چپ','هم‌تیمی','حریف راست'][x.p]}</small>${hCard(x.c,true)}</div>`).join(''):'<span class="game-help" style="color:#d1fae5">کارت‌های دور بعدی اینجا قرار می‌گیرند</span>';
 $('pasoor-hand').innerHTML=hHands[0].slice().sort((a,b)=>hSuits.indexOf(a.s)-hSuits.indexOf(b.s)||b.v-a.v).map(c=>hCard(c,hPhase!=='play'||hTurn!==0||hGameOver)).join('');
 document.querySelectorAll('#pasoor-hand [data-card]').forEach(b=>b.addEventListener('click',()=>hUserPlay(b.dataset.card)));
 $('pasoor-player-score').textContent=hTeamTricks[0].toLocaleString('fa-IR');$('pasoor-ai-score').textContent=hTeamTricks[1].toLocaleString('fa-IR');
 ['hokm-user-count','hokm-left-count','hokm-top-count','hokm-right-count'].forEach((id,i)=>$(id).textContent=hHands[[0,1,2,3][i]].length+' کارت');
 $('hokm-select').classList.toggle('hidden',hPhase!=='trump');
}
function pasoorNewGame(){
 pasoorStarted=true;hShuffle();hHands=[[],[],[],[]];for(let round=0;round<5;round++)for(let p=0;p<4;p++)hHands[p].push(hDeck.shift());
 hTrick=[];hTrump=null;hLeader=0;hTurn=0;hTeamTricks=[0,0];hPhase='trump';hGameOver=false;
 $('pasoor-message').textContent='۵ کارت اول دستت را ببین و خال حکم را انتخاب کن. شما و هم‌تیمی‌تان روبه‌روی هم هستید.';
 hRender();
}
function hFinishTrump(suit){if(hPhase!=='trump')return;hTrump=suit;for(let round=0;round<8;round++)for(let p=0;p<4;p++)hHands[p].push(hDeck.shift());hPhase='play';hTurn=hLeader;$('pasoor-message').textContent='حکم '+suit+' انتخاب شد. شما شروع می‌کنی؛ اگر از خال شروع‌شده کارت داری باید همان خال را بازی کنی.';hRender();if(hTurn!==0)hAiSequence()}
document.querySelectorAll('[data-trump]').forEach(b=>b.addEventListener('click',()=>hFinishTrump(b.dataset.trump)));
function hLegal(c,p=0){const lead=hTrick.length?hTrick[0].c.s:null;return !lead||!hHands[p].some(x=>x.s===lead)||c.s===lead}
function hUserPlay(id){if(hPhase!=='play'||hTurn!==0||hGameOver)return;const ix=hHands[0].findIndex(c=>c.id===id);if(ix<0)return;const c=hHands[0][ix];if(!hLegal(c,0)){$('pasoor-message').textContent='از خال شروع‌شده کارت داری؛ باید همان خال را بازی کنی.';return}hPlayCard(0,ix);hAiSequence()}
function hPlayCard(p,ix){const c=hHands[p].splice(ix,1)[0];hTrick.push({p,c});hTurn=(p+1)%4;hRender();if(hTrick.length===4)setTimeout(hResolveTrick,650)}
function hAiSequence(){if(hPhase!=='play'||hGameOver||hTrick.length===4)return;if(hTurn===0){hRender();return}setTimeout(()=>{if(hPhase!=='play'||hGameOver||hTrick.length===4)return;const p=hTurn,lead=hTrick.length?hTrick[0].c.s:null;let options=hHands[p].map((c,i)=>({c,i}));if(lead&&options.some(x=>x.c.s===lead))options=options.filter(x=>x.c.s===lead);let chosen;if(!hTrick.length)chosen=options.sort((a,b)=>b.c.v-a.c.v)[0];else chosen=options[Math.floor(Math.random()*options.length)];hPlayCard(p,chosen.i);if(hTrick.length<4)hAiSequence()},480)}
function hResolveTrick(){if(hTrick.length!==4)return;const lead=hTrick[0].c.s;function power(x){return (x.c.s===hTrump?100:0)+(x.c.s===lead?10:0)+x.c.v}const winner=hTrick.reduce((best,x)=>power(x)>power(best)?x:best).p;const team=winner%2===0?0:1;hTeamTricks[team]++;hLeader=winner;hTurn=winner;hTrick=[];if(hHands.every(hand=>hand.length===0)){hGameOver=true;hPhase='done';const won=hTeamTricks[0]>hTeamTricks[1]?0:1;$('pasoor-message').textContent=`دست تمام شد؛ تیم ${won===0?'شما':'حریف'} برنده شد (${hTeamTricks[0]} به ${hTeamTricks[1]} دور). برای بازی دوباره «بازی جدید» را بزن.`;hRender();return}$('pasoor-message').textContent=`این دور را ${['شما','حریف چپ','هم‌تیمی','حریف راست'][winner]} برد. ${winner===0?'نوبت شماست.': 'حریف شروع می‌کند.'}`;hRender();if(hTurn!==0)hAiSequence()}
$('pasoor-new').addEventListener('click',pasoorNewGame);
// بازی مار مستقل از نقشه
const snakeCanvas=$('snake-board'), snakeCtx=snakeCanvas.getContext('2d');
const CELL=20, COLS=snakeCanvas.width/CELL, ROWS=snakeCanvas.height/CELL;
let snake=[], snakeDir={x:1,y:0}, snakeNext={x:1,y:0}, snakeFood={x:10,y:8}, snakeScore=0, snakeTimer=null, snakeRunning=false;
function snakeFoodNew(){do{snakeFood={x:Math.floor(Math.random()*COLS),y:Math.floor(Math.random()*ROWS)}}while(snake.some(p=>p.x===snakeFood.x&&p.y===snakeFood.y))}
function snakeDraw(){
 snakeCtx.clearRect(0,0,snakeCanvas.width,snakeCanvas.height);
 const bg=snakeCtx.createLinearGradient(0,0,snakeCanvas.width,snakeCanvas.height);bg.addColorStop(0,'#071b2b');bg.addColorStop(1,'#102b3d');snakeCtx.fillStyle=bg;snakeCtx.fillRect(0,0,snakeCanvas.width,snakeCanvas.height);
 snakeCtx.strokeStyle='rgba(125,211,252,.09)';snakeCtx.lineWidth=1;for(let x=0;x<=COLS;x++){snakeCtx.beginPath();snakeCtx.moveTo(x*CELL,0);snakeCtx.lineTo(x*CELL,snakeCanvas.height);snakeCtx.stroke()}for(let y=0;y<=ROWS;y++){snakeCtx.beginPath();snakeCtx.moveTo(0,y*CELL);snakeCtx.lineTo(snakeCanvas.width,y*CELL);snakeCtx.stroke()}
 snakeCtx.save();snakeCtx.shadowColor='#fb7185';snakeCtx.shadowBlur=16;snakeCtx.fillStyle='#fb7185';snakeCtx.beginPath();snakeCtx.arc(snakeFood.x*CELL+CELL/2,snakeFood.y*CELL+CELL/2,CELL*.34,0,Math.PI*2);snakeCtx.fill();snakeCtx.restore();
 snake.forEach((p,i)=>{snakeCtx.fillStyle=i===0?'#a3e635':(i%2?'#22c55e':'#10b981');snakeCtx.beginPath();snakeCtx.roundRect(p.x*CELL+2,p.y*CELL+2,CELL-4,CELL-4,6);snakeCtx.fill();if(i===0){snakeCtx.fillStyle='#082f49';snakeCtx.beginPath();snakeCtx.arc(p.x*CELL+CELL*.65,p.y*CELL+CELL*.35,2,0,Math.PI*2);snakeCtx.fill();snakeCtx.beginPath();snakeCtx.arc(p.x*CELL+CELL*.65,p.y*CELL+CELL*.65,2,0,Math.PI*2);snakeCtx.fill()}})
 if(!snakeRunning){snakeCtx.fillStyle='rgba(2,6,23,.72)';snakeCtx.fillRect(0,0,snakeCanvas.width,snakeCanvas.height);snakeCtx.fillStyle='#f8fafc';snakeCtx.font='bold 25px Vazirmatn,Tahoma,sans-serif';snakeCtx.textAlign='center';snakeCtx.fillText(snake.length?'بازی تمام شد!':'آماده‌ای؟',snakeCanvas.width/2,snakeCanvas.height/2-8);snakeCtx.font='16px Vazirmatn,Tahoma,sans-serif';snakeCtx.fillStyle='#bae6fd';snakeCtx.fillText(snake.length?'برای شروع دوباره دکمه را بزن':'شروع را بزن و حرکت کن',snakeCanvas.width/2,snakeCanvas.height/2+25)}
}
function snakeStart(){clearInterval(snakeTimer);snake=[{x:Math.floor(COLS/2),y:Math.floor(ROWS/2)},{x:Math.floor(COLS/2)-1,y:Math.floor(ROWS/2)},{x:Math.floor(COLS/2)-2,y:Math.floor(ROWS/2)}];snakeDir={x:1,y:0};snakeNext={x:1,y:0};snakeScore=0;snakeRunning=true;$('snake-score').textContent='۰';$('snake-message').textContent='عالیه! خوراکی‌ها را بخور و به دیوار یا بدن خودت برخورد نکن.';snakeFoodNew();snakeDraw();snakeTimer=setInterval(snakeStep,115)}
function snakeStep(){if(!snakeRunning)return;snakeDir=snakeNext;const head={x:snake[0].x+snakeDir.x,y:snake[0].y+snakeDir.y};if(head.x<0||head.x>=COLS||head.y<0||head.y>=ROWS||snake.some((p,i)=>i<snake.length-1&&p.x===head.x&&p.y===head.y)){snakeRunning=false;clearInterval(snakeTimer);$('snake-message').textContent='بازی تمام شد! امتیاز شما: '+snakeScore+' — برای شروع دوباره دکمه را بزن.';snakeDraw();return}snake.unshift(head);if(head.x===snakeFood.x&&head.y===snakeFood.y){snakeScore++;$('snake-score').textContent=snakeScore.toLocaleString('fa-IR');snakeFoodNew()}else snake.pop();snakeDraw()}
function snakeTurn(d){if(!snakeRunning)return;const dirs={up:{x:0,y:-1},down:{x:0,y:1},left:{x:-1,y:0},right:{x:1,y:0}};const n=dirs[d];if(n&&!(n.x===-snakeDir.x&&n.y===-snakeDir.y))snakeNext=n}
$('snake-start').addEventListener('click',snakeStart);document.querySelectorAll('.game-pad button').forEach(b=>b.addEventListener('click',()=>snakeTurn(b.dataset.dir)));
document.addEventListener('keydown',e=>{
 if(e.key==='Enter'&&!gamePage.classList.contains('hidden')&&!snakeRunning){e.preventDefault();snakeStart();return}
const k=e.key.toLowerCase();const mapKeys={'arrowup':'up','w':'up','arrowdown':'down','s':'down','arrowleft':'left','a':'left','arrowright':'right','d':'right'};if(mapKeys[k]&&document.activeElement!==$('city-search')){e.preventDefault();snakeTurn(mapKeys[k])}});
snakeDraw();

</script>
</body></html>
"""
@app.get("/")
def index():
    return render_template_string(HTML)

@app.get("/poster.png")
def poster():
    image_path = Path(__file__).with_name("poster_168_minab.png")
    if not image_path.is_file():
        return "فایل پوستر کنار app.py قرار نگرفته است.", 404
    return send_file(image_path, mimetype="image/png", conditional=True)

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
