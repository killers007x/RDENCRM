import os
import sys
import json
import shutil
import requests
import subprocess
import tempfile
from pathlib import Path
from packaging import version
from datetime import datetime


class AutoUpdater:
    """نظام التحديثات التلقائية"""
    
    def __init__(self, config_file='update_config.json'):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
        # تحديد المسارات
        if getattr(sys, 'frozen', False):
            self.app_dir = Path(sys.executable).parent
            self.is_frozen = True
        else:
            self.app_dir = Path(__file__).parent
            self.is_frozen = False
        
        self.current_version = self.config.get('current_version', '1.0.0')
        self.temp_dir = self.app_dir / 'temp_update'
        
    def _load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'current_version': '1.0.0',
            'repo_type': 'github',
            'repo_owner': 'YOUR_USERNAME',
            'repo_name': 'YOUR_REPO_NAME',
            'access_token': 'YOUR_TOKEN',
            'branch': 'main',
            'auto_check': True,
            'last_check': None
        }
    
    def _save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
            
    def _get_secure_token(self):
        return os.environ.get('CRM_UPDATE_TOKEN') or self.config.get('access_token')

    def check_for_updates(self):
        try:
            repo_type = self.config.get('repo_type', 'github')
            if repo_type == 'github':
                return self._check_github()
            elif repo_type == 'gitlab':
                return self._check_gitlab()
            return {'available': False, 'error': 'Unsupported repo type'}
        except Exception as e:
            return {'available': False, 'error': str(e)}
    
    def _check_github(self):
        owner = self.config['repo_owner']
        repo = self.config['repo_name']
        token = self._get_secure_token()
        
        headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
        url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                release = response.json()
                latest_version = release['tag_name'].lstrip('v')
                
                if version.parse(latest_version) > version.parse(self.current_version):
                    assets = release.get('assets', [])
                    download_url = None
                    for asset in assets:
                        if asset['name'].endswith('.exe') or asset['name'].endswith('.zip'):
                            download_url = asset['browser_download_url']
                            break
                    
                    return {
                        'available': True,
                        'current_version': self.current_version,
                        'latest_version': latest_version,
                        'download_url': download_url,
                        'release_notes': release.get('body', ''),
                        'published_at': release.get('published_at', '')
                    }
            return {'available': False, 'message': 'Already up to date'}
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _check_gitlab(self):
        # Placeholder for GitLab logic if needed
        return {'available': False, 'message': 'GitLab check not implemented yet'}

    def download_update(self, download_url, progress_callback=None):
        try:
            self.temp_dir.mkdir(exist_ok=True)
            filename = download_url.split('/')[-1]
            file_path = self.temp_dir / filename
            
            headers = {}
            if 'github.com' in download_url:
                headers['Authorization'] = f'token {self._get_secure_token()}'
                headers['Accept'] = 'application/octet-stream'
            
            response = requests.get(download_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size:
                            progress_callback((downloaded / total_size) * 100)
            
            return {'success': True, 'file_path': str(file_path)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def apply_update(self, update_file):
        try:
            update_path = Path(update_file)
            if self.is_frozen:
                # في حالة EXE، نحتاج لسكربت مساعد للاستبدال
                script_content = f'''
import os, sys, time, shutil
from pathlib import Path
time.sleep(2)
app_dir = Path(r"{self.app_dir}")
update_file = Path(r"{update_file}")
try:
    if update_file.suffix == '.zip':
        import zipfile
        with zipfile.ZipFile(update_file, 'r') as z: z.extractall(app_dir / 'temp_extract')
        for item in (app_dir / 'temp_extract').iterdir():
            dest = app_dir / item.name
            if dest.exists():
                if dest.is_file(): dest.unlink()
                else: shutil.rmtree(dest)
            shutil.move(str(item), str(dest))
        shutil.rmtree(app_dir / 'temp_extract')
    elif update_file.suffix == '.exe':
        current_exe = Path(sys.executable)
        shutil.copy2(current_exe, current_exe.with_suffix('.old'))
        shutil.copy2(update_file, current_exe)
    update_file.unlink()
    os.startfile(sys.executable)
except Exception as e: print(e)
'''
                script_path = self.app_dir / '_updater_helper.py'
                with open(script_path, 'w') as f: f.write(script_content)
                subprocess.Popen([sys.executable, str(script_path)])
                sys.exit(0)
            else:
                return {'success': True, 'message': 'Update applied (Dev mode)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_version(self, new_version):
        self.current_version = new_version
        self.config['current_version'] = new_version
        self.config['last_check'] = datetime.now().isoformat()
        self._save_config()