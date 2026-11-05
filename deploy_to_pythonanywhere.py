import os
import urllib.request
import json
import time

TOKEN = '5a83680d62b77009ea9f955065653ab2f724048b'
USERNAME = 'Subash'
DOMAIN = 'Subash.pythonanywhere.com'
PROJECT_DIR = r'C:\Users\Subhash Kumar\.gemini\antigravity\scratch\ms_sandip_kumar_accounts'

def upload_file_to_pa(remote_rel_path, local_abs_path):
    remote_path = f"/home/{USERNAME}/ms_sandip_kumar_accounts/{remote_rel_path.replace(os.sep, '/')}"
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{remote_path}"
    
    with open(local_abs_path, 'rb') as f:
        file_bytes = f.read()
    
    boundary = "----WebKitFormBoundaryPAAccountsDeploy"
    content_disposition = f'--{boundary}\r\nContent-Disposition: form-data; name="content"; filename="{os.path.basename(local_abs_path)}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode('utf-8')
    footer = f'\r\n--{boundary}--\r\n'.encode('utf-8')
    data = content_disposition + file_bytes + footer
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Token {TOKEN}',
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req) as resp:
        return resp.status

def update_wsgi_file():
    wsgi_content = """# +++++++++++ MS SANDIP KUMAR ACCOUNTS JJM BIHAR +++++++++++
import sys
import os

project_home = '/home/Subash/ms_sandip_kumar_accounts'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)

from app import app as application
"""
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path/var/www/subash_pythonanywhere_com_wsgi.py"
    boundary = "----WebKitFormBoundaryPAAccountsDeploy"
    content_disposition = f'--{boundary}\r\nContent-Disposition: form-data; name="content"; filename="subash_pythonanywhere_com_wsgi.py"\r\nContent-Type: text/plain\r\n\r\n'.encode('utf-8')
    footer = f'\r\n--{boundary}--\r\n'.encode('utf-8')
    data = content_disposition + wsgi_content.encode('utf-8') + footer
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Token {TOKEN}',
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        },
        method='POST'
    )
    with urllib.request.urlopen(req) as resp:
        print("WSGI file updated. Status:", resp.status)

def update_webapp_config():
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/"
    payload = {
        'source_directory': f'/home/{USERNAME}/ms_sandip_kumar_accounts',
        'working_directory': f'/home/{USERNAME}/ms_sandip_kumar_accounts',
        'force_https': True
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Token {TOKEN}',
            'Content-Type': 'application/json'
        },
        method='PATCH'
    )
    with urllib.request.urlopen(req) as resp:
        print("Webapp config updated:", resp.read().decode())

def reload_webapp():
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/"
    req = urllib.request.Request(
        url,
        headers={'Authorization': f'Token {TOKEN}'},
        method='POST'
    )
    with urllib.request.urlopen(req) as resp:
        print("Webapp reloaded successfully! Status:", resp.status)

def main():
    print("=== STARTING PYTHONANYWHERE DEPLOYMENT ===")
    
    # 1. Gather all files
    files_to_upload = []
    for root, dirs, files in os.walk(PROJECT_DIR):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv']]
        for f in files:
            if f in ['test_pa_upload.py', 'deploy_to_pythonanywhere.py'] or f.endswith(('.pyc', '.exe')):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, PROJECT_DIR)
            files_to_upload.append((rel, full))
            
    print(f"Uploading {len(files_to_upload)} files to PythonAnywhere...")
    for idx, (rel, full) in enumerate(files_to_upload, 1):
        status = upload_file_to_pa(rel, full)
        print(f"[{idx}/{len(files_to_upload)}] Uploaded {rel} -> HTTP {status}")
        
    # 2. Update WSGI
    print("\nUpdating WSGI configuration...")
    update_wsgi_file()
    
    # 3. Update Webapp configuration
    print("\nUpdating Webapp configuration (force_https, working_directory)...")
    update_webapp_config()
    
    # 4. Reload webapp
    print("\nReloading webapp on PythonAnywhere...")
    reload_webapp()
    
    # 5. Verify live response
    print("\nTesting live site response...")
    time.sleep(3)
    try:
        live_url = f"https://{DOMAIN}/"
        req = urllib.request.Request(live_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode('utf-8')
            print(f"LIVE SITE STATUS: {resp.status}")
            if "M/S Sandip Kumar" in content or "Accounts" in content:
                print("SUCCESS: Site loaded correctly with branding!")
            else:
                print("Warning: Response content snippet:", content[:300])
    except Exception as e:
        print("Error checking live site:", e)

if __name__ == '__main__':
    main()
