from flask import Flask, render_template_string

app = Flask(__name__)

HTML = r"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>نقشه مبدأ و مقصد ایران</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Tahoma, Arial, sans-serif; background: #f1f5f9; color: #172033; }
    header { background: #1457c5; color: white; padding: 18px 12px; text-align: center; }
    header h2 { margin: 0 0 8px; }
    .panel { max-width: 1100px; width: calc(100% - 24px); margin: 18px auto; padding: 16px; background: white; border-radius: 12px; }
    .searches, .coordinates, .route-info { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    .search-box, .item, .route-card { background: #f1f5f9; padding: 14px; border-radius: 10px; min-width: 0; }
    input { display: block; width: 100%; padding: 12px; margin-top: 10px; border: 1px solid #cbd5e1; border-radius: 7px; font-family: Tahoma, Arial, sans-serif; font-size: 14px; }
    button { border: 0; border-radius: 7px; padding: 11px 14px; margin: 8px 4px 0 0; background: #1457c5; color: white; font-family: Tahoma, Arial, sans-serif; font-size: 14px; cursor: pointer; }
    button:hover { filter: brightness(.9); }
    .destination-btn { background: #16804a; }
    .secondary-btn { background: #475569; }
    .danger-btn { background: #b91c1c; }
    #map { width: 100%; height: 55vh; min-height: 350px; border-radius: 10px; margin-top: 12px; background: #e2e8f0; }
    #status { padding: 10px 0; line-height: 1.9; color: #334155; }
    .coordinates, .route-info { margin-top: 14px; }
    .value { direction: ltr; text-align: left; font-size: 15px; font-weight: bold; margin: 7px 0 12px; overflow-wrap: anywhere; }
    .hint { font-size: 12px; color: #64748b; line-height: 1.9; }
    .route-card strong { display: block; margin-bottom: 8px; }
    .route-number { font-size: 20px; font-weight: bold; color: #1457c5; }
    .actions { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
    @media (max-width: 650px) {
      .searches, .coordinates, .route-info { grid-template-columns: 1fr; }
      #map { height: 55vh; min-height: 320px; }
    }
  </style>
</head>
<body>
<header>
  <h2>انتخاب مبدأ و مقصد روی نقشه ایران</h2>
  <div>مختصات ذخیره می‌شود و مسیر جاده‌ای بین دو نقطه محاسبه می‌شود.</div>
</header>

<main class="panel">
  <div class="searches">
    <section class="search-box">
      <strong>📍 مبدأ</strong>
      <input id="originSearch" type="text" placeholder="مثلاً لای‌بید، اصفهان">
      <button onclick="searchPlace('origin')">جست‌وجوی مبدأ</button>
      <button class="secondary-btn" onclick="selectMode('origin')">انتخاب مبدأ روی نقشه</button>
    </section>
    <section class="search-box">
      <strong>🏁 مقصد</strong>
      <input id="destinationSearch" type="text" placeholder="مثلاً اصفهان">
      <button class="destination-btn" onclick="searchPlace('destination')">جست‌وجوی مقصد</button>
      <button class="secondary-btn" onclick="selectMode('destination')">انتخاب مقصد روی نقشه</button>
    </section>
  </div>

  <p id="status">برای شروع، مبدأ و مقصد را انتخاب کن.</p>
  <div id="map"></div>
  <p class="hint">برای انتخاب نقطه، دکمه مبدأ یا مقصد را بزن و بعد روی نقشه کلیک کن. مختصات در همین مرورگر ذخیره می‌شود و با رفرش صفحه باقی می‌ماند.</p>

  <div class="coordinates">
    <section class="item">
      <strong>📍 مختصات مبدأ</strong>
      <div>عرض جغرافیایی (Latitude)</div>
      <div class="value" id="originLat">—</div>
      <div>طول جغرافیایی (Longitude)</div>
      <div class="value" id="originLng">—</div>
      <button onclick="copyPoint('origin')">کپی مختصات مبدأ</button>
    </section>
    <section class="item">
      <strong>🏁 مختصات مقصد</strong>
      <div>عرض جغرافیایی (Latitude)</div>
      <div class="value" id="destinationLat">—</div>
      <div>طول جغرافیایی (Longitude)</div>
      <div class="value" id="destinationLng">—</div>
      <button class="destination-btn" onclick="copyPoint('destination')">کپی مختصات مقصد</button>
    </section>
  </div>

  <section class="route-info">
    <div class="route-card">
      <strong>🚗 فاصله جاده‌ای</strong>
      <div id="routeDistance" class="route-number">—</div>
      <div id="routeDuration" class="hint">پس از انتخاب مبدأ و مقصد محاسبه می‌شود.</div>
    </div>
    <div class="route-card">
      <strong>🧭 وضعیت مسیر</strong>
      <div id="routeStatus">هنوز مسیری محاسبه نشده است.</div>
      <div class="actions">
        <button onclick="calculateRoute()">محاسبه مسیر جاده‌ای</button>
