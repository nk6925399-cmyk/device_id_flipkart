import http.server
import socketserver
import urllib.parse
import json
import time
import random
import os
import sys
from http.cookies import SimpleCookie

# Ensure UTF-8 output on Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

PORT = int(os.environ.get('PORT', 5000))
DB_FILE = os.path.join(os.path.dirname(__file__), 'devices.json')
ADMIN_PASSWORD = "Guddu@20034"
SESSION_SECRET = "GUDDU_SECURE_SESSION_SECRET_KEY_12345"

# Initialize devices file if not exists
if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Print logs to stdout so we can debug incoming requests
        sys.stdout.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format%args))
        sys.stdout.flush()

    def load_devices(self):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_devices(self, data):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def is_authenticated(self):
        cookie_header = self.headers.get('Cookie', '')
        if not cookie_header:
            return False
        
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        
        if 'session_token' in cookie:
            return cookie['session_token'].value == SESSION_SECRET
        return False

    def serve_login_page(self, error_msg=""):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

        error_box = ""
        if error_msg:
            error_box = f"""
            <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:#EF4444; padding:12px; border-radius:10px; font-size:13px; text-align:center; margin-bottom:20px; font-weight:600;">
                ⚠️ {error_msg}
            </div>
            """

        login_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADMIN LOGIN - Device Auth Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }}
        body {{ background: linear-gradient(135deg, #06070a 0%, #0c0d15 100%); color: #E2E8F0; min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }}
        .login-card {{ background: rgba(22, 22, 34, 0.5); border: 1px solid rgba(255, 255, 255, 0.04); backdrop-filter: blur(12px); border-radius: 24px; padding: 36px 30px; width: 360px; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4); text-align: center; }}
        .lock-icon {{ font-size: 42px; margin-bottom: 16px; display: inline-block; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.08); }} 100% {{ transform: scale(1); }} }}
        h1 {{ font-size: 22px; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 6px; }}
        h1 span {{ color: #6366F1; }}
        p {{ font-size: 12px; color: #9CA3AF; margin-bottom: 28px; }}
        .input-group {{ margin-bottom: 20px; text-align: left; }}
        label {{ font-size: 11px; text-transform: uppercase; color: #9CA3AF; letter-spacing: 0.5px; display: block; margin-bottom: 8px; font-weight: 600; }}
        input {{ width: 100%; background: #07080d; border: 1px solid rgba(255, 255, 255, 0.08); color: white; padding: 14px 16px; border-radius: 12px; font-size: 15px; text-align: center; transition: all 0.2s ease; }}
        input:focus {{ outline: none; border-color: #6366F1; box-shadow: 0 0 12px rgba(99, 102, 241, 0.2); }}
        .login-btn {{ background: #6366F1; color: white; border: none; width: 100%; padding: 14px; border-radius: 12px; font-size: 14px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3); transition: all 0.2s ease; margin-top: 10px; }}
        .login-btn:hover {{ background: #4F46E5; box-shadow: 0 4px 24px rgba(99, 102, 241, 0.45); }}
    </style>
</head>
<body>
    <div class="login-card">
        <span class="lock-icon">🔒</span>
        <h1><span>DEVICE</span> AUTH PANEL</h1>
        <p>ADMINS Device Registration System</p>
        
        {error_box}
        
        <form method="POST" action="/login">
            <div class="input-group">
                <label>Enter Control Password</label>
                <input type="password" name="password" placeholder="••••••••" required autofocus>
            </div>
            <button type="submit" class="login-btn">ACCESS PANEL</button>
        </form>
    </div>
</body>
</html>"""
        self.wfile.write(login_html.encode('utf-8'))

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # 1. API DEVICE VALIDATION ENDPOINT
        if path == '/validate.php' or path == '/validate':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            device_id = query_params.get('device_id', [''])[0].strip()
            if not device_id:
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Device ID is empty'}).encode('utf-8'))
                return

            devices_data = self.load_devices()
            if device_id not in devices_data:
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Your Device Not Register By Admin'}).encode('utf-8'))
                return

            device_info = devices_data[device_id]
            current_time = int(time.time())
            expires_at = device_info.get('expires_at', 0)

            # Check if expired
            if expires_at < current_time:
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Your Device Registration Expired'}).encode('utf-8'))
                return

            time_left = expires_at - current_time
            self.wfile.write(json.dumps({
                'status': 'success',
                'message': 'Device is registered and active.',
                'expires_at': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expires_at)),
                'time_left_seconds': time_left,
                'time_left_mins': round(time_left / 60, 1)
            }).encode('utf-8'))
            return

        # 2. CHECK SECURITY FOR WEB PANEL ACCESS
        if not self.is_authenticated():
            self.serve_login_page()
            return

        # 3. SERVE WEB DASHBOARD
        if path == '/' or path == '/index.html' or path == '/index.php':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()

            devices_data = self.load_devices()
            current_time = int(time.time())

            # Calculate stats
            total_devices = len(devices_data)
            active_devices = 0
            expired_devices = 0

            for d, info in devices_data.items():
                exp = info.get('expires_at', 0)
                if exp > current_time:
                    active_devices += 1
                else:
                    expired_devices += 1

            # Check for messages
            msg = query_params.get('msg', [''])[0]
            success_box = ""
            if msg == 'registered':
                success_box = """
                <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); color:#10B981; padding:12px; border-radius:10px; font-size:13px; text-align:center; margin-bottom:20px; font-weight:600;">
                    ✅ Device registered successfully!
                </div>
                """
            elif msg == 'deleted':
                success_box = """
                <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:#EF4444; padding:12px; border-radius:10px; font-size:13px; text-align:center; margin-bottom:20px; font-weight:600;">
                    🗑️ Device revoked successfully!
                </div>
                """

            # Build device table rows
            table_rows = ""
            if not devices_data:
                table_rows = """
                <div class="no-keys-box">
                    <span>📱</span>
                    <h6>No Devices Registered</h6>
                    <p>Register a Device ID to grant access.</p>
                </div>
                """
            else:
                table_rows += """
                <table>
                    <thead>
                        <tr>
                            <th>Device ID</th>
                            <th>Registered Time</th>
                            <th>Status</th>
                            <th>Time Left</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                # Reverse list to show newest first
                for dev_id in reversed(list(devices_data.keys())):
                    info = devices_data[dev_id]
                    status = 'active'
                    status_badge = 'Active'
                    time_left_str = ''
                    expiry_str = ''

                    exp = info.get('expires_at', 0)
                    created = info.get('created_at', 0)
                    created_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created))
                    expiry_str = 'Expires: ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(exp))
                    
                    if exp > current_time:
                        status = 'active'
                        status_badge = 'Active'
                        diff = exp - current_time
                        if diff < 60:
                            time_left_str = f"{diff} seconds remaining"
                        elif diff < 3600:
                            time_left_str = f"{round(diff / 60)} mins remaining"
                        elif diff < 86400:
                            time_left_str = f"{round(diff / 3600, 1)} hours remaining"
                        else:
                            time_left_str = f"{round(diff / 86400, 1)} days remaining"
                    else:
                        status = 'expired'
                        status_badge = 'Expired'
                        time_left_str = 'Expired'

                    table_rows += f"""
                    <tr>
                        <td class="td-key">{dev_id}</td>
                        <td>{created_str}</td>
                        <td><span class="badge badge-{status}">{status_badge}</span></td>
                        <td>
                            <div class="time-left-container">{time_left_str}</div>
                            <div class="time-left-expiry">{expiry_str}</div>
                        </td>
                        <td>
                            <form method="POST" action="/delete_device" style="display:inline;" onsubmit="return confirm('Are you sure you want to revoke this device?');">
                                <input type="hidden" name="device_id" value="{dev_id}">
                                <button type="submit" class="action-btn">Revoke</button>
                            </form>
                        </td>
                    </tr>
                    """
                table_rows += "</tbody></table>"

            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADMIN PANEL - Device Registration System</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }}
        body {{ background: linear-gradient(135deg, #090A0F 0%, #12131C 100%); color: #E2E8F0; min-height: 100vh; padding: 24px; }}
        header {{ background: rgba(22, 22, 34, 0.6); border: 1px solid rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px); border-radius: 16px; padding: 18px 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); }}
        .header-title-container {{ display: flex; align-items: center; gap: 12px; }}
        .status-dot {{ width: 10px; height: 10px; background: #10B981; border-radius: 50%; box-shadow: 0 0 12px #10B981; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }} 70% {{ transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }} 100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }} }}
        header h1 {{ font-size: 20px; font-weight: 600; letter-spacing: 0.5px; }}
        header h1 span {{ color: #6366F1; }}
        .header-actions {{ display: flex; align-items: center; gap: 16px; }}
        .logout-btn {{ background: rgba(239, 68, 68, 0.1); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); padding: 8px 16px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; text-decoration: none; transition: all 0.2s ease; }}
        .logout-btn:hover {{ background: #EF4444; color: white; box-shadow: 0 0 12px rgba(239, 68, 68, 0.3); }}
        .server-status-pill {{ background: rgba(16, 185, 129, 0.1); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.2); padding: 6px 14px; border-radius: 30px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 24px; }}
        .stat-card {{ background: rgba(22, 22, 34, 0.4); border: 1px solid rgba(255, 255, 255, 0.03); border-radius: 16px; padding: 20px; display: flex; align-items: center; gap: 16px; position: relative; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15); transition: all 0.3s ease; }}
        .stat-card:hover {{ transform: translateY(-2px); border-color: rgba(255, 255, 255, 0.08); }}
        .stat-icon {{ width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; }}
        .stat-total .stat-icon {{ background: rgba(245, 158, 11, 0.1); color: #F59E0B; }}
        .stat-total::after {{ content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 3px; background: #F59E0B; box-shadow: 0 0 12px #F59E0B; }}
        .stat-active .stat-icon {{ background: rgba(16, 185, 129, 0.1); color: #10B981; }}
        .stat-active::after {{ content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 3px; background: #10B981; box-shadow: 0 0 12px #10B981; }}
        .stat-expired .stat-icon {{ background: rgba(239, 68, 68, 0.1); color: #EF4444; }}
        .stat-expired::after {{ content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 3px; background: #EF4444; box-shadow: 0 0 12px #EF4444; }}
        .stat-details h3 {{ font-size: 12px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
        .stat-details p {{ font-size: 28px; font-weight: 700; }}
        .dashboard-body {{ display: grid; grid-template-columns: 360px 1fr; gap: 24px; align-items: start; }}
        @media (max-width: 900px) {{ .dashboard-body {{ grid-template-columns: 1fr; }} }}
        .card {{ background: rgba(22, 22, 34, 0.4); border: 1px solid rgba(255, 255, 255, 0.03); border-radius: 20px; padding: 24px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); }}
        .card-title {{ font-size: 16px; font-weight: 600; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }}
        .card-subtitle {{ font-size: 12px; color: #9CA3AF; margin-bottom: 20px; }}
        .input-field {{ width: 100%; background: #07080d; border: 1px solid rgba(255, 255, 255, 0.08); color: white; padding: 12px 14px; border-radius: 10px; font-size: 14px; transition: all 0.2s ease; margin-bottom: 16px; text-align: center; }}
        .input-field:focus {{ outline: none; border-color: #6366F1; box-shadow: 0 0 12px rgba(99, 102, 241, 0.2); }}
        .gen-option {{ display: flex; align-items: center; justify-content: space-between; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.04); border-radius: 12px; padding: 12px 14px; margin-bottom: 10px; cursor: pointer; transition: all 0.2s ease; }}
        .gen-option:hover {{ background: rgba(255, 255, 255, 0.04); border-color: rgba(255, 255, 255, 0.08); }}
        .gen-option.active {{ background: rgba(99, 102, 241, 0.05); border-color: #6366F1; }}
        .option-text h4 {{ font-size: 13px; font-weight: 600; margin-bottom: 2px; }}
        .option-text p {{ font-size: 10px; color: #9CA3AF; }}
        .option-radio {{ position: relative; width: 16px; height: 16px; border: 2px solid rgba(255, 255, 255, 0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; }}
        .gen-option.active .option-radio {{ border-color: #6366F1; }}
        .gen-option.active .option-radio::after {{ content: ''; width: 8px; height: 8px; background: #6366F1; border-radius: 50%; }}
        .custom-time-panel {{ display: none; background: rgba(0, 0, 0, 0.2); border: 1px dashed rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px; margin-top: -6px; margin-bottom: 12px; }}
        .custom-time-inputs {{ display: flex; gap: 8px; }}
        .custom-time-inputs input, .custom-time-inputs select {{ background: #0F0F16; border: 1px solid rgba(255, 255, 255, 0.1); color: white; padding: 8px 10px; border-radius: 6px; font-size: 13px; }}
        .custom-time-inputs input {{ width: 70px; text-align: center; }}
        .custom-time-inputs select {{ flex: 1; }}
        .register-btn {{ background: #6366F1; color: white; border: none; width: 100%; padding: 14px; border-radius: 12px; font-size: 14px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3); transition: all 0.2s ease; margin-top: 8px; }}
        .register-btn:hover {{ background: #4F46E5; box-shadow: 0 4px 24px rgba(99, 102, 241, 0.45); transform: translateY(-1px); }}
        .table-container {{ overflow-x: auto; margin-top: 12px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th {{ font-size: 11px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }}
        td {{ font-size: 13px; padding: 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.03); vertical-align: middle; }}
        tr:hover td {{ background: rgba(255, 255, 255, 0.01); }}
        .td-key {{ font-family: monospace; font-size: 14px; font-weight: 600; color: white; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 30px; font-size: 10px; font-weight: 600; text-transform: uppercase; }}
        .badge-active {{ background: rgba(16, 185, 129, 0.1); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.2); }}
        .badge-expired {{ background: rgba(239, 68, 68, 0.1); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); }}
        .time-left-container {{ font-size: 12px; color: #D1D5DB; }}
        .time-left-expiry {{ font-size: 10px; color: #9CA3AF; margin-top: 2px; }}
        .action-btn {{ background: rgba(239, 68, 68, 0.1); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); padding: 6px 12px; border-radius: 8px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }}
        .action-btn:hover {{ background: #EF4444; color: white; box-shadow: 0 0 12px rgba(239, 68, 68, 0.3); }}
        .no-keys-box {{ display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; text-align: center; }}
        .no-keys-box span {{ font-size: 40px; margin-bottom: 16px; }}
        .no-keys-box h6 {{ font-size: 14px; font-weight: 600; margin-bottom: 6px; }}
        .no-keys-box p {{ font-size: 12px; color: #9CA3AF; }}
    </style>
</head>
<body>
    <header>
        <div class="header-title-container">
            <div class="status-dot"></div>
            <h1><span>DEVICE</span> AUTH PANEL</h1>
        </div>
        <div class="header-actions">
            <form method="POST" action="/logout">
                <button type="submit" class="logout-btn">LOG OUT</button>
            </form>
            <div class="server-status-pill">Server: Online</div>
        </div>
    </header>

    {success_box}

    <div class="stats-grid">
        <div class="stat-card stat-total">
            <div class="stat-icon">📱</div>
            <div class="stat-details">
                <h3>Total Registered</h3>
                <p>{total_devices}</p>
            </div>
        </div>
        <div class="stat-card stat-active">
            <div class="stat-icon">🟢</div>
            <div class="stat-details">
                <h3>Active Devices</h3>
                <p>{active_devices}</p>
            </div>
        </div>
        <div class="stat-card stat-expired">
            <div class="stat-icon">🔴</div>
            <div class="stat-details">
                <h3>Expired Devices</h3>
                <p>{expired_devices}</p>
            </div>
        </div>
    </div>

    <div class="dashboard-body">
        <div class="card">
            <h2 class="card-title">⚙️ Register Device</h2>
            <p class="card-subtitle">Manually add a Device ID to register it</p>

            <form method="POST" action="/register_device">
                <label style="font-size: 11px; text-transform: uppercase; color: #9CA3AF; letter-spacing: 0.5px; display: block; margin-bottom: 8px; font-weight: 600; text-align:left;">Device ID</label>
                <input type="text" name="device_id" class="input-field" placeholder="e.g. 3a9e8f4c27b01d3a" required autocomplete="off">

                <label style="font-size: 11px; text-transform: uppercase; color: #9CA3AF; letter-spacing: 0.5px; display: block; margin-bottom: 8px; font-weight: 600; text-align:left;">Select Duration</label>
                <div class="gen-option active" id="opt_1_min" onclick="selectOption('1_min')">
                    <div class="option-text">
                        <h4>1 Minute</h4>
                        <p>Super Short Testing</p>
                    </div>
                    <div class="option-radio"></div>
                </div>

                <div class="gen-option" id="opt_10_min" onclick="selectOption('10_min')">
                    <div class="option-text">
                        <h4>10 Minutes</h4>
                        <p>Quick Testing</p>
                    </div>
                    <div class="option-radio"></div>
                </div>

                <div class="gen-option" id="opt_1_month" onclick="selectOption('1_month')">
                    <div class="option-text">
                        <h4>1 Month</h4>
                        <p>Premium Access</p>
                    </div>
                    <div class="option-radio"></div>
                </div>

                <div class="gen-option" id="opt_custom" onclick="selectOption('custom')">
                    <div class="option-text">
                        <h4>Custom Time</h4>
                        <p>Custom License Duration</p>
                    </div>
                    <div class="option-radio"></div>
                </div>

                <div class="custom-time-panel" id="customTimePanel">
                    <div class="custom-time-inputs">
                        <input type="number" name="custom_value" value="1" min="1">
                        <select name="custom_unit">
                            <option value="minutes">Minutes</option>
                            <option value="hours">Hours</option>
                            <option value="days" selected>Days</option>
                        </select>
                    </div>
                </div>

                <input type="hidden" name="duration_type" id="durationTypeInput" value="1_min">
                <button type="submit" class="register-btn">Register Device</button>
            </form>
        </div>

        <div class="card">
            <h2 class="card-title">🛡️ Registered Devices</h2>
            <p class="card-subtitle">Review active device registrations and durations</p>
            <div class="table-container">
                {table_rows}
            </div>
        </div>
    </div>

    <script>
        function selectOption(type) {{
            document.querySelectorAll('.gen-option').forEach(opt => {{
                opt.classList.remove('active');
            }});
            
            document.getElementById('opt_' + type).classList.add('active');
            document.getElementById('durationTypeInput').value = type;

            const customPanel = document.getElementById('customTimePanel');
            if (type === 'custom') {{
                customPanel.style.display = 'block';
            }} else {{
                customPanel.style.display = 'none';
            }}
        }}
    </script>
</body>
</html>"""
            self.wfile.write(html_content.encode('utf-8'))
            return

        self.send_error(404, "Page Not Found")

    def do_POST(self):
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path

            # 1. PROCESS ADMIN LOGIN REQUEST
            if path == '/login':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                params = urllib.parse.parse_qs(post_data)

                password = params.get('password', [''])[0].strip()

                if password == ADMIN_PASSWORD:
                    self.send_response(303)
                    self.send_header('Set-Cookie', f'session_token={SESSION_SECRET}; Path=/; HttpOnly')
                    self.send_header('Location', '/')
                    self.end_headers()
                else:
                    self.serve_login_page("Incorrect Password! Access Denied.")
                return

            # 2. LOG OUT REQUEST
            if path == '/logout':
                self.send_response(303)
                self.send_header('Set-Cookie', 'session_token=deleted; Path=/; Max-Age=0')
                self.send_header('Location', '/')
                self.end_headers()
                return

            # 3. SECURE ACTION: REGISTER DEVICE
            if path == '/register_device':
                if not self.is_authenticated():
                    self.send_error(403, "Forbidden")
                    return

                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                params = urllib.parse.parse_qs(post_data)

                device_id = params.get('device_id', [''])[0].strip()
                duration_type = params.get('duration_type', ['1_min'])[0]

                if not device_id:
                    self.send_response(303)
                    self.send_header('Location', '/?error=empty_id')
                    self.end_headers()
                    return

                duration_seconds = 60
                if duration_type == '10_min':
                    duration_seconds = 600
                elif duration_type == '1_month':
                    duration_seconds = 30 * 86400
                elif duration_type == 'custom':
                    custom_val = int(params.get('custom_value', ['1'])[0])
                    custom_unit = params.get('custom_unit', ['days'])[0]
                    if custom_val <= 0:
                        custom_val = 1
                    if custom_unit == 'minutes':
                        duration_seconds = custom_val * 60
                    elif custom_unit == 'hours':
                        duration_seconds = custom_val * 3600
                    else: # days
                        duration_seconds = custom_val * 86400

                current_time = int(time.time())
                expires_at = current_time + duration_seconds

                devices_data = self.load_devices()
                devices_data[device_id] = {
                    'created_at': current_time,
                    'expires_at': expires_at,
                    'duration_seconds': duration_seconds
                }
                self.save_devices(devices_data)

                self.send_response(303)
                self.send_header('Location', '/?msg=registered')
                self.end_headers()
                return

            # 4. SECURE ACTION: DELETE/REVOKE DEVICE
            if path == '/delete_device':
                if not self.is_authenticated():
                    self.send_error(403, "Forbidden")
                    return

                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                params = urllib.parse.parse_qs(post_data)

                device_id = params.get('device_id', [''])[0].strip()
                devices_data = self.load_devices()
                if device_id in devices_data:
                    del devices_data[device_id]
                    self.save_devices(devices_data)

                self.send_response(303)
                self.send_header('Location', '/?msg=deleted')
                self.end_headers()
                return

            self.send_error(404, "Endpoint Not Found")
        except Exception as e:
            sys.stderr.write(f"Exception in do_POST: {str(e)}\n")
            sys.stderr.flush()
            self.send_response(500)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            err_html = f"""<!DOCTYPE html>
<html>
<head><title>500 Internal Server Error</title></head>
<body style="background:#090A0F; color:#E2E8F0; font-family:sans-serif; padding:40px; text-align:center;">
    <h1 style="color:#EF4444;">⚠️ 500 Internal Server Error</h1>
    <p style="margin-top:20px; font-size:16px;">{str(e)}</p>
    <p style="color:#9CA3AF; font-size:12px; margin-top:40px;">Please check write permissions for devices.json in your deployment directory.</p>
</body>
</html>"""
            self.wfile.write(err_html.encode('utf-8'))

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"🚀 DEVICE AUTH Control Panel running on: http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
