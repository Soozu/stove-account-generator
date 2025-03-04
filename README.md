# Stove Account Generator v1.0.1

## What's New
- Improved password generation
- Fixed dark mode issues
- Added update detection in installer
- Performance improvements

## Files
- Stove_Account_Generator_Setup_v1.0.1.exe (Installer)
- Stove_Account_Generator_v1.0.1.exe (Standalone)

## Installation
1. Uninstall previous version (recommended)
2. Download and run Stove_Account_Generator_Setup_v1.0.1.exe
3. Follow the installation wizard

## Note
Your existing accounts and settings will be preserved during the update.

A Python-based GUI application for automated Stove account generation with built-in account management features.

## Features

- **Automated Account Creation**
  - Automated form filling
  - CAPTCHA handling support
  - Email verification integration
  - Custom password length settings (8-15 characters)

- **Account Management**
  - Save and manage generated accounts
  - Import/Export functionality
  - Account status tracking
  - Built-in account viewer

- **User Interface**
  - Modern GUI with dark/light theme
  - Real-time logging
  - Progress tracking
  - User-friendly settings

## Requirements

- Windows 10 or later
- Python 3.8 or higher
- Google Chrome browser
- NSIS (for building installer)

## Building from Source

1. Install NSIS (Nullsoft Scriptable Install System)
2. Run the build script:
```bash
python build.py
```

The built application and installer will be in the `builds` directory.

## Configuration

- **Password Settings**: Configure password length (8-15 characters)
- **Theme Settings**: Choose between light and dark themes
- **Account Storage**: Accounts are stored in `accounts.json` and `accounts.txt`

## Usage

1. Launch the application
2. Configure desired settings
3. Enter the number of accounts to generate
4. Click "Start Generation"
5. Complete CAPTCHA when prompted
6. Monitor progress in the log window

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Selenium](https://www.selenium.dev/) for web automation
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for modern UI
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) for browser automation

## Disclaimer

This tool is for educational purposes only. Use at your own risk and responsibility. 