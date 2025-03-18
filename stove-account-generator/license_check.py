import tkinter as tk
import customtkinter as ctk
import json
import os
import sys
import requests
from license_manager import LicenseManager
from gui_interface import AccountGeneratorGUI
from PIL import Image, ImageTk
from datetime import datetime, timedelta
from tkinter import messagebox
from itertools import cycle
import threading
import time

class LicenseCheckWindow:
    def __init__(self):
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create the main window
        self.root = ctk.CTk()
        self.root.title("STOVE Account Generator - License Verification")
        self.root.geometry("500x750")  # Increased height to ensure buttons are visible
        self.root.resizable(False, False)
        
        # Try to set window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
                # Convert to PhotoImage
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.root.iconphoto(True, icon_photo)
        except Exception as e:
            print(f"Failed to load icon: {e}")
        
        # Initialize license manager
        self.license_manager = LicenseManager()
        
        # Check server status
        self.server_online = self.check_server_status()
        
        # Modify loading animation variables
        self.loading = False
        self.loading_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.loading_index = 0
        self.loading_after_id = None
        
        # Read version from version.txt if it exists, otherwise use default
        try:
            with open('version.txt', 'r') as f:
                self.APP_VERSION = f.read().strip().lstrip('v')
        except:
            self.APP_VERSION = "0.3.0"  # Updated version number
        
        # Add server URLs
        self.license_server_url = "https://stoveserver-production.up.railway.app"
        self.logger_url = "https://stove-license-logger-production.up.railway.app"
        
        # Create GUI elements
        self.create_gui()
        
        # Center window on screen
        self.center_window()
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        # Disable close button
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize time update
        self.time_remaining = None
        self.update_time_id = None
        
    def check_server_status(self):
        """Check if the license server is online"""
        try:
            # Use the health check endpoint
            response = requests.get(
                "https://stoveserver-production.up.railway.app/health",  # Updated to production URL
                timeout=5  # 5 seconds timeout
            )
            
            if response.status_code == 200:
                return True
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"Server connection error: {str(e)}")  # Add logging
            return False

    def create_gui(self):
        # Create main container with padding
        container = ctk.CTkFrame(self.root)
        container.pack(fill="both", expand=True, padx=30, pady=30)  # Increased padding
        
        # Add server status indicator
        status_frame = ctk.CTkFrame(container, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 15))  # Increased bottom padding
        
        status_text = "Server Status: Online" if self.server_online else "Server Status: Offline"
        status_color = "#2ecc71" if self.server_online else "#e74c3c"  # Green if online, red if offline
        
        self.server_status_label = ctk.CTkLabel(
            status_frame,
            text=status_text,
            font=("Helvetica", 12, "bold"),
            text_color=status_color
        )
        self.server_status_label.pack()
        
        if not self.server_online:
            offline_msg = ctk.CTkLabel(
                status_frame,
                text="Server is currently offline. Please contact developer for assistance.",
                font=("Helvetica", 12),
                text_color="#f39c12",  # Orange warning color
                wraplength=400
            )
            offline_msg.pack(pady=5)
        
        # Add logo if exists
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((100, 100), Image.Resampling.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_image)
                # Use CTkLabel instead of tk.Label for better dark mode compatibility
                logo_label = ctk.CTkLabel(container, image=logo_photo, text="")
                logo_label.image = logo_photo
                logo_label.pack(pady=10)
        except Exception as e:
            print(f"Failed to load logo: {e}")
        
        # Add title
        title = ctk.CTkLabel(
            container,
            text="STOVE Account Generator",
            font=("Helvetica", 24, "bold")
        )
        title.pack(pady=10)
        
        # Add subtitle
        subtitle = ctk.CTkLabel(
            container,
            text="License Verification Required",
            font=("Helvetica", 16)
        )
        subtitle.pack(pady=5)
        
        # Add welcome message
        welcome = ctk.CTkLabel(
            container,
            text="Please enter your license key to access the generator.",
            wraplength=400,
            font=("Helvetica", 12)
        )
        welcome.pack(pady=10)
        
        # Add contact info with custom styling
        contact_frame = ctk.CTkFrame(container, fg_color="transparent")
        contact_frame.pack(pady=10)
        
        contact_label = ctk.CTkLabel(
            contact_frame,
            text="Need a license key? Contact us on Discord:",
            font=("Helvetica", 12)
        )
        contact_label.pack()
        
        discord_label = ctk.CTkLabel(
            contact_frame,
            text=self.license_manager.get_contact_info(),
            text_color="#5865F2",  # Discord blue color
            font=("Helvetica", 12, "bold")
        )
        discord_label.pack()
        
        # Create frame for license key with better styling
        key_frame = ctk.CTkFrame(container, fg_color="transparent")
        key_frame.pack(pady=(30, 20), padx=20, fill="x")  # Increased top padding
        
        # Add license key input with better styling
        self.license_var = tk.StringVar()
        self.license_entry = ctk.CTkEntry(
            key_frame,
            textvariable=self.license_var,
            width=400,
            height=45,
            placeholder_text="Enter your license key here and press Enter",
            font=("Helvetica", 12),
            border_width=2
        )
        self.license_entry.pack(pady=10)
        
        # Bind Enter key to verify_license
        self.license_entry.bind('<Return>', lambda event: self.verify_license())
        
        # Add hint label for Enter key
        hint_label = ctk.CTkLabel(
            key_frame,
            text="Press Enter to activate license",
            font=("Helvetica", 10, "italic"),
            text_color="#666666"
        )
        hint_label.pack(pady=(0, 10))
        
        # Add time remaining frame with more space
        time_frame = ctk.CTkFrame(container, fg_color="transparent")
        time_frame.pack(pady=(20, 30))  # Increased padding
        
        # Add time remaining label
        self.time_label = ctk.CTkLabel(
            time_frame,
            text="Time Remaining: Not activated",
            font=("Helvetica", 14, "bold"),
            text_color="#3498db"  # Blue color
        )
        self.time_label.pack()
        
        # Add expiry date label
        self.expiry_label = ctk.CTkLabel(
            time_frame,
            text="Expiry Date: Not activated",
            font=("Helvetica", 12),
            text_color="#666666"  # Using hex color instead of named color
        )
        self.expiry_label.pack(pady=5)
        
        # Add loading label after status label
        self.loading_label = ctk.CTkLabel(
            container,
            text="",
            font=("Helvetica", 14),
            text_color="#3498db"
        )
        self.loading_label.pack(pady=5)
        
        # Add detailed error label
        self.error_detail_label = ctk.CTkLabel(
            container,
            text="",
            font=("Helvetica", 12),
            text_color="#e74c3c",
            wraplength=400
        )
        self.error_detail_label.pack(pady=5)
        
        # Add buttons with better styling and spacing
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x", expand=True, pady=(20, 30))  # Increased padding
        
        # Button container for better organization
        buttons_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_container.pack(expand=True, fill="both", padx=30)  # Added padding
        
        # Activate button with hover effect and improved visibility
        self.activate_btn = ctk.CTkButton(
            buttons_container,
            text="ACTIVATE LICENSE",
            command=self.verify_license,
            width=400,
            height=60,
            font=("Helvetica", 16, "bold"),
            fg_color="#2ecc71",  # Brighter green
            hover_color="#27ae60",
            border_width=2,
            border_color="#2ecc71",
            corner_radius=10
        )
        self.activate_btn.pack(pady=(0, 20))  # Increased padding between buttons
        
        # Exit button with hover effect
        self.exit_btn = ctk.CTkButton(
            buttons_container,
            text="Exit",
            command=self.on_close,
            width=400,
            height=45,
            font=("Helvetica", 12),
            fg_color="#e74c3c",
            hover_color="#c0392b",
            corner_radius=10
        )
        self.exit_btn.pack(pady=(0, 15))  # Added bottom padding
        
        # Status label with better spacing
        self.status_label = ctk.CTkLabel(
            container,
            text="",
            font=("Helvetica", 12),
            text_color="#e74c3c"
        )
        self.status_label.pack(pady=(10, 20))  # Increased padding
        
        # Version label at bottom with more space
        version_label = ctk.CTkLabel(
            container,
            text=f"Version {self.APP_VERSION}",
            font=("Helvetica", 10),
            text_color="#666666"
        )
        version_label.pack(pady=(10, 0))  # Added top padding
        
    def update_time_remaining(self):
        """Update the time remaining display"""
        if self.time_remaining:
            now = datetime.now()
            time_left = self.time_remaining - now
            
            if time_left.total_seconds() <= 0:
                self.time_label.configure(
                    text="License Expired",
                    text_color="#e74c3c"  # Red color
                )
                if self.update_time_id:
                    self.root.after_cancel(self.update_time_id)
                return False
            
            # Calculate days, hours, minutes
            days = time_left.days
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            
            # Update time remaining label
            time_text = f"Time Remaining: {days}d {hours}h {minutes}m"
            self.time_label.configure(
                text=time_text,
                text_color="#3498db"  # Blue color
            )
            
            # Schedule next update
            self.update_time_id = self.root.after(60000, self.update_time_remaining)  # Update every minute
            return True
        return False
        
    def start_loading_animation(self):
        """Start the loading animation"""
        self.loading = True
        self.loading_index = 0
        self._update_loading_animation()
        
    def stop_loading_animation(self):
        """Stop the loading animation"""
        self.loading = False
        if self.loading_after_id:
            self.root.after_cancel(self.loading_after_id)
            self.loading_after_id = None
        self.loading_label.configure(text="")
        
    def _update_loading_animation(self):
        """Update the loading animation frame"""
        if not self.loading:
            return
        
        char = self.loading_chars[self.loading_index]
        self.loading_label.configure(text=f"Verifying license... {char}")
        
        self.loading_index = (self.loading_index + 1) % len(self.loading_chars)
        self.loading_after_id = self.root.after(100, self._update_loading_animation)

    def show_error(self, title, message, detail=None):
        """Show error message with optional details"""
        self.status_label.configure(
            text=message,
            text_color="#e74c3c"
        )
        
        if detail:
            self.error_detail_label.configure(text=detail)
        else:
            self.error_detail_label.configure(text="")
            
        messagebox.showerror(title, message)

    def verify_license(self):
        key = self.license_var.get().strip()
        
        # Clear previous error messages
        self.error_detail_label.configure(text="")
        self.status_label.configure(text="")
        
        if not key:
            self.show_error(
                "Error",
                "Please enter a license key",
                "The license key field cannot be empty."
            )
            return
            
        if not key.startswith("STOVE-"):
            self.show_error(
                "Error",
                "Invalid key format",
                "License key must start with 'STOVE-' followed by the date and unique identifier."
            )
            return

        try:
            # Start loading animation
            self.start_loading_animation()
            self.activate_btn.configure(state="disabled")
            
            # Extract user ID from license key
            user_id = key.split('-')[2] if len(key.split('-')) > 2 else 'unknown'
            
            validation_result = self.license_manager.validate_license(key)
            
            # Stop loading animation
            self.stop_loading_animation()
            
            if isinstance(validation_result, dict) and validation_result.get('error'):
                error_type = validation_result.get('error')
                # Log failed attempt with reason
                self.log_validation_attempt(key, 'failed', {
                    'reason': error_type,
                    'action': 'login_failed',
                    'user_id': user_id
                })
                # ... rest of error handling ...
                return
            
            if validation_result is True:
                # Log successful validation immediately after confirming it's valid
                self.log_validation_attempt(key, 'valid', {
                    'action': 'login_success',
                    'user_id': user_id,
                    'expiry_date': self.time_remaining.isoformat() if self.time_remaining else None
                })
                
                # Update UI and show success message
                self.status_label.configure(
                    text="License verified successfully!",
                    text_color="#2ecc71"
                )
                messagebox.showinfo("Success", "License verified successfully!")
                self.activate_btn.configure(state="disabled")
                self.root.after(1500, self.launch_main_app)
            else:
                # Log invalid attempt
                self.log_validation_attempt(key, 'invalid', {
                    'action': 'login_failed',
                    'user_id': user_id,
                    'reason': 'invalid_key'
                })
                self.show_error(
                    "Invalid License",
                    "Invalid license key",
                    "The license key could not be verified. Please check and try again."
                )
                
        except Exception as e:
            self.stop_loading_animation()
            # Log error
            self.log_validation_attempt(key, 'error', {
                'action': 'error',
                'error_message': str(e),
                'user_id': user_id
            })
            self.show_error(
                "Error",
                "License verification failed",
                str(e)
            )
        finally:
            self.activate_btn.configure(state="normal")

    def log_validation_attempt(self, license_key, status, additional_info=None):
        """Send validation log to logging server"""
        try:
            headers = {
                'X-API-Key': 'STOVE_ADMIN_2024_SECRET',
                'Content-Type': 'application/json'
            }
            
            # Get system info
            import platform
            device_info = {
                'os': platform.system(),
                'version': platform.version(),
                'machine': platform.machine(),
                'hostname': platform.node()
            }
            
            data = {
                'license_key': license_key,
                'user_id': additional_info.get('user_id', 'unknown'),
                'status': status,
                'device_info': device_info,
                'additional_info': additional_info or {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Send log to logging server
            response = requests.post(
                "https://stove-license-logger-production.up.railway.app/api/log/validation",
                headers=headers,
                json=data,
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"Failed to log validation attempt: {response.text}")
                
        except Exception as e:
            print(f"Error logging validation attempt: {str(e)}")

    def launch_main_app(self):
        if self.update_time_id:
            self.root.after_cancel(self.update_time_id)
        self.root.destroy()  # Close license window
        app = AccountGeneratorGUI()  # Launch main application
        app.root.mainloop()
        
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def on_close(self):
        # Stop loading animation
        self.stop_loading_animation()
        
        if self.update_time_id:
            self.root.after_cancel(self.update_time_id)
            
        if tk.messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.root.destroy()
            sys.exit(0)
            
    def run(self):
        self.root.mainloop()

def main():
    app = LicenseCheckWindow()
    app.run()

if __name__ == "__main__":
    main() 