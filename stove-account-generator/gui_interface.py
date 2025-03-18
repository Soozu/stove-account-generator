import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
from datetime import datetime
import threading
from account_generator import CrossfireAccountGenerator
import os
import customtkinter as ctk
from PIL import Image, ImageTk
import webbrowser  # Import webbrowser module
from customtkinter import CTkImage  # Import CTkImage
import queue  # Add queue for communication between threads
import sys
import io
from maintenance import MaintenanceManager  # Import the maintenance manager
import logging
from license_manager import LicenseManager  # Import the license manager

class ConsoleRedirector(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        
    def write(self, string):
        self.text_widget.insert("end", string)
        self.text_widget.see("end")
        self.text_widget.update_idletasks()
        
    def flush(self):
        pass

class AccountGeneratorGUI:
    def __init__(self):
        # Create the main window using customtkinter
        self.root = ctk.CTk()
        self.root.title("STOVE Account Generator")
        self.root.geometry("1000x600")
        self.root.resizable(False, False)  # Disable resizing
        
        # Read version from version.txt if it exists, otherwise use default
        try:
            with open('version.txt', 'r') as f:
                self.APP_VERSION = f.read().strip().lstrip('v')
        except:
            self.APP_VERSION = "0.2.2"  # Update this to match your current version
        
        # Update window title with version
        self.root.title(f"STOVE Account Generator v{self.APP_VERSION}")
        
        # Initialize maintenance manager with current version
        self.maintenance = MaintenanceManager(self.APP_VERSION)
        
        # Set initial appearance mode
        ctk.set_appearance_mode("Light")  # Default theme
        ctk.set_default_color_theme("blue")  # You can change this to other themes
        
        # Initialize default settings
        self.current_theme = "Light"
        self.saved_password_length = 12  # Default password length
        
        # Load saved settings
        self.load_settings()
        
        # Initialize generator
        self.generator = None
        self.is_generating = False
        
        # Create queues for thread communication
        self.captcha_queue = queue.Queue()
        self.verification_queue = queue.Queue()
        
        # Initialize UI elements that need to be accessed globally
        self.update_label = None
        self.health_text = None
        self.time_remaining_label = None  # Add this line
        
        # Create the GUI
        self.create_gui()
        
        # Check for updates on startup (after GUI is created)
        self.root.after(1000, self.check_for_updates)
        
        # Schedule periodic maintenance tasks
        self.schedule_maintenance()
        
    def load_settings(self):
        """Load settings from the JSON file."""
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                # Load theme
                saved_theme = settings.get('theme', 'Light')
                ctk.set_appearance_mode(saved_theme)
                self.current_theme = saved_theme
                # Store password length
                self.saved_password_length = settings.get('password_length', 12)
                # Store email service settings
                self.saved_email_service = settings.get('email_service', 'yopmail.com')
                self.saved_custom_domain = settings.get('custom_domain', '')
        except:
            ctk.set_appearance_mode("Light")
            self.current_theme = "Light"
            self.saved_password_length = 12
            self.saved_email_service = 'yopmail.com'
            self.saved_custom_domain = ''
        
    def create_gui(self):
        # Create main container
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create header
        self.create_header()
        
        # Create tabs
        self.create_tabs()
        
    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_container)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Load and display logo
        try:
            logo_path = r"C:\Users\kingp\OneDrive\Desktop\Project\logo.png"
            logo_image = Image.open(logo_path)
            logo_image = logo_image.resize((40, 40), Image.Resampling.LANCZOS)
            
            # Use CTkImage instead of PhotoImage
            logo_photo = CTkImage(logo_image)
            
            logo_label = ctk.CTkLabel(header_frame, image=logo_photo, text="")
            logo_label.image = logo_photo  # Keep a reference to prevent garbage collection
            logo_label.pack(side="left", padx=5)
            
        except Exception as e:
            print(f"Failed to load logo: {str(e)}")
        
        # Logo and title
        title_label = ctk.CTkLabel(
            header_frame, 
            text="Stove Account Generator", 
            font=("Helvetica", 20, "bold")
        )
        title_label.pack(side="left", padx=10)
        
        # Add license info frame
        license_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        license_frame.pack(side="right", padx=10)
        
        # Add time remaining label
        self.time_remaining_label = ctk.CTkLabel(
            license_frame,
            text="License: Loading...",
            font=("Helvetica", 12),
            text_color="#3498db"  # Blue color
        )
        self.time_remaining_label.pack(side="top")
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            license_frame, 
            text="Status: Ready"
        )
        self.status_label.pack(side="bottom")
        
        # Theme toggle button
        self.theme_button = ctk.CTkButton(
            header_frame, 
            text="Switch to Dark Mode",
            command=self.toggle_theme
        )
        self.theme_button.pack(side="right", padx=10)
        
        # Login button
        ctk.CTkButton(
            header_frame,
            text="Login to STOVE",
            command=self.open_login_page
        ).pack(side="right", padx=10)
        
        # Start license time update
        self.update_license_time()
        
    def update_license_time(self):
        """Update the license time remaining display"""
        try:
            with open('license.json', 'r') as f:
                license_data = json.load(f)
                expiry_str = license_data.get('expiry_date')
                
                if expiry_str:
                    # Add time to the date if not present
                    if len(expiry_str.split()) == 1:
                        expiry_str += " 23:59:59"
                    
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    time_left = expiry_date - now
                    
                    if time_left.total_seconds() <= 0:
                        self.time_remaining_label.configure(
                            text="License: Expired",
                            text_color="#e74c3c"  # Red color
                        )
                    else:
                        # Calculate days, hours, minutes
                        days = time_left.days
                        hours = time_left.seconds // 3600
                        minutes = (time_left.seconds % 3600) // 60
                        
                        # Update time remaining label
                        time_text = f"License: {days}d {hours}h {minutes}m remaining"
                        self.time_remaining_label.configure(
                            text=time_text,
                            text_color="#2ecc71" if days > 7 else "#f39c12"  # Green if more than 7 days, orange if less
                        )
        except Exception as e:
            print(f"Error updating license time: {str(e)}")
            self.time_remaining_label.configure(
                text="License: Error",
                text_color="#e74c3c"  # Red color
            )
        
        # Update every minute
        self.root.after(60000, self.update_license_time)
        
    def create_tabs(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        
        # Generator tab
        self.generator_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.generator_tab, text="Generator")
        self.create_generator_tab()
        
        # Accounts tab
        self.accounts_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.accounts_tab, text="Accounts")
        self.create_accounts_tab()
        
        # Settings tab
        self.settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_tab, text="Settings")
        self.create_settings_tab()
        
        # Settings tab
        self.maintenance_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.maintenance_tab, text="Maintenance")
        self.create_maintenance_tab()
        
    def create_generator_tab(self):
        # Left panel - Generator controls
        control_frame = ttk.LabelFrame(self.generator_tab, text="Generator Controls", padding="25")
        control_frame.grid(row=0, column=0, sticky="nsew", padx=(25, 15), pady=25)
        
        # Create a centered frame for controls with visual style
        center_frame = ttk.Frame(control_frame)
        center_frame.pack(expand=True, fill="both", padx=25, pady=15)
        
        # Title for controls section
        title_label = ttk.Label(
            center_frame,
            text="Account Generation Settings",
            font=("Helvetica", 12, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Number of accounts with proper spacing and styling
        accounts_frame = ttk.Frame(center_frame)
        accounts_frame.pack(fill="x", pady=(0, 20))
        ttk.Label(
            accounts_frame,
            text="Number of Accounts:",
            font=("Helvetica", 10)
        ).pack(side="left", padx=(0, 10))
        
        # Spinbox with custom style
        self.num_accounts = ttk.Spinbox(
            accounts_frame,
            from_=1,
            to=100,
            width=10,
            font=("Helvetica", 10)
        )
        self.num_accounts.pack(side="left")
        self.num_accounts.set("1")
        
        # Add separator
        ttk.Separator(center_frame, orient="horizontal").pack(fill="x", pady=15)
        
        # Button frame for generate and stop buttons
        button_frame = ttk.Frame(center_frame)
        button_frame.pack(fill="x", pady=15)
        
        # Create custom style for the buttons
        style = ttk.Style()
        style.configure(
            "Generate.TButton",
            font=("Helvetica", 11, "bold"),
            padding=10
        )
        style.configure(
            "Stop.TButton",
            font=("Helvetica", 11, "bold"),
            padding=10
        )
        
        # Generate button
        self.generate_btn = ttk.Button(
            button_frame, 
            text="Generate Accounts",
            command=self.start_generation,
            style="Generate.TButton",
            width=25
        )
        self.generate_btn.pack(expand=True, pady=(0, 10))
        
        # Stop button (initially disabled)
        self.stop_btn = ttk.Button(
            button_frame,
            text="Stop Generation",
            command=self.stop_generation,
            style="Stop.TButton",
            width=25,
            state="disabled"
        )
        self.stop_btn.pack(expand=True)
        
        # Right panel - Generation log with enhanced styling
        log_frame = ttk.LabelFrame(
            self.generator_tab,
            text="Generation Log",
            padding="25"
        )
        log_frame.grid(row=0, column=1, sticky="nsew", padx=(15, 25), pady=25)
        
        # Log title
        log_title = ttk.Label(
            log_frame,
            text="Real-time Generation Output",
            font=("Helvetica", 11, "bold")
        )
        log_title.pack(pady=(0, 10))
        
        # Create log text widget with enhanced styling and dark mode support
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=20, 
            width=60,
            bg='#2B2B2B',  # Dark background
            fg='#A9B7C6',  # Light gray text
            insertbackground='#A9B7C6',  # Cursor color
            selectbackground='#214283',  # Selection background
            selectforeground='#A9B7C6',  # Selection text color
            font=('Consolas', 10),
            padx=15,
            pady=15,
            wrap=tk.WORD
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add a clear log button
        clear_button = ttk.Button(
            log_frame,
            text="Clear Log",
            command=lambda: self.log_text.delete(1.0, tk.END),
            width=15
        )
        clear_button.pack(pady=(10, 0))
        
        # Configure grid weights for better size ratio (1:4)
        self.generator_tab.grid_columnconfigure(1, weight=4)
        self.generator_tab.grid_columnconfigure(0, weight=1)
        self.generator_tab.grid_rowconfigure(0, weight=1)
        
        # Redirect stdout to log text widget
        self.stdout_redirector = ConsoleRedirector(self.log_text)
        
    def create_accounts_tab(self):
        # Toolbar
        toolbar = ttk.Frame(self.accounts_tab)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Left side buttons
        left_buttons = ttk.Frame(toolbar)
        left_buttons.pack(side="left")
        
        # Configure style for dark mode compatibility
        style = ttk.Style()
        style.configure("Treeview", 
            background="#2B2B2B",
            foreground="#A9B7C6",
            fieldbackground="#2B2B2B"
        )
        style.configure("Treeview.Heading",
            background="#383838",
            foreground="#A9B7C6"
        )
        style.map("Treeview",
            background=[('selected', '#214283')],
            foreground=[('selected', '#FFFFFF')]
        )
        
        # Button styles
        style.configure(
            "Login.TButton",
            font=("Helvetica", 10, "bold"),
            padding=5
        )
        
        ttk.Button(left_buttons, text="Import", command=self.import_accounts).pack(side="left", padx=5)
        ttk.Button(left_buttons, text="Refresh", command=self.refresh_accounts).pack(side="left", padx=5)
        ttk.Button(left_buttons, text="Export", command=self.export_accounts).pack(side="left", padx=5)
        ttk.Button(left_buttons, text="Delete", command=self.delete_account).pack(side="left", padx=5)
        
        self.login_btn = ttk.Button(
            left_buttons,
            text="Login Selected",
            command=self.login_selected_account,
            style="Login.TButton"
        )
        self.login_btn.pack(side="left", padx=5)
        
        # Search frame (right side)
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side="right", padx=5)
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_accounts)
        
        # Create and style the search entry
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", padx=5)
        
        # Accounts table with dark mode styling
        columns = ("No.", "Email", "Password", "STOVE ID", "Created", "Last Used", "Status")
        self.accounts_tree = ttk.Treeview(self.accounts_tab, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.accounts_tree.heading(col, text=col)
            width = 100 if col in ("Email", "Password", "STOVE ID") else 80
            self.accounts_tree.column(col, width=width)
        
        self.accounts_tree.grid(row=1, column=0, sticky="nsew")
        
        # Scrollbar with dark mode styling
        scrollbar = ttk.Scrollbar(self.accounts_tab, orient="vertical", command=self.accounts_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.accounts_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure grid weights
        self.accounts_tab.grid_columnconfigure(0, weight=1)
        self.accounts_tab.grid_rowconfigure(1, weight=1)
        
        # Bind double-click event
        self.accounts_tree.bind("<Double-1>", self.show_account_details)
        
    def create_settings_tab(self):
        settings_frame = ttk.LabelFrame(self.settings_tab, text="Generator Settings", padding="10")
        settings_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Email Service Settings
        email_frame = ttk.LabelFrame(settings_frame, text="Email Service", padding="10")
        email_frame.pack(fill="x", pady=5)

        # Email service selection - Updated options
        ttk.Label(email_frame, text="Select Email Service:").pack(side="left", padx=5)
        self.email_service = ttk.Combobox(
            email_frame,
            values=["yopmail.com", "10minutemail.net"],  # Removed guerrillamail.com
            state="readonly",
            width=20
        )
        self.email_service.pack(side="left", padx=5)
        self.email_service.set("yopmail.com")  # Default to yopmail

        # Email domain customization
        domain_frame = ttk.Frame(settings_frame)
        domain_frame.pack(fill="x", pady=5)
        ttk.Label(domain_frame, text="Custom Domain:").pack(side="left", padx=5)
        self.custom_domain = ttk.Entry(domain_frame, width=25)
        self.custom_domain.pack(side="left", padx=5)
        ttk.Label(
            domain_frame, 
            text="(Leave empty to use selected service)",
            foreground="gray"
        ).pack(side="left", padx=5)

        # Add separator
        ttk.Separator(settings_frame, orient="horizontal").pack(fill="x", pady=10)

        # Password settings (existing code)
        password_frame = ttk.Frame(settings_frame)
        password_frame.pack(fill="x", pady=5)
        
        ttk.Label(password_frame, text="Password Length:").pack(side="left")
        self.password_length = ttk.Spinbox(
            password_frame, 
            from_=8,
            to=15,
            width=10
        )
        self.password_length.pack(side="left", padx=5)
        self.password_length.set(str(self.saved_password_length))

        # Add note about password constraints
        ttk.Label(
            settings_frame, 
            text="Note: Password length must be between 8 and 15 characters",
            foreground="gray"
        ).pack(pady=5)

        # Save button
        ttk.Button(settings_frame, text="Save Settings", command=self.save_settings).pack(pady=20)
        
    def create_maintenance_tab(self):
        """Create the maintenance tab with system health and update features"""
        # Main frame
        main_frame = ttk.LabelFrame(self.maintenance_tab, text="System Maintenance", padding="10")
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Update section
        update_frame = ttk.LabelFrame(main_frame, text="Updates", padding="10")
        update_frame.pack(fill="x", pady=5)
        
        # Create and store update label
        self.update_label = ttk.Label(update_frame, text=f"Current Version: v{self.APP_VERSION}")
        self.update_label.pack(pady=5)
        
        ttk.Button(update_frame, text="Check for Updates", 
                  command=self.check_for_updates).pack(pady=5)
        
        # System Health section
        health_frame = ttk.LabelFrame(main_frame, text="System Health", padding="10")
        health_frame.pack(fill="x", pady=5)
        
        # Create and store health text widget
        self.health_text = scrolledtext.ScrolledText(health_frame, height=8, width=50)
        self.health_text.pack(pady=5)
        
        ttk.Button(health_frame, text="Run Health Check", 
                  command=self.check_system_health).pack(pady=5)
        
        # Log Management section
        log_frame = ttk.LabelFrame(main_frame, text="Log Management", padding="10")
        log_frame.pack(fill="x", pady=5)
        
        ttk.Button(log_frame, text="View Logs", 
                  command=self.view_logs).pack(side="left", padx=5)
        ttk.Button(log_frame, text="Clear Old Logs", 
                  command=self.clear_old_logs).pack(side="left", padx=5)
        
        # Error Reports section
        error_frame = ttk.LabelFrame(main_frame, text="Error Reports", padding="10")
        error_frame.pack(fill="x", pady=5)
        
        ttk.Button(error_frame, text="View Error Reports", 
                  command=self.view_error_reports).pack(side="left", padx=5)
        ttk.Button(error_frame, text="Clear Old Reports", 
                  command=self.clear_old_reports).pack(side="left", padx=5)
        
    def start_generation(self):
        if self.is_generating:
            messagebox.showwarning("Warning", "Generation already in progress!")
            return
            
        try:
            num_accounts = int(self.num_accounts.get())
            if num_accounts < 1:
                raise ValueError("Number of accounts must be positive")
                
            # Get the selected email service from settings
            try:
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    email_service = settings.get('email_service', 'yopmail.com')
            except:
                email_service = 'yopmail.com'  # Default if settings can't be loaded
            
            # Get password length from settings
            password_length = settings.get('password_length', 12)
            
            # Initialize generator with selected email service
            self.generator = CrossfireAccountGenerator(
                password_length=password_length,
                email_service=email_service
            )
            
            self.generate_btn.state(["disabled"])
            self.stop_btn.state(["!disabled"])  # Enable stop button
            self.is_generating = True
            self.status_label.configure(text="Status: Generating accounts...")
            
            # Clear log
            self.log_text.delete(1.0, tk.END)
            
            # Start generation in a separate thread
            def generation_thread():
                old_stdout = sys.stdout
                sys.stdout = self.stdout_redirector
                try:
                    self.generate_accounts(num_accounts)
                finally:
                    sys.stdout = old_stdout
            
            thread = threading.Thread(target=generation_thread)
            thread.daemon = True
            thread.start()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            
    def stop_generation(self):
        """Stop the account generation process and close Chrome"""
        if not self.is_generating:
            return
            
        try:
            if self.generator:
                self.generator.close()  # Close Chrome
                self.generator = None
                
            self.is_generating = False
            self.generate_btn.state(["!disabled"])
            self.stop_btn.state(["disabled"])
            self.status_label.configure(text="Status: Ready")
            self.log_text.insert("end", "\nGeneration stopped by user.\n")
            self.log_text.see("end")
            
        except Exception as e:
            self.log_text.insert("end", f"\nError stopping generation: {str(e)}\n")
            self.log_text.see("end")
            
    def generate_accounts(self, num_accounts):
        try:
            if not self.generator:
                # Get password length from settings
                try:
                    password_length = int(self.password_length.get())
                    # Ensure password length is within valid range
                    password_length = min(max(password_length, 8), 15)
                except (ValueError, AttributeError):
                    password_length = 12  # Default if invalid or not set
                
                self.generator = None  # Reset generator
                self.generator = CrossfireAccountGenerator(password_length=password_length)
            
            for i in range(num_accounts):
                if not self.is_generating:  # Check if generation was stopped
                    break
                    
                self.log_text.insert("end", f"\nGenerating account {i+1}/{num_accounts}...\n")
                self.log_text.see("end")
                
                # Create account with our custom verification handler
                def verification_handler():
                    # Clear any previous items in queues
                    while not self.captcha_queue.empty():
                        self.captcha_queue.get()
                    while not self.verification_queue.empty():
                        self.verification_queue.get()
                        
                    self.show_captcha_dialog()
                    # Wait for user to confirm
                    try:
                        self.captcha_queue.get(timeout=300)  # 5 minute timeout
                        return True
                    except queue.Empty:
                        return False
                
                if self.generator.create_account(verification_handler=verification_handler):
                    self.log_text.insert("end", "Account created successfully!\n")
                else:
                    self.log_text.insert("end", "Failed to create account\n")
                
                self.root.update_idletasks()
                
        except Exception as e:
            self.log_text.insert("end", f"Error: {str(e)}\n")
            
        finally:
            self.is_generating = False
            self.generate_btn.state(["!disabled"])
            self.stop_btn.state(["disabled"])
            self.status_label.configure(text="Status: Ready")
            self.refresh_accounts()
            
    def refresh_accounts(self):
        # Clear existing items
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
            
        try:
            # Check if file exists first
            if not os.path.exists('generated_accounts.json'):
                print("No accounts file found")
                return
                
            # Check if file is empty
            if os.path.getsize('generated_accounts.json') == 0:
                print("Accounts file is empty")
                return
                
            # Try to load and parse the accounts file
            try:
                with open('generated_accounts.json', 'r', encoding='utf-8') as f:
                    accounts = json.load(f)
                    
                if not isinstance(accounts, list):
                    print("Invalid accounts data format")
                    return
                
                # Add accounts to the tree view
                for index, account in enumerate(accounts, start=1):
                    status = "Active" if account.get('last_used', 'Never') != 'Never' else "Inactive"
                    self.accounts_tree.insert("", "end", values=(
                        index,  # Account number
                        account.get('email', 'N/A'),
                        account.get('password', 'N/A'),
                        account.get('stove_id', 'N/A'),
                        account.get('created_at', 'N/A'),
                        account.get('last_used', 'Never'),
                        status  # Account status
                    ))
                    
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {str(e)}")
                # Try to reset the file if it's corrupted
                with open('generated_accounts.json', 'w', encoding='utf-8') as f:
                    json.dump([], f)
                    
        except Exception as e:
            print(f"Error refreshing accounts: {str(e)}")
            # Ensure the file exists with valid JSON
            with open('generated_accounts.json', 'w', encoding='utf-8') as f:
                json.dump([], f)
            
    def filter_accounts(self, *args):
        search_term = self.search_var.get().lower()
        self.refresh_accounts()  # Reset the view
        
        if search_term:
            for item in self.accounts_tree.get_children():
                values = self.accounts_tree.item(item)['values']
                if not any(search_term in str(value).lower() for value in values):
                    self.accounts_tree.detach(item)
                    
    def export_accounts(self):
        """Export accounts to a CSV file."""
        try:
            # Open file dialog to select save location
            file_path = tk.filedialog.asksaveasfilename(
                title="Save Accounts As",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not file_path:
                return  # User canceled the save dialog
            
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write header
                f.write("No.,Email,STOVE ID,Created,Last Used,Status\n")
                
                for item in self.accounts_tree.get_children():
                    values = self.accounts_tree.item(item)['values']
                    f.write(','.join(map(str, values)) + '\n')
            
            messagebox.showinfo("Export Complete", "Accounts exported successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export accounts: {str(e)}")
        
    def delete_account(self):
        selected = self.accounts_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an account to delete")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected account(s)?"):
            # Implement delete functionality
            pass
            
    def save_settings(self):
        try:
            # Get current password length
            password_length = int(self.password_length.get())
            
            # Validate password length
            if password_length < 8 or password_length > 15:
                messagebox.showerror("Error", "Password length must be between 8 and 15 characters")
                return
            
            # Get email service settings
            email_service = self.email_service.get()
            custom_domain = self.custom_domain.get().strip()
            
            # Save settings
            settings = {
                "password_length": password_length,
                "theme": self.current_theme,
                "email_service": email_service,
                "custom_domain": custom_domain
            }
            
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=4)
                
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for password length")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
        
    def import_accounts(self):
        """Import accounts from a text file"""
        try:
            # Open file dialog
            file_path = tk.filedialog.askopenfilename(
                title="Select Account File",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Read and parse the file
            imported_accounts = []
            current_account = {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line.startswith('='):
                    if current_account:
                        imported_accounts.append(current_account)
                        current_account = {}
                    continue
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if 'email' in key:
                        current_account['email'] = value
                    elif 'password' in key:
                        current_account['password'] = value
                    elif 'stove' in key:
                        current_account['stove_id'] = value
                    elif 'created' in key:
                        current_account['created_at'] = value
                    
            # Add the last account if exists
            if current_account:
                imported_accounts.append(current_account)
            
            if not imported_accounts:
                messagebox.showwarning("Warning", "No valid accounts found in the file")
                return
            
            # Load existing accounts
            try:
                with open('generated_accounts.json', 'r') as f:
                    existing_accounts = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_accounts = []
            
            # Check for duplicates
            existing_emails = {acc.get('email') for acc in existing_accounts}
            new_accounts = []
            duplicates = 0
            
            for acc in imported_accounts:
                if acc.get('email') not in existing_emails:
                    if 'created_at' not in acc:
                        acc['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_accounts.append(acc)
                    existing_emails.add(acc.get('email'))
                else:
                    duplicates += 1
            
            # Update accounts file
            existing_accounts.extend(new_accounts)
            with open('generated_accounts.json', 'w') as f:
                json.dump(existing_accounts, f, indent=4)
            
            # Update accounts.txt
            with open('accounts.txt', 'a', encoding='utf-8') as f:
                for acc in new_accounts:
                    f.write('\n' + '='*50 + '\n')
                    f.write(f"Account created at: {acc.get('created_at', 'N/A')}\n")
                    f.write(f"Email: {acc.get('email', 'N/A')}\n")
                    f.write(f"Password: {acc.get('password', 'N/A')}\n")
                    f.write(f"STOVE ID: {acc.get('stove_id', 'N/A')}\n")
                    f.write('='*50 + '\n')
            
            # Refresh the accounts view
            self.refresh_accounts()
            
            # Show success message
            messagebox.showinfo(
                "Import Complete",
                f"Successfully imported {len(new_accounts)} accounts\n"
                f"Skipped {duplicates} duplicate accounts"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import accounts: {str(e)}")
        
    def show_account_details(self, event):
        """Show details of the selected account."""
        selected_item = self.accounts_tree.selection()
        if not selected_item:
            return  # No selection made

        item_values = self.accounts_tree.item(selected_item)['values']
        if item_values:
            account_details = (
                f"Account No: {item_values[0]}\n"
                f"Email: {item_values[1]}\n"
                f"STOVE ID: {item_values[2]}\n"
                f"Created: {item_values[3]}\n"
                f"Last Used: {item_values[4]}\n"
                f"Status: {item_values[5]}"
            )
            
            detail_window = tk.Toplevel(self.root)
            detail_window.title("Account Details")
            detail_window.geometry("300x250")
            
            ttk.Label(detail_window, text=account_details).pack(pady=10)
            
            # Copy Email Button
            ttk.Button(detail_window, text="Copy Email", command=lambda: self.copy_to_clipboard(item_values[1])).pack(pady=5)
            # Copy Password Button
            ttk.Button(detail_window, text="Copy Password", command=lambda: self.copy_to_clipboard(item_values[2])).pack(pady=5)
        
    def copy_to_clipboard(self, text):
        """Copy the given text to the clipboard."""
        self.root.clipboard_clear()  # Clear the clipboard
        self.root.clipboard_append(text)  # Append the new text
        messagebox.showinfo("Copied", f"{text} copied to clipboard!")
        
    def open_login_page(self):
        """Open the STOVE login page in the default web browser."""
        webbrowser.open("https://accounts.onstove.com/login")
        
    def toggle_theme(self):
        """Toggle between light and dark mode."""
        if self.current_theme == "Light":
            ctk.set_appearance_mode("Dark")
            self.current_theme = "Dark"
            self.theme_button.configure(text="Switch to Light Mode")
            
            # Update log text colors for dark mode
            self.log_text.configure(
                bg='#2B2B2B',
                fg='#A9B7C6',
                insertbackground='#A9B7C6',
                selectbackground='#214283',
                selectforeground='#A9B7C6'
            )
            
            # Update treeview colors for dark mode
            style = ttk.Style()
            style.configure("Treeview",
                background="#2B2B2B",
                foreground="#A9B7C6",
                fieldbackground="#2B2B2B"
            )
            style.configure("Treeview.Heading",
                background="#383838",
                foreground="#A9B7C6"
            )
            style.map("Treeview",
                background=[('selected', '#214283')],
                foreground=[('selected', '#FFFFFF')]
            )
        else:
            ctk.set_appearance_mode("Light")
            self.current_theme = "Light"
            self.theme_button.configure(text="Switch to Dark Mode")
            
            # Update log text colors for light mode
            self.log_text.configure(
                bg='white',
                fg='black',
                insertbackground='black',
                selectbackground='#0078D7',
                selectforeground='white'
            )
            
            # Update treeview colors for light mode
            style = ttk.Style()
            style.configure("Treeview",
                background="white",
                foreground="black",
                fieldbackground="white"
            )
            style.configure("Treeview.Heading",
                background="SystemButtonFace",
                foreground="black"
            )
            style.map("Treeview",
                background=[('selected', '#0078D7')],
                foreground=[('selected', 'white')]
            )
        
    def show_captcha_dialog(self):
        """Show dialog for CAPTCHA completion"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("CAPTCHA Verification")
        dialog.geometry("300x200")
        dialog.transient(self.root)  # Make dialog modal
        dialog.grab_set()  # Make dialog modal
        
        # Center the dialog on the screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Add instructions
        ctk.CTkLabel(
            dialog,
            text="Please complete the CAPTCHA in the browser.\nOnce completed, click the button below.",
            wraplength=250,
            font=("Helvetica", 12)
        ).pack(pady=20)
        
        # Status label
        status_label = ctk.CTkLabel(
            dialog,
            text="Waiting for CAPTCHA completion...",
            text_color="orange",
            font=("Helvetica", 11)
        )
        status_label.pack(pady=5)
        
        # Add confirmation button
        confirm_button = ctk.CTkButton(
            dialog,
            text="I've Completed the CAPTCHA",
            command=lambda: self.handle_captcha_confirmation(dialog, status_label)
        )
        confirm_button.pack(pady=10)
        
        # Add cancel button
        ctk.CTkButton(
            dialog,
            text="Cancel",
            fg_color="red",
            command=lambda: self.handle_captcha_cancellation(dialog)
        ).pack(pady=5)
        
        return True  # Return True to indicate dialog was shown
        
    def handle_captcha_cancellation(self, dialog):
        """Handle CAPTCHA cancellation"""
        try:
            # Put False in queue to indicate cancellation
            self.captcha_queue.put(False)
            dialog.destroy()
        except Exception as e:
            print(f"Error in CAPTCHA cancellation: {str(e)}")
            
    def handle_captcha_confirmation(self, dialog, status_label):
        """Handle CAPTCHA confirmation button click"""
        try:
            # Update status
            status_label.configure(text="CAPTCHA confirmed!", text_color="green")
            # Put confirmation in queue
            self.captcha_queue.put(True)
            # Close dialog after a short delay
            self.root.after(1000, dialog.destroy)
        except Exception as e:
            status_label.configure(text=f"Error: {str(e)}", text_color="red")
            self.captcha_queue.put(False)  # Put False in queue to indicate error
        
    def show_verification_dialog(self):
        """Show dialog for verification code confirmation"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Verification Code")
        dialog.geometry("300x200")  # Made slightly taller
        dialog.transient(self.root)  # Make dialog modal
        dialog.grab_set()  # Make dialog modal
        
        # Center the dialog on the screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Add instructions
        ctk.CTkLabel(
            dialog,
            text="Please click the 'Confirm Verification Code' button\nin the browser and click the button below when done.",
            wraplength=250,
            font=("Helvetica", 12)
        ).pack(pady=20)
        
        # Status label
        status_label = ctk.CTkLabel(
            dialog,
            text="Waiting for verification...",
            text_color="orange",
            font=("Helvetica", 11)
        )
        status_label.pack(pady=5)
        
        # Add confirmation button
        confirm_button = ctk.CTkButton(
            dialog,
            text="I've Confirmed the Code",
            command=lambda: self.handle_verification_confirmation(dialog, status_label)
        )
        confirm_button.pack(pady=10)
        
        # Add cancel button
        ctk.CTkButton(
            dialog,
            text="Cancel",
            fg_color="red",
            command=dialog.destroy
        ).pack(pady=5)
        
        # Wait for dialog to be closed
        self.root.wait_window(dialog)
        
    def handle_verification_confirmation(self, dialog, status_label):
        """Handle verification confirmation button click"""
        try:
            # Update status
            status_label.configure(text="Verification confirmed!", text_color="green")
            # Put confirmation in queue
            self.verification_queue.put(True)
            # Close dialog after a short delay
            self.root.after(1000, dialog.destroy)
        except Exception as e:
            status_label.configure(text=f"Error: {str(e)}", text_color="red")
        
    def login_selected_account(self):
        """Login to the selected account"""
        selected = self.accounts_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an account to login")
            return
            
        # Get account details
        account_values = self.accounts_tree.item(selected[0])['values']
        email = account_values[1]  # Email is in second column
        
        # Get password from JSON file
        try:
            with open('generated_accounts.json', 'r', encoding='utf-8') as f:
                accounts = json.load(f)
                account = next((acc for acc in accounts if acc.get('email') == email), None)
                if not account or 'password' not in account:
                    messagebox.showerror("Error", "Could not find password for selected account")
                    return
                    
                # Start login process in a separate thread
                def login_thread():
                    try:
                        from stove_login import StoveLogin
                        
                        # Create login handler with CAPTCHA handling
                        def captcha_handler():
                            # Clear any previous items in queues
                            while not self.captcha_queue.empty():
                                self.captcha_queue.get()
                                
                            self.show_captcha_dialog()
                            return True
                            
                        login_handler = StoveLogin(captcha_handler=captcha_handler)
                        
                        if login_handler.login(email, account['password']):
                            # Update last used time and status
                            account['last_used'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            account['status'] = "Active"  # Set status to Active
                            with open('generated_accounts.json', 'w', encoding='utf-8') as f:
                                json.dump(accounts, f, indent=4)
                            self.refresh_accounts()
                            messagebox.showinfo("Success", "Login successful! Account status updated to Active.")
                        else:
                            messagebox.showerror("Error", "Login failed")
                    except Exception as e:
                        messagebox.showerror("Error", f"Login failed: {str(e)}")
                    finally:
                        if login_handler:
                            login_handler.close()
                
                thread = threading.Thread(target=login_thread)
                thread.daemon = True
                thread.start()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not read account data: {str(e)}")
        
    def check_for_updates(self):
        """Check for application updates"""
        try:
            if not self.update_label:
                return
                
            self.update_label.configure(text="Checking for updates...")
            
            # Get update info from maintenance manager
            update_info = self.maintenance.check_for_updates()
            
            # Handle error case
            if "error" in update_info:
                messagebox.showerror(
                    "Update Check Failed", 
                    f"Failed to check for updates: {update_info['error']}"
                )
                self.update_label.configure(text=f"Current Version: v{self.APP_VERSION}")
                return
            
            # Handle update available
            if update_info["update_available"]:
                # Format release notes and date
                release_notes = update_info.get('release_notes', "No release notes available")
                published_date = update_info.get('published_at', '').split('T')[0] if update_info.get('published_at') else 'N/A'
                latest_version = update_info.get('latest_version', 'Unknown')
                
                message = (
                    f"A new version is available!\n\n"
                    f"Current version: v{self.APP_VERSION}\n"
                    f"Latest version: v{latest_version}\n"
                    f"Released on: {published_date}\n\n"
                    f"Release Notes:\n{release_notes}\n\n"
                    "Would you like to download and install it now?"
                )
                
                if messagebox.askyesno("Update Available", message):
                    download_url = update_info.get("download_url")
                    if download_url:
                        self.download_and_install_update(download_url)
                    else:
                        messagebox.showerror(
                            "Update Error",
                            "No download URL available for your platform."
                        )
                else:
                    self.update_label.configure(
                        text=f"Current Version: v{self.APP_VERSION} (Update available: v{latest_version})"
                    )
            else:
                messagebox.showinfo(
                    "Update Check",
                    f"You are running the latest version (v{self.APP_VERSION})"
                )
                self.update_label.configure(text=f"Current Version: v{self.APP_VERSION} (Up to date)")
                
        except Exception as e:
            self.maintenance.report_error(e, {"context": "update_check"})
            messagebox.showerror("Error", f"Failed to check for updates: {str(e)}")
            if self.update_label:
                self.update_label.configure(text=f"Current Version: v{self.APP_VERSION}")

    def download_and_install_update(self, download_url):
        """Download and install the update"""
        if not download_url:
            messagebox.showerror("Update Error", "No download URL available for your platform.")
            return
            
        try:
            # Create progress bar
            progress_frame = ttk.LabelFrame(self.maintenance_tab, text="Download Progress")
            progress_frame.pack(fill="x", padx=10, pady=5)
            
            progress_label = ttk.Label(progress_frame, text="Downloading update...")
            progress_label.pack(pady=2)
            
            progress = ttk.Progressbar(progress_frame, mode='determinate')
            progress.pack(fill="x", padx=5, pady=5)
            
            def update_progress(percent):
                progress['value'] = percent
                progress_label.configure(text=f"Downloading update... {percent:.1f}%")
                self.root.update_idletasks()
            
            def download_thread():
                try:
                    installer_path = self.maintenance.download_update(download_url)
                    if installer_path:
                        self.root.after(0, progress_frame.destroy)
                        
                        # Update version.txt with new version
                        try:
                            update_info = self.maintenance.check_for_updates()
                            if update_info.get("latest_version"):
                                with open('version.txt', 'w') as f:
                                    f.write(f"v{update_info['latest_version']}")
                        except Exception as e:
                            logging.error(f"Failed to update version.txt: {str(e)}")
                        
                        response = messagebox.askyesno(
                            "Update Downloaded",
                            "The update has been downloaded. The application will "
                            "close to install the update. Continue?"
                        )
                        
                        if response:
                            if self.maintenance.install_update(installer_path):
                                messagebox.showinfo(
                                    "Update Ready",
                                    "The application will now close to complete the update."
                                )
                                self.root.quit()
                            else:
                                messagebox.showerror(
                                    "Update Failed",
                                    "Failed to start the installer. Please try again."
                                )
                    else:
                        messagebox.showerror(
                            "Download Failed",
                            "Failed to download the update. Please try again later."
                        )
                except Exception as e:
                    self.maintenance.report_error(e, {"context": "update_install"})
                    messagebox.showerror("Error", f"Failed to install update: {str(e)}")
                finally:
                    if progress_frame.winfo_exists():
                        progress_frame.destroy()
            
            thread = threading.Thread(target=download_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.maintenance.report_error(e, {"context": "update_download"})
            messagebox.showerror("Error", f"Failed to download update: {str(e)}")

    def check_system_health(self):
        """Run system health check"""
        try:
            if not self.health_text:
                return

            health_data = self.maintenance.system_health_check()
            
            # Format health check results
            health_report = "System Health Check Results:\n\n"
            
            # System Info
            health_report += "System Information:\n"
            for key, value in health_data["system"].items():
                health_report += f"- {key}: {value}\n"
            
            # Memory
            health_report += "\nMemory Usage:\n"
            mem = health_data["memory"]
            health_report += (
                f"- Total: {mem['total'] / (1024**3):.2f} GB\n"
                f"- Available: {mem['available'] / (1024**3):.2f} GB\n"
                f"- Usage: {mem['percent']}%\n"
            )
            
            # Disk
            health_report += "\nDisk Usage:\n"
            disk = health_data["disk"]
            health_report += (
                f"- Total: {disk['total'] / (1024**3):.2f} GB\n"
                f"- Free: {disk['free'] / (1024**3):.2f} GB\n"
                f"- Usage: {disk['percent']}%\n"
            )
            
            # Required Components
            health_report += "\nRequired Components:\n"
            health_report += f"- Chrome Installed: {health_data['chrome_installed']}\n"
            
            # Required Files
            health_report += "\nRequired Files:\n"
            for file, exists in health_data["required_files"].items():
                health_report += f"- {file}: {'✓' if exists else '✗'}\n"
            
            # Settings
            health_report += "\nSettings Status:\n"
            health_report += f"- Settings Valid: {health_data['settings_valid']}\n"
            
            # Clear and update health text
            self.health_text.delete('1.0', tk.END)
            self.health_text.insert('1.0', health_report)
            
        except Exception as e:
            self.maintenance.report_error(e, {"context": "health_check"})
            messagebox.showerror("Error", f"Failed to perform health check: {str(e)}")

    def view_logs(self):
        """Open log viewer"""
        try:
            if not os.path.exists(self.maintenance.log_dir):
                messagebox.showinfo("No Logs", "No log files found.")
                return
                
            log_files = [f for f in os.listdir(self.maintenance.log_dir) 
                        if f.endswith('.log') or f.endswith('.log.gz')]
            
            if not log_files:
                messagebox.showinfo("No Logs", "No log files found.")
                return
                
            # Create log viewer window
            log_window = ctk.CTkToplevel(self.root)
            log_window.title("Log Viewer")
            log_window.geometry("800x600")
            
            # Create log file selector
            selector_frame = ttk.Frame(log_window)
            selector_frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(selector_frame, text="Select Log File:").pack(side="left")
            
            log_var = tk.StringVar()
            log_combo = ttk.Combobox(selector_frame, textvariable=log_var)
            log_combo['values'] = log_files
            log_combo.pack(side="left", padx=5)
            
            # Create log viewer
            log_text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD)
            log_text.pack(fill="both", expand=True, padx=5, pady=5)
            
            def load_log(*args):
                log_file = log_var.get()
                if not log_file:
                    return
                    
                log_path = os.path.join(self.maintenance.log_dir, log_file)
                try:
                    if log_file.endswith('.gz'):
                        import gzip
                        with gzip.open(log_path, 'rt') as f:
                            content = f.read()
                    else:
                        with open(log_path, 'r') as f:
                            content = f.read()
                            
                    log_text.delete(1.0, tk.END)
                    log_text.insert(1.0, content)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load log file: {str(e)}")
            
            log_var.trace('w', load_log)
            if log_files:
                log_combo.set(log_files[0])
                
        except Exception as e:
            self.maintenance.report_error(e, {"context": "view_logs"})
            messagebox.showerror("Error", f"Failed to open log viewer: {str(e)}")

    def clear_old_logs(self):
        """Clear old log files"""
        try:
            self.maintenance.manage_logs()
            messagebox.showinfo("Success", "Old log files have been cleared.")
        except Exception as e:
            self.maintenance.report_error(e, {"context": "clear_logs"})
            messagebox.showerror("Error", f"Failed to clear old logs: {str(e)}")

    def view_error_reports(self):
        """View error reports"""
        try:
            reports_dir = "error_reports"
            if not os.path.exists(reports_dir):
                messagebox.showinfo("No Reports", "No error reports found.")
                return
                
            report_files = [f for f in os.listdir(reports_dir) 
                          if f.endswith('.json')]
            
            if not report_files:
                messagebox.showinfo("No Reports", "No error reports found.")
                return
                
            # Create report viewer window
            report_window = ctk.CTkToplevel(self.root)
            report_window.title("Error Report Viewer")
            report_window.geometry("800x600")
            
            # Create report selector
            selector_frame = ttk.Frame(report_window)
            selector_frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(selector_frame, text="Select Report:").pack(side="left")
            
            report_var = tk.StringVar()
            report_combo = ttk.Combobox(selector_frame, textvariable=report_var)
            report_combo['values'] = report_files
            report_combo.pack(side="left", padx=5)
            
            # Create report viewer
            report_text = scrolledtext.ScrolledText(report_window, wrap=tk.WORD)
            report_text.pack(fill="both", expand=True, padx=5, pady=5)
            
            def load_report(*args):
                report_file = report_var.get()
                if not report_file:
                    return
                    
                report_path = os.path.join(reports_dir, report_file)
                try:
                    with open(report_path, 'r') as f:
                        report_data = json.load(f)
                        
                    report_text.delete(1.0, tk.END)
                    report_text.insert(1.0, json.dumps(report_data, indent=4))
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load report: {str(e)}")
            
            report_var.trace('w', load_report)
            if report_files:
                report_combo.set(report_files[0])
                
        except Exception as e:
            self.maintenance.report_error(e, {"context": "view_reports"})
            messagebox.showerror("Error", f"Failed to open report viewer: {str(e)}")

    def clear_old_reports(self):
        """Clear old error reports"""
        try:
            self.maintenance.cleanup_old_files()
            messagebox.showinfo("Success", "Old error reports have been cleared.")
        except Exception as e:
            self.maintenance.report_error(e, {"context": "clear_reports"})
            messagebox.showerror("Error", f"Failed to clear old reports: {str(e)}")

    def schedule_maintenance(self):
        """Schedule periodic maintenance tasks"""
        try:
            # Run maintenance tasks every 24 hours
            self.maintenance.cleanup_old_files()
            self.maintenance.manage_logs()
            
            # Schedule next maintenance
            self.root.after(24 * 60 * 60 * 1000, self.schedule_maintenance)
            
        except Exception as e:
            self.maintenance.report_error(e, {"context": "scheduled_maintenance"})

    def on_close(self):
        """Handle application close"""
        try:
            # Cancel any pending updates
            if hasattr(self, 'root') and self.root:
                self.root.after_cancel('all')
        except:
            pass
        self.root.quit()

    def run(self):
        self.root.mainloop()
        
if __name__ == "__main__":
    app = AccountGeneratorGUI()
    app.run() 