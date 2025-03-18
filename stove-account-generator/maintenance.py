import os
import sys
import json
import logging
import requests
import platform
import psutil
import shutil
from datetime import datetime
from pathlib import Path
import subprocess
import hashlib
from typing import Dict, List, Optional

class MaintenanceManager:
    def __init__(self, app_version: str = "1.0.1"):
        self.app_version = app_version
        self.github_repo = "Soozu/stove-account-generator"
        self.log_dir = "logs"
        self.max_log_files = 5
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        log_file = os.path.join(self.log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def check_for_updates(self) -> Dict:
        """Check for new version on GitHub"""
        try:
            # Add timestamp to prevent caching
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest?t={int(datetime.now().timestamp())}"
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Stove-Account-Generator',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            # Use session to prevent caching
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(api_url)
            response.raise_for_status()
            
            latest = response.json()
            
            # Check if we actually got release data
            if not latest:
                return {"error": "No release data found"}
                
            latest_version = latest['tag_name'].lstrip('v')  # Remove 'v' prefix if present
            current_version = self.app_version.lstrip('v')  # Remove 'v' prefix if present
            
            # Parse version strings into tuples of integers
            def parse_version(version_str):
                try:
                    return tuple(map(int, version_str.split('.')))
                except (ValueError, AttributeError):
                    logging.error(f"Invalid version format: {version_str}")
                    return (0, 0, 0)
            
            latest_parts = parse_version(latest_version)
            current_parts = parse_version(current_version)
            
            # Compare versions
            update_available = latest_parts > current_parts
            
            # Get Windows installer asset
            download_url = None
            if latest.get('assets'):
                for asset in latest['assets']:
                    if asset['name'].lower().endswith('.exe'):
                        download_url = asset['browser_download_url']
                        break
            
            # Log the check results
            logging.info(f"Update check - Current: {current_version}, Latest: {latest_version}, Update available: {update_available}")
            
            return {
                "update_available": update_available,
                "current_version": current_version,
                "latest_version": latest_version,
                "download_url": download_url,
                "release_notes": latest.get('body', 'No release notes available'),
                "published_at": latest.get('published_at', ''),
                "release_url": latest.get('html_url', '')
            }
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error checking for updates: {str(e)}")
            return {"error": f"Failed to connect to GitHub: {str(e)}"}
        except Exception as e:
            logging.error(f"Error checking for updates: {str(e)}")
            return {"error": str(e)}

    def download_update(self, download_url: str) -> Optional[str]:
        """Download the latest version"""
        try:
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                # Create downloads directory if it doesn't exist
                downloads_dir = "downloads"
                if not os.path.exists(downloads_dir):
                    os.makedirs(downloads_dir)
                
                # Get the filename from the URL
                file_name = os.path.basename(download_url)
                download_path = os.path.join(downloads_dir, file_name)
                
                # Download with progress tracking
                total_size = int(response.headers.get('content-length', 0))
                block_size = 8192
                downloaded = 0
                
                with open(download_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=block_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            # Log download progress
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                logging.info(f"Download progress: {percent:.1f}%")
                
                return download_path
            else:
                logging.error(f"Download failed with status code: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error downloading update: {str(e)}")
            return None

    def install_update(self, installer_path: str) -> bool:
        """Install the downloaded update"""
        try:
            if not os.path.exists(installer_path):
                logging.error("Installer file not found")
                return False
                
            if sys.platform == 'win32':
                # Run installer with appropriate flags
                subprocess.Popen([installer_path, '/SILENT', '/CLOSEAPPLICATIONS'])
                return True
            else:
                logging.error("Automatic installation is only supported on Windows")
                return False
                
        except Exception as e:
            logging.error(f"Error installing update: {str(e)}")
            return False

    def system_health_check(self) -> Dict:
        """Perform system health check"""
        health_data = {
            "system": {
                "os": platform.system(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "chrome_installed": self._check_chrome_installed(),
            "required_files": self._check_required_files(),
            "settings_valid": self._validate_settings()
        }
        
        return health_data

    def _check_chrome_installed(self) -> bool:
        """Check if Chrome is installed"""
        if sys.platform == 'win32':
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            return os.path.exists(chrome_path)
        return False

    def _check_required_files(self) -> Dict:
        """Check if all required files exist"""
        required_files = {
            "settings.json": os.path.exists("settings.json"),
            "accounts.json": os.path.exists("accounts.json"),
            "chromedriver.exe": os.path.exists("chromedriver.exe"),
            "logo.png": os.path.exists("logo.png")
        }
        return required_files

    def _validate_settings(self) -> bool:
        """Validate settings file"""
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                required_keys = ['password_length', 'theme']
                return all(key in settings for key in required_keys)
        except:
            return False

    def manage_logs(self):
        """Manage log files - keep only recent logs"""
        try:
            # Get current active log file name
            current_log = None
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.FileHandler):
                    current_log = os.path.basename(handler.baseFilename)
                    break

            log_files = sorted(
                [f for f in os.listdir(self.log_dir) if f.endswith('.log')],
                key=lambda x: os.path.getmtime(os.path.join(self.log_dir, x)),
                reverse=True
            )
            
            # Remove old log files
            for log_file in log_files[self.max_log_files:]:
                os.remove(os.path.join(self.log_dir, log_file))
                
            # Compress old logs, but skip the current active log
            for log_file in log_files[:self.max_log_files]:
                if log_file != current_log and not log_file.endswith('.gz'):
                    self._compress_log(os.path.join(self.log_dir, log_file))
                    
        except Exception as e:
            logging.error(f"Error managing logs: {str(e)}")

    def _compress_log(self, log_path: str):
        """Compress a log file"""
        try:
            import gzip
            with open(log_path, 'rb') as f_in:
                with gzip.open(f"{log_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(log_path)
        except Exception as e:
            logging.error(f"Error compressing log {log_path}: {str(e)}")

    def report_error(self, error: Exception, context: Dict = None):
        """Report error with context"""
        try:
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": self._get_traceback(),
                "system_info": self.system_health_check(),
                "context": context or {}
            }
            
            # Save error report
            reports_dir = "error_reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
                
            report_file = os.path.join(
                reports_dir,
                f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(report_file, 'w') as f:
                json.dump(error_data, f, indent=4)
                
            logging.error(f"Error report saved to {report_file}")
            
            # Optionally send to remote service
            # self._send_error_report(error_data)
            
        except Exception as e:
            logging.error(f"Error reporting error: {str(e)}")

    def _get_traceback(self) -> str:
        """Get formatted traceback"""
        import traceback
        return traceback.format_exc()

    def cleanup_old_files(self, days_old: int = 30):
        """Clean up old temporary files"""
        try:
            # Clean up old error reports
            self._cleanup_directory("error_reports", days_old)
            
            # Clean up old downloads
            self._cleanup_directory("downloads", days_old)
            
            # Manage logs
            self.manage_logs()
            
        except Exception as e:
            logging.error(f"Error cleaning up files: {str(e)}")

    def _cleanup_directory(self, directory: str, days_old: int):
        """Clean up files older than specified days in directory"""
        if not os.path.exists(directory):
            return
            
        now = datetime.now()
        for file_name in os.listdir(directory):
            file_path = os.path.join(directory, file_name)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if (now - file_time).days > days_old:
                    os.remove(file_path)

    def verify_file_integrity(self, file_path: str, expected_hash: str) -> bool:
        """Verify file integrity using SHA-256"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash == expected_hash
        except Exception as e:
            logging.error(f"Error verifying file integrity: {str(e)}")
            return False 