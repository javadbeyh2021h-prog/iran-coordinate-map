from flask import Flask, render_template_string

app = Flask(__name__)

HTML = r"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>انتخاب مختصات مبدأ و مقصد</title>

    <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    >

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Tahoma, Arial, sans-serif;
            background: #f1f5f9;
            color: #172033;
        }

        header {
            background: #1457c5;
            color: white;
            padding: 16px;
            text-align: center;
        }

        header h2 {
            margin: 0 0 8px;
        }

        .panel {
            max-width: 1100px;
            width: calc(100% - 24px);
            margin: 18px auto;
            padding: 16px;
            background: white;
            border-radius: 12px;
        }

        .searches,
        .coordinates {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
        }

        .search-box,
        .item {
            background: #f1f5f9;
            padding: 14px;
            border-radius: 10px;
            min-width: 0;
        }

        input {
            display: block;
            width: 100%;
            padding: 12px;
            margin-top: 10px;
            border: 1px solid #cbd5e1;
            border-radius: 7px;
            font-family: Tahoma, Arial, sans-serif;
            font-size: 14px;
        }

        button {
            border: 0;
            border-radius: 7px;
            padding: 11px 14px;
            margin: 8px 4px 0 0;
            background: #1457c5;
            color: white;
            font-family: Tahoma, Arial, sans-serif;
            font-size: 14px;
            cursor: pointer;
        }

        button:hover {
            filter: brightness(0.9);
        }

        .destination-btn {
            background: #16804a;
        }

        .secondary-btn {
            background: #475569;
        }

        #map {
            width: 100%;
            height: 55vh;
            min-height: 350px;
            border-radius: 10px;
            margin-top: 12px;
            background: #e2e8f0;
        }

        #status {
            padding: 10px 0;
            line-height: 1.9;
            color: #334155;
        }

        .coordinates {
            margin-top: 14px;
        }

        .value {
            direction: ltr;
            text-align: left;
            font-size: 15px;
            font-weight: bold;
            margin: 7px 0 12px;
            overflow-wrap: anywhere;
        }

        .hint {
            font-size: 12px;
            color: #64748b;
            line-height: 1.9;
        }

        @media (max-width: 650px) {
            .searches,
            .coordinates {
                grid-template-columns: 1fr;
            }

            #map {
                height: 55vh;
                min-height: 320px;
            }
        }
    </style>
</head>

<body>
<header>
    <h2>انتخاب مختصات مبدأ و مقصد</h2>
    <div>مبدأ و مقصد را روی نقشه ایران انتخاب کن.</div>
</header>

<main class="panel">

    <div class="searches">
        <section class="search-box">
            <strong>📍 مبدأ</strong>

            <input
                id="originSearch"
                type="text"
                placeholder="مثلاً لای‌بید، اصفهان"
            >

            <button onclick="searchPlace('origin')">
                جست‌وجوی مبدأ
            </button>

            <button
                class="secondary-btn"
                onclick="selectMode('origin')"
            >
                انتخاب مبدأ روی نقشه
            </button>
        </section>

        <section class="search-box">
            <strong>🏁 مقصد</strong>

            <input
                id="destinationSearch"
                type="text"
                placeholder="مثلاً اصفهان"
            >

            <button
                class="destination-btn"
                onclick="searchPlace('destination')"
            >
                جست‌وجوی مقصد
            </button>

            <button
                class="secondary-btn"
                onclick="selectMode('destination')"
            >
                انتخاب مقصد روی نقشه
            </button>
        </section>
    </div>

    <p id="status">
        برای شروع، مبدأ یا مقصد را انتخاب کن.
    </p>

    <div id="map"></div>

    <p class="hint">
        برای انتخاب نقطه، ابتدا دکمه مبدأ یا مقصد را بزن،
        سپس روی محل موردنظر در نقشه کلیک کن.
    </p>

    <div class="coordinates">
        <section class="item">
            <strong>📍 مختصات مبدأ</strong>

            <div>عرض جغرافیایی (Latitude)</div>
            <div class="value" id="originLat">—</div>

            <div>طول جغرافیایی (Longitude)</div>
            <div class="value" id="originLng">—</div>

            <button onclick="copyPoint('origin')">
                کپی مختصات مبدأ
            </button>
        </section>

        <section class="item">
            <strong>🏁 مختصات مقصد</strong>

            <div>عرض جغرافیایی (Latitude)</div>
            <div class="value" id="destinationLat">—</div>

            <div>طول جغرافیایی (Longitude)</div>
            <div class="value" id="destinationLng">—</div>

            <button
                class="destination-btn"
                onclick="copyPoint('destination')"
            >
                کپی مختصات مقصد
            </button>
        </section>
    </div>

    <button onclick="copyBoth()">کپی مبدأ و مقصد</button>

</main>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
    const statusBox = document.getElementById('status');

    let map = null;
    let mode = 'origin';

    const points = {
        origin: {
            lat: null,
            lng: null,
            marker: null
        },
        destination: {
            lat: null,
            lng: null,
            marker: null
        }
    };

    function setStatus(message) {
        statusBox.textContent = message;
    }

    function initializeMap() {
        if (typeof L === 'undefined') {
            setStatus(
                'نقشه بارگذاری نشد. اتصال اینترنت و دسترسی به سرویس نقشه را بررسی کن.'
            );
            return;
        }

        map = L.map('map').setView([32.0, 53.0], 5);

        L.tileLayer(
            'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            {
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap contributors'
            }
        ).addTo(map);

        map.on('click', function(event) {
            setPoint(
                mode,
                event.latlng.lat,
                event.latlng.lng,
                false
            );
        });

        setTimeout(function() {
            map.invalidateSize();
        }, 300);
    }

    function selectMode(which) {
        mode = which;

        if (which === 'origin') {
            setStatus(
                'انتخاب مبدأ فعال شد. حالا روی نقطه موردنظر در نقشه کلیک کن.'
            );
        } else {
            setStatus(
                'انتخاب مقصد فعال شد. حالا روی نقطه موردنظر در نقشه کلیک کن.'
            );
        }
    }

    function setPoint(which, lat, lng, zoom) {
        if (!map) {
            setStatus('نقشه هنوز آماده نیست. کمی صبر کن.');
            return;
        }

        const point = points[which];

        point.lat = Number(lat);
        point.lng = Number(lng);

        document.getElementById(which + 'Lat').textContent =
            point.lat.toFixed(6);

        document.getElementById(which + 'Lng').textContent =
            point.lng.toFixed(6);

        const label = which === 'origin' ? 'مبدأ' : 'مقصد';

        if (point.marker) {
            point.marker.setLatLng([point.lat, point.lng]);
        } else {
            point.marker = L.marker(
                [point.lat, point.lng]
            ).addTo(map);
        }

        point.marker.bindPopup(
            label +
            '<br>عرض: ' + point.lat.toFixed(6) +
            '<br>طول: ' + point.lng.toFixed(6)
        );

        if (zoom) {
            map.setView([point.lat, point.lng], 15);
            point.marker.openPopup();
        }

        setStatus(
            label + ' انتخاب شد. می‌توانی نقطه دیگر را هم انتخاب کنی.'
        );
    }

    async function searchPlace(which) {
        const inputId = which === 'origin'
            ? 'originSearch'
            : 'destinationSearch';

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
                q: query,
                format: 'jsonv2',
                countrycodes: 'ir',
                limit: '5',
                'accept-language': 'fa'
            });

            const response = await fetch(
                'https://nominatim.openstreetmap.org/search?' +
                params.toString(),
                {
                    headers: {
                        'Accept': 'application/json'
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Search request failed');
            }

            const results = await response.json();

            if (!results.length) {
                setStatus(
                    'مکانی پیدا نشد. نام شهر یا آدرس را دقیق‌تر وارد کن.'
                );
                return;
            }

            let result = results[0];

            if (results.length > 1) {
                const choices = results.map(function(item, index) {
                    return (index + 1) + '. ' + item.display_name;
                }).join('\n\n');

                const answer = prompt(
                    'شماره مکان موردنظر را وارد کن:\n\n' + choices,
                    '1'
                );

                if (answer === null) {
                    setStatus('جست‌وجو لغو شد.');
                    return;
                }

                const selectedIndex = Number(answer) - 1;

                if (
                    !Number.isInteger(selectedIndex) ||
                    selectedIndex < 0 ||
                    selectedIndex >= results.length
                ) {
                    alert('شماره انتخابی معتبر نیست.');
                    setStatus('لطفاً دوباره جست‌وجو کن.');
                    return;
                }

                result = results[selectedIndex];
            }

            setPoint(
                which,
                Number(result.lat),
                Number(result.lon),
                true
            );

        } catch (error) {
            setStatus(
                'جست‌وجو ناموفق بود. اتصال اینترنت یا دسترسی به سرویس جست‌وجو را بررسی کن.'
            );
        }
    }

    async function copyText(text) {
        try {
            if (
                navigator.clipboard &&
                window.isSecureContext
            ) {
                await navigator.clipboard.writeText(text);
            } else {
                throw new Error('Clipboard unavailable');
            }

            alert('مختصات کپی شد.');

        } catch (error) {
            prompt('متن زیر را انتخاب و کپی کن:', text);
        }
    }

    function copyPoint(which) {
        const point = points[which];

        if (point.lat === null || point.lng === null) {
            alert(
                which === 'origin'
                    ? 'ابتدا مبدأ را انتخاب کن.'
                    : 'ابتدا مقصد را انتخاب کن.'
            );
            return;
        }

        copyText(
            point.lat.toFixed(6) + ', ' +
            point.lng.toFixed(6)
        );
    }

    function copyBoth() {
        if (
            points.origin.lat === null ||
            points.origin.lng === null ||
            points.destination.lat === null ||
            points.destination.lng === null
        ) {
            alert('ابتدا هم مبدأ و هم مقصد را انتخاب کن.');
            return;
        }

        const text =
            'مبدأ: ' +
            points.origin.lat.toFixed(6) + ', ' +
            points.origin.lng.toFixed(6) +
            '\n' +
            'مقصد: ' +
            points.destination.lat.toFixed(6) + ', ' +
            points.destination.lng.toFixed(6);

        copyText(text);
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
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
