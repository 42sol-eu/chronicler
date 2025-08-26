# Redmine Integration for Chronicler

This directory contains scripts to access Redmine project data and list tickets.

## Files

- `redmine_client.py` - Main Redmine client with username/password authentication
- `redmine_api_key.py` - Alternative client using API key authentication  
- `redmine_tickets.py` - Standalone script using username/password
- `redmine_api_key.py` - Standalone script using API key

## Setup

### Option 1: Username/Password Authentication

Add to your `~/.env` file:
```
redmine_user_name = "your_username"
redmine_password = "your_password"
```

### Option 2: API Key Authentication (Recommended)

1. Visit https://stap-software-redmine.stadlerrail.com/my/api_key to get your API key
2. Add to your `~/.env` file:
```
redmine_api_key = "your_api_key_here"
```

## Usage

### Via Chronicler CLI

```bash
# List all tickets in table format
chronicler redmine

# List tickets in JSON format
chronicler redmine --format json

# Use custom URL
chronicler redmine --url "https://stap-software-redmine.stadlerrail.com/projects/other-project/issues"
```

### Standalone Scripts

```bash
# Using username/password
python redmine_tickets.py

# Using API key
python redmine_api_key.py
```

## Configuration

The default project URL is:
`https://stap-software-redmine.stadlerrail.com/projects/linwqezmkvcypxhrbdoa/issues`

## Troubleshooting

If you're getting HTML responses instead of JSON:

1. **VPN Connection**: Make sure you're connected to the company VPN
2. **Network Authentication**: The Redmine instance might be behind NetScaler AAA or similar
3. **API Access**: Verify that API access is enabled for your account
4. **Credentials**: Double-check your username/password or API key
5. **Permissions**: Ensure you have access to the specific project

### Common Issues

**"Received HTML response instead of JSON"**
- This usually means you're being redirected to a login page
- Check if you need VPN access
- Verify your credentials are correct

**"redmine_user_name/redmine_user and redmine_password must be set"**
- Check the format in your `~/.env` file
- Make sure there are no extra quotes or spaces

**"HTTP 401/403 errors"**
- Your credentials may be incorrect
- You might not have permission to access the project
- Try the API key method instead

### Testing Connection

You can test if you can reach the Redmine instance:

```bash
curl -H "Accept: application/json" "https://stap-software-redmine.stadlerrail.com/issues.json?key=YOUR_API_KEY&limit=1"
```

If this returns HTML instead of JSON, the issue is network/authentication related.

## Features

- **Rich Table Output**: Displays tickets in a formatted table with colors
- **JSON Export**: Can output data in JSON format for further processing
- **Progress Indicators**: Shows progress while fetching large numbers of tickets
- **Pagination Handling**: Automatically fetches all tickets across multiple pages
- **Error Handling**: Comprehensive error messages and troubleshooting tips
- **Flexible Authentication**: Supports both username/password and API key methods

## Example Output

```
                                           Project Issues (45 total)                                            
┏━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ ID    ┃ Subject                                          ┃ Status     ┃ Priority ┃ Assigned To   ┃ Created   ┃ Updated   ┃
┡━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 12345 │ Fix login issue                                  │ In Progress│ High     │ John Doe      │ 2025-08-20│ 2025-08-25│
│ 12344 │ Update documentation                             │ New        │ Normal   │ Unassigned    │ 2025-08-19│ 2025-08-19│
└───────┴──────────────────────────────────────────────────┴────────────┴──────────┴───────────────┴───────────┴───────────┘

Successfully retrieved 45 issues!
```
