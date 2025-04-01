# STOVE Account Generator (Terminal)

A Python-based terminal application for automated STOVE account generation with built-in account management and license validation system.

## Key Features

### Account Generation
- **Automated Registration**
  - Smart form filling with randomized data
  - Manual CAPTCHA handling
  - Automated email verification process
  - Secure password generation
  - Rate limiting protection

### Account Management
- **Comprehensive Storage System**
  - JSON-based account database
  - Backup text file storage
  - Account status tracking
  - Automatic saving to FREE ACCOUNTS folder
  - Daily account organization

### Security Features
- **License System**
  - Free license keys available from @Ohh on Discord
  - Automatic validation
  - Monthly expiration system
  - Device tracking
  - Activity logging

### System Tools
- **Maintenance Features**
  - Automatic updates
  - Error reporting
  - Log management
  - System health monitoring
  - Configuration manager

## System Requirements

- Windows 10 or later
- Python 3.8+
- Google Chrome browser
- 4GB RAM minimum
- Internet connection

## Installation

### Quick Install
1. Download latest release
2. Run the executable
3. Enter license key when prompted
4. Start generating accounts

### Developer Installation
```bash
git clone https://github.com/soozu/stove-account-generator.git
cd stove-account-generator
pip install -r requirements.txt
python terminal_generator.py
```

## Building from Source

1. Run build script:
```bash
python build.py
```
Built files will be in `dist` directory

## Usage Guide

1. **Initial Setup**
   - Launch application
   - Contact @Ohh on Discord for free license
   - Enter license key when prompted

2. **Basic Operation**
   - Select "Generate Accounts" from menu
   - Enter number of accounts (1-100)
   - Handle CAPTCHA when prompted
   - Monitor progress in terminal

3. **Account Management**
   - View recent accounts from menu
   - Check system health
   - View logs
   - Check for updates

4. **Maintenance**
   - Regular system health checks
   - Automatic updates
   - Log viewing
   - Error reporting

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
- Terminal Interface
- Web Automation: Selenium/undetected-chromedriver
- Database: JSON
- Networking: Requests
- Email: TempMailHandler

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
- undetected-chromedriver for browser control
- Python community for support

## Contact

For all inquiries, contact @Ohh on Discord
Free support and license keys available
Educational use only 
