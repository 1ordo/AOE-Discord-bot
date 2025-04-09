# AOE Discord Bot

A versatile Discord bot featuring translation capabilities, daily quotes, role management, and automated moderation.

## Features

- Multi-language support with automatic translation
- Daily quotes system integrated with Google Sheets
- Advanced role management system
- Poll creation and management
- Thread translation
- AI command integration
- Event logging and monitoring

## Prerequisites

- Python 3.12+
- MySQL Database
- Discord Bot Token
- Google Sheets API credentials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AOE-Bot.git
cd AOE-Bot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your configuration values in `.env`

4. Database setup:
   - Create a MySQL database
   - Update the database credentials in your `.env` file

5. Google Sheets setup:
   - Create a Google Cloud Project
   - Enable Google Sheets API
   - Create service account credentials
   - Save the credentials JSON file as `resources/credentials.json`
   - Share your Google Sheet with the service account email

## Usage

Run the bot:
```bash
python main.py
```

## Commands

- `/translate`: Translate text between languages
- `/poll`: Create interactive polls
- `/quote`: Get the quote of the day
- `/role`: Manage role assignments
- (Add other command documentation)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository.