from flask import Flask, render_template_string, request, jsonify, send_file, copy_current_request_context
import requests
import math
import re
from pathlib import Path
import os, sqlite3, hmac, html, secrets
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from datetime import datetime, timezone
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
DB_PATH = os.environ.get("VISITORS_DB_PATH", str(Path(__file__).with_name("dalahoo_visitors.sqlite3")))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
USER_COOKIE = "dalahoo_user_id"
def db_connect():
    c=sqlite3.connect(DB_PATH, timeout=10); c.row_factory=sqlite3.Row; return c
def init_db():
    with db_connect() as c:
        c.execute("CREATE TABLE IF NOT EXISTS registered_users (user_id TEXT PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL, registered_at TEXT NOT NULL)")
        c.execute("CREATE TABLE IF NOT EXISTS game_runs (run_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, game TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT, points INTEGER NOT NULL DEFAULT 0, result TEXT, FOREIGN KEY(user_id) REFERENCES registered_users(user_id))")
def user_id_from_cookie():
    value=request.cookies.get(USER_COOKIE, "")
    return value if len(value)==32 and all(ch in "0123456789abcdef" for ch in value) else ""

def ensure_anonymous_user():
    """Create a browser-linked anonymous player; no name or surname is requested."""
    uid=user_id_from_cookie()
    with db_connect() as c:
        if uid and c.execute("SELECT 1 FROM registered_users WHERE user_id=?", (uid,)).fetchone():
            return uid, None
        uid=secrets.token_hex(16)
        now=datetime.now(timezone.utc).isoformat(timespec="seconds")
        # The legacy table requires first/last name; these are internal placeholders only.
        c.execute("INSERT INTO registered_users(user_id,first_name,last_name,registered_at) VALUES(?,?,?,?)",
                  (uid, "بازیکن", uid[-4:].upper(), now))
    return uid, uid

init_db()
HEADERS = {"User-Agent": "DebirnetRouteDemo/1.0 (Iran route planner)"}
HTML = r"""
<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta name="google-site-verification" content="fnbXC-pgbizfam1Zk1UDoWmiGicWBg2MSEOBUqFpmwc" />
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

/* Clearly illustrated playing cards: corner rank, suit pips, face-card art */
.playing-card{position:relative;overflow:hidden;width:66px;height:98px;flex:0 0 auto;padding:4px;border:1px solid #d6d3d1;border-radius:8px;background:linear-gradient(135deg,#fff 0%,#fffdf7 55%,#f1eee5 100%);color:#111827;display:block;box-shadow:0 4px 9px #02061740;font-family:Georgia,'Times New Roman',serif;transition:transform .12s ease,box-shadow .12s ease}
.playing-card.red-card{color:#c91f37}.playing-card.black-card{color:#111827}.playing-card:disabled{opacity:1}
.card-corner{position:absolute;z-index:2;display:flex;flex-direction:column;align-items:center;line-height:.95;font-size:12px;font-weight:900;gap:2px}.card-corner strong{font-size:15px}.card-corner b{font-size:12px}.top-corner{left:5px;top:5px}.bottom-corner{right:5px;bottom:5px;transform:rotate(180deg)}
.pip-grid{position:absolute;inset:22px 13px;display:grid;grid-template-columns:repeat(2,1fr);grid-template-rows:repeat(5,1fr);align-items:center;justify-items:center;font-size:14px;line-height:1}
.pip{font-style:normal;display:block}.pip:nth-child(even){transform:rotate(180deg)}
.pip-n1{grid-template-columns:1fr;grid-template-rows:1fr;align-items:center;justify-items:center;font-size:24px}
.pip-n2{grid-template-rows:1fr 1fr}.pip-n3{grid-template-rows:1fr 1fr 1fr}
.pip-n4,.pip-n5{grid-template-rows:repeat(3,1fr)}.pip-n6{grid-template-rows:repeat(3,1fr)}
.pip-n7,.pip-n8,.pip-n9,.pip-n10{grid-template-rows:repeat(5,1fr)}
.pip-grid .pip:nth-child(5){grid-column:1 / 3}
.ace-art{position:absolute;inset:22px 8px;display:flex;align-items:center;justify-content:center;font-size:42px;font-weight:900}
.face-art{position:absolute;inset:24px 9px;display:flex;flex-direction:column;align-items:center;justify-content:center;border:2px double currentColor;border-radius:5px;background:repeating-linear-gradient(45deg,#f7e7bd 0,#f7e7bd 4px,#fffaf0 4px,#fffaf0 8px);text-shadow:0 1px #fff;font-size:24px}
.face-crown{font-size:30px;line-height:1.1}.face-letter{font-family:Georgia,serif;font-size:16px;font-weight:900;background:#fff9;padding:1px 5px;border-radius:4px}
.ace-card{background:linear-gradient(135deg,#fffdf7,#e7dcc0)}.hokm-trick .playing-card{width:54px;height:80px}.hokm-trick .pip-grid{inset:19px 10px;font-size:11px}.hokm-trick .ace-art{font-size:31px}.hokm-trick .face-art{inset:21px 7px}.hokm-trick .face-crown{font-size:23px}
@media(max-width:600px){.playing-card{width:49px;height:76px;padding:3px;border-radius:6px}.card-corner{font-size:9px}.card-corner strong{font-size:12px}.card-corner b{font-size:9px}.top-corner{left:3px;top:4px}.bottom-corner{right:3px;bottom:4px}.pip-grid{inset:18px 9px;font-size:10px}.pip-n1{font-size:19px}.ace-art{inset:19px 5px;font-size:31px}.face-art{inset:20px 6px;font-size:19px}.face-crown{font-size:23px}.face-letter{font-size:12px}.hokm-trick .playing-card{width:42px;height:64px}.hokm-trick .pip-grid{inset:17px 8px;font-size:9px}.hokm-trick .ace-art{font-size:25px}}

.face-card .face-art{display:flex;align-items:center;justify-content:center;width:100%;height:68%;padding:2px}
.face-card .face-portrait{width:100%;height:100%;max-height:100%;display:block;filter:drop-shadow(0 1px 1px #0002)}
.face-card .card-corner{z-index:2;background:#ffffffdc;border-radius:3px;padding:1px 2px}
.face-card .face-art{position:relative}
@media(max-width:600px){.face-card .face-art{height:65%;padding:1px}.face-card .face-portrait{width:100%;height:100%}}

/* Dalahoo Professional Refresh — visual-only layer; gameplay and routes stay unchanged */
:root{
 --primary:#4f46e5;--success:#059669;--danger:#e11d48;
 --bg:#f4f6fb;--card:#ffffff;--text:#172033;--muted:#667085;--border:#e5e9f2;
 --shadow-soft:0 12px 32px rgba(25,35,75,.075);--shadow-hover:0 18px 42px rgba(25,35,75,.14)
}
html{scroll-behavior:smooth}
body{background:radial-gradient(ellipse at 12% 0%,#e5e9ff 0,transparent 36%),radial-gradient(ellipse at 92% 12%,#d9f7ed 0,transparent 28%),var(--bg);min-height:100vh}
header{background:rgba(255,255,255,.88);backdrop-filter:blur(14px);border-bottom:1px solid rgba(226,232,240,.85);box-shadow:0 5px 24px rgba(15,23,42,.045);padding:20px}
h1{font-size:clamp(22px,3vw,30px);letter-spacing:-.4px;background:linear-gradient(100deg,#4338ca,#0f766e);-webkit-background-clip:text;background-clip:text;color:transparent}
.subtitle{font-size:13px;letter-spacing:.1px}
.live{box-shadow:0 4px 12px #10b98112;font-weight:800}
.dash-wrap{max-width:1180px;margin:32px auto;padding-bottom:48px}
.dash-welcome{position:relative;isolation:isolate;overflow:hidden;padding:clamp(24px,4vw,42px);border:1px solid #ffffff40;background:linear-gradient(118deg,#312e81 0%,#4f46e5 48%,#0f766e 100%);box-shadow:0 22px 48px rgba(49,46,129,.2)}
.dash-welcome:after{content:"";position:absolute;z-index:-1;width:260px;height:260px;border:1px solid #ffffff26;border-radius:50%;left:-65px;top:-125px;box-shadow:0 0 0 30px #ffffff0a,0 0 0 65px #ffffff08}
.dash-welcome h2{font-size:clamp(23px,3vw,32px);line-height:1.55}
.dash-welcome p{max-width:760px;font-size:14px}
.dash-grid{gap:18px;margin-top:24px}
.dash-tile{position:relative;overflow:hidden;min-height:178px;padding:23px;background:rgba(255,255,255,.94);border:1px solid #e4e8f2;border-radius:22px;box-shadow:var(--shadow-soft);transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease}
.dash-tile:before{content:"";position:absolute;inset:0 0 auto;height:4px;background:linear-gradient(90deg,#4f46e5,#14b8a6);opacity:.0;transition:opacity .2s ease}
.dash-tile:hover{transform:translateY(-5px);box-shadow:var(--shadow-hover);border-color:#c7d2fe}
.dash-tile:hover:before{opacity:1}
.tile-icon{display:grid;place-items:center;width:58px;height:58px;margin:0 0 15px;border-radius:18px;background:linear-gradient(135deg,#eef2ff,#dff7f0);font-size:31px;box-shadow:inset 0 0 0 1px #ffffff}
.dash-tile strong{font-size:17px;line-height:1.7}
.dash-tile span:last-child{font-size:13px;line-height:2}
.card,.game-card,.poster-card{border-radius:22px;border-color:#e4e8f2;box-shadow:var(--shadow-soft)}
.card,.game-card{padding:clamp(16px,2.5vw,24px)}
.game-wrap{max-width:960px;margin-top:24px}
.game-title,.section-title{letter-spacing:-.15px}
.game-score{background:linear-gradient(135deg,#eef2ff,#e0f2fe);border:1px solid #dbeafe;color:#3730a3;border-radius:12px}
button{transition:transform .16s ease,box-shadow .16s ease,filter .16s ease}
button:hover:not(:disabled){filter:brightness(1.015)}
button:active:not(:disabled){transform:translateY(1px)}
.game-btn{background:linear-gradient(110deg,#4f46e5,#4338ca);box-shadow:0 6px 15px #4f46e526}
.back-btn{border:1px solid #d8deeb;background:#fff;box-shadow:0 4px 12px #0f172a08}
.copy-btn,.copy-all{border-radius:12px}
.reset{background:linear-gradient(110deg,#475569,#1e293b)}
input{background:#fbfcff;border-color:#dfe5f0;transition:border-color .16s ease,box-shadow .16s ease}
input:focus{border-color:#818cf8;box-shadow:0 0 0 4px #6366f11a}
.help{border-radius:14px;background:linear-gradient(110deg,#eff8ff,#f0fdfa);border-color:#cce8f8;border-right-color:#38bdf8}
.info{border-radius:16px}
.map-card{border-radius:22px}
#map{border-radius:16px}
.result{border-radius:18px}
.stat{border-radius:14px;padding:15px}
.pasoor-area{border-radius:18px}
.hokm-table{border-radius:22px}
#leaderboard-content table{width:100%;border-collapse:separate;border-spacing:0;overflow:hidden;border:1px solid var(--border);border-radius:14px;background:#fff}
#leaderboard-content th{background:#eef2ff;color:#3730a3;font-weight:900}
#leaderboard-content td,#leaderboard-content th{padding:12px 10px!important;text-align:right;white-space:nowrap}
#leaderboard-content tr:hover td{background:#f8faff}
.top-actions{margin-top:18px}
:focus-visible{outline:3px solid #818cf8;outline-offset:3px}
@media(max-width:991px){.dash-wrap{margin-top:20px}.map-card{height:58vh;border-radius:20px}}
@media(max-width:600px){
 header{padding:16px 12px}.live{margin-bottom:8px}
 .dash-wrap{margin:18px auto;padding-left:12px;padding-right:12px}
 .dash-welcome{border-radius:20px;padding:22px}
 .dash-grid{grid-template-columns:1fr;gap:12px;margin-top:16px}
 .dash-tile{min-height:0;padding:18px;border-radius:18px;display:grid;grid-template-columns:54px minmax(0,1fr);column-gap:14px;align-items:center}
 .tile-icon{grid-row:1 / span 2;width:52px;height:52px;margin:0;font-size:28px;border-radius:15px}
 .dash-tile strong{margin:0;font-size:16px}
 .dash-tile span:last-child{font-size:12px;line-height:1.8}
 .game-wrap{padding-left:12px;padding-right:12px;margin-top:14px}
 .game-card{padding:15px;border-radius:18px}
 .game-head{align-items:flex-start}
 .game-title{font-size:16px}
 .game-tools{gap:7px}
 .game-btn{padding:10px 12px;font-size:12px}
 .map-card{padding:8px;min-height:360px;height:52vh}
 #map{min-height:340px}
 #leaderboard-content{max-width:100%;overflow-x:auto}
 #leaderboard-content td,#leaderboard-content th{padding:9px 8px!important;font-size:12px}
}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important;animation:none!important}}

</style>
</head>
<body>
<header><span class="live">● دالاهو</span><h1>دالاهو</h1><p class="subtitle" id="site-subtitle">داشبورد ابزارها و سرگرمی‌های دالاهو</p></header>
<section id="dashboard" class="dash-wrap">
 <div class="dash-welcome"><h2>به دالاهو خوش آمدید 👋</h2><p>از این داشبورد ابزار موردنظرتان را انتخاب کنید. نقشه و بازی‌ها هرکدام در صفحه جداگانه باز می‌شوند.</p></div>
 <div class="dash-grid">
  <button class="dash-tile" type="button" data-open="route-page"><span class="tile-icon">🗺️</span><strong>نقشه مسیر ایران</strong><span>انتخاب مبدأ و مقصد، محاسبه مسیر و کپی مختصات</span></button>
  <button class="dash-tile" type="button" data-open="games-page"><span class="tile-icon">🎮</span><strong>بخش بازی‌ها</strong><span>ورود به بازی مار و پاسور</span></button>
  <button class="dash-tile" type="button" data-open="fuel-page"><span class="tile-icon">⛽</span><strong>استعلام سوخت</strong><span>ورود به بخش استعلام سوخت؛ امکانات این قسمت بعداً تکمیل می‌شود.</span></button>
  <button class="dash-tile" type="button" data-open="leaderboard-page"><span class="tile-icon">🏆</span><strong>برترین‌های دالاهو</strong><span>رتبه‌بندی کاربران بر اساس مجموع امتیاز همیشگی دو بازی مار و حکم</span></button>
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
<div id="fuel-page" class="page hidden">
 <section class="game-wrap"><div class="game-card">
  <div class="game-head"><h2 class="game-title">⛽ استعلام سهمیه سوخت UTCMS</h2></div>
  <p class="game-help">اطلاعات این فرم فقط برای همین استعلام استفاده می‌شود. برای دریافت کپچا روی دکمه بزنید و کد تصویر رسمی را دستی وارد کنید.</p>
  <form id="fuel-form" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-top:16px">
   <label>شماره ملی / شناسه ملی<input id="fuel-national" required autocomplete="off" maxlength="12" placeholder="شماره ملی یا شناسه ملی" style="margin-top:7px"></label>
   <label>سال<input id="fuel-year" required value="۱۴۰۵" style="margin-top:7px"></label>
   <label>ماه<select id="fuel-month" required style="width:100%;padding:13px;margin-top:7px;border:2px solid var(--border);border-radius:12px"><option value="">انتخاب ماه</option><option>فروردین</option><option>اردیبهشت</option><option>خرداد</option><option>تیر</option><option>مرداد</option><option>شهریور</option><option>مهر</option><option>آبان</option><option>آذر</option><option>دی</option><option>بهمن</option><option>اسفند</option></select></label>
   <label>نوع سهمیه<select id="fuel-type" style="width:100%;padding:13px;margin-top:7px;border:2px solid var(--border);border-radius:12px"><option>پایه</option><option>عملکردی</option></select></label>
   <label>نوع پلاک<select id="fuel-plate-type" style="width:100%;padding:13px;margin-top:7px;border:2px solid var(--border);border-radius:12px"><option>پلاک ملی</option><option>منطقه آزاد</option></select></label>
   <div style="grid-column:1/-1;min-width:0">
    <label for="fuel-plate-left" style="display:block;margin-bottom:8px">شماره پلاک — مطابق چیدمان پلاک ملی UTCMS</label>
    <div dir="ltr" style="display:flex;align-items:stretch;justify-content:center;max-width:460px;margin:0 auto;border:2px solid #202b35;border-radius:10px;overflow:hidden;background:#fff;min-height:62px">
     <div aria-hidden="true" style="width:28px;flex:0 0 28px;background:linear-gradient(to bottom,#159447 0 33%,#fff 33% 66%,#d92535 66%);border-right:1px solid #202b35;display:flex;align-items:center;justify-content:center;color:#123;font-size:8px;writing-mode:vertical-rl">IR.IRAN</div>
     <input id="fuel-plate-left" class="plate-part" required inputmode="numeric" autocomplete="off" maxlength="2" pattern="[0-9۰-۹]{2}" aria-label="دو رقم سمت چپ پلاک" placeholder="۶۳" style="width:20%;min-width:0;border:0;border-radius:0;text-align:center;font-size:20px;font-weight:800;padding:8px 2px;color:#111;background:#fff">
     <select id="fuel-plate-letter" class="plate-part" required aria-label="حرف پلاک" style="width:23%;min-width:0;border:0;border-left:1px solid #202b35;border-right:1px solid #202b35;border-radius:0;text-align:center;font-size:18px;padding:4px 0;color:#111;background:#fff"><option value="">حرف</option><option>الف</option><option>ب</option><option>پ</option><option>ت</option><option>ث</option><option>ج</option><option>چ</option><option>ح</option><option>خ</option><option>د</option><option>ذ</option><option>ر</option><option>ز</option><option>ژ</option><option>س</option><option>ش</option><option>ص</option><option>ض</option><option>ط</option><option>ظ</option><option>ع</option><option>غ</option><option>ف</option><option>ق</option><option>ک</option><option>گ</option><option>ل</option><option>م</option><option>ن</option><option>و</option><option>ه</option><option>ی</option><option>معلولین</option><option>تشریفات</option></select>
     <input id="fuel-plate-middle" class="plate-part" required inputmode="numeric" autocomplete="off" maxlength="3" pattern="[0-9۰-۹]{3}" aria-label="سه رقم وسط پلاک" placeholder="۴۳۶" style="width:29%;min-width:0;border:0;border-radius:0;text-align:center;font-size:20px;font-weight:800;padding:8px 2px;color:#111;background:#fff">
     <div style="width:24%;min-width:68px;border-left:2px solid #202b35;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#111;background:#fff"><span style="font-size:10px;font-weight:800">ایران</span><input id="fuel-plate-code" class="plate-part" required inputmode="numeric" autocomplete="off" maxlength="2" pattern="[0-9۰-۹]{2}" aria-label="کد دو رقمی ایران" placeholder="۷۲" style="width:100%;min-width:0;border:0;border-radius:0;text-align:center;font-size:18px;font-weight:800;padding:2px;color:#111;background:#fff"></div>
    </div>
    <p style="margin:7px 0 0;font-size:12px;color:var(--muted);text-align:center">از چپ به راست: دو رقم، حرف، سه رقم و کد دو رقمی ایران</p>
   </div>
   <label style="grid-column:1/-1">کد امنیتی تصویر<input id="fuel-captcha" required autocomplete="off" placeholder="کد داخل تصویر کپچا" style="margin-top:7px"></label>
   <div style="grid-column:1/-1;display:flex;gap:10px;flex-wrap:wrap"><button class="game-btn" type="button" id="fuel-get-captcha">دریافت / تازه‌سازی کپچا</button><button class="game-btn" type="submit">استعلام سهمیه</button></div>
  </form>
  <div id="fuel-captcha-box" class="hidden" style="margin-top:14px;padding:10px;border:1px solid var(--border);border-radius:12px;text-align:center"><img id="fuel-captcha-image" alt="تصویر صفحه UTCMS شامل کپچا" style="max-width:100%;border:1px solid var(--border);border-radius:8px"></div>
  <div id="fuel-status" role="status" style="margin-top:14px;padding:12px;border-radius:10px;background:#eff6ff;color:#1d4ed8;line-height:1.9">برای شروع، تصویر کپچا را دریافت کنید.</div><div id="fuel-result" style="margin-top:14px;overflow:auto"></div>
 </div></section>
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
  <div class="game-pad" aria-label="کنترل لمسی بازی"><button type="button" data-dir="up" aria-label="حرکت به بالا">▲<small>بالا</small></button><button type="button" data-dir="right" aria-label="حرکت به راست">◀<small>چپ</small></button><button type="button" data-dir="down" aria-label="حرکت به پایین">▼<small>پایین</small></button><button type="button" data-dir="left" aria-label="حرکت به چپ">▶<small>راست</small></button></div>
 </div>
</section>
</div>
<div id="leaderboard-page" class="page hidden"><section class="game-wrap"><div class="game-card"><div class="game-head"><h2 class="game-title">🏆 برترین‌های دالاهو</h2><button class="game-btn" id="leaderboard-refresh" type="button">به‌روزرسانی</button></div><p class="game-help">رتبه‌بندی بر اساس مجموع امتیاز ثبت‌شده در بازی مار و حکم است. این جدول برای همه بازدیدکنندگان قابل مشاهده است.</p><div id="leaderboard-content" style="overflow:auto;margin-top:16px">در حال دریافت رتبه‌بندی…</div></div></section></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const $=id=>document.getElementById(id);
// ورود بدون ثبت‌نام؛ برای امتیازدهی یک شناسه ناشناس خودکار ساخته می‌شود.
const dashboard=$('dashboard'), routePage=$('route-page'), gamePage=$('game-page'), gamesPage=$('games-page'), pasoorPage=$('pasoor-page'), fuelPage=$('fuel-page'), pageActions=$('page-actions');
const leaderboardPage=$('leaderboard-page');const appPages=[routePage,gamePage,gamesPage,pasoorPage,fuelPage,leaderboardPage];
function openPage(id){dashboard.classList.add('hidden');appPages.forEach(p=>p.classList.toggle('hidden',p.id!==id));pageActions.classList.remove('hidden');const labels={'route-page':'نقشه مسیر ایران','games-page':'انتخاب بازی','game-page':'بازی مار کلاسیک','pasoor-page':'پاسور دالاهو','fuel-page':'استعلام سوخت','leaderboard-page':'برترین‌های دالاهو'};$('site-subtitle').textContent=labels[id]||'دالاهو';if(id==='route-page'){setTimeout(()=>map.invalidateSize(),80)}if(id==='game-page'){snakeDraw()}if(id==='pasoor-page'&&!pasoorStarted){pasoorNewGame()}if(id==='leaderboard-page'){loadLeaderboard()}}
document.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',()=>openPage(b.dataset.open)));

const fuelStatus=$('fuel-status');function fuelMsg(t,ok=false){fuelStatus.textContent=t;fuelStatus.style.background=ok?'#f0fdf4':'#eff6ff';fuelStatus.style.color=ok?'#166534':'#1d4ed8'}
$('fuel-get-captcha').addEventListener('click',async()=>{fuelMsg('در حال اتصال به UTCMS…');try{const r=await fetch('/fuel/captcha',{method:'POST'});if(!r.ok){let d={};try{d=await r.json()}catch{}throw Error(d.error||'گرفتن کپچا ناموفق بود')}const blob=await r.blob();$('fuel-captcha-image').src=URL.createObjectURL(blob);$('fuel-captcha-box').classList.remove('hidden');fuelMsg('تصویر صفحه UTCMS نمایش داده شد؛ کد امنیتی را از روی تصویر وارد کنید.',true)}catch(e){fuelMsg(e.message)}});
$('fuel-form').addEventListener('submit',async e=>{e.preventDefault();fuelMsg('در حال ارسال استعلام…');$('fuel-result').innerHTML='';const data={national_id:$('fuel-national').value.trim(),year:$('fuel-year').value.trim(),month:$('fuel-month').value,quota_type:$('fuel-type').value,plate_type:$('fuel-plate-type').value,plate_parts:{left:$('fuel-plate-left').value.trim(),letter:$('fuel-plate-letter').value,middle:$('fuel-plate-middle').value.trim(),code:$('fuel-plate-code').value.trim()},captcha:$('fuel-captcha').value.trim()};try{const r=await fetch('/fuel/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const d=await r.json();if(!r.ok)throw Error(d.error||'استعلام انجام نشد');if(!d.rows?.length){fuelMsg(d.message||'جدول نتیجه شناسایی نشد.');return}let h='<table style="width:100%;border-collapse:collapse;text-align:center"><thead><tr style="background:#075e59;color:white"><th style="padding:10px">ردیف</th><th style="padding:10px">دوره</th><th style="padding:10px">سهمیه (لیتر)</th></tr></thead><tbody>';for(const x of d.rows)h+='<tr>'+[x.row,x.period,x.quota].map(v=>'<td style="padding:10px;border:1px solid var(--border)">'+String(v??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))+'</td>').join('')+'</tr>'; $('fuel-result').innerHTML=h+'</tbody></table>';fuelMsg('نتیجه استعلام دریافت شد.',true)}catch(e){fuelMsg(e.message)}});

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

// امتیازهای بازی از سرور ثبت می‌شوند؛ هر نوبت بازی فقط یک بار قابل ثبت است.
let snakeRunId=null, hokmRunId=null;
async function startScoredGame(game){
 try{const r=await fetch('/game_start',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({game})});const d=await r.json();if(!r.ok)throw new Error(d.error||'ثبت شروع بازی ناموفق بود');return d.run_id;}
 catch(e){alert(e.message||'برای ثبت امتیاز ارتباط با سرور برقرار نشد.');return null;}
}
async function submitGameResult(runId,game,score,result){
 if(!runId)return;try{const r=await fetch('/game_finish',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({run_id:runId,game,score,result})});const d=await r.json();if(!r.ok)throw new Error(d.error||'ثبت امتیاز ناموفق بود');if(d.ok){if(game==='snake')$('snake-message').textContent+=' امتیاز ثبت‌شده در دالاهو: '+d.points.toLocaleString('fa-IR')+'؛ مجموع امتیاز شما: '+d.total_points.toLocaleString('fa-IR')+'.';else $('pasoor-message').textContent+=' امتیاز این دست: '+d.points.toLocaleString('fa-IR')+'؛ مجموع امتیاز شما: '+d.total_points.toLocaleString('fa-IR')+'.';}}
 catch(e){alert(e.message||'امتیاز ثبت نشد؛ اتصال اینترنت را بررسی کنید.');}
}
async function loadLeaderboard(){const box=$('leaderboard-content');box.textContent='در حال دریافت رتبه‌بندی…';try{const r=await fetch('/leaderboard',{credentials:'same-origin',cache:'no-store'});const d=await r.json();if(!r.ok)throw new Error(d.error||'خطا در دریافت رتبه‌بندی');if(!d.rows.length){box.innerHTML='<p>هنوز امتیازی ثبت نشده است. اولین نفر باشید!</p>';return}box.innerHTML='<table style="width:100%;border-collapse:collapse;text-align:right"><thead><tr><th style="padding:10px;border-bottom:1px solid var(--border)">رتبه</th><th style="padding:10px;border-bottom:1px solid var(--border)">نام کاربر</th><th style="padding:10px;border-bottom:1px solid var(--border)">مجموع امتیاز</th><th style="padding:10px;border-bottom:1px solid var(--border)">بازی مار</th><th style="padding:10px;border-bottom:1px solid var(--border)">بازی حکم</th></tr></thead><tbody>'+d.rows.map(x=>'<tr><td style="padding:10px;border-bottom:1px solid var(--border)">'+x.rank.toLocaleString('fa-IR')+'</td><td style="padding:10px;border-bottom:1px solid var(--border)">'+escapeText(x.name)+'</td><td style="padding:10px;border-bottom:1px solid var(--border);font-weight:900">'+x.total.toLocaleString('fa-IR')+'</td><td style="padding:10px;border-bottom:1px solid var(--border)">'+x.snake.toLocaleString('fa-IR')+'</td><td style="padding:10px;border-bottom:1px solid var(--border)">'+x.hokm.toLocaleString('fa-IR')+'</td></tr>').join('')+'</tbody></table>';}catch(e){box.textContent='دریافت رتبه‌بندی ناموفق بود: '+e.message}}
function escapeText(v){const el=document.createElement('span');el.textContent=String(v??'');return el.innerHTML}
$('leaderboard-refresh').addEventListener('click',loadLeaderboard);

// حکم چهار نفره: شما و بازیکن روبه‌رو در یک تیم هستید
let pasoorStarted=false, hDeck=[], hHands=[[],[],[],[]], hTrick=[], hTrump=null, hLeader=0, hTurn=0, hTeamTricks=[0,0], hPhase='trump', hGameOver=false;
const hSuits=['♠','♥','♦','♣'], hRanks=[{v:2,t:'۲'},{v:3,t:'۳'},{v:4,t:'۴'},{v:5,t:'۵'},{v:6,t:'۶'},{v:7,t:'۷'},{v:8,t:'۸'},{v:9,t:'۹'},{v:10,t:'۱۰'},{v:11,t:'سرباز'},{v:12,t:'بی‌بی'},{v:13,t:'شاه'},{v:14,t:'آس'}];
function hShuffle(){hDeck=[];for(const su of hSuits)for(const r of hRanks)hDeck.push({s:su,v:r.v,t:r.t,id:su+r.v});for(let i=hDeck.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[hDeck[i],hDeck[j]]=[hDeck[j],hDeck[i]]}}
function hFacePortrait(kind, red){
 const ink=red?'#9f1239':'#172554';
 const robe=kind==='Q'?'#7c3aed':kind==='K'?'#b45309':'#0f766e';
 const crown=kind==='Q'
  ? `<path d="M24 24 L17 7 L29 17 L40 3 L51 17 L63 7 L56 25 Z" fill="#facc15" stroke="#92400e" stroke-width="2"/><circle cx="17" cy="7" r="3" fill="#ef4444"/><circle cx="40" cy="3" r="3" fill="#3b82f6"/><circle cx="63" cy="7" r="3" fill="#ef4444"/>`
  : kind==='K'
  ? `<path d="M22 23 L18 6 L33 16 L42 2 L51 16 L66 6 L61 24 Z" fill="#facc15" stroke="#92400e" stroke-width="2"/><path d="M37 3 L47 11 L42 18 L34 11 Z" fill="#dc2626"/>`
  : `<path d="M25 23 L20 7 L35 16 L43 4 L51 16 L65 7 L60 24 Z" fill="#facc15" stroke="#92400e" stroke-width="2"/><circle cx="43" cy="10" r="4" fill="#2563eb"/>`;
 const hair=kind==='Q'?'#3f2a1d':'#38251b';
 const face=`<ellipse cx="43" cy="42" rx="17" ry="20" fill="#f5c9a5" stroke="#7c4a2d" stroke-width="1.4"/><path d="M26 40 Q20 19 43 19 Q66 19 60 41 L56 31 Q43 24 30 32 Z" fill="${hair}"/><circle cx="36" cy="42" r="1.8" fill="#1f2937"/><circle cx="50" cy="42" r="1.8" fill="#1f2937"/><path d="M38 51 Q43 55 49 50" fill="none" stroke="#9a3412" stroke-width="1.5" stroke-linecap="round"/>`;
 const outfit=kind==='Q'
  ? `<path d="M24 84 Q24 61 34 59 L43 65 L52 59 Q64 62 64 84 Z" fill="${robe}" stroke="#312e81" stroke-width="1.5"/><path d="M34 61 L43 74 L52 61" fill="#fef3c7" stroke="#d4a72c" stroke-width="2"/><circle cx="43" cy="77" r="3" fill="#facc15"/>`
  : kind==='K'
  ? `<path d="M22 84 Q23 61 34 59 L43 66 L52 59 Q63 62 65 84 Z" fill="${robe}" stroke="#78350f" stroke-width="1.5"/><path d="M34 60 L43 73 L52 60" fill="#fef3c7" stroke="#d4a72c" stroke-width="2"/><path d="M43 69 L47 78 L43 82 L39 78 Z" fill="#dc2626"/>`
  : `<path d="M23 84 Q24 61 34 59 L43 65 L52 59 Q63 62 64 84 Z" fill="${robe}" stroke="#134e4a" stroke-width="1.5"/><path d="M34 61 L43 74 L52 61" fill="#fef3c7" stroke="#d4a72c" stroke-width="2"/><path d="M38 76 L43 71 L48 76 L43 81 Z" fill="#facc15"/>`;
 return `<svg class="face-portrait" viewBox="0 0 86 92" role="img" aria-label="${kind==='Q'?'بی‌بی':kind==='K'?'شاه':'سرباز'}"><rect x="2" y="2" width="82" height="88" rx="7" fill="#fff7e6" stroke="#d6b46a" stroke-width="2"/><rect x="6" y="6" width="74" height="80" rx="5" fill="none" stroke="${ink}" stroke-width="1" opacity=".45"/>${outfit}${face}${crown}<path d="M12 76 Q18 69 23 76 M63 76 Q68 69 74 76" fill="none" stroke="#d6b46a" stroke-width="1.5"/></svg>`;
}
function hCard(c,disabled=false){
 const red=c.s==='♥'||c.s==='♦';
 const label=({11:'J',12:'Q',13:'K',14:'A'})[c.v]||String(c.v);
 const face=c.v>=11&&c.v<=13;
 const pipCount=Math.min(c.v,10);
 const pips=face?`<span class="face-art">${hFacePortrait(label,red)}</span>`:
   c.v===14?`<span class="ace-art">${c.s}</span>`:
   `<span class="pip-grid pip-n${pipCount}">${Array.from({length:pipCount},()=>`<i class="pip">${c.s}</i>`).join('')}</span>`;
 return `<button type="button" class="playing-card ${red?'red-card':'black-card'} ${face?'face-card':''} ${c.v===14?'ace-card':''}" data-card="${c.id}" aria-label="${label} ${c.s}" ${disabled?'disabled':''}>
 <span class="card-corner top-corner"><strong>${label}</strong><b>${c.s}</b></span>${pips}<span class="card-corner bottom-corner"><strong>${label}</strong><b>${c.s}</b></span></button>`
}
function hRender(){
 $('pasoor-table').innerHTML=hTrick.length?hTrick.map(x=>`<div class="hokm-play"><small>${['شما','حریف چپ','هم‌تیمی','حریف راست'][x.p]}</small>${hCard(x.c,true)}</div>`).join(''):'<span class="game-help" style="color:#d1fae5">کارت‌های دور بعدی اینجا قرار می‌گیرند</span>';
 $('pasoor-hand').innerHTML=hHands[0].slice().sort((a,b)=>hSuits.indexOf(a.s)-hSuits.indexOf(b.s)||b.v-a.v).map(c=>hCard(c,hPhase!=='play'||hTurn!==0||hGameOver)).join('');
 document.querySelectorAll('#pasoor-hand [data-card]').forEach(b=>b.addEventListener('click',()=>hUserPlay(b.dataset.card)));
 $('pasoor-player-score').textContent=hTeamTricks[0].toLocaleString('fa-IR');$('pasoor-ai-score').textContent=hTeamTricks[1].toLocaleString('fa-IR');
 ['hokm-user-count','hokm-left-count','hokm-top-count','hokm-right-count'].forEach((id,i)=>$(id).textContent=hHands[[0,1,2,3][i]].length+' کارت');
 $('hokm-select').classList.toggle('hidden',hPhase!=='trump');
}
async function pasoorNewGame(){
 pasoorStarted=true;hokmRunId=null;hokmRunId=await startScoredGame('hokm');hShuffle();hHands=[[],[],[],[]];for(let round=0;round<5;round++)for(let p=0;p<4;p++)hHands[p].push(hDeck.shift());
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
function hResolveTrick(){if(hTrick.length!==4)return;const lead=hTrick[0].c.s;function power(x){return (x.c.s===hTrump?100:0)+(x.c.s===lead?10:0)+x.c.v}const winner=hTrick.reduce((best,x)=>power(x)>power(best)?x:best).p;const team=winner%2===0?0:1;hTeamTricks[team]++;hLeader=winner;hTurn=winner;hTrick=[];if(hHands.every(hand=>hand.length===0)){hGameOver=true;hPhase='done';const won=hTeamTricks[0]>hTeamTricks[1]?0:1;submitGameResult(hokmRunId,'hokm',hTeamTricks[0],won===0?'win':'loss');hokmRunId=null;$('pasoor-message').textContent=`دست تمام شد؛ تیم ${won===0?'شما':'حریف'} برنده شد (${hTeamTricks[0]} به ${hTeamTricks[1]} دور). برای بازی دوباره «بازی جدید» را بزن.`;hRender();return}$('pasoor-message').textContent=`این دور را ${['شما','حریف چپ','هم‌تیمی','حریف راست'][winner]} برد. ${winner===0?'نوبت شماست.': 'حریف شروع می‌کند.'}`;hRender();if(hTurn!==0)hAiSequence()}
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
async function snakeStart(){clearInterval(snakeTimer);snakeRunning=false;snakeRunId=null;snakeRunId=await startScoredGame('snake');if(!snakeRunId)return;snake=[{x:Math.floor(COLS/2),y:Math.floor(ROWS/2)},{x:Math.floor(COLS/2)-1,y:Math.floor(ROWS/2)},{x:Math.floor(COLS/2)-2,y:Math.floor(ROWS/2)}];snakeDir={x:1,y:0};snakeNext={x:1,y:0};snakeScore=0;snakeRunning=true;$('snake-score').textContent='۰';$('snake-message').textContent='عالیه! خوراکی‌ها را بخور و به دیوار یا بدن خودت برخورد نکن.';snakeFoodNew();snakeDraw();snakeTimer=setInterval(snakeStep,115)}
function snakeStep(){if(!snakeRunning)return;snakeDir=snakeNext;const head={x:snake[0].x+snakeDir.x,y:snake[0].y+snakeDir.y};if(head.x<0||head.x>=COLS||head.y<0||head.y>=ROWS||snake.some((p,i)=>i<snake.length-1&&p.x===head.x&&p.y===head.y)){snakeRunning=false;clearInterval(snakeTimer);$('snake-message').textContent='بازی تمام شد! امتیاز شما: '+snakeScore+' — برای شروع دوباره دکمه را بزن.';const finishedRun=snakeRunId;snakeRunId=null;submitGameResult(finishedRun,'snake',snakeScore,'finished');snakeDraw();return}snake.unshift(head);if(head.x===snakeFood.x&&head.y===snakeFood.y){snakeScore++;$('snake-score').textContent=snakeScore.toLocaleString('fa-IR');snakeFoodNew()}else snake.pop();snakeDraw()}
function snakeTurn(d){
 if(!snakeRunning)return;
 const dirs={up:{x:0,y:-1},down:{x:0,y:1},left:{x:-1,y:0},right:{x:1,y:0}};
 const n=dirs[d]; if(!n)return;
 // Direction changes are relative to the current committed direction, preventing accidental 180-degree turns.
 if(n.x===-snakeDir.x&&n.y===-snakeDir.y)return;
 snakeNext={x:n.x,y:n.y};
}
$('snake-start').addEventListener('click',snakeStart);document.querySelectorAll('.game-pad button').forEach(b=>b.addEventListener('click',()=>snakeTurn(b.dataset.dir)));
document.addEventListener('keydown',e=>{
 if(gamePage.classList.contains('hidden'))return;
 if(e.key==='Enter'&&!snakeRunning){e.preventDefault();snakeStart();return}
 const k=e.key.toLowerCase();
 const mapKeys={'arrowup':'up','w':'up','arrowdown':'down','s':'down','arrowleft':'left','a':'left','arrowright':'right','d':'right'};
 if(mapKeys[k]&&!['INPUT','TEXTAREA'].includes(document.activeElement?.tagName)){e.preventDefault();snakeTurn(mapKeys[k])}
});
document.querySelectorAll('.game-pad button[data-dir]').forEach(b=>{
 b.addEventListener('pointerdown',e=>{e.preventDefault();snakeTurn(b.dataset.dir)});
});
snakeDraw();

</script>
</body></html>
"""
@app.get("/")
def index():
    return render_template_string(HTML)

@app.post("/game_start")
def game_start():
    data=request.get_json(silent=True) or {}; game=str(data.get("game", ""))
    if game not in ("snake", "hokm"): return jsonify(error="نوع بازی معتبر نیست."),400
    uid,new_uid=ensure_anonymous_user()
    run_id=secrets.token_hex(16); now=datetime.now(timezone.utc).isoformat(timespec="seconds")
    with db_connect() as c:
        c.execute("INSERT INTO game_runs(run_id,user_id,game,started_at) VALUES(?,?,?,?)",(run_id,uid,game,now))
    response=jsonify(ok=True,run_id=run_id)
    if new_uid:
        response.set_cookie(USER_COOKIE,new_uid,max_age=60*60*24*365*5,httponly=True,samesite="Lax",secure=request.is_secure)
    return response

@app.post("/game_finish")
def game_finish():
    uid=user_id_from_cookie()
    if not uid: return jsonify(error="شناسه بازی پیدا نشد؛ بازی را یک بار دیگر شروع کنید."),401
    data=request.get_json(silent=True) or {}; run_id=str(data.get("run_id", "")); game=str(data.get("game", "")); result=str(data.get("result", ""))
    try: score=int(data.get("score", 0))
    except (TypeError,ValueError): return jsonify(error="امتیاز معتبر نیست."),400
    if not run_id or game not in ("snake", "hokm"): return jsonify(error="اطلاعات بازی کامل نیست."),400
    # قوانین امتیاز: مار به ازای هر خوراکی یک امتیاز تا سقف ۵۰؛ حکم برد ۱۰ و باخت ۲ امتیاز.
    if game=="snake":
        if result!="finished" or score<1: return jsonify(error="برای امتیاز گرفتن باید حداقل یک خوراکی بخورید و بازی تمام شود."),400
        points=min(score,50)
    else:
        if result not in ("win","loss"): return jsonify(error="نتیجه بازی حکم معتبر نیست."),400
        points=10 if result=="win" else 2
    now=datetime.now(timezone.utc).isoformat(timespec="seconds")
    with db_connect() as c:
        row=c.execute("SELECT user_id,game,finished_at FROM game_runs WHERE run_id=?",(run_id,)).fetchone()
        if not row or row["user_id"]!=uid or row["game"]!=game: return jsonify(error="بازی معتبر پیدا نشد."),400
        if row["finished_at"]: return jsonify(error="امتیاز این بازی قبلاً ثبت شده است."),409
        c.execute("UPDATE game_runs SET finished_at=?,points=?,result=? WHERE run_id=? AND finished_at IS NULL",(now,points,result,run_id))
        total=c.execute("SELECT COALESCE(SUM(points),0) FROM game_runs WHERE user_id=?",(uid,)).fetchone()[0]
    return jsonify(ok=True,points=points,total_points=total)

@app.get("/leaderboard")
def leaderboard():
    with db_connect() as c:
        rows=c.execute("""SELECT u.user_id,
          COALESCE(SUM(g.points),0) AS total,
          COALESCE(SUM(CASE WHEN g.game='snake' THEN g.points ELSE 0 END),0) AS snake,
          COALESCE(SUM(CASE WHEN g.game='hokm' THEN g.points ELSE 0 END),0) AS hokm
          FROM registered_users u LEFT JOIN game_runs g ON g.user_id=u.user_id
          GROUP BY u.user_id
          HAVING COALESCE(SUM(g.points),0)>0
          ORDER BY total DESC,u.user_id ASC LIMIT 100""").fetchall()
    return jsonify(rows=[{"rank":i,"name":"بازیکن ناشناس #"+r["user_id"][-4:].upper(),"total":r["total"],"snake":r["snake"],"hokm":r["hokm"]} for i,r in enumerate(rows,1)])

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


# UTCMS Playwright bridge; transient sessions only, no identity data stored in SQLite.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
import threading
_FUEL_SESSIONS = {}
_FUEL_LOCK = threading.RLock()
_FUEL_URL = "https://utcms.ir/ShowFuelQuota.aspx"

# Run all synchronous Playwright operations on one dedicated thread.
# This avoids inheriting an asyncio event loop from the hosting/request thread
# and keeps each browser/page session on the same thread.
_FUEL_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dalahoo-playwright")
def _fuel_thread(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        task = copy_current_request_context(fn)
        return _FUEL_EXECUTOR.submit(task, *args, **kwargs).result()
    return wrapper

def _fuel_sid():
    sid=request.cookies.get("dalahoo_fuel_sid","")
    return sid if len(sid)==32 and all(c in "0123456789abcdef" for c in sid) else secrets.token_hex(16)

@app.post("/fuel/captcha")
@_fuel_thread
def fuel_captcha():
    if sync_playwright is None:
        return jsonify(error="Playwright نصب نیست؛ requirements و نصب Chromium را در Render بررسی کنید."),503
    sid=_fuel_sid()
    with _FUEL_LOCK:
        old=_FUEL_SESSIONS.pop(sid,None)
        if old:
            try: old["context"].close(); old["browser"].close(); old["pw"].stop()
            except Exception: pass
        try:
            pw=sync_playwright().start(); browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
            context=browser.new_context(viewport={"width":1280,"height":1000},locale="fa-IR"); page=context.new_page()
            page.goto(_FUEL_URL,wait_until="domcontentloaded",timeout=45000); page.wait_for_timeout(1500)
            _FUEL_SESSIONS[sid]={"pw":pw,"browser":browser,"context":context,"page":page}
            from flask import Response
            response=Response(page.screenshot(full_page=True,type="png"),mimetype="image/png")
            response.headers["Cache-Control"]="no-store"
            response.set_cookie("dalahoo_fuel_sid",sid,httponly=True,samesite="Lax",secure=request.is_secure,max_age=1800)
            return response
        except Exception as e:
            return jsonify(error="اتصال به UTCMS ناموفق بود: "+str(e)[:180]),502

@app.post("/fuel/submit")
@_fuel_thread
def fuel_submit():
    if sync_playwright is None: return jsonify(error="Playwright در محیط اجرا نصب نیست."),503
    sid=request.cookies.get("dalahoo_fuel_sid",""); d=request.get_json(silent=True) or {}
    plate_parts=d.get("plate_parts") or {}
    if any(not str(d.get(k,"")).strip() for k in ("national_id","year","month","quota_type","plate_type","captcha")) or any(not str(plate_parts.get(k,"")).strip() for k in ("left","letter","middle","code")):
        return jsonify(error="همه فیلدها از جمله چهار بخش شماره پلاک را تکمیل کنید."),400
    with _FUEL_LOCK:
        item=_FUEL_SESSIONS.get(sid)
        if not item: return jsonify(error="نشست کپچا منقضی شده؛ دوباره کپچا بگیرید."),409
        page=item["page"]
        try:
            # Match common Persian accessible names first; if UTCMS changes its markup this reports an error instead of guessing silently.
            def fill(patterns,value):
                for pat in patterns:
                    for getter in (page.get_by_label,page.get_by_placeholder):
                        try:
                            loc=getter(re.compile(pat,re.I))
                            if loc.count(): loc.first.fill(str(value)); return True
                        except Exception: pass
                return False
            fill([r"شماره ملی",r"شناسه ملی"],d["national_id"])
            fill([r"کد امنیتی",r"کد.*تصویر",r"عبارت.*تصویر"],d["captcha"])
            # UTCMS plate widget is segmented: left two digits, letter, middle three digits, Iran code.
            parts=plate_parts
            def western_digits(value):
                return str(value).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩","01234567890123456789"))
            # Locate the plate label, then collect the nearby visible text inputs in visual left-to-right order.
            plate_label=page.get_by_text(re.compile(r"شماره پلاک وسیله نقلیه"))
            plate_inputs=[]
            try:
                label_box=plate_label.first.bounding_box() if plate_label.count() else None
                if label_box:
                    for inp in page.locator("input:visible").all():
                        try:
                            box=inp.bounding_box()
                            if box and label_box["y"]-5 <= box["y"] <= label_box["y"]+115 and box["width"]>12 and box["height"]>10:
                                plate_inputs.append((box["x"],inp))
                        except Exception: pass
            except Exception: pass
            plate_inputs=sorted(plate_inputs,key=lambda item:item[0])
            plate_values=[western_digits(parts["left"]),str(parts["letter"]),western_digits(parts["middle"]),western_digits(parts["code"])]
            if len(plate_inputs)>=4:
                for (_,inp),value in zip(plate_inputs[-4:],plate_values):
                    try: inp.fill(value)
                    except Exception: pass
            else:
                # Fallback for a single-field variant of the official form.
                combined=f'{parts["left"]}-{parts["letter"]}-{parts["middle"]}-ایران{parts["code"]}'
                fill([r"شماره پلاک",r"پلاک"],combined)
            # Select options by visible Persian text where available.
            for sel in page.locator("select:visible").all():
                opts=sel.locator("option").all_text_contents()
                if any(d["month"] in x for x in opts):
                    try: sel.select_option(label=d["month"])
                    except Exception: pass
                elif any(d["year"] in x for x in opts):
                    try: sel.select_option(label=d["year"])
                    except Exception: pass
            for value in (d["quota_type"],d["plate_type"]):
                try:
                    loc=page.get_by_label(re.compile(re.escape(value),re.I))
                    if loc.count(): loc.first.check()
                except Exception: pass
            submit=page.get_by_role("button",name=re.compile("مشاهده سهمیه"))
            if not submit.count(): submit=page.locator("input[type=submit],button[type=submit]")
            if not submit.count(): return jsonify(error="دکمه مشاهده سهمیه در صفحه UTCMS پیدا نشد؛ احتمالاً ساختار فرم تغییر کرده است."),502
            submit.first.click(timeout=10000); page.wait_for_timeout(1500)
            rows=[]
            for tr in page.locator("table tr").all():
                cells=[re.sub(r"\s+"," ",c.inner_text().strip()) for c in tr.locator("th,td").all()]
                if len(cells)>=3 and not ("ردیف" in " ".join(cells) and "سهمیه" in " ".join(cells)):
                    rows.append({"row":cells[0],"period":cells[1],"quota":cells[2]})
            if rows: return jsonify(ok=True,rows=rows)
            message=re.sub(r"\s+"," ",page.locator("body").inner_text())[:350]
            return jsonify(ok=True,rows=[],message="جدول نتیجه شناسایی نشد. پیام صفحه UTCMS: "+message)
        except Exception as e:
            return jsonify(error="استعلام خودکار کامل نشد: "+str(e)[:180]+". ممکن است انتخابگرهای فرم UTCMS نیاز به تنظیم داشته باشند."),502


if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000,debug=False)
