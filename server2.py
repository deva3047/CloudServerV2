import os, time, sys, subprocess, webbrowser, socket, urllib.request, urllib.parse, threading, json, shutil, datetime, base64, mimetypes

BOLD  = "\033[1m"
RED   = "\033[1;91m"
GREEN = "\033[1;92m"
GREY  = "\033[1;96m"
YELLOW= "\033[1;93m"
BLUE  = "\033[1;94m"
WHITE = "\033[1;37m"
ORANGE= "\033[1;33m"
PUR   = "\033[1;97m"
P     = "\033[1;95m"
RESET = "\033[0m"

ANALYTICS_FILE = os.path.join(os.path.expanduser('~'), '.server_analytics.json')

def load_analytics():
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "link_opens": 0,
        "server_starts": 0,
        "files_uploaded": 0,
        "files_deleted": 0,
        "tunnel_sessions": 0,
        "html_pages_created": 0,
        "last_start": None,
        "history": []
    }

def save_analytics(data):
    try:
        with open(ANALYTICS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def log_event(key, note=None):
    data = load_analytics()
    if key in data and isinstance(data[key], int):
        data[key] += 1
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {"event": key, "time": ts}
    if note:
        entry["note"] = note
    data.setdefault("history", []).append(entry)
    if len(data["history"]) > 100:
        data["history"] = data["history"][-100:]
    if key == "server_starts":
        data["last_start"] = ts
    save_analytics(data)

def is_termux():
    return os.environ.get('TERMUX_VERSION') is not None or os.path.exists('/data/data/com.termux')

def is_windows():
    return sys.platform == 'win32'

TERMUX = is_termux()
WINDOWS = is_windows()
LINUX = not TERMUX and not WINDOWS

if TERMUX:
    PREFIX   = os.environ.get('PREFIX', '/data/data/com.termux/files/usr')
    WEB_ROOT = os.path.join(PREFIX, 'share/apache2/default-site/htdocs')
    SUDO     = []
elif WINDOWS:
    _candidates = [r'C:\xampp\htdocs', r'D:\xampp\htdocs', r'C:\wamp64\www', r'C:\wamp\www']
    WEB_ROOT = next((p for p in _candidates if os.path.exists(os.path.dirname(p))),
                    os.path.join(os.path.expanduser('~'), 'server_root'))
    SUDO = []
else:
    WEB_ROOT = '/var/www/html'
    SUDO     = ['sudo']

_win_server_proc = None

def clear():
    os.system('cls' if WINDOWS else 'clear')

def term_width():
    try:
        return shutil.get_terminal_size(fallback=(100, 24)).columns
    except Exception:
        return 100

def slow(text, color=RESET, delay=0.008):
    try:
        sys.stdout.write(color)
        sys.stdout.flush()
        for ch in text:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(delay)
    finally:
        sys.stdout.write(RESET + '\n')
        sys.stdout.flush()

def baner():
    w = term_width()
    ascii_lines = [
        "███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗ ",
        "██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗",
        "███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝",
        "╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██╔══╝  ██╔══██╗",
        "███████║███████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║",
        "╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝",
    ]
    art_w = max(len(l) for l in ascii_lines)
    print()
    for line in ascii_lines:
        sys.stdout.write(BLUE + '\t\t')
        for ch in line:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(0.001)
        sys.stdout.write(RESET + '\n')
        sys.stdout.flush()

    def type_out(text):
        for ch in text:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(0.001)

    type_out(f"\t\t       {WHITE}Ver 2.3{RESET}  by {GREY}[ Jay Joshi ]{RESET}\n")
    type_out(f"\t {GREEN}https://github.com/deva3047{RESET}\n")
    type_out(f"\t {GREEN}https://www.instagram.com/deva_3047_?igsh=czkxemIxc2QxcTF1{RESET}\n")
    type_out(f"\t     {WHITE}Easy To Create Server{RESET}\n")
    type_out(f"\t {BLUE}{'=' * 74}{RESET}\n\n")
    sys.stdout.flush()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def get_public_ip():
    try:
        with urllib.request.urlopen('https://api.ipify.org', timeout=5) as r:
            return r.read().decode('utf-8').strip()
    except Exception:
        return None

def is_apache_installed():
    if WINDOWS:
        xampp_exe = os.path.join(os.path.dirname(WEB_ROOT), 'apache', 'bin', 'httpd.exe')
        return os.path.exists(xampp_exe) or _php_available()
    cmd = 'apachectl' if TERMUX else 'apache2'
    result = subprocess.run(['which', cmd], capture_output=True, text=True)
    return result.returncode == 0

def _php_available():
    try:
        result = subprocess.run(['php', '--version'], capture_output=True, text=True, shell=WINDOWS)
        return result.returncode == 0
    except Exception:
        return False

def is_apache_running():
    global _win_server_proc
    if WINDOWS:
        if _win_server_proc and _win_server_proc.poll() is None:
            return True
        result = subprocess.run('tasklist', capture_output=True, text=True, shell=True)
        return 'httpd.exe' in result.stdout
    if TERMUX:
        try:
            result = subprocess.run(['pgrep', '-x', 'httpd'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    try:
        result = subprocess.run(['sudo', 'service', 'apache2', 'status'], capture_output=True, text=True)
        return 'active (running)' in result.stdout
    except Exception:
        return False

def sanitize_name(name):
    safe_name = name.replace(' ', '_')
    if safe_name == name:
        return name, False
    old_path = os.path.join(WEB_ROOT, name)
    new_path = os.path.join(WEB_ROOT, safe_name)
    old_path_exists = os.path.exists(old_path)
    new_path_exists = os.path.exists(new_path)
    if old_path_exists:
        try:
            if LINUX:
                result = subprocess.run(['sudo', 'mv', old_path, new_path], capture_output=True, text=True)
                if result.returncode != 0:
                    return name, False
            elif WINDOWS:
                import tempfile
                tmp_path = os.path.join(WEB_ROOT, '__temp_rename__' + str(int(time.time())))
                os.rename(old_path, tmp_path)
                os.rename(tmp_path, new_path)
            else:
                os.rename(old_path, new_path)
            return safe_name, True
        except Exception as e:
            # rollback: tmp_path is defined in WINDOWS branch above; recover if possible
            if WINDOWS:
                _rb_tmp = os.path.join(WEB_ROOT, '__temp_rename__' + str(int(time.time()) - 1))
                for candidate in [
                    os.path.join(WEB_ROOT, next(
                        (n for n in os.listdir(WEB_ROOT) if n.startswith('__temp_rename__')), ''
                    )),
                ]:
                    if os.path.exists(candidate):
                        try:
                            os.rename(candidate, old_path)
                        except Exception:
                            pass
                        break
            return name, False
    elif new_path_exists:
        return safe_name, False
    return name, False

def find_cloudflared():
    if WINDOWS:
        candidates = [
            'cloudflared.exe',
            os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'), 'cloudflared', 'cloudflared.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'), 'cloudflared', 'cloudflared.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'cloudflared', 'cloudflared.exe'),
            os.path.join(os.environ.get('USERPROFILE', r'C:\Users\Public'), 'cloudflared.exe'),
            os.path.join(os.environ.get('USERPROFILE', r'C:\Users\Public'), 'Downloads', 'cloudflared.exe'),
            r'C:\cloudflared\cloudflared.exe',
            r'C:\cloudflared.exe',
        ]
        for path in candidates:
            if os.path.isfile(path):
                return f'"{path}"'
        try:
            result = subprocess.run('where cloudflared', capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                found = result.stdout.strip().splitlines()[0].strip()
                if found:
                    return f'"{found}"'
        except Exception:
            pass
        return None
    else:
        search_paths = [
            '/data/data/com.termux/files/usr/bin/cloudflared',
            '/usr/local/bin/cloudflared',
            '/usr/bin/cloudflared',
            os.path.join(os.path.expanduser('~'), 'cloudflared'),
            os.path.join(os.path.expanduser('~'), 'bin', 'cloudflared'),
        ]
        for path in search_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        result = subprocess.run(['which', 'cloudflared'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return None

def get_cloudflared_download_url():
    import urllib.request, json
    try:
        api = 'https://api.github.com/repos/cloudflare/cloudflared/releases/latest'
        req = urllib.request.Request(api, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            release = json.loads(r.read().decode())
        assets = release.get('assets', [])
        if WINDOWS:
            for a in assets:
                if 'windows-amd64.exe' in a['name']:
                    return a['browser_download_url'], a['name']
        elif TERMUX:
            import platform
            arch = platform.machine().lower()
            keyword = 'arm64' if 'aarch64' in arch or 'arm64' in arch else 'arm'
            for a in assets:
                if f'linux-{keyword}' in a['name'] and a['name'].endswith('.tar.gz'):
                    return a['browser_download_url'], a['name']
            for a in assets:
                if 'linux-arm' in a['name']:
                    return a['browser_download_url'], a['name']
        else:
            for a in assets:
                if 'linux-amd64' in a['name'] and a['name'].endswith('.deb'):
                    return a['browser_download_url'], a['name']
        return None, None
    except Exception:
        if WINDOWS:
            return 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe', 'cloudflared-windows-amd64.exe'
        elif TERMUX:
            return 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.tar.gz', 'cloudflared-linux-arm64.tar.gz'
        else:
            return 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb', 'cloudflared-linux-amd64.deb'

def download_with_progress(url, dest_path, label='Downloading'):
    def _reporthook(count, block_size, total_size):
        if total_size > 0:
            pct = min(int(count * block_size * 100 / total_size), 100)
            done = pct // 3
            bar  = '█' * done + '░' * (34 - done)
            sys.stdout.write(f'\r  {GREEN}{label}{RESET}  [{BLUE}{bar}{RESET}]  {WHITE}{pct}%{RESET}   ')
            sys.stdout.flush()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlretrieve(url, dest_path, reporthook=_reporthook)
        sys.stdout.write('\n')
        sys.stdout.flush()
        return True
    except Exception as e:
        sys.stdout.write('\n')
        slow(f'  Download error: {e}', RED)
        return False

def install_cloudflared_auto():
    if TERMUX:
        slow('\n  Trying: pkg install cloudflared ...', YELLOW)
        try:
            result = subprocess.run(
                ['pkg', 'install', '-y', 'cloudflared'],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                slow('  cloudflared installed via pkg!', GREEN)
                return True
            slow('  pkg install failed. Trying manual download...', YELLOW)
        except Exception:
            slow('  pkg method failed. Trying manual download...', YELLOW)

    slow('\n  Fetching latest cloudflared release info...', YELLOW)
    url, fname = get_cloudflared_download_url()
    if not url:
        slow('  Could not fetch download URL. Check your internet.', RED)
        return False

    slow(f'  Downloading: {fname}', BLUE)

    if WINDOWS:
        dest = os.path.join(os.environ.get('USERPROFILE', r'C:\Users\Public'), 'cloudflared.exe')
        ok   = download_with_progress(url, dest, 'cloudflared.exe')
        if ok and os.path.isfile(dest):
            slow(f'  Saved to: {dest}', GREEN)
            slow('  cloudflared installed successfully!', GREEN)
            return True

    elif TERMUX:
        tmp_dir = os.path.join(os.environ.get('PREFIX', '/data/data/com.termux/files/usr'), 'tmp')
        tmp = os.path.join(tmp_dir, fname)
        os.makedirs(tmp_dir, exist_ok=True)
        ok  = download_with_progress(url, tmp, 'cloudflared')
        if ok:
            bin_dir = '/data/data/com.termux/files/usr/bin'
            bin_path = os.path.join(bin_dir, 'cloudflared')
            if fname.endswith('.tar.gz'):
                import tarfile
                try:
                    with tarfile.open(tmp, 'r:gz') as tar:
                        for member in tar.getmembers():
                            if 'cloudflared' in member.name and not member.name.endswith('/'):
                                member.name = 'cloudflared'
                                tar.extract(member, path=bin_dir, filter='data')
                    os.chmod(bin_path, 0o755)
                    slow('  cloudflared installed to Termux bin!', GREEN)
                    return True
                except Exception as e:
                    slow(f'  Extract error: {e}', RED)
            else:
                shutil.copy2(tmp, bin_path)
                os.chmod(bin_path, 0o755)
                slow('  cloudflared installed to Termux bin!', GREEN)
                return True

    else:
        tmp = f'/tmp/{fname}'
        ok  = download_with_progress(url, tmp, 'cloudflared')
        if ok:
            try:
                subprocess.run(['sudo', 'dpkg', '-i', tmp], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                slow('  cloudflared installed via dpkg!', GREEN)
                return True
            except Exception as e:
                slow(f'  dpkg error: {e}', RED)
                try:
                    subprocess.run(['sudo', 'apt-get', 'install', '-f', '-y'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    slow('  Dependencies fixed and cloudflared installed!', GREEN)
                    return True
                except Exception:
                    pass

    return False

def repair_cloudflared():
    clear()
    print(BLUE + '\n  ╔══════════════════════════════════════════════════╗')
    print('  ║       Cloudflare Tunnel — Diagnosis & Repair     ║')
    print('  ╚══════════════════════════════════════════════════╝' + RESET)
    print()

    slow('  [1/4]  Checking cloudflared installation...', YELLOW)
    cf_cmd = find_cloudflared()
    if cf_cmd:
        slow(f'  Found: {cf_cmd}', GREEN)
    else:
        slow('  cloudflared NOT found!', RED)
        slow('  Auto-installing cloudflared...', YELLOW)
        ok = install_cloudflared_auto()
        if ok:
            cf_cmd = find_cloudflared()
            if cf_cmd:
                slow(f'  Installed at: {cf_cmd}', GREEN)
            else:
                slow('  Installed but path not found. Please restart.', YELLOW)
                input(GREEN + "\n  Press Enter to return..." + RESET)
                return
        else:
            slow('  Auto-install failed!', RED)
            input(GREEN + "\n  Press Enter to return..." + RESET)
            return

    print()
    slow('  [2/4]  Checking cloudflared version...', YELLOW)
    try:
        ver_result = subprocess.run(
            f'{cf_cmd} --version',
            shell=True, capture_output=True, text=True, timeout=10
        )
        if ver_result.returncode == 0:
            slow(f'  Version: {ver_result.stdout.strip() or ver_result.stderr.strip()}', GREEN)
        else:
            slow('  Version check failed!', RED)
    except Exception as e:
        slow(f'  Version check error: {e}', RED)

    print()
    slow('  [3/4]  Checking Apache server...', YELLOW)
    if is_apache_running():
        slow('  Apache is RUNNING ✓', GREEN)
    else:
        slow('  Apache is NOT running!', RED)
        slow('  Please start the server first using Option 02!', ORANGE)

    print()
    slow('  [4/4]  Testing tunnel connection...', YELLOW)
    slow('  Running quick test (10 seconds)...', GREY)

    import re as _re
    test_url  = [None]
    test_proc = [None]
    test_err  = [None]

    def _test_run():
        try:
            cmd = f'{cf_cmd} --protocol http2 tunnel --url http://127.0.0.1:80'
            proc = subprocess.Popen(
                cmd, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            test_proc[0] = proc
            for line in proc.stdout:
                match = _re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
                if match:
                    test_url[0] = match.group(0)
                    break
                if 'error' in line.lower() or 'failed' in line.lower():
                    test_err[0] = line.strip()
        except Exception as e:
            test_err[0] = str(e)

    t = threading.Thread(target=_test_run, daemon=True)
    t.start()
    t.join(timeout=15)

    if test_proc[0]:
        try:
            test_proc[0].terminate()
        except Exception:
            pass

    print()
    if test_url[0]:
        slow(f'  ✅  Tunnel TEST SUCCESSFUL!', GREEN)
        slow(f'  Test URL: {test_url[0]}', BLUE)
    elif test_err[0]:
        slow(f'  ❌  Tunnel Error: {test_err[0]}', RED)
    else:
        slow('  ⚠  Tunnel timeout - internet may be slow.', YELLOW)

    print()
    print(GREEN + '  ✓ Diagnosis complete!' + RESET)
    input(GREEN + "\n  Press Enter to return to main menu..." + RESET)

def get_xampp_download_url():
    import urllib.request, re
    try:
        fallback = 'https://sourceforge.net/projects/xampp/files/XAMPP%20Windows/8.2.12/xampp-windows-x64-8.2.12-0-VS16-installer.exe/download'
        try:
            req = urllib.request.Request(
                'https://www.apachefriends.org/download.html',
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                html = r.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'https://[^\s"\'<>]*xampp-windows-x64-[\d.]+-\d+-VS\d+-installer\.exe', html)
            if matches:
                return matches[0], os.path.basename(matches[0])
        except Exception:
            pass
        return fallback, 'xampp-installer.exe'
    except Exception:
        return 'https://sourceforge.net/projects/xampp/files/XAMPP%20Windows/8.2.12/xampp-windows-x64-8.2.12-0-VS16-installer.exe/download', 'xampp-installer.exe'

def install_apache():
    clear()
    print(BLUE + '\n  ╔══════════════════════════════════════════════════╗')
    print('  ║          Auto Installer — SERVER TOOL           ║')
    print('  ╚══════════════════════════════════════════════════╝' + RESET)
    print()

    if WINDOWS:
        slow('  [1/2]  Apache + PHP Setup  (Windows)', YELLOW)
        print()
        if _php_available() or is_apache_installed():
            slow('  Apache / PHP already installed!', GREEN)
        else:
            slow('  Checking winget availability...', GREY)
            winget_ok = subprocess.run('winget --version', shell=True, capture_output=True).returncode == 0
            if winget_ok:
                slow('  winget found — installing XAMPP automatically...', GREEN)
                try:
                    result = subprocess.run(
                        'winget install --id ApacheFriends.XAMPP --silent --accept-package-agreements --accept-source-agreements',
                        shell=True, capture_output=True, text=True
                    )
                    if result.returncode == 0 or 'successfully installed' in result.stdout.lower():
                        slow('  XAMPP installed successfully via winget!', GREEN)
                        slow('  Restart this tool to detect XAMPP.', YELLOW)
                    else:
                        winget_ok = False
                except Exception:
                    winget_ok = False

            if not winget_ok:
                slow('  Fetching latest XAMPP download link...', GREY)
                xampp_url, xampp_fname = get_xampp_download_url()
                dest = os.path.join(os.environ.get('TEMP', r'C:\Temp'), 'xampp-installer.exe')
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                ok = download_with_progress(xampp_url, dest, 'XAMPP')
                if ok and os.path.isfile(dest):
                    slow('  Download complete! Launching XAMPP installer...', GREEN)
                    try:
                        subprocess.Popen([dest], shell=True)
                    except Exception as e:
                        slow(f'  Could not launch installer: {e}', RED)
                else:
                    webbrowser.open('https://www.apachefriends.org')

        print()
        slow('  [2/2]  Installing cloudflared  (Windows)...', YELLOW)
        if find_cloudflared():
            slow('  cloudflared is already installed!', GREEN)
        else:
            winget_cf = subprocess.run('winget --version', shell=True, capture_output=True).returncode == 0
            cf_done = False
            if winget_cf:
                try:
                    result = subprocess.run(
                        'winget install --id Cloudflare.cloudflared --silent --accept-package-agreements --accept-source-agreements',
                        shell=True, capture_output=True, text=True
                    )
                    if result.returncode == 0 or 'successfully installed' in result.stdout.lower():
                        slow('  cloudflared installed via winget!', GREEN)
                        cf_done = True
                except Exception:
                    pass
            if not cf_done:
                install_cloudflared_auto()
        input(GREEN + "\n  Press Enter to return to main menu..." + RESET)
        return

    if TERMUX:
        slow('  [1/2] Installing Apache2 (Termux)...', YELLOW)
        if is_apache_installed():
            slow('  Apache2 already installed!', GREEN)
        else:
            try:
                subprocess.run(['pkg', 'update', '-y'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['pkg', 'install', '-y', 'apache2'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                slow('  Apache2 installed successfully!', GREEN)
            except subprocess.CalledProcessError as e:
                slow(f'  Error: {e}', RED)
        print()
        slow('  [2/2] Installing cloudflared (Termux)...', YELLOW)
        if find_cloudflared():
            slow('  cloudflared already installed!', GREEN)
        else:
            install_cloudflared_auto()
        print()
        input(GREEN + "\n  Press Enter to return to main menu..." + RESET)
        return

    slow('  [1/2] Installing Apache2 (Linux)...', YELLOW)
    if is_apache_installed():
        slow('  Apache2 already installed!', GREEN)
    else:
        try:
            subprocess.run(['sudo', 'apt', 'update'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'apache2'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'chown', '-R', 'www-data:www-data', WEB_ROOT], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'chmod', '-R', '775', WEB_ROOT], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            slow('  Apache2 installed successfully!', GREEN)
        except subprocess.CalledProcessError as e:
            slow(f'  Error: {e}', RED)
    print()
    slow('  [2/2] Installing cloudflared (Linux)...', YELLOW)
    if find_cloudflared():
        slow('  cloudflared already installed!', GREEN)
    else:
        install_cloudflared_auto()
    print()
    print(GREEN + '  ✓ All done! Apache2 + cloudflared setup complete.' + RESET)
    input(GREEN + "\n  Press Enter to return to main menu..." + RESET)

def start_server():
    global _win_server_proc
    clear()
    if is_apache_running():
        slow('Server is already running!', YELLOW)
        input(GREEN + "\nPress Enter to return to main menu..." + RESET)
        return
    try:
        if WINDOWS:
            xampp_httpd = os.path.join(os.path.dirname(WEB_ROOT), 'apache', 'bin', 'httpd.exe')
            if os.path.exists(xampp_httpd):
                _win_server_proc = subprocess.Popen([xampp_httpd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                slow('XAMPP Apache started successfully.', GREEN)
            elif _php_available():
                os.makedirs(WEB_ROOT, exist_ok=True)
                _win_server_proc = subprocess.Popen(
                    ['php', '-S', '0.0.0.0:80', '-t', WEB_ROOT],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                slow('PHP built-in server started successfully.', GREEN)
            else:
                slow('No Apache or PHP found. Install XAMPP or PHP.', RED)
                input(GREEN + "\nPress Enter to return to main menu..." + RESET)
                return
        elif TERMUX:
            subprocess.run(['apachectl', 'start'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            slow('Server started successfully.', GREEN)
        else:
            subprocess.run(['sudo', 'service', 'apache2', 'start'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            slow('Server started successfully.', GREEN)
        log_event("server_starts")
    except subprocess.CalledProcessError as e:
        slow(f'Error starting server: {e}', RED)
    input(GREEN + "\nPress Enter to return to main menu..." + RESET)

def stop_server():
    global _win_server_proc
    clear()
    if not is_apache_running():
        slow('Server is already stopped!', YELLOW)
        input(GREEN + "\nPress Enter to return to main menu..." + RESET)
        return
    try:
        if WINDOWS:
            if _win_server_proc and _win_server_proc.poll() is None:
                _win_server_proc.terminate()
                _win_server_proc = None
            else:
                subprocess.run('taskkill /F /IM httpd.exe', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif TERMUX:
            subprocess.run(['apachectl', 'stop'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(['sudo', 'service', 'apache2', 'stop'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        slow('Server stopped successfully.', GREEN)
    except subprocess.CalledProcessError as e:
        slow(f'Error stopping server: {e}', RED)
    input(GREEN + "\nPress Enter to return to main menu..." + RESET)

def restart_server():
    global _win_server_proc
    clear()
    try:
        if WINDOWS:
            # Stop
            if _win_server_proc and _win_server_proc.poll() is None:
                _win_server_proc.terminate()
                _win_server_proc = None
            else:
                subprocess.run('taskkill /F /IM httpd.exe', shell=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            # Start
            xampp_httpd = os.path.join(os.path.dirname(WEB_ROOT), 'apache', 'bin', 'httpd.exe')
            if os.path.exists(xampp_httpd):
                _win_server_proc = subprocess.Popen([xampp_httpd],
                                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                slow('Server restarted successfully (XAMPP).', GREEN)
            elif _php_available():
                os.makedirs(WEB_ROOT, exist_ok=True)
                _win_server_proc = subprocess.Popen(
                    ['php', '-S', '0.0.0.0:80', '-t', WEB_ROOT],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                slow('Server restarted successfully (PHP).', GREEN)
            else:
                slow('No Apache or PHP found. Install XAMPP or PHP.', RED)
        elif TERMUX:
            subprocess.run(['apachectl', 'restart'], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            slow('Server restarted successfully.', GREEN)
        else:
            subprocess.run(['sudo', 'service', 'apache2', 'restart'], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            slow('Server restarted successfully.', GREEN)
        log_event("server_starts")
    except subprocess.CalledProcessError as e:
        slow(f'Error restarting server: {e}', RED)
    input(GREEN + "\nPress Enter to return to main menu..." + RESET)



def image_to_base64_src(path):
    try:
        mime, _ = mimetypes.guess_type(path)
        if not mime:
            mime = "image/jpeg"
        with open(path, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')
        return f"data:{mime};base64,{data}"
    except Exception:
        return None


def image_to_server(path, filename=None):
    try:
        os.makedirs(WEB_ROOT, exist_ok=True)
        name = filename or os.path.basename(path)
        safe_name = name.replace(' ', '_')
        dest = os.path.join(WEB_ROOT, safe_name)
        if LINUX:
            subprocess.run(['sudo', 'cp', path, dest], check=True)
            subprocess.run(['sudo', 'chmod', '775', dest], check=True)
            subprocess.run(['sudo', 'chown', 'www-data:www-data', dest], check=True)
        else:
            shutil.copy2(path, dest)
        return f"/{safe_name}", True
    except Exception as e:
        return str(e), False



def _generate_html_code(data):
    theme_map = {
        "Dark Blue":   {"bg": "#0d1117", "card": "#161b22", "accent": "#58a6ff", "text": "#e6edf3", "sub": "#8b949e", "btn": "#1f6feb", "nav": "#161b22", "border": "#30363d", "grad1": "#0d1117", "grad2": "#161b22"},
        "Midnight":    {"bg": "#0a0a0f", "card": "#12121a", "accent": "#a78bfa", "text": "#e2e2ff", "sub": "#7c7c9c", "btn": "#6d28d9", "nav": "#12121a", "border": "#2d2d4e", "grad1": "#0a0a0f", "grad2": "#1a1a2e"},
        "Forest":      {"bg": "#0d1f0d", "card": "#122012", "accent": "#4ade80", "text": "#d1fad7", "sub": "#6b9c6b", "btn": "#16a34a", "nav": "#122012", "border": "#1e3a1e", "grad1": "#0d1f0d", "grad2": "#162816"},
        "Sunset":      {"bg": "#1a0a00", "card": "#2a1200", "accent": "#fb923c", "text": "#fff1e6", "sub": "#b07050", "btn": "#ea580c", "nav": "#2a1200", "border": "#3d2010", "grad1": "#1a0a00", "grad2": "#2d1500"},
        "Ocean":       {"bg": "#020f1a", "card": "#061825", "accent": "#38bdf8", "text": "#e0f2fe", "sub": "#5a8eaa", "btn": "#0284c7", "nav": "#061825", "border": "#0f3347", "grad1": "#020f1a", "grad2": "#071e2e"},
        "Rose Gold":   {"bg": "#1a0d10", "card": "#271218", "accent": "#f9a8d4", "text": "#fce7f3", "sub": "#a06070", "btn": "#be185d", "nav": "#271218", "border": "#3d1a25", "grad1": "#1a0d10", "grad2": "#2a1520"},
        "White Clean": {"bg": "#f8fafc", "card": "#ffffff", "accent": "#3b82f6", "text": "#1e293b", "sub": "#64748b", "btn": "#2563eb", "nav": "#1e293b", "border": "#e2e8f0", "grad1": "#f0f4ff", "grad2": "#e8f0fe"},
        "Matrix":      {"bg": "#000000", "card": "#001100", "accent": "#00ff41", "text": "#00ff41", "sub": "#008f11", "btn": "#003b00", "nav": "#001100", "border": "#003300", "grad1": "#000000", "grad2": "#001a00"},
        "Cyber Red":   {"bg": "#0a0000", "card": "#140000", "accent": "#ff0033", "text": "#ffe0e0", "sub": "#882233", "btn": "#aa0022", "nav": "#140000", "border": "#3a0010", "grad1": "#0a0000", "grad2": "#1a0008"},
        "Neon Purple": {"bg": "#06000f", "card": "#10001e", "accent": "#bf00ff", "text": "#f0d0ff", "sub": "#7040a0", "btn": "#7700cc", "nav": "#10001e", "border": "#2a0050", "grad1": "#06000f", "grad2": "#160030"},
        "Ice Hacker":  {"bg": "#000810", "card": "#001020", "accent": "#00e5ff", "text": "#d0f8ff", "sub": "#307090", "btn": "#007799", "nav": "#001020", "border": "#003355", "grad1": "#000810", "grad2": "#001830"},
        "Blood Gold":  {"bg": "#0d0800", "card": "#1a1000", "accent": "#ffaa00", "text": "#fff3d0", "sub": "#997730", "btn": "#cc8800", "nav": "#1a1000", "border": "#3d2c00", "grad1": "#0d0800", "grad2": "#1a1400"},
        "Ghost White": {"bg": "#e8e8e8", "card": "#ffffff", "accent": "#222222", "text": "#111111", "sub": "#555555", "btn": "#000000", "nav": "#111111", "border": "#cccccc", "grad1": "#f0f0f0", "grad2": "#e0e0e0"},
        "Toxic":       {"bg": "#000d00", "card": "#001500", "accent": "#aaff00", "text": "#eeffcc", "sub": "#607030", "btn": "#558800", "nav": "#001500", "border": "#1a3300", "grad1": "#000d00", "grad2": "#001200"},
        "Stealth":     {"bg": "#090909", "card": "#111111", "accent": "#ff6600", "text": "#f0e8e0", "sub": "#886655", "btn": "#cc4400", "nav": "#111111", "border": "#2a1a0d", "grad1": "#090909", "grad2": "#181008"},
    }

    t = theme_map.get(data.get("theme", "Dark Blue"), theme_map["Dark Blue"])
    title           = data.get("title", "My Website")
    heading         = data.get("heading", "Welcome")
    tagline         = data.get("tagline", "")
    body_text       = data.get("body_text", "").replace("\n", "<br>")
    author          = data.get("author", "")
    show_contact    = data.get("show_contact", False)
    email           = data.get("email", "")
    phone           = data.get("phone", "")
    show_gallery    = data.get("show_gallery", False)
    image_urls      = data.get("image_urls", [])
    show_cards      = data.get("show_cards", False)
    card_data       = data.get("card_data", [])
    footer_text     = data.get("footer_text", f"© {datetime.datetime.now().year} {author or title}")
    custom_css      = data.get("custom_css", "")
    show_links      = data.get("show_links", False)
    link_data       = data.get("link_data", [])

    social_url      = data.get("social_url", "")
    social_desc     = data.get("social_desc", tagline or f"{title} - {heading}")
    social_image    = data.get("social_image", "")
    social_twitter  = data.get("social_twitter", "")
    social_site_name = data.get("social_site_name", title)
    social_type     = data.get("social_type", "website")
    whatsapp_number = data.get("whatsapp_number", "")
    whatsapp_msg    = data.get("whatsapp_msg", f"Hi! I visited {title}")
    show_social     = data.get("show_social", False)

    og_tags = f"""
  <meta property="og:type"        content="{social_type}">
  <meta property="og:url"         content="{social_url}">
  <meta property="og:title"       content="{title}">
  <meta property="og:description" content="{social_desc}">
  <meta property="og:site_name"   content="{social_site_name}">
  {'<meta property="og:image" content="' + social_image + '">' if social_image else ''}
  {'<meta property="og:image:width"  content="1200">' if social_image else ''}
  {'<meta property="og:image:height" content="630">'  if social_image else ''}

  <meta name="twitter:card"        content="summary_large_image">
  <meta name="twitter:title"       content="{title}">
  <meta name="twitter:description" content="{social_desc}">
  {'<meta name="twitter:site"  content="@' + social_twitter.lstrip('@') + '">' if social_twitter else ''}
  {'<meta name="twitter:image" content="' + social_image + '">' if social_image else ''}

  <meta name="description" content="{social_desc}">
  <meta name="author"      content="{author}">
  <meta name="robots"      content="index, follow">
""" if show_social or social_url or social_desc else ""

    gallery_html = ""
    if show_gallery and image_urls:
        imgs = ""
        for url in image_urls:
            url = url.strip()
            if url:
                imgs += f'<div class="gal-item"><img src="{url}" alt="gallery image" onerror="this.parentElement.style.display=\'none\'"></div>\n'
        if imgs:
            gallery_html = f'''
  <section class="section">
    <h2 class="section-title">Gallery</h2>
    <div class="gallery">{imgs}</div>
  </section>'''

    cards_html = ""
    if show_cards and card_data:
        cards = ""
        for c in card_data:
            ct = c.get("title", "").strip()
            cd = c.get("desc", "").strip()
            if ct or cd:
                cards += f'<div class="card"><h3 class="card-title">{ct}</h3><p class="card-desc">{cd}</p></div>\n'
        if cards:
            cards_html = f'''
  <section class="section">
    <h2 class="section-title">Features</h2>
    <div class="cards-grid">{cards}</div>
  </section>'''

    links_html = ""
    if show_links and link_data:
        link_items = ""
        for lnk in link_data:
            lt = lnk.get("label", "").strip()
            lu = lnk.get("url", "").strip()
            lo = lnk.get("open_new", True)
            if lt and lu:
                target = ' target="_blank" rel="noopener"' if lo else ''
                link_items += f'<a href="{lu}" class="hyper-link"{target}>{lt}</a>\n'
        if link_items:
            links_html = f'''
  <section class="section">
    <h2 class="section-title">Links</h2>
    <div class="links-row">{link_items}</div>
  </section>'''

    contact_html = ""
    if show_contact and (email or phone or whatsapp_number):
        items = ""
        if email:
            items += f'<a href="mailto:{email}" class="contact-btn">✉ {email}</a>'
        if phone:
            items += f'<a href="tel:{phone}" class="contact-btn">📞 {phone}</a>'
        if whatsapp_number:
            wa_clean = whatsapp_number.replace('+', '').replace(' ', '').replace('-', '')
            wa_link  = f"https://wa.me/{wa_clean}?text={urllib.parse.quote(whatsapp_msg) if whatsapp_msg else ''}"
            items += f'<a href="{wa_link}" target="_blank" class="contact-btn whatsapp-btn">💬 WhatsApp</a>'
        contact_html = f'''
  <section class="section">
    <h2 class="section-title">Contact</h2>
    <div class="contact-row">{items}</div>
  </section>'''

    matrix_script = ""
    if data.get("theme") == "Matrix":
        matrix_script = """
<canvas id="matrix-canvas" style="position:fixed;top:0;left:0;z-index:-1;opacity:0.13;pointer-events:none;"></canvas>
<script>
(function(){
  var c=document.getElementById('matrix-canvas');
  var ctx=c.getContext('2d');
  c.width=window.innerWidth; c.height=window.innerHeight;
  window.addEventListener('resize',function(){c.width=window.innerWidth;c.height=window.innerHeight;drops=Array(Math.floor(c.width/fs)).fill(1);});
  var fs=14,cols=Math.floor(c.width/fs),drops=Array(cols).fill(1);
  var chars='アイウエオカキクケコ0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ@#$%^&*()';
  setInterval(function(){
    ctx.fillStyle='rgba(0,0,0,0.05)';ctx.fillRect(0,0,c.width,c.height);
    ctx.fillStyle='#00ff41';ctx.font=fs+'px monospace';
    for(var i=0;i<drops.length;i++){
      ctx.fillText(chars[Math.floor(Math.random()*chars.length)],i*fs,drops[i]*fs);
      if(drops[i]*fs>c.height&&Math.random()>0.975)drops[i]=0;
      drops[i]++;
    }
  },35);
})();
</script>"""

    glitch_css = ""
    if data.get("theme") in ("Cyber Red", "Neon Purple", "Ice Hacker", "Stealth"):
        glitch_css = """
    .hero h1 {
      text-shadow: 2px 0 var(--accent), -2px 0 var(--btn);
      animation: glitch 3s infinite;
    }
    @keyframes glitch {
      0%,95%,100% { text-shadow: 2px 0 var(--accent), -2px 0 var(--btn); }
      96% { text-shadow: -4px 0 var(--accent), 4px 0 var(--btn), 0 0 20px var(--accent); }
      97% { text-shadow: 4px 0 var(--accent), -4px 0 var(--btn); clip-path: inset(10% 0 20% 0); }
      98% { text-shadow: -2px 0 var(--btn), 2px 0 var(--accent); clip-path: inset(60% 0 10% 0); }
      99% { text-shadow: 2px 0 var(--accent), -2px 0 var(--btn); clip-path: none; }
    }
    .card { border-left: 3px solid var(--accent); }
    .card:hover { box-shadow: 0 0 20px var(--accent)44; }
    nav { border-bottom: 1px solid var(--accent)55; box-shadow: 0 2px 20px var(--accent)22; }
"""
    elif data.get("theme") == "Matrix":
        glitch_css = """
    body { font-family: 'Courier New', monospace !important; }
    .hero h1 { color: #00ff41; text-shadow: 0 0 20px #00ff41; }
    .card { border-left: 2px solid #00ff41; }
    .card:hover { box-shadow: 0 0 15px #00ff4166; }
    .nav-brand { text-shadow: 0 0 10px var(--accent); }
    .section-title { text-shadow: 0 0 8px var(--accent); }
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
{og_tags}
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:     {t['bg']};
      --card:   {t['card']};
      --accent: {t['accent']};
      --text:   {t['text']};
      --sub:    {t['sub']};
      --btn:    {t['btn']};
      --nav:    {t['nav']};
      --border: {t['border']};
    }}

    html {{ scroll-behavior: smooth; }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      line-height: 1.7;
      min-height: 100vh;
    }}

    nav {{
      background: var(--nav);
      border-bottom: 1px solid var(--border);
      position: sticky; top: 0; z-index: 100;
      backdrop-filter: blur(12px);
    }}
    .nav-inner {{
      max-width: 1100px; margin: 0 auto;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 24px; height: 60px;
    }}
    .nav-brand {{
      font-size: 1.25rem; font-weight: 700;
      color: var(--accent); text-decoration: none; letter-spacing: -0.5px;
    }}
    .nav-links {{ display: flex; gap: 20px; list-style: none; }}
    .nav-links a {{
      color: var(--sub); text-decoration: none; font-size: 0.9rem;
      transition: color .2s;
    }}
    .nav-links a:hover {{ color: var(--accent); }}

    .hero {{
      background: linear-gradient(135deg, {t['grad1']} 0%, {t['grad2']} 100%);
      padding: 100px 24px 80px;
      text-align: center;
      position: relative; overflow: hidden;
    }}
    .hero::before {{
      content: '';
      position: absolute; inset: 0;
      background: radial-gradient(ellipse 80% 60% at 50% 0%, {t['accent']}18 0%, transparent 70%);
      pointer-events: none;
    }}
    .hero-badge {{
      display: inline-block;
      background: {t['accent']}22;
      color: var(--accent);
      border: 1px solid {t['accent']}44;
      border-radius: 99px;
      padding: 4px 18px;
      font-size: 0.82rem;
      font-weight: 600;
      letter-spacing: 1px;
      text-transform: uppercase;
      margin-bottom: 22px;
    }}
    .hero h1 {{
      font-size: clamp(2.2rem, 6vw, 4rem);
      font-weight: 800;
      line-height: 1.15;
      letter-spacing: -1.5px;
      margin-bottom: 18px;
      background: linear-gradient(135deg, var(--text) 0%, var(--accent) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .hero-tagline {{
      font-size: 1.15rem;
      color: var(--sub);
      max-width: 560px;
      margin: 0 auto 36px;
    }}
    .hero-btn {{
      display: inline-block;
      background: var(--btn);
      color: #ffffff;
      padding: 13px 38px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 600;
      font-size: 1rem;
      transition: opacity .2s, transform .2s;
      box-shadow: 0 4px 20px {t['btn']}55;
    }}
    .hero-btn:hover {{ opacity: 0.88; transform: translateY(-2px); }}

    .section {{
      max-width: 1100px; margin: 0 auto;
      padding: 60px 24px;
    }}
    .section-title {{
      font-size: 1.8rem; font-weight: 700;
      color: var(--accent);
      margin-bottom: 32px;
      padding-bottom: 12px;
      border-bottom: 2px solid var(--border);
    }}

    .body-text {{
      background: var(--card);
      border: 1px solid var(--border);
      border-left: 4px solid var(--accent);
      border-radius: 10px;
      padding: 28px 32px;
      font-size: 1.05rem;
      color: var(--text);
      line-height: 1.9;
    }}

    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 20px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px 20px;
      transition: transform .2s, border-color .2s, box-shadow .2s;
    }}
    .card:hover {{ transform: translateY(-4px); border-color: var(--accent); }}
    .card-title {{
      font-size: 1.1rem; font-weight: 700;
      color: var(--accent); margin-bottom: 10px;
    }}
    .card-desc {{ color: var(--sub); font-size: 0.95rem; }}

    .gallery {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 12px;
    }}
    .gal-item {{
      border-radius: 10px; overflow: hidden;
      aspect-ratio: 4/3;
      background: var(--card);
      border: 1px solid var(--border);
    }}
    .gal-item img {{ width: 100%; height: 100%; object-fit: cover; transition: transform .3s; }}
    .gal-item:hover img {{ transform: scale(1.06); }}

    .contact-row {{ display: flex; flex-wrap: wrap; gap: 14px; }}
    .contact-btn {{
      background: var(--card);
      border: 1px solid var(--accent);
      color: var(--accent);
      padding: 11px 28px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 600;
      transition: background .2s, color .2s;
    }}
    .contact-btn:hover {{ background: var(--accent); color: var(--bg); }}
    .whatsapp-btn {{
      border-color: #25d366;
      color: #25d366;
    }}
    .whatsapp-btn:hover {{
      background: #25d366;
      color: #ffffff;
    }}

    .links-row {{ display: flex; flex-wrap: wrap; gap: 12px; }}
    .hyper-link {{
      display: inline-flex; align-items: center; gap: 6px;
      background: var(--card);
      border: 1px solid var(--border);
      color: var(--accent);
      padding: 10px 22px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 600;
      font-size: 0.95rem;
      transition: background .2s, border-color .2s, transform .2s;
    }}
    .hyper-link::after {{ content: ' ↗'; font-size: 0.85em; opacity: 0.7; }}
    .hyper-link:hover {{
      background: var(--accent);
      color: var(--bg);
      border-color: var(--accent);
      transform: translateY(-2px);
    }}

    footer {{
      background: var(--nav);
      border-top: 1px solid var(--border);
      text-align: center;
      padding: 22px 24px;
      color: var(--sub);
      font-size: 0.9rem;
    }}

    @media (max-width: 600px) {{
      .nav-links {{ display: none; }}
      .hero {{ padding: 70px 16px 60px; }}
    }}

    {glitch_css}
    {custom_css}
  </style>
</head>
<body>

  <nav>
    <div class="nav-inner">
      <a class="nav-brand" href="#">{title}</a>
      <ul class="nav-links">
        <li><a href="#about">About</a></li>
        {'<li><a href="#cards">Features</a></li>' if show_cards and card_data else ''}
        {'<li><a href="#gallery">Gallery</a></li>' if show_gallery and image_urls else ''}
        {'<li><a href="#contact">Contact</a></li>' if show_contact and (email or phone or whatsapp_number) else ''}
        {'<li><a href="#links">Links</a></li>' if show_links and link_data else ''}
      </ul>
    </div>
  </nav>

  <div class="hero">
    {'<div class="hero-badge">' + author + '</div>' if author else ''}
    <h1>{heading}</h1>
    {'<p class="hero-tagline">' + tagline + '</p>' if tagline else ''}
    <a href="#about" class="hero-btn">Explore ↓</a>
  </div>

  {'<section id="about" class="section"><h2 class="section-title">About</h2><div class="body-text">' + body_text + '</div></section>' if body_text else ''}

  {'<div id="cards">' + cards_html + '</div>' if cards_html else ''}

  {'<div id="gallery">' + gallery_html + '</div>' if gallery_html else ''}

  {'<div id="contact">' + contact_html + '</div>' if contact_html else ''}

  {'<div id="links">' + links_html + '</div>' if links_html else ''}

  <footer>{footer_text}</footer>

  {matrix_script}
</body>
</html>
"""
    return html


def _save_html_to_server(html_code, filename):
    os.makedirs(WEB_ROOT, exist_ok=True)
    safe_filename = filename.replace(' ', '_')
    if not safe_filename.endswith('.html'):
        safe_filename += '.html'
    dest = os.path.join(WEB_ROOT, safe_filename)
    try:
        if LINUX:
            import tempfile
            tmp = os.path.join('/tmp', safe_filename)
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(html_code)
            subprocess.run(['sudo', 'cp', tmp, dest], check=True)
            subprocess.run(['sudo', 'chmod', '775', dest], check=True)
            subprocess.run(['sudo', 'chown', 'www-data:www-data', dest], check=True)
        else:
            with open(dest, 'w', encoding='utf-8') as f:
                f.write(html_code)
        return True, safe_filename
    except Exception as e:
        return False, str(e)


def create_html_page():
    clear()

    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext, filedialog

        BG      = "#0a0e14"
        CARD    = "#0d1117"
        CARD2   = "#111820"
        BORDER  = "#1e2d3d"
        ACCENT  = "#00e5ff"
        ACCENT2 = "#1565c0"
        ACCENT3 = "#00c853"
        FG      = "#cdd9e5"
        FG2     = "#768390"
        RED_C   = "#ff1744"
        YEL_C   = "#ffd600"
        GRN_C   = "#00e676"
        PUR_C   = "#d500f9"
        FONT    = ("Consolas", 10) if WINDOWS else ("DejaVu Sans Mono", 10)
        FONT_B  = ("Consolas", 10, "bold") if WINDOWS else ("DejaVu Sans Mono", 10, "bold")
        FONT_H  = ("Consolas", 12, "bold") if WINDOWS else ("DejaVu Sans Mono", 12, "bold")
        FONT_S  = ("Consolas", 9)  if WINDOWS else ("DejaVu Sans Mono", 9)

        THEMES = [
            "Dark Blue", "Midnight", "Forest", "Sunset", "Ocean", "Rose Gold", "White Clean",
            "── HACKER THEMES ──",
            "Matrix", "Cyber Red", "Neon Purple", "Ice Hacker",
            "Blood Gold", "Toxic", "Stealth", "Ghost White"
        ]
        THEME_COLORS = {
            "Dark Blue": "#58a6ff", "Midnight": "#a78bfa", "Forest": "#4ade80",
            "Sunset": "#fb923c", "Ocean": "#38bdf8", "Rose Gold": "#f9a8d4",
            "White Clean": "#3b82f6",
            "Matrix": "#00ff41", "Cyber Red": "#ff0033", "Neon Purple": "#bf00ff",
            "Ice Hacker": "#00e5ff", "Blood Gold": "#ffaa00",
            "Toxic": "#aaff00", "Stealth": "#ff6600", "Ghost White": "#222222",
        }

        root = tk.Tk()
        root.title("SERVER  |  HTML Page Creator  v2.3")
        root.geometry("820x780")
        root.resizable(True, True)
        root.configure(bg=BG)
        root.minsize(720, 650)

        hdr = tk.Frame(root, bg="#001f3f", height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  ▶  HTML PAGE CREATOR  //  SOCIAL TAGS  //  LOCAL IMG UPLOAD",
                 font=FONT_H, bg="#001f3f", fg=ACCENT, anchor="w").pack(side="left", padx=16, pady=16)
        tk.Label(hdr, text="v2.3", font=FONT_S, bg="#001f3f", fg=FG2).pack(side="right", padx=16)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Hacker.TNotebook", background=BG, borderwidth=0)
        style.configure("Hacker.TNotebook.Tab",
                        background=CARD2, foreground=FG2,
                        font=FONT_B, padding=[14, 6])
        style.map("Hacker.TNotebook.Tab",
                  background=[("selected", CARD)],
                  foreground=[("selected", ACCENT)])

        nb = ttk.Notebook(root, style="Hacker.TNotebook")
        nb.pack(fill="both", expand=True, padx=8, pady=(6, 0))

        def make_tab(label):
            frame = tk.Frame(nb, bg=BG)
            nb.add(frame, text=f"  {label}  ")
            canvas = tk.Canvas(frame, bg=BG, highlightthickness=0)
            vsb = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            body = tk.Frame(canvas, bg=BG, padx=20, pady=10)
            bwin = canvas.create_window((0, 0), window=body, anchor="nw")
            body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(bwin, width=e.width))
            canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
            return body

        def sec_lbl(parent, text, color=ACCENT):
            f = tk.Frame(parent, bg=BG)
            f.pack(fill="x", pady=(10, 4))
            tk.Frame(f, bg=color, height=1).pack(fill="x")
            tk.Label(f, text=f"  ▸  {text}", font=FONT_B, bg=BG, fg=color, anchor="w").pack(anchor="w", pady=(4, 0))

        def entry_row(parent, label, default="", width=None):
            r = tk.Frame(parent, bg=BG)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label, font=FONT_S, bg=BG, fg=FG2,
                     width=24, anchor="w").pack(side="left")
            kw = {"width": width} if width else {}
            e = tk.Entry(r, bg=CARD, fg=FG, font=FONT, insertbackground=FG,
                         relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT, **kw)
            e.pack(side="left", fill="x", expand=True, padx=(6, 0), ipady=4)
            if default:
                e.insert(0, default)
            return e

        tab1 = make_tab("📄 Basic")

        sec_lbl(tab1, "PAGE INFORMATION")
        e_title    = entry_row(tab1, "Page Title *",        "My Awesome Website")
        e_filename = entry_row(tab1, "File Name *",         "index")
        e_heading  = entry_row(tab1, "Hero Heading *",      "Welcome to My Website")
        e_tagline  = entry_row(tab1, "Tagline / Subtitle",  "A website made with SERVER TOOL")
        e_author   = entry_row(tab1, "Author / Brand",      "")

        sec_lbl(tab1, "COLOR THEME")
        tfrm = tk.Frame(tab1, bg=BG)
        tfrm.pack(fill="x", pady=4)
        tk.Label(tfrm, text="Theme", font=FONT_S, bg=BG, fg=FG2, width=24, anchor="w").pack(side="left")
        theme_var = tk.StringVar(value="Dark Blue")
        theme_dd  = ttk.Combobox(tfrm, textvariable=theme_var, values=THEMES,
                                  state="readonly", width=24, font=FONT)
        theme_dd.pack(side="left", padx=6)
        preview_lbl = tk.Label(tfrm, text="  ●  Dark Blue", font=FONT_B, bg=BG, fg="#58a6ff")
        preview_lbl.pack(side="left", padx=10)

        def _theme_changed(*a):
            t = theme_var.get()
            if t.startswith("──"):
                theme_var.set("Matrix")
                t = "Matrix"
            c = THEME_COLORS.get(t, ACCENT)
            preview_lbl.config(text=f"  ●  {t}", fg=c)
        theme_dd.bind("<<ComboboxSelected>>", _theme_changed)

        sec_lbl(tab1, "PAGE CONTENT")
        tk.Label(tab1, text="Body / About Text:", font=FONT_S, bg=BG, fg=FG2, anchor="w").pack(anchor="w")
        txt_body = scrolledtext.ScrolledText(
            tab1, bg=CARD, fg=FG, font=FONT, height=5,
            insertbackground=FG, relief="flat",
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT
        )
        txt_body.pack(fill="x", pady=(4, 0))
        txt_body.insert("end", "Write your content here...\n\nThis is the About / Body section.")

        sec_lbl(tab1, "FOOTER")
        e_footer = entry_row(tab1, "Footer Text", "")

        sec_lbl(tab1, "CUSTOM CSS", PUR_C)
        txt_css = scrolledtext.ScrolledText(
            tab1, bg="#050a05", fg="#00ff41", font=("Courier New", 9) if WINDOWS else ("DejaVu Sans Mono", 9),
            height=3, insertbackground="#00ff41", relief="flat",
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT
        )
        txt_css.pack(fill="x", pady=4)
        txt_css.insert("end", "/* Your custom CSS here */\n")

        tab2 = make_tab("🔗 Social Tags")

        sec_lbl(tab2, "OPEN GRAPH / WHATSAPP / FACEBOOK TAGS", "#25d366")
        tk.Label(tab2, text=(
            "Set these tags so your website shows title, description and image preview\n"
            "when shared on WhatsApp, Facebook or Twitter! 🔥"
        ), font=FONT_S, bg=BG, fg=YEL_C, justify="left").pack(anchor="w", pady=(4, 8))

        e_og_url      = entry_row(tab2, "Website URL",       "https://your-site.com")
        e_og_desc     = entry_row(tab2, "Description",       "Check out my amazing website!")
        e_og_sitename = entry_row(tab2, "Site Name",         "")
        e_og_type     = entry_row(tab2, "OG Type",           "website")

        sec_lbl(tab2, "SOCIAL PREVIEW IMAGE", YEL_C)
        tk.Label(tab2, text=(
            "This image will appear as thumbnail when someone shares your link.\n"
            "Option A: Enter URL  |  Option B: Upload image from PC"
        ), font=FONT_S, bg=BG, fg=FG2, justify="left").pack(anchor="w", pady=(2, 6))

        e_og_image = entry_row(tab2, "Image URL (Option A)", "https://your-site.com/og-image.jpg")

        og_img_frame = tk.Frame(tab2, bg=BG)
        og_img_frame.pack(fill="x", pady=4)
        tk.Label(og_img_frame, text="Upload from PC (Option B)", font=FONT_S,
                 bg=BG, fg=FG2, width=24, anchor="w").pack(side="left")
        og_img_path_var = tk.StringVar(value="")
        og_img_lbl = tk.Label(og_img_frame, textvariable=og_img_path_var,
                               font=FONT_S, bg=CARD, fg=GRN_C,
                               width=32, anchor="w", padx=6)
        og_img_lbl.pack(side="left", padx=(6, 8), ipady=4)

        def browse_og_image():
            path = filedialog.askopenfilename(
                title="Select OG Preview Image",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.webp *.svg"), ("All", "*.*")]
            )
            if path:
                og_img_path_var.set(os.path.basename(path))
                og_img_path_var._full_path = path
                e_og_image.delete(0, "end")
                e_og_image.insert(0, f"[PC image: {os.path.basename(path)}]")

        tk.Button(og_img_frame, text="📁 Browse",
                  command=browse_og_image,
                  bg=ACCENT2, fg="white", font=FONT_S,
                  relief="flat", bd=0, padx=12, pady=4,
                  cursor="hand2").pack(side="left")

        og_img_path_var._full_path = ""

        sec_lbl(tab2, "TWITTER CARD", "#1da1f2")
        e_twitter = entry_row(tab2, "Twitter Handle (@user)", "")

        sec_lbl(tab2, "WHATSAPP CLICK-TO-CHAT", "#25d366")
        e_wa_num = entry_row(tab2, "WhatsApp Number",  "+91XXXXXXXXXX")
        e_wa_msg = entry_row(tab2, "Default Message",  "Hi! I visited your website")

        tab3 = make_tab("🖼️ Images")

        sec_lbl(tab3, "GALLERY IMAGES — URL + LOCAL PC UPLOAD", YEL_C)
        tk.Label(tab3, text=(
            "Add images to gallery via URL or directly from your PC!\n"
            "Images uploaded from PC will be copied to the server."
        ), font=FONT_S, bg=BG, fg=FG2, justify="left").pack(anchor="w", pady=(2, 8))

        show_gal_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tab3, text="✅  Add gallery section to page",
                       variable=show_gal_var,
                       bg=BG, fg=FG2, selectcolor=CARD,
                       activebackground=BG, activeforeground=FG, font=FONT).pack(anchor="w", pady=(0, 8))

        tk.Label(tab3, text="Image URLs (ek per line):", font=FONT_S, bg=BG, fg=FG2, anchor="w").pack(anchor="w")
        txt_imgs = scrolledtext.ScrolledText(
            tab3, bg=CARD, fg=FG, font=FONT_S, height=5,
            insertbackground=FG, relief="flat",
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT
        )
        txt_imgs.pack(fill="x", pady=(4, 8))
        txt_imgs.insert("end", "https://example.com/image1.jpg\nhttps://example.com/image2.jpg")

        sec_lbl(tab3, "PC IMAGE UPLOAD (Will be copied to server)", GRN_C)
        local_imgs_frame = tk.Frame(tab3, bg=CARD,
                                    highlightthickness=1, highlightbackground=BORDER)
        local_imgs_frame.pack(fill="x", pady=4)

        local_img_listbox = tk.Listbox(local_imgs_frame, bg=CARD, fg=GRN_C,
                                        font=FONT_S, height=5, relief="flat", bd=0,
                                        selectbackground=ACCENT2)
        local_img_listbox.pack(fill="x", padx=6, pady=6)

        local_img_paths = []

        def add_local_images():
            paths = filedialog.askopenfilenames(
                title="Select Images to Upload",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.webp *.svg *.bmp"), ("All Files", "*.*")]
            )
            for p in paths:
                if p not in local_img_paths:
                    local_img_paths.append(p)
                    local_img_listbox.insert("end", f"  📷  {os.path.basename(p)}")

        def remove_local_image():
            sel = local_img_listbox.curselection()
            if sel:
                idx = sel[0]
                local_img_paths.pop(idx)
                local_img_listbox.delete(idx)

        img_btn_row = tk.Frame(tab3, bg=BG)
        img_btn_row.pack(fill="x", pady=4)
        tk.Button(img_btn_row, text="📁  Add Images from PC",
                  command=add_local_images,
                  bg=ACCENT2, fg="white", font=FONT_S,
                  relief="flat", bd=0, padx=14, pady=6, cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(img_btn_row, text="✕  Remove Selected",
                  command=remove_local_image,
                  bg="#21262d", fg=RED_C, font=FONT_S,
                  relief="flat", bd=0, padx=14, pady=6, cursor="hand2").pack(side="left")

        tk.Label(tab3,
                 text="💡 PC images will be copied to WEB_ROOT and automatically added to gallery.",
                 font=FONT_S, bg=BG, fg=YEL_C, anchor="w", wraplength=650, justify="left").pack(anchor="w", pady=(8, 0))

        tab4 = make_tab("🃏 Cards & Contact")

        sec_lbl(tab4, "FEATURE CARDS")
        show_cards_var = tk.BooleanVar(value=True)
        tk.Checkbutton(tab4, text="✅  Add feature cards section",
                       variable=show_cards_var,
                       bg=BG, fg=FG2, selectcolor=CARD,
                       activebackground=BG, activeforeground=FG, font=FONT).pack(anchor="w")

        cards_frame = tk.Frame(tab4, bg=BG)
        cards_frame.pack(fill="x", pady=4)
        card_entries = []

        def add_card_row(title_val="", desc_val=""):
            r = tk.Frame(cards_frame, bg=CARD2,
                         highlightthickness=1, highlightbackground=BORDER)
            r.pack(fill="x", pady=2)
            tk.Label(r, text="Title:", font=FONT_S, bg=CARD2, fg=FG2, width=6).pack(side="left", padx=(6,0))
            et = tk.Entry(r, bg=CARD, fg=FG, font=FONT_S, relief="flat", bd=0,
                          insertbackground=FG, width=22,
                          highlightthickness=1, highlightbackground=BORDER)
            et.pack(side="left", padx=4, pady=4)
            et.insert(0, title_val)
            tk.Label(r, text="Desc:", font=FONT_S, bg=CARD2, fg=FG2).pack(side="left")
            ed = tk.Entry(r, bg=CARD, fg=FG, font=FONT_S, relief="flat", bd=0,
                          insertbackground=FG,
                          highlightthickness=1, highlightbackground=BORDER)
            ed.pack(side="left", fill="x", expand=True, padx=(4, 6), pady=4)
            ed.insert(0, desc_val)
            def remove():
                card_entries.remove((et, ed))
                r.destroy()
            tk.Button(r, text="✕", command=remove, bg=CARD2, fg=RED_C,
                      font=FONT_S, relief="flat", bd=0, cursor="hand2", padx=6).pack(side="right", padx=4)
            card_entries.append((et, ed))

        add_card_row("⚡ Fast",       "Optimized for speed and performance.")
        add_card_row("🔒 Secure",    "Built with security best practices.")
        add_card_row("📱 Responsive","Looks great on all devices.")

        tk.Button(tab4, text="＋ Add Card",
                  bg=CARD, fg=ACCENT, font=FONT_S, relief="flat", bd=0,
                  padx=12, pady=5, cursor="hand2",
                  command=lambda: add_card_row("Card Title", "Card description.")).pack(anchor="w", pady=(4, 0))

        sec_lbl(tab4, "CONTACT INFO")
        show_contact_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tab4, text="✅  Add contact section",
                       variable=show_contact_var,
                       bg=BG, fg=FG2, selectcolor=CARD,
                       activebackground=BG, activeforeground=FG, font=FONT).pack(anchor="w")
        e_email = entry_row(tab4, "Email", "")
        e_phone = entry_row(tab4, "Phone", "")

        tab5 = make_tab("🔗 Hyperlinks")

        sec_lbl(tab5, "HYPERLINKS SECTION", ACCENT)
        tk.Label(tab5, text=(
            "Add clickable links to your page (portfolio, social media, docs, etc.)\n"
            "Each link opens in a new tab. They appear as styled arrow buttons on the page."
        ), font=FONT_S, bg=BG, fg=FG2, justify="left").pack(anchor="w", pady=(2, 8))

        show_links_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tab5, text="✅  Add hyperlinks section to page",
                       variable=show_links_var,
                       bg=BG, fg=FG2, selectcolor=CARD,
                       activebackground=BG, activeforeground=FG, font=FONT).pack(anchor="w", pady=(0, 8))

        link_entries_frame = tk.Frame(tab5, bg=BG)
        link_entries_frame.pack(fill="x", pady=4)
        link_entries = []

        def add_link_row(label_val="", url_val=""):
            r = tk.Frame(link_entries_frame, bg=CARD2,
                         highlightthickness=1, highlightbackground=BORDER)
            r.pack(fill="x", pady=2)
            tk.Label(r, text="Label:", font=FONT_S, bg=CARD2, fg=FG2, width=7).pack(side="left", padx=(6, 0))
            el = tk.Entry(r, bg=CARD, fg=FG, font=FONT_S, relief="flat", bd=0,
                          insertbackground=FG, width=20,
                          highlightthickness=1, highlightbackground=BORDER)
            el.pack(side="left", padx=4, pady=4)
            el.insert(0, label_val)
            tk.Label(r, text="URL:", font=FONT_S, bg=CARD2, fg=FG2).pack(side="left")
            eu = tk.Entry(r, bg=CARD, fg=FG, font=FONT_S, relief="flat", bd=0,
                          insertbackground=FG,
                          highlightthickness=1, highlightbackground=BORDER)
            eu.pack(side="left", fill="x", expand=True, padx=(4, 6), pady=4)
            eu.insert(0, url_val)
            def remove_link():
                link_entries.remove((el, eu))
                r.destroy()
            tk.Button(r, text="✕", command=remove_link, bg=CARD2, fg=RED_C,
                      font=FONT_S, relief="flat", bd=0, cursor="hand2", padx=6).pack(side="right", padx=4)
            link_entries.append((el, eu))

        add_link_row("GitHub", "https://github.com/")
        add_link_row("Portfolio", "https://yoursite.com")
        add_link_row("Instagram", "https://instagram.com/")

        tk.Button(tab5, text="＋ Add Link",
                  bg=CARD, fg=ACCENT, font=FONT_S, relief="flat", bd=0,
                  padx=12, pady=5, cursor="hand2",
                  command=lambda: add_link_row("Link Label", "https://")).pack(anchor="w", pady=(4, 0))

        tk.Label(tab5,
                 text="💡 Links appear as styled buttons on your page with ↗ arrow icon.",
                 font=FONT_S, bg=BG, fg=YEL_C, anchor="w", wraplength=650).pack(anchor="w", pady=(12, 0))

        status_frame = tk.Frame(root, bg="#0d1117",
                                highlightthickness=1, highlightbackground=BORDER)
        status_frame.pack(fill="x", padx=8, pady=(4, 0))
        status_var = tk.StringVar(value="  Ready — Fill details and click [ Create & Upload ]")
        tk.Label(status_frame, textvariable=status_var, font=FONT_S,
                 bg="#0d1117", fg=FG2, anchor="w", padx=8, pady=6).pack(side="left")

        url_var = tk.StringVar(value="")
        url_lbl = tk.Label(status_frame, textvariable=url_var, font=FONT_B,
                           bg="#0d1117", fg=GRN_C, anchor="e", padx=8, pady=6,
                           cursor="hand2")
        url_lbl.pack(side="right")

        btn_bar = tk.Frame(root, bg="#060a0f", height=52)
        btn_bar.pack(fill="x", padx=8, pady=(4, 8))
        btn_bar.pack_propagate(False)

        def hbtn(parent, text, cmd, bg, fg="white"):
            b = tk.Button(parent, text=text, command=cmd,
                          bg=bg, fg=fg, font=FONT_B,
                          relief="flat", bd=0, padx=18, pady=10,
                          activebackground=bg, activeforeground=fg, cursor="hand2",
                          highlightthickness=1, highlightbackground=bg)
            b.pack(side="left", padx=(0, 6), pady=6)
            return b

        def do_create():
            title_val    = e_title.get().strip()
            filename_val = e_filename.get().strip()
            heading_val  = e_heading.get().strip()

            if not title_val or not filename_val or not heading_val:
                messagebox.showwarning("Missing Fields",
                    "Page Title, File Name, and Hero Heading are required!", parent=root)
                return

            status_var.set("  ⏳  Working...")
            root.update_idletasks()

            uploaded_server_urls = []
            for img_path in local_img_paths:
                url_path, ok = image_to_server(img_path)
                if ok:
                    uploaded_server_urls.append(url_path)
                else:
                    b64 = image_to_base64_src(img_path)
                    if b64:
                        uploaded_server_urls.append(b64)

            imgs_raw = txt_imgs.get("1.0", "end").strip()
            url_imgs = [u.strip() for u in imgs_raw.splitlines()
                        if u.strip() and "example.com" not in u]
            all_images = url_imgs + uploaded_server_urls

            og_image_val = e_og_image.get().strip()
            og_full_path = getattr(og_img_path_var, '_full_path', '')
            if og_full_path and os.path.isfile(og_full_path):
                og_url, ok2 = image_to_server(og_full_path)
                if ok2:
                    local_ip = get_local_ip()
                    og_image_val = f"http://{local_ip}{og_url}"
                else:
                    og_image_val = image_to_base64_src(og_full_path) or og_image_val

            cards_list = []
            for et, ed in card_entries:
                ct = et.get().strip(); cd = ed.get().strip()
                if ct or cd:
                    cards_list.append({"title": ct, "desc": cd})

            links_list = []
            for el, eu in link_entries:
                ll = el.get().strip(); lu = eu.get().strip()
                if ll and lu:
                    links_list.append({"label": ll, "url": lu, "open_new": True})

            data = {
                "title":          title_val,
                "heading":        heading_val,
                "tagline":        e_tagline.get().strip(),
                "body_text":      txt_body.get("1.0", "end").strip(),
                "theme":          theme_var.get(),
                "author":         e_author.get().strip(),
                "show_contact":   show_contact_var.get(),
                "email":          e_email.get().strip(),
                "phone":          e_phone.get().strip(),
                "show_gallery":   show_gal_var.get(),
                "image_urls":     all_images,
                "show_cards":     show_cards_var.get(),
                "card_data":      cards_list,
                "show_links":     show_links_var.get(),
                "link_data":      links_list,
                "footer_text":    e_footer.get().strip() or f"© {datetime.datetime.now().year} {e_author.get().strip() or title_val}",
                "custom_css":     txt_css.get("1.0", "end").strip(),
                "social_url":     e_og_url.get().strip(),
                "social_desc":    e_og_desc.get().strip(),
                "social_image":   og_image_val,
                "social_twitter": e_twitter.get().strip(),
                "social_site_name": e_og_sitename.get().strip() or title_val,
                "social_type":    e_og_type.get().strip() or "website",
                "show_social":    True,
                "whatsapp_number": e_wa_num.get().strip(),
                "whatsapp_msg":   e_wa_msg.get().strip(),
            }

            status_var.set("  ⏳  Generating HTML...")
            root.update_idletasks()
            html_code = _generate_html_code(data)

            status_var.set("  📤  Saving to server...")
            root.update_idletasks()
            ok, result = _save_html_to_server(html_code, filename_val)

            if ok:
                local_ip = get_local_ip()
                local_url = f"http://localhost/{result}"
                lan_url   = f"http://{local_ip}/{result}"
                url_var.set(f"✅  {local_url}")
                status_var.set(f"  ✅  '{result}' created & uploaded!")

                if LINUX:
                    subprocess.run(['sudo', 'service', 'apache2', 'restart'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif TERMUX:
                    subprocess.run(['apachectl', 'restart'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                log_event("html_pages_created", result)
                log_event("files_uploaded", result)
                url_lbl.bind("<Button-1>", lambda _e: webbrowser.open(local_url))

                messagebox.showinfo("Page Created! 🎉",
                    f"✅  HTML page created & uploaded!\n\n"
                    f"📄  File    : {result}\n"
                    f"🌐  Local   : {local_url}\n"
                    f"📡  LAN     : {lan_url}\n\n"
                    f"🔗  Social tags ready!\n"
                    f"📷  Local images uploaded: {len(local_img_paths)}\n\n"
                    f"💡  Run Option 09 to generate a secure link!",
                    parent=root)
            else:
                status_var.set(f"  ❌  Error: {result}")
                messagebox.showerror("Upload Failed", f"Error:\n{result}", parent=root)

        def do_preview():
            title_val   = e_title.get().strip() or "Preview"
            heading_val = e_heading.get().strip() or "Preview"
            imgs_raw    = txt_imgs.get("1.0", "end").strip()
            url_imgs    = [u.strip() for u in imgs_raw.splitlines()
                           if u.strip() and "example.com" not in u]

            b64_imgs = []
            for p in local_img_paths:
                b64 = image_to_base64_src(p)
                if b64:
                    b64_imgs.append(b64)

            cards_list = []
            for et, ed in card_entries:
                ct = et.get().strip(); cd = ed.get().strip()
                if ct or cd:
                    cards_list.append({"title": ct, "desc": cd})

            links_list = []
            for el, eu in link_entries:
                ll = el.get().strip(); lu = eu.get().strip()
                if ll and lu:
                    links_list.append({"label": ll, "url": lu, "open_new": True})

            data = {
                "title":          title_val,
                "heading":        heading_val,
                "tagline":        e_tagline.get().strip(),
                "body_text":      txt_body.get("1.0", "end").strip(),
                "theme":          theme_var.get(),
                "author":         e_author.get().strip(),
                "show_contact":   show_contact_var.get(),
                "email":          e_email.get().strip(),
                "phone":          e_phone.get().strip(),
                "show_gallery":   show_gal_var.get(),
                "image_urls":     url_imgs + b64_imgs,
                "show_cards":     show_cards_var.get(),
                "card_data":      cards_list,
                "show_links":     show_links_var.get(),
                "link_data":      links_list,
                "footer_text":    e_footer.get().strip() or title_val,
                "custom_css":     txt_css.get("1.0", "end").strip(),
                "social_url":     e_og_url.get().strip(),
                "social_desc":    e_og_desc.get().strip(),
                "social_image":   e_og_image.get().strip(),
                "social_twitter": e_twitter.get().strip(),
                "social_site_name": e_og_sitename.get().strip() or title_val,
                "social_type":    "website",
                "show_social":    True,
                "whatsapp_number": e_wa_num.get().strip(),
                "whatsapp_msg":   e_wa_msg.get().strip(),
            }
            html_code = _generate_html_code(data)
            tmp_path = os.path.join(os.path.expanduser('~'), '_server_preview_.html')
            try:
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    f.write(html_code)
                webbrowser.open(f'file:///{tmp_path}' if WINDOWS else f'file://{tmp_path}')
                status_var.set("  👁️  Preview opened in browser!")
            except Exception as ex:
                messagebox.showerror("Preview Error", str(ex), parent=root)

        hbtn(btn_bar, "⬆  Create & Upload",    do_create,       "#00695c")
        hbtn(btn_bar, "👁  Preview",            do_preview,       ACCENT2)
        hbtn(btn_bar, "✕  Close",              root.destroy,      "#1c2128", FG2)

        tk.Label(btn_bar,
                 text="💡 Option 09 → Cloudflare Secure Link  |  Social tags auto-added ✓",
                 font=FONT_S, bg="#060a0f", fg=YEL_C).pack(side="right", padx=16)

        root.mainloop()

    except ImportError:
        clear()
        print(BLUE + '\n  ╔══════════════════════════════════════════════════╗')
        print('  ║       HTML Page Creator — Terminal Mode          ║')
        print('  ╚══════════════════════════════════════════════════╝' + RESET)
        print()

        def _ask(prompt, default=""):
            val = input(f"  {YELLOW}{prompt}{f' [{default}]' if default else ''}: {RESET}").strip()
            return val if val else default

        title_val    = _ask("Page Title",          "My Website")
        filename_val = _ask("File Name (no .html)", "index")
        heading_val  = _ask("Hero Heading",         "Welcome")
        tagline_val  = _ask("Tagline",              "")
        author_val   = _ask("Author / Brand",       "")
        body_val     = _ask("Body Text",            "Your content here.")
        og_desc      = _ask("Social Description",   tagline_val or "My website")
        og_url       = _ask("Website URL (for tags)", "")
        wa_num       = _ask("WhatsApp Number (optional)", "")

        slow("\n  Available Themes:", YELLOW)
        themes = [
            "Dark Blue", "Midnight", "Forest", "Sunset", "Ocean", "Rose Gold", "White Clean",
            "Matrix", "Cyber Red", "Neon Purple", "Ice Hacker", "Blood Gold", "Toxic", "Stealth"
        ]
        for i, t in enumerate(themes, 1):
            print(f"  {BLUE}[{i:2d}]{RESET}  {t}")
        try:
            ti = int(input(f"\n  {YELLOW}Choose theme [1]: {RESET}").strip() or "1") - 1
            theme_val = themes[max(0, min(ti, len(themes)-1))]
        except ValueError:
            theme_val = "Dark Blue"

        email_val = _ask("Email (optional)", "")
        phone_val = _ask("Phone (optional)", "")
        footer_val = _ask("Footer Text", f"© {datetime.datetime.now().year} {author_val or title_val}")
        show_contact = bool(email_val or phone_val or wa_num)

        card_data_list = []
        add_c = input(f"  {YELLOW}Add feature cards? (y/n) [y]: {RESET}").strip().lower()
        if add_c != 'n':
            card_data_list = [
                {"title": "⚡ Fast",       "desc": "Optimized for speed."},
                {"title": "🔒 Secure",     "desc": "Security best practices."},
                {"title": "📱 Responsive", "desc": "Works on all devices."},
            ]

        data = {
            "title": title_val, "heading": heading_val, "tagline": tagline_val,
            "body_text": body_val, "theme": theme_val, "author": author_val,
            "show_contact": show_contact, "email": email_val, "phone": phone_val,
            "show_gallery": False, "image_urls": [],
            "show_cards": bool(card_data_list), "card_data": card_data_list,
            "show_links": False, "link_data": [],
            "footer_text": footer_val, "custom_css": "",
            "social_url": og_url, "social_desc": og_desc,
            "social_image": "", "social_twitter": "",
            "social_site_name": title_val, "social_type": "website",
            "show_social": bool(og_url or og_desc),
            "whatsapp_number": wa_num, "whatsapp_msg": f"Hi! I visited {title_val}",
        }

        slow("\n  Generating HTML...", YELLOW)
        html_code = _generate_html_code(data)

        slow("  Saving to server...", YELLOW)
        ok, result = _save_html_to_server(html_code, filename_val)

        if ok:
            local_ip = get_local_ip()
            log_event("html_pages_created", result)
            log_event("files_uploaded", result)
            if LINUX:
                subprocess.run(['sudo', 'service', 'apache2', 'restart'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif TERMUX:
                subprocess.run(['apachectl', 'restart'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            slow(f"\n  ✅  Page created: {result}", GREEN)
            slow(f"  🌐  Local:  http://localhost/{result}", BLUE)
            slow(f"  📡  LAN:    http://{local_ip}/{result}", BLUE)
            slow(f"  🔗  Social tags have been added!", GREEN)
            slow(f"  💡  Run Option 09 to generate a secure link!", YELLOW)
        else:
            slow(f"  ❌  Error: {result}", RED)

        input(GREEN + "\n  Press Enter to return to main menu..." + RESET)




def upload_file_gui():
    try:
        import tkinter as tk
        from tkinter import filedialog, ttk, messagebox

        selected_paths = []
        uploaded_names = []

        root = tk.Tk()
        root.title("SERVER  |  Upload File & Directory Manager")
        root.geometry("660x500")
        root.resizable(False, False)
        root.configure(bg="#0d1117")

        BG      = "#0d1117"
        CARD    = "#161b22"
        BORDER  = "#30363d"
        ACCENT  = "#238636"
        ACCENT2 = "#1f6feb"
        ACCENT3 = "#9e6a03"
        FG      = "#e6edf3"
        FG2     = "#8b949e"
        RED_C   = "#f85149"
        GREEN_C = "#3fb950"
        FONT    = ("Segoe UI", 10) if WINDOWS else ("DejaVu Sans", 10)
        FONT_B  = ("Segoe UI", 10, "bold") if WINDOWS else ("DejaVu Sans", 10, "bold")
        FONT_H  = ("Segoe UI", 12, "bold") if WINDOWS else ("DejaVu Sans", 12, "bold")
        FONT_S  = ("Segoe UI", 9)  if WINDOWS else ("DejaVu Sans", 9)

        header = tk.Frame(root, bg=ACCENT2, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="  SERVER  |  Upload File & Directory Manager",
                 font=FONT_H, bg=ACCENT2, fg="white", anchor="w").pack(side="left", padx=14, pady=14)

        body = tk.Frame(root, bg=BG, padx=20, pady=12)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Selected Files & Folders", font=FONT_B, bg=BG, fg=FG).pack(anchor="w")
        tk.Label(body, text="Browse files or folders to upload to your web server.",
                 font=FONT, bg=BG, fg=FG2).pack(anchor="w", pady=(2, 8))

        list_frame = tk.Frame(body, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        list_frame.pack(fill="both", expand=True)

        sb = tk.Scrollbar(list_frame, bg=CARD, troughcolor=CARD)
        sb.pack(side="right", fill="y")

        listbox = tk.Listbox(list_frame, bg=CARD, fg=FG, font=FONT,
                             selectbackground=ACCENT2, selectforeground="white",
                             activestyle="none", relief="flat", bd=0,
                             yscrollcommand=sb.set, height=10)
        listbox.pack(fill="both", expand=True, padx=6, pady=6)
        sb.config(command=listbox.yview)

        status_var = tk.StringVar(value="No files or folders selected.")
        tk.Label(body, textvariable=status_var, font=FONT_S, bg=BG, fg=FG2, anchor="w").pack(anchor="w", pady=(6, 2))

        progress_var = tk.DoubleVar(value=0)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("green.Horizontal.TProgressbar", troughcolor=CARD, background=GREEN_C, thickness=7)
        ttk.Progressbar(body, variable=progress_var, maximum=100,
                        style="green.Horizontal.TProgressbar").pack(fill="x", pady=(0, 10))

        info_frame = tk.Frame(body, bg=CARD, highlightbackground="#30363d", highlightthickness=1)
        info_frame.pack(fill="x", pady=(0, 10))

        info_header = tk.Frame(info_frame, bg="#0d2137")
        info_header.pack(fill="x")
        tk.Label(info_header, text="  📂  Uploaded Files — Local URLs",
                 font=FONT_B, bg="#0d2137", fg=ACCENT2, anchor="w").pack(side="left", padx=10, pady=5)

        info_text = tk.Text(info_frame, bg=CARD, fg=GREEN_C, font=FONT_S,
                            height=3, relief="flat", bd=0, state="disabled", wrap="word")
        info_text.pack(fill="x", padx=10, pady=(4, 8))

        def update_info_links():
            info_text.config(state="normal")
            info_text.delete("1.0", "end")
            local_ip = get_local_ip()
            for name in uploaded_names:
                url = f"http://localhost/{name}"
                url_lan = f"http://{local_ip}/{name}"
                info_text.insert("end", f"  ➜  {url}   |   LAN: {url_lan}\n")
            info_text.config(state="disabled")

        def browse_files():
            paths = filedialog.askopenfilenames(
                title="Select files to upload",
                filetypes=[
                    ("Web Files", "*.php *.html *.htm *.js *.css *.json *.xml *.txt *.png *.jpg *.gif *.svg"),
                    ("All Files", "*.*")
                ]
            )
            for p in paths:
                if p not in selected_paths:
                    selected_paths.append(p)
                    listbox.insert("end", f"  📄  {os.path.basename(p)}")
            status_var.set(f"{len(selected_paths)} item(s) ready.")
            progress_var.set(0)

        def browse_dir():
            folder = filedialog.askdirectory(title="Select a folder to upload")
            if folder and folder not in selected_paths:
                selected_paths.append(folder)
                listbox.insert("end", f"  📁  {os.path.basename(folder)}/  [folder]")
            status_var.set(f"{len(selected_paths)} item(s) ready.")
            progress_var.set(0)

        def clear_list():
            selected_paths.clear()
            listbox.delete(0, "end")
            uploaded_names.clear()
            status_var.set("No files or folders selected.")
            progress_var.set(0)
            info_text.config(state="normal")
            info_text.delete("1.0", "end")
            info_text.config(state="disabled")

        def copy_path(src, dest_dir):
            name = os.path.basename(src)
            safe_name = name.replace(' ', '_')
            if os.path.isdir(src):
                dest = os.path.join(dest_dir, safe_name)
                if LINUX:
                    r = subprocess.run(['sudo', 'cp', '-r', src, dest], capture_output=True, text=True)
                    if r.returncode == 0:
                        subprocess.run(['sudo', 'chmod', '-R', '775', dest], capture_output=True)
                        subprocess.run(['sudo', 'chown', '-R', 'www-data:www-data', dest], capture_output=True)
                        return True, safe_name
                    return False, name
                else:
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest)
                    return True, safe_name
            else:
                dest = os.path.join(dest_dir, safe_name)
                if LINUX:
                    r = subprocess.run(['sudo', 'cp', src, dest], capture_output=True, text=True)
                    if r.returncode == 0:
                        subprocess.run(['sudo', 'chmod', '775', dest], capture_output=True)
                        subprocess.run(['sudo', 'chown', 'www-data:www-data', dest], capture_output=True)
                        return True, safe_name
                    return False, name
                else:
                    shutil.copy2(src, dest)
                    return True, safe_name

        def do_upload():
            if not selected_paths:
                messagebox.showwarning("Nothing Selected", "Please select at least one file or folder first.", parent=root)
                return
            os.makedirs(WEB_ROOT, exist_ok=True)
            uploaded_names.clear()
            total, success = len(selected_paths), 0
            for i, fp in enumerate(selected_paths, 1):
                orig_name = os.path.basename(fp)
                status_var.set(f"Uploading {'folder' if os.path.isdir(fp) else 'file'}: {orig_name}  ({i}/{total})")
                root.update_idletasks()
                try:
                    ok, final_name = copy_path(fp, WEB_ROOT)
                    if ok:
                        success += 1
                        uploaded_names.append(final_name + ('/' if os.path.isdir(fp) else ''))
                        listbox.itemconfig(i - 1, fg=GREEN_C)
                    else:
                        listbox.itemconfig(i - 1, fg=RED_C)
                except Exception:
                    listbox.itemconfig(i - 1, fg=RED_C)
                progress_var.set((i / total) * 100)
                root.update_idletasks()
                time.sleep(0.12)

            if success > 0:
                log_event("files_uploaded", f"{success} item(s)")
                if LINUX:
                    subprocess.run(['sudo', 'service', 'apache2', 'restart'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif TERMUX:
                    subprocess.run(['apachectl', 'restart'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                update_info_links()

            failed = total - success
            status_var.set(f"✅  Done — {success}/{total} uploaded.")
            msg = f"✅  {success} item(s) uploaded to:\n{WEB_ROOT}"
            if failed:
                msg += f"\n\n❌  {failed} item(s) failed."
            msg += f"\n\n🌐  Share via Cloudflare tunnel:\n   Main menu > Option 09"
            messagebox.showinfo("Upload Complete", msg, parent=root)

        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(fill="x")

        def btn(parent, text, cmd, bg, fg="white"):
            b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                          font=FONT_B, relief="flat", bd=0, padx=14, pady=8,
                          activebackground=bg, activeforeground=fg, cursor="hand2")
            b.pack(side="left", padx=(0, 8))
            return b

        btn(btn_frame, "📄  Browse Files",  browse_files, ACCENT2)
        btn(btn_frame, "📁  Browse Folder", browse_dir,   ACCENT3)
        btn(btn_frame, "⬆  Upload Now",     do_upload,    ACCENT)
        btn(btn_frame, "✕  Clear",          clear_list,   "#21262d", FG2)

        tk.Label(body, text=f"Web Root:  {WEB_ROOT}", font=FONT_S,
                 bg=BG, fg=FG2).pack(anchor="w", pady=(8, 0))
        tk.Label(body, text="💡 Tip: After uploading files, start Cloudflare tunnel using Option 09!", font=FONT_S,
                 bg=BG, fg="#e3b341").pack(anchor="w", pady=(2, 0))

        root.protocol("WM_DELETE_WINDOW", root.destroy)
        root.mainloop()

    except ImportError:
        slow('tkinter not available. Enter file/folder path manually:', YELLOW)
        path = input(YELLOW + 'Path: ' + RESET).strip().strip("'\"")
        if path and os.path.exists(path):
            try:
                os.makedirs(WEB_ROOT, exist_ok=True)
                name = os.path.basename(path)
                safe_name = name.replace(' ', '_')
                dest = os.path.join(WEB_ROOT, safe_name)
                if os.path.isdir(path):
                    if LINUX:
                        subprocess.run(['sudo', 'cp', '-r', path, dest], check=True)
                        subprocess.run(['sudo', 'chmod', '-R', '775', dest], check=True)
                        subprocess.run(['sudo', 'chown', '-R', 'www-data:www-data', dest], check=True)
                    else:
                        if os.path.exists(dest):
                            shutil.rmtree(dest)
                        shutil.copytree(path, dest)
                    log_event("files_uploaded", f"folder:{safe_name}")
                    slow(f'Folder uploaded: {safe_name}', GREEN)
                    slow(f'http://localhost/{safe_name}/', BLUE)
                else:
                    if LINUX:
                        subprocess.run(['sudo', 'cp', path, dest], check=True)
                        subprocess.run(['sudo', 'chmod', '775', dest], check=True)
                        subprocess.run(['sudo', 'chown', 'www-data:www-data', dest], check=True)
                    else:
                        shutil.copy2(path, dest)
                    log_event("files_uploaded", safe_name)
                    slow(f'Uploaded: {safe_name}', GREEN)
                    slow(f'http://localhost/{safe_name}', BLUE)
            except Exception as e:
                slow(f'Error: {e}', RED)
        else:
            slow('Path not found.', RED)
        input(GREEN + "\nPress Enter to return to main menu..." + RESET)

def upload_file():
    clear()
    upload_file_gui()

def list_files():
    clear()
    slow(f'Contents of {WEB_ROOT}:', YELLOW)
    try:
        entries = os.listdir(WEB_ROOT) if os.path.exists(WEB_ROOT) else []
        if entries:
            dirs  = sorted([e for e in entries if os.path.isdir(os.path.join(WEB_ROOT, e))])
            files = sorted([e for e in entries if os.path.isfile(os.path.join(WEB_ROOT, e))])
            print()
            for d in dirs:
                try:
                    size_info = f'  [{sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(os.path.join(WEB_ROOT, d)) for f in fs) // 1024} KB]'
                except Exception:
                    size_info = ''
                print(YELLOW + f'  📁  {d}/{size_info}' + RESET)
            for f in files:
                try:
                    size_info = f'  [{os.path.getsize(os.path.join(WEB_ROOT, f)) // 1024} KB]'
                except Exception:
                    size_info = ''
                print(WHITE + f'  📄  {f}{size_info}' + RESET)
            print()
            slow(f'  Total: {len(dirs)} folder(s),  {len(files)} file(s)', GREY)
        else:
            slow('  (empty — no files or folders)', GREY)
    except Exception as e:
        slow(f'Error: {str(e)}', RED)
    input(GREEN + "\nPress Enter to return to main menu..." + RESET)

def delete_file():
    while True:
        clear()
        slow(f'  Contents of {WEB_ROOT}:', YELLOW)
        print()

        try:
            entries = sorted(os.listdir(WEB_ROOT)) if os.path.exists(WEB_ROOT) else []
        except Exception as e:
            slow(f'  Error listing: {str(e)}', RED)
            input(GREEN + "\nPress Enter to return to main menu..." + RESET)
            return

        if not entries:
            slow('  (empty — no files or folders)', GREY)
            input(GREEN + "\nPress Enter to return to main menu..." + RESET)
            return

        for i, entry in enumerate(entries, 1):
            full = os.path.join(WEB_ROOT, entry)
            if os.path.isdir(full):
                try:
                    size = sum(
                        os.path.getsize(os.path.join(r, f))
                        for r, _, fs in os.walk(full) for f in fs
                    ) // 1024
                    size_str = f'{size} KB'
                except Exception:
                    size_str = ''
                print(f'  {BLUE}[{WHITE}{i:2d}{BLUE}]{RESET}  {YELLOW}📁  {entry}/{RESET}  {GREY}{size_str}{RESET}')
            else:
                try:
                    size_str = f'{os.path.getsize(full) // 1024} KB'
                except Exception:
                    size_str = ''
                print(f'  {BLUE}[{WHITE}{i:2d}{BLUE}]{RESET}  {WHITE}📄  {entry}{RESET}  {GREY}{size_str}{RESET}')

        print()
        slow('  💡 Enter one or more numbers (e.g. 1  or  1,3,5  or  2-4)', GREY)
        raw = input(PUR + '  Select number(s) to delete (Enter = cancel): ' + RESET).strip()

        if not raw:
            slow('  Cancelled.', YELLOW)
            input(GREEN + "\nPress Enter to return to main menu..." + RESET)
            return

        selected_indices = set()
        try:
            for part in raw.replace(' ', '').split(','):
                if '-' in part:
                    a, b = part.split('-', 1)
                    selected_indices.update(range(int(a), int(b) + 1))
                else:
                    selected_indices.add(int(part))
        except ValueError:
            slow('  ❌  Invalid input. Please enter numbers only.', RED)
            input(GREEN + "\nPress Enter to try again..." + RESET)
            continue

        valid   = sorted(i for i in selected_indices if 1 <= i <= len(entries))
        invalid = selected_indices - set(valid)

        if not valid:
            slow('  ❌  No valid numbers selected.', RED)
            input(GREEN + "\nPress Enter to try again..." + RESET)
            continue

        if invalid:
            slow(f'  ⚠  Ignored out-of-range numbers: {sorted(invalid)}', YELLOW)

        to_delete = [entries[i - 1] for i in valid]
        print()
        slow('  Selected for deletion:', RED)
        for name in to_delete:
            full = os.path.join(WEB_ROOT, name)
            icon = '📁' if os.path.isdir(full) else '📄'
            print(f'    {RED}{icon}  {name}{RESET}')

        print()
        confirm = input(RED + f'  Delete {len(to_delete)} item(s)? (y/n): ' + RESET).strip().lower()

        if confirm != 'y':
            slow('  Deletion cancelled.', YELLOW)
            input(GREEN + "\nPress Enter to return to main menu..." + RESET)
            return

        print()
        success_count = 0
        for name in to_delete:
            fp     = os.path.join(WEB_ROOT, name)
            is_dir = os.path.isdir(fp)
            kind   = 'folder' if is_dir else 'file'
            try:
                if LINUX:
                    cmd    = ['sudo', 'rm', '-rf', fp] if is_dir else ['sudo', 'rm', fp]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    ok     = result.returncode == 0
                    err    = result.stderr.strip()
                else:
                    if is_dir:
                        shutil.rmtree(fp)
                    else:
                        os.remove(fp)
                    ok, err = True, ''

                if ok:
                    log_event("files_deleted", name)
                    success_count += 1
                    slow(f'  ✅  Deleted {kind}: {name}', GREEN)
                else:
                    slow(f'  ❌  Error deleting "{name}": {err}', RED)

            except Exception as e:
                slow(f'  ❌  Exception deleting "{name}": {str(e)}', RED)

        print()
        slow(f'  Done — {success_count}/{len(to_delete)} item(s) deleted.', GREEN if success_count == len(to_delete) else YELLOW)

        again = input(PUR + '  Delete more files? (y/n): ' + RESET).strip().lower()
        if again != 'y':
            input(GREEN + "\nPress Enter to return to main menu..." + RESET)
            return

def open_server_page():
    clear()
    slow('Opening server page in browser...', YELLOW)
    try:
        webbrowser.open('http://localhost')
        log_event("link_opens", "localhost")
        slow('Server page opened.', GREEN)
    except Exception as e:
        slow(f'Error: {str(e)}', RED)
    input(GREEN + "\nPress Enter to return to main menu..." + RESET)

def share_server_link():
    clear()
    slow('Fetching IPs...', YELLOW)
    local_ip  = get_local_ip()
    public_ip = get_public_ip()
    log_event("link_opens", f"shared:{local_ip}")
    slow(f'Local  IP : http://{local_ip}', BLUE)
    if public_ip:
        slow(f'Public IP : http://{public_ip}', BLUE)
        slow('Note: Port 80 must be open in firewall/router for public access.', YELLOW)
    else:
        slow('Unable to fetch Public IP. Check your internet connection.', RED)
    input(GREEN + "\nPress Enter to return to main menu..." + RESET)

def create_cloudflared_link():
    clear()
    print(BLUE + '\n  ╔══════════════════════════════════════════════════╗')
    print('  ║       Generate Secure Link — Cloudflare          ║')
    print('  ╚══════════════════════════════════════════════════╝' + RESET)
    print()

    cloudflared_cmd = find_cloudflared()

    if not cloudflared_cmd:
        print(RED + '\n  cloudflared Not Found!' + RESET)
        print()
        if WINDOWS:
            slow('  To install: winget install Cloudflare.cloudflared', YELLOW)
        slow('  Or run Option 01 for auto install', GREY)
        print()
        choice = input(f'  {YELLOW}Install now? (y/n): {RESET}').strip().lower()
        if choice == 'y':
            ok = install_cloudflared_auto()
            if ok:
                cloudflared_cmd = find_cloudflared()
                if not cloudflared_cmd:
                    slow('  Installed but path not found. Please restart.', YELLOW)
                    input(GREEN + "\n  Press Enter to return to main menu..." + RESET)
                    return
            else:
                slow('  Install failed. Try Option 01.', RED)
                input(GREEN + "\n  Press Enter to return to main menu..." + RESET)
                return
        else:
            input(GREEN + "  Press Enter to return to main menu..." + RESET)
            return

    if not is_apache_running():
        slow('  ⚠  WARNING: Apache server is NOT RUNNING!', YELLOW)
        go = input(f'  {YELLOW}Start tunnel anyway? (y/n): {RESET}').strip().lower()
        if go != 'y':
            input(GREEN + "\n  Press Enter to return to main menu..." + RESET)
            return
        print()

    try:
        entries = os.listdir(WEB_ROOT) if os.path.exists(WEB_ROOT) else []
    except Exception:
        entries = []

    dirs  = sorted([e for e in entries if os.path.isdir(os.path.join(WEB_ROOT, e))])
    files = sorted([e for e in entries if os.path.isfile(os.path.join(WEB_ROOT, e))])
    all_entries = dirs + files

    slow(f'  Files in: {WEB_ROOT}', YELLOW)
    print()

    if not all_entries:
        slow('  (empty — no files uploaded yet)', GREY)
        print()
        chosen_path = ''
        chosen_name = 'Entire Server'
    else:
        print(f'  {BLUE}[{WHITE} 0 {BLUE}]{RESET}  {GREEN}🌐  Entire Server Root  (host everything){RESET}')
        print()
        for i, entry in enumerate(all_entries, 1):
            full = os.path.join(WEB_ROOT, entry)
            if os.path.isdir(full):
                try:
                    size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(full) for f in fs) // 1024
                    size_str = f'{size} KB'
                except Exception:
                    size_str = ''
                print(f'  {BLUE}[{WHITE}{i:2d}{BLUE}]{RESET}  {YELLOW}📁  {entry}/{RESET}  {GREY}{size_str}{RESET}')
            else:
                try:
                    size_str = f'{os.path.getsize(full) // 1024} KB'
                except Exception:
                    size_str = ''
                print(f'  {BLUE}[{WHITE}{i:2d}{BLUE}]{RESET}  {WHITE}📄  {entry}{RESET}  {GREY}{size_str}{RESET}')

        print()
        try:
            choice = input(PUR + '  Choose number to host (0 = entire server): ' + RESET).strip()
            num = int(choice)
            if num == 0:
                chosen_path = ''
                chosen_name = 'Entire Server'
            elif 1 <= num <= len(all_entries):
                chosen_name = all_entries[num - 1]
                chosen_path = chosen_name
            else:
                slow('  Invalid. Using entire server.', YELLOW)
                chosen_path = ''
                chosen_name = 'Entire Server'
        except (ValueError, Exception):
            chosen_path = ''
            chosen_name = 'Entire Server'

        if chosen_path and ' ' in chosen_path:
            safe_name, was_renamed = sanitize_name(chosen_path)
            if was_renamed:
                slow(f'  ✅ Auto-fix: "{chosen_path}" → "{safe_name}"', GREEN)
                chosen_path = safe_name
                chosen_name = safe_name
            elif safe_name != chosen_path:
                slow(f'  ℹ  Using safe name: "{safe_name}"', YELLOW)
                chosen_path = safe_name
                chosen_name = safe_name

        print()
        slow(f'  Selected: {chosen_name}', GREEN)

    print()
    slow('  Please wait... (30-60 seconds)', GREY)

    log_event("tunnel_sessions", chosen_path or "root")

    import re as _re

    detected_url = [None]
    tunnel_proc  = [None]

    def _run_tunnel():
        try:
            cmd = f'{cloudflared_cmd} tunnel --url http://127.0.0.1:80'
            proc = subprocess.Popen(
                cmd, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            tunnel_proc[0] = proc
            for line in proc.stdout:
                match = _re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
                if match and not detected_url[0]:
                    base_url      = match.group(0)
                    detected_url[0] = base_url
                    direct_link   = f"{base_url}/{chosen_path}" if chosen_path else base_url

                    print()
                    print(BLUE + '  ╔' + '═' * 56 + '╗' + RESET)
                    print(BLUE + '  ║' + WHITE + '  🎉  YOUR LINK IS READY!'.ljust(56) + BLUE + '║' + RESET)
                    print(BLUE + '  ╠' + '═' * 56 + '╣' + RESET)
                    print(BLUE + '  ║' + RESET + f'  🌐  {GREEN}{direct_link}{RESET}')
                    print(BLUE + '  ╚' + '═' * 56 + '╝' + RESET)
                    print()
                    slow('  Press Ctrl+C — ONLY the TUNNEL will stop, SERVER KEEPS RUNNING!', YELLOW)

        except Exception as e:
            slow(f'  Tunnel error: {e}', RED)

    t = threading.Thread(target=_run_tunnel, daemon=True)
    t.start()

    try:
        t.join()
    except KeyboardInterrupt:
        slow('\n  Stopping tunnel...', YELLOW)
        if tunnel_proc[0]:
            try:
                tunnel_proc[0].terminate()
            except Exception:
                pass

    print()
    if detected_url[0] and chosen_path:
        slow(f'  Your link was: {detected_url[0]}/{chosen_path}', BLUE)
    input(GREEN + "\nPress Enter to return to main menu..." + RESET)

def server_analytics():
    # ── helpers ────────────────────────────────────────────────────────────────
    def sec_line(w, char='─', color=GREY):
        print(f"  {color}{char * min(w - 6, 70)}{RESET}")

    def section_header(w, title, icon=''):
        sec_line(w, '─', GREY)
        label = f"  {icon}  {title}" if icon else f"  {title}"
        print(f"{YELLOW}{label}{RESET}")
        sec_line(w, '─', GREY)

    def smart_bar(val, max_ref=50, bar_len=28):
        filled = min(int((val / max_ref) * bar_len), bar_len) if max_ref > 0 else 0
        pct    = min(int((val / max_ref) * 100), 100) if max_ref > 0 else 0
        if pct >= 75:
            bar_color = RED
        elif pct >= 40:
            bar_color = YELLOW
        else:
            bar_color = GREEN
        bar = bar_color + "█" * filled + GREY + "░" * (bar_len - filled) + RESET
        return bar, pct

    def format_uptime(seconds):
        days,  rem   = divmod(int(seconds), 86400)
        hours, rem   = divmod(rem, 3600)
        mins,  secs  = divmod(rem, 60)
        parts = []
        if days:  parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        if mins:  parts.append(f"{mins}m")
        parts.append(f"{secs}s")
        return " ".join(parts)

    def export_analytics(data):
        export_path = os.path.join(os.path.expanduser('~'), 'server_analytics_export.json')
        try:
            with open(export_path, 'w') as f:
                json.dump(data, f, indent=4)
            slow(f'  ✅  Exported to: {export_path}', GREEN)
        except Exception as e:
            slow(f'  ✗  Export failed: {e}', RED)

    # ── main render ────────────────────────────────────────────────────────────
    while True:
        clear()
        data = load_analytics()
        w    = term_width()
        box  = min(w - 4, 72)
        pad  = ' ' * max(0, (w - box - 2) // 2)

        # ── Top Banner ────────────────────────────────────────────────────────
        print()
        print(f"{BLUE}{pad}╔{'═' * box}╗{RESET}")
        print(f"{BLUE}{pad}║{WHITE}{'  ◈  SERVER ANALYTICS  ◈'.center(box)}{BLUE}║{RESET}")
        now_str = datetime.datetime.now().strftime("  %Y-%m-%d  %H:%M:%S  ")
        print(f"{BLUE}{pad}║{GREY}{now_str.center(box)}{BLUE}║{RESET}")
        print(f"{BLUE}{pad}╚{'═' * box}╝{RESET}")
        print()

        # ── Activity Counters ─────────────────────────────────────────────────
        section_header(w, "ACTIVITY COUNTERS", "📊")
        print()

        stats = [
            ("Link / Page Opens",   "link_opens",         GREEN,  "🔗"),
            ("Server Starts",       "server_starts",      YELLOW, "🚀"),
            ("Files Uploaded",      "files_uploaded",     BLUE,   "📤"),
            ("Files Deleted",       "files_deleted",      RED,    "🗑 "),
            ("Tunnel Sessions",     "tunnel_sessions",    PUR,    "🌐"),
            ("HTML Pages Created",  "html_pages_created", ORANGE, "🖥 "),
        ]
        all_vals  = [data.get(k, 0) for _, k, _, _ in stats]
        max_val   = max(all_vals) if any(all_vals) else 1

        for label, key, color, icon in stats:
            val        = data.get(key, 0)
            bar, pct   = smart_bar(val, max_ref=max(max_val, 1))
            count_str  = str(val).rjust(5)
            pct_str    = f"({pct:>3}%)".rjust(7)
            print(f"  {icon}  {color}{label:<22}{RESET}  {bar}  {WHITE}{count_str}{RESET}  {GREY}{pct_str}{RESET}")

        total_events = sum(all_vals)
        print()
        print(f"  {GREY}  Total Recorded Events :{RESET}  {WHITE}{total_events}{RESET}")
        print()

        # ── Uptime & Time ──────────────────────────────────────────────────────
        section_header(w, "SERVER UPTIME & TIME INFO", "⏱ ")
        print()

        last_start = data.get("last_start", None)
        now        = datetime.datetime.now()

        if last_start:
            try:
                start_dt   = datetime.datetime.strptime(last_start, "%Y-%m-%d %H:%M:%S")
                delta      = now - start_dt
                uptime_str = format_uptime(delta.total_seconds())
                uptime_col = GREEN if delta.total_seconds() < 3600 else YELLOW
            except Exception:
                uptime_str = "N/A"
                uptime_col = RED
        else:
            uptime_str = "Server never started"
            uptime_col = GREY

        print(f"  ⏱   {WHITE}Last Server Start   :{RESET}  {GREY}{last_start if last_start else 'Never'}{RESET}")
        print(f"  ⏳  {WHITE}Uptime Since Start  :{RESET}  {uptime_col}{uptime_str}{RESET}")
        print(f"  🕐  {WHITE}Current Time        :{RESET}  {WHITE}{now.strftime('%A, %d %B %Y  %H:%M:%S')}{RESET}")
        print()

        # ── System Info ────────────────────────────────────────────────────────
        section_header(w, "SYSTEM & WEB ROOT INFO", "💻")
        print()

        platform_name  = 'Windows' if WINDOWS else ('Termux/Android' if TERMUX else 'Linux')
        running_now    = is_apache_running()
        installed_now  = is_apache_installed()
        local_ip_now   = get_local_ip()
        cf_path        = find_cloudflared()
        status_txt     = f"{GREEN}● RUNNING  ✓{RESET}" if running_now else f"{RED}● STOPPED  ✗{RESET}"
        install_txt    = f"{GREEN}✓  Installed{RESET}"  if installed_now else f"{RED}✗  Not Found{RESET}"
        cf_txt         = f"{GREEN}✓  {cf_path}{RESET}"  if cf_path       else f"{RED}✗  Not Installed{RESET}"

        print(f"  💻  {WHITE}Platform         :{RESET}  {PUR}{platform_name}{RESET}")
        print(f"  ⚙   {WHITE}Apache           :{RESET}  {install_txt}")
        print(f"  🟢  {WHITE}Server Status    :{RESET}  {status_txt}")
        print(f"  🌐  {WHITE}Local IP         :{RESET}  {BLUE}{local_ip_now}{RESET}")
        print(f"  📂  {WHITE}Web Root         :{RESET}  {ORANGE}{WEB_ROOT}{RESET}")
        print(f"  🔧  {WHITE}cloudflared      :{RESET}  {cf_txt}")

        try:
            if os.path.exists(WEB_ROOT):
                total_size = sum(
                    os.path.getsize(os.path.join(r, f))
                    for r, _, fs in os.walk(WEB_ROOT) for f in fs
                )
                dir_count  = len([e for e in os.listdir(WEB_ROOT) if os.path.isdir(os.path.join(WEB_ROOT, e))])
                file_count = len([e for e in os.listdir(WEB_ROOT) if os.path.isfile(os.path.join(WEB_ROOT, e))])
                if total_size >= 1024 * 1024:
                    size_str = f"{total_size/(1024*1024):.2f} MB"
                elif total_size >= 1024:
                    size_str = f"{total_size/1024:.1f} KB"
                else:
                    size_str = f"{total_size} B"
                print(f"  📦  {WHITE}Web Root Size    :{RESET}  {GREY}{size_str}  │  {dir_count} folder(s)  │  {file_count} file(s){RESET}")
        except Exception:
            pass

        # ── Recent Activity ────────────────────────────────────────────────────
        print()
        section_header(w, "RECENT ACTIVITY  (last 10 events)", "📋")
        print()

        history   = data.get("history", [])
        icons_map = {
            "link_opens":        ("🔗", GREEN),
            "server_starts":     ("🚀", YELLOW),
            "files_uploaded":    ("📤", BLUE),
            "files_deleted":     ("🗑 ", RED),
            "tunnel_sessions":   ("🌐", PUR),
            "html_pages_created":("🖥 ", ORANGE),
        }
        label_map = {
            "link_opens":         "Link / Page Opened",
            "server_starts":      "Server Started",
            "files_uploaded":     "File Uploaded",
            "files_deleted":      "File Deleted",
            "tunnel_sessions":    "Tunnel Session",
            "html_pages_created": "HTML Page Created",
        }

        if history:
            for evt in reversed(history[-10:]):
                ico, ecol = icons_map.get(evt["event"], ("•", WHITE))
                friendly  = label_map.get(evt["event"], evt["event"])
                note_str  = f"  {GREY}→ {evt['note']}{RESET}" if evt.get("note") else ""
                print(f"    {GREY}{evt['time']}{RESET}   {ico}   {ecol}{friendly:<26}{RESET}{note_str}")
        else:
            print(f"  {GREY}  No activity recorded yet.{RESET}")

        # ── Footer ─────────────────────────────────────────────────────────────
        print()
        print(f"  {BLUE}{'═' * min(w - 6, 70)}{RESET}")
        print(
            f"\n  {YELLOW}[R]{RESET} Reset All Data"
            f"   {YELLOW}[E]{RESET} Export to JSON"
            f"   {YELLOW}[Enter]{RESET} Back to Menu"
        )
        print(f"  {BLUE}{'─' * min(w - 6, 70)}{RESET}")

        choice = input(f"\n  {PUR}Enter choice: {RESET}").strip().lower()

        if choice == 'r':
            print()
            confirm = input(f"  {RED}⚠  This will erase all analytics data. Confirm? (y/n): {RESET}").strip().lower()
            if confirm == 'y':
                save_analytics({
                    "link_opens": 0, "server_starts": 0, "files_uploaded": 0,
                    "files_deleted": 0, "tunnel_sessions": 0, "html_pages_created": 0,
                    "last_start": None, "history": []
                })
                slow('  ✅  Analytics data has been reset successfully.', GREEN)
                time.sleep(1)
            else:
                slow('  ↩  Reset cancelled.', GREY)
                time.sleep(0.6)
        elif choice == 'e':
            print()
            export_analytics(data)
            input(GREEN + "\n  Press Enter to continue..." + RESET)
        else:
            break


def auto_fix_spaces_in_webroot():
    if not os.path.exists(WEB_ROOT):
        return
    try:
        entries = os.listdir(WEB_ROOT)
    except Exception:
        return
    fixed = []
    for entry in entries:
        if ' ' in entry:
            safe = entry.replace(' ', '_')
            old_path = os.path.join(WEB_ROOT, entry)
            new_path = os.path.join(WEB_ROOT, safe)
            try:
                if WINDOWS:
                    tmp_path = os.path.join(WEB_ROOT, '__tmp_rename__')
                    if os.path.exists(tmp_path):
                        shutil.rmtree(tmp_path) if os.path.isdir(tmp_path) else os.remove(tmp_path)
                    os.rename(old_path, tmp_path)
                    os.rename(tmp_path, new_path)
                elif LINUX:
                    subprocess.run(['sudo', 'mv', old_path, new_path], check=True, capture_output=True)
                else:
                    os.rename(old_path, new_path)
                fixed.append((entry, safe))
            except Exception:
                pass
    return fixed

def main():
    _fixed = auto_fix_spaces_in_webroot()

    while True:
        clear()
        baner()

        if _fixed:
            for old_n, new_n in _fixed:
                slow(f'  ✅ Auto-fixed: "{old_n}" → "{new_n}"', GREEN)
            _fixed = []

        running = is_apache_running()
        cf_ok   = find_cloudflared() is not None
        status  = GREEN + "● RUNNING" + RESET if running else RED + "● STOPPED" + RESET
        w = term_width()
        label = "Server Status: ● RUNNING"
        pad   = max(0, (w - len(label)) // 2)
        print(' ' * pad + f"Server Status: {status}\n")

        slow('\n\t\t' + RED+'['+WHITE+'01'+RED+']  '+ORANGE+'Install Apache2         '+RED+'['+WHITE+'05'+RED+']  '+ORANGE+'Upload File & Dir        '+RED+'['+WHITE+'09'+RED+']  '+ORANGE+'Generate Secure Link', delay=0.003)
        slow(  '')
        slow(  '\t\t' + RED+'['+WHITE+'02'+RED+']  '+ORANGE+'Start Server            '+RED+'['+WHITE+'06'+RED+']  '+ORANGE+'Delete File & Dir        '+RED+'['+WHITE+'10'+RED+']  '+ORANGE+'List Files', delay=0.003)
        slow(  '')
        slow(  '\t\t' + RED+'['+WHITE+'03'+RED+']  '+ORANGE+'Stop Server             '+RED+'['+WHITE+'07'+RED+']  '+ORANGE+'Open Server Page         '+RED+'['+WHITE+'11'+RED+']  '+ORANGE+'Restart Server', delay=0.003)
        slow(  '')
        slow(  '\t\t' + RED+'['+WHITE+'04'+RED+']  '+ORANGE+'Create HTML Page   ✨   '+RED+'['+WHITE+'08'+RED+']  '+ORANGE+'Send Server Link         '+RED+'['+WHITE+'12'+RED+']  '+ORANGE+'Analytics Dashboard', delay=0.003)
        slow(  '')
        slow(  '\t\t' + RED+'['+WHITE+'99'+RED+']  '+ORANGE+'Exit', delay=0.003)

        try:
            choice = int(input(PUR + '\n\nChoose Your Choice: ' + RESET))
        except ValueError:
            slow("Invalid choice.", RED)
            input(GREEN + "\nPress Enter to return to main menu..." + RESET)
            continue

        actions = {
            1:  install_apache,
            2:  start_server,
            3:  stop_server,
            4:  create_html_page,
            5:  upload_file,
            6:  delete_file,
            7:  open_server_page,
            8:  share_server_link,
            9:  create_cloudflared_link,
            10: list_files,
            11: restart_server,
            12: server_analytics,
        }

        if choice == 99:
            slow("Exiting........", GREEN)
            sys.exit(0)
        elif choice in actions:
            actions[choice]()
        else:
            slow("Invalid choice.", RED)
            input(GREEN + "\nPress Enter to return to main menu..." + RESET)

if __name__ == "__main__":
    main()
