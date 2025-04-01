# STOVE Account Generator v0.5.3

A Python-based application for automated STOVE account generation with built-in account management and license validation system.

## Key Features

### Account Generation
- **Automated Registration**
  - Smart form filling with randomized data
  - Manual CAPTCHA handling for reliability
  - Automated email verification process
  - Secure password generation
  - Rate limiting protection

### Account Management
- **Comprehensive Storage System**
  - JSON-based account database
  - Backup text file storage
  - Account status tracking (Active/Inactive/Verified)
  - Import/Export functionality
  - Bulk account operations

### Security Features
- **License System**
  - Free license keys available from @Ohh on Discord
  - Automatic validation with expiration dates
  - Offline grace period
  - Device tracking
  - Activity logging

### User Interface
- **Modern Design**
  - Dark/Light theme support
  - Real-time progress tracking
  - Detailed logging window
  - Status indicators
  - Error handling with user-friendly messages

### Maintenance
- **System Tools**
  - Automatic updates via GitHub releases
  - Error reporting
  - Log management
  - Database backup/restore
  - Configuration manager

## System Requirements

- Windows 10 or later
- Python 3.8+
- Google Chrome browser
- 4GB RAM minimum
- Internet connection
- NSIS (for building installer)

## Installation

### Quick Install
1. Download latest release (v0.5.3)
2. Run installer
3. Desktop shortcut will be created automatically
4. Previous versions will be removed automatically

### Developer Installation
```bash
git clone https://github.com/soozu/stove-account-generator.git
cd stove-account-generator
pip install -r requirements.txt
python terminal_generator.py
```

## Building from Source

1. Install NSIS
2. Run build script:
```bash
python build.py
```
Built files will be in `builds/v{version}` directory

## Configuration Options

### Account Generation
- Password length: 8-15 characters
- Generation delay: 0-60 seconds
- Proxy support: HTTP/SOCKS
- Custom email domains
- Name generation patterns

### Interface
- Theme selection (Dark/Light)
- Log level (Debug/Info/Error)
- Window size/position memory
- Custom font settings
- Shortcut preferences

### Storage
- Account database location
- Backup frequency
- Export format (JSON/TXT/CSV)
- Auto-cleanup settings
- Data encryption options

## Usage Guide

1. **Initial Setup**
   - Launch application
   - Contact @Ohh on Discord for free license
   - Enter license key when prompted

2. **Basic Operation**
   - Configure desired settings
   - Set number of accounts (1-100)
   - Click "Start Generation"
   - Handle CAPTCHA if needed
   - Monitor progress

3. **Account Management**
   - View generated accounts
   - Export accounts
   - Check account status
   - Perform bulk operations

4. **Maintenance**
   - Regular backups
   - Clear old logs
   - Update when prompted
   - Report any issues

## Support

- Discord: Contact @Ohh for:
  - Free license keys
  - Technical support
  - Feature requests
  - Bug reports
  - General inquiries

## License & Legal

- **License**: Free for educational purposes
- **Support**: Free support via Discord
- **Updates**: Free automatic updates
- **Disclaimer**: This software is for educational purposes only
- **Usage**: Use responsibly and at your own risk

## Technical Details

### Core Components
- GUI: CustomTkinter
- Web Automation: Selenium/undetected-chromedriver
- Database: JSON/SQLite
- Networking: Requests/Socket
- Encryption: Cryptography

### File Structure
stove-account-generator/
├── terminal_generator.py  # Main terminal interface
├── account_generator.py   # Core generation logic
├── license_manager.py     # License validation
├── maintenance.py        # System maintenance
├── email_handler.py      # Email verification
└── settings.json         # Configuration

## Contributing

This is an educational project. Feel free to:
1. Fork the repository
2. Create feature branch
3. Submit pull requests
4. Report issues
5. Suggest improvements

## Acknowledgments

- Selenium for automation
- CustomTkinter for UI
- undetected-chromedriver for browser control
- Python community for support

## Contact

For all inquiries, contact @Ohh on Discord
Free support and license keys available
Educational use only 
