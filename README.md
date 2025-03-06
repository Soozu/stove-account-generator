# Stove Account Generator

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

## Installation

### Using Installer
1. Download the latest release
2. Run the installer
3. Follow the installation wizard

### Manual Installation
1. Clone the repository
```bash
git clone https://github.com/soozu/stove-account-generator.git
cd stove-account-generator
```

2. Install required packages
```bash
pip install -r requirements.txt
```

3. Run the application
```bash
python gui_interface.py
```

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

# STOVE License Server

A secure license validation server for the STOVE Account Generator.

## Setup

1. Clone the repository
2. Create a `.env` file based on `.env.example`
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Variables

Copy `.env.example` to `.env` and configure:
- `API_KEY`: Your secure API key for admin operations
- `DB_PATH`: Path to the license database file
- `ENCRYPTION_KEY`: Your encryption key for secure communication
- `SERVER_URL`: Your server's URL

## Deployment

1. Set up a Railway account
2. Connect your GitHub repository
3. Configure environment variables in Railway dashboard
4. Deploy

## Security Notes

- Keep your `.env` file secure and never commit it
- Regularly rotate API keys
- Monitor server logs for unauthorized access attempts
- Use HTTPS in production

## License

Private - All rights reserved

## Contact

For support or inquiries, contact on Discord: Ohhh#8261 