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
        <button class="secondary-btn" onclick="openGoogleMaps()">باز کردن مسیر در گوگل‌مپ</button>
      </div>
    </div>
  </section>

  <div class="actions">
    <button onclick="copyBoth()">کپی مبدأ و مقصد</button>
    <button class="secondary-btn" onclick="savePoints()">ذخیره مختصات</button>
    <button class="danger-btn" onclick="clearAll()">پاک کردن مبدأ و مقصد</button>
  </div>
</main>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  const statusBox = document.getElementById('status');
  let map = null;
  let mode = 'origin';
  let routeLayer = null;
  let routeRequestId = 0;

  const points = {
    origin: { lat: null, lng: null, marker: null },
    destination: { lat: null, lng: null, marker: null }
  };

  function setStatus(message) {
    statusBox.textContent = message;
  }

  function savePoints() {
    try {
      const saved = {
        origin: { lat: points.origin.lat, lng: points.origin.lng },
        destination: { lat: points.destination.lat, lng: points.destination.lng }
      };
      localStorage.setItem('iranCoordinateMapPoints', JSON.stringify(saved));
      setStatus('مختصات مبدأ و مقصد در همین مرورگر ذخیره شد.');
    } catch (error) {
      setStatus('ذخیره خودکار در این مرورگر در دسترس نیست؛ مختصات را کپی کن.');
    }
  }

  function loadSavedPoints() {
    try {
      const raw = localStorage.getItem('iranCoordinateMapPoints');
      if (!raw) return;
      const saved = JSON.parse(raw);
      if (saved.origin && Number.isFinite(saved.origin.lat) && Number.isFinite(saved.origin.lng)) {
        setPoint('origin', saved.origin.lat, saved.origin.lng, false, false);
      }
      if (saved.destination && Number.isFinite(saved.destination.lat) && Number.isFinite(saved.destination.lng)) {
        setPoint('destination', saved.destination.lat, saved.destination.lng, false, false);
      }
      if (points.origin.lat !== null || points.destination.lat !== null) {
        setStatus('مختصات ذخیره‌شده از قبل بازیابی شد.');
        if (points.origin.lat !== null && points.destination.lat !== null) calculateRoute();
      }
    } catch (error) {
      localStorage.removeItem('iranCoordinateMapPoints');
    }
  }

  function initializeMap() {
    if (typeof L === 'undefined') {
      setStatus('نقشه بارگذاری نشد. اتصال اینترنت یا دسترسی به سرویس نقشه را بررسی کن.');
      return;
    }
    map = L.map('map').setView([32.0, 53.0], 5);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    map.on('click', function(event) {
      setPoint(mode, event.latlng.lat, event.latlng.lng, false);
    });
    setTimeout(function() { map.invalidateSize(); }, 300);
    loadSavedPoints();
  }

  function selectMode(which) {
    mode = which;
    setStatus(which === 'origin'
      ? 'انتخاب مبدأ فعال شد. حالا روی نقطه موردنظر در نقشه کلیک کن.'
      : 'انتخاب مقصد فعال شد. حالا روی نقطه موردنظر در نقشه کلیک کن.');
  }

  function setPoint(which, lat, lng, zoom, persist = true) {
    if (!map) {
      setStatus('نقشه هنوز آماده نیست. کمی صبر کن.');
      return;
    }
    const point = points[which];
    point.lat = Number(lat);
    point.lng = Number(lng);

    document.getElementById(which + 'Lat').textContent = point.lat.toFixed(6);
    document.getElementById(which + 'Lng').textContent = point.lng.toFixed(6);

    const label = which === 'origin' ? 'مبدأ' : 'مقصد';
    if (point.marker) {
      point.marker.setLatLng([point.lat, point.lng]);
    } else {
      point.marker = L.marker([point.lat, point.lng]).addTo(map);
    }
    point.marker.bindPopup(label + '<br>عرض: ' + point.lat.toFixed(6) +
      '<br>طول: ' + point.lng.toFixed(6));

    if (zoom) {
      map.setView([point.lat, point.lng], 14);
      point.marker.openPopup();
    }
    if (persist) {
      try {
        localStorage.setItem('iranCoordinateMapPoints', JSON.stringify({
          origin: { lat: points.origin.lat, lng: points.origin.lng },
          destination: { lat: points.destination.lat, lng: points.destination.lng }
        }));
      } catch (error) {}
    }

    clearRouteDisplay();
    setStatus(label + ' انتخاب شد.');
    if (points.origin.lat !== null && points.destination.lat !== null) {
      calculateRoute();
    }
  }

  async function searchPlace(which) {
    const inputId = which === 'origin' ? 'originSearch' : 'destinationSearch';
    const query = document.getElementById(inputId).value.trim();
    if (!query) {
      alert('ابتدا نام شهر یا مکان را وارد کن.');
      return;
    }
    if (!map) {
      setStatus('نقشه هنوز آماده نیست.');
      return;
    }
    setStatus('در حال جست‌وجوی مکان؛ لطفاً صبر کن...');
    try {
      const params = new URLSearchParams({
        q: query, format: 'jsonv2', countrycodes: 'ir', limit: '5', 'accept-language': 'fa'
      });
      const response = await fetch('https://nominatim.openstreetmap.org/search?' + params.toString(), {
        headers: { 'Accept': 'application/json' }
      });
      if (!response.ok) throw new Error('Search request failed');
      const results = await response.json();
      if (!results.length) {
        setStatus('مکانی پیدا نشد. نام شهر یا آدرس را دقیق‌تر وارد کن.');
        return;
      }
      let result = results[0];
      if (results.length > 1) {
        const choices = results.map((item, index) => (index + 1) + '. ' + item.display_name).join('\n\n');
        const answer = prompt('شماره مکان موردنظر را وارد کن:\n\n' + choices, '1');
        if (answer === null) {
          setStatus('جست‌وجو لغو شد.');
          return;
        }
        const selectedIndex = Number(answer) - 1;
        if (!Number.isInteger(selectedIndex) || selectedIndex < 0 || selectedIndex >= results.length) {
          alert('شماره انتخابی معتبر نیست.');
          return;
        }
        result = results[selectedIndex];
      }
      setPoint(which, Number(result.lat), Number(result.lon), true);
    } catch (error) {
      setStatus('جست‌وجو ناموفق بود. اتصال اینترنت یا دسترسی به سرویس جست‌وجو را بررسی کن.');
    }
  }

  function clearRouteDisplay() {
    routeRequestId++;
    if (routeLayer && map) {
      map.removeLayer(routeLayer);
      routeLayer = null;
    }
    document.getElementById('routeDistance').textContent = '—';
    document.getElementById('routeDuration').textContent = 'پس از انتخاب مبدأ و مقصد محاسبه می‌شود.';
    document.getElementById('routeStatus').textContent = 'هنوز مسیری محاسبه نشده است.';
  }

  async function calculateRoute() {
    if (points.origin.lat === null || points.destination.lat === null) {
      setStatus('برای محاسبه مسیر، ابتدا مبدأ و مقصد را انتخاب کن.');
      return;
    }
    const requestId = ++routeRequestId;
    document.getElementById('routeStatus').textContent = 'در حال محاسبه مسیر جاده‌ای...';
    document.getElementById('routeDistance').textContent = '...';
    document.getElementById('routeDuration').textContent = 'لطفاً چند لحظه صبر کن.';
    try {
      const start = points.origin.lng + ',' + points.origin.lat;
      const end = points.destination.lng + ',' + points.destination.lat;
      const url = 'https://router.project-osrm.org/route/v1/driving/' +
        start + ';' + end + '?overview=full&geometries=geojson&steps=false';
      const response = await fetch(url);
      if (!response.ok) throw new Error('Route request failed');
      const data = await response.json();
      if (requestId !== routeRequestId) return;
      if (data.code !== 'Ok' || !data.routes || !data.routes.length) {
        throw new Error('No route');
      }
      const route = data.routes[0];
      const km = route.distance / 1000;
      const minutes = Math.round(route.duration / 60);
      document.getElementById('routeDistance').textContent = km.toLocaleString('fa-IR', { maximumFractionDigits: 1 }) + ' کیلومتر';
      let durationText = minutes < 60
        ? minutes.toLocaleString('fa-IR') + ' دقیقه (تخمینی)'
        : Math.floor(minutes / 60).toLocaleString('fa-IR') + ' ساعت و ' +
          (minutes % 60).toLocaleString('fa-IR') + ' دقیقه (تخمینی)';
      document.getElementById('routeDuration').textContent = 'زمان رانندگی: ' + durationText;
      document.getElementById('routeStatus').textContent = 'مسیر جاده‌ای روی نقشه نمایش داده شد.';
      routeLayer = L.geoJSON(route.geometry, {
        style: { color: '#e11d48', weight: 5, opacity: 0.85 }
      }).addTo(map);
      map.fitBounds(routeLayer.getBounds(), { padding: [25, 25] });
      setStatus('مسیر جاده‌ای محاسبه شد. فاصله و زمان تقریبی را پایین نقشه می‌بینی.');
    } catch (error) {
      if (requestId !== routeRequestId) return;
      document.getElementById('routeDistance').textContent = 'در دسترس نیست';
      document.getElementById('routeDuration').textContent = 'سرویس مسیر پاسخ نداد یا برای این نقاط مسیر پیدا نکرد.';
      document.getElementById('routeStatus').textContent = 'مسیر جاده‌ای محاسبه نشد. دوباره تلاش کن یا از گوگل‌مپ استفاده کن.';
      setStatus('محاسبه مسیر ناموفق بود. ممکن است سرویس مسیریابی موقتاً در دسترس نباشد.');
    }
  }

  function openGoogleMaps() {
    if (points.origin.lat === null || points.destination.lat === null) {
      alert('ابتدا هم مبدأ و هم مقصد را انتخاب کن.');
      return;
    }
    const url = 'https://www.google.com/maps/dir/?api=1&origin=' +
      points.origin.lat + ',' + points.origin.lng + '&destination=' +
      points.destination.lat + ',' + points.destination.lng + '&travelmode=driving';
    window.open(url, '_blank', 'noopener');
  }

  async function copyText(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        alert('مختصات کپی شد.');
      } else {
        throw new Error('Clipboard unavailable');
      }
    } catch (error) {
      prompt('متن زیر را انتخاب و کپی کن:', text);
    }
  }

  function copyPoint(which) {
    const point = points[which];
    if (point.lat === null || point.lng === null) {
      alert(which === 'origin' ? 'ابتدا مبدأ را انتخاب کن.' : 'ابتدا مقصد را انتخاب کن.');
      return;
    }
    copyText(point.lat.toFixed(6) + ', ' + point.lng.toFixed(6));
  }

  function copyBoth() {
    if (points.origin.lat === null || points.destination.lat === null) {
      alert('ابتدا هم مبدأ و هم مقصد را انتخاب کن.');
      return;
    }
    copyText('مبدأ: ' + points.origin.lat.toFixed(6) + ', ' + points.origin.lng.toFixed(6) +
      '\nمقصد: ' + points.destination.lat.toFixed(6) + ', ' + points.destination.lng.toFixed(6));
  }

  function clearAll() {
    if (!confirm('مبدأ و مقصد ذخیره‌شده پاک شوند؟')) return;
    ['origin', 'destination'].forEach(function(which) {
      const point = points[which];
      if (point.marker && map) map.removeLayer(point.marker);
      point.marker = null;
      point.lat = null;
      point.lng = null;
      document.getElementById(which + 'Lat').textContent = '—';
      document.getElementById(which + 'Lng').textContent = '—';
      document.getElementById(which + 'Search').value = '';
    });
    try { localStorage.removeItem('iranCoordinateMapPoints'); } catch (error) {}
    clearRouteDisplay();
    setStatus('مبدأ و مقصد پاک شدند. می‌توانی نقاط جدید انتخاب کنی.');
  }

  window.addEventListener('load', initializeMap);
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
