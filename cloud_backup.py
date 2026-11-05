"""
Cloud Backup Utility for M/S Sandip Kumar Accounts & Finance Management Portal
Backs up to:
1. Microsoft OneDrive Cloud Folder (24/7 Live Sync)
2. Desktop Cloud Zip Archive
3. GitHub Cloud Repository (subashrajsp143-beep/ms-sandip-kumar-accounts)
"""
import os
import shutil
import zipfile
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'database', 'sandip_accounts.db')
BACKUPS_DIR = os.path.join(BASE_DIR, 'database', 'backups')
ONEDRIVE_DIR = r"C:\Users\Subhash Kumar\OneDrive"
ONEDRIVE_BACKUP_FOLDER = os.path.join(ONEDRIVE_DIR, "M_S_SANDIP_KUMAR_ACCOUNTS_BACKUP")
DESKTOP_DIR = os.path.join(ONEDRIVE_DIR, "Desktop")
ZIP_BACKUP_FILE = os.path.join(DESKTOP_DIR, "MS_SANDIP_KUMAR_ACCOUNTS_CLOUD_BACKUP.zip")

def run_cloud_backup():
    results = {
        'onedrive_db': False,
        'onedrive_folder': False,
        'zip_archive': False,
        'github_push': False,
        'messages': []
    }

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # 1. Sync to OneDrive Cloud Folder
    try:
        os.makedirs(ONEDRIVE_BACKUP_FOLDER, exist_ok=True)
        onedrive_backups_sub = os.path.join(ONEDRIVE_BACKUP_FOLDER, "daily_backups")
        os.makedirs(onedrive_backups_sub, exist_ok=True)

        if os.path.exists(DB_FILE):
            dest_live = os.path.join(ONEDRIVE_BACKUP_FOLDER, "sandip_accounts_LIVE.db")
            dest_snap = os.path.join(onedrive_backups_sub, f"sandip_accounts_{timestamp}.db")
            shutil.copy2(DB_FILE, dest_live)
            shutil.copy2(DB_FILE, dest_snap)
            results['onedrive_db'] = True
            results['onedrive_folder'] = True
            results['messages'].append(f"Copied live DB & snapshot to OneDrive: {ONEDRIVE_BACKUP_FOLDER}")
        
        # Copy daily backups
        if os.path.exists(BACKUPS_DIR):
            for f in os.listdir(BACKUPS_DIR):
                if f.endswith('.db'):
                    shutil.copy2(os.path.join(BACKUPS_DIR, f), onedrive_backups_sub)
    except Exception as e:
        results['messages'].append(f"OneDrive Backup Error: {str(e)}")

    # 2. Create Clean Zip Archive on Desktop
    try:
        os.makedirs(DESKTOP_DIR, exist_ok=True)
        with zipfile.ZipFile(ZIP_BACKUP_FILE, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(BASE_DIR):
                # Skip __pycache__ and git internal objects to keep zip light and clean
                dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git')]
                for file in files:
                    if file.endswith('.pyc') or file.endswith('.log'):
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, BASE_DIR)
                    zipf.write(full_path, rel_path)
        results['zip_archive'] = True
        results['messages'].append(f"Created complete project zip on Desktop: {ZIP_BACKUP_FILE}")
    except Exception as e:
        results['messages'].append(f"Zip Creation Error: {str(e)}")

    # 3. Commit & Push to GitHub Cloud
    try:
        commit_msg = f"Cloud Backup Snapshot: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "add", "-A"], cwd=BASE_DIR, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        res = subprocess.run(
            ["git", "-c", "credential.helper=", "push", "origin", "main"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        if res.returncode == 0:
            results['github_push'] = True
            results['messages'].append("Successfully pushed latest updates to GitHub Cloud (subashrajsp143-beep/ms-sandip-kumar-accounts)")
        else:
            results['messages'].append(f"GitHub Push warning: {res.stderr.strip()}")
    except Exception as e:
        results['messages'].append(f"GitHub Push Error: {str(e)}")

    return results

if __name__ == '__main__':
    print("=" * 65)
    print("  M/S SANDIP KUMAR — CLOUD BACKUP RUNNER")
    print("=" * 65)
    res = run_cloud_backup()
    for m in res['messages']:
        print("  ->", m)
    print("=" * 65)
    print("Cloud Backup Finished!")
