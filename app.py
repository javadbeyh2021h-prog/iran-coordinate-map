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
