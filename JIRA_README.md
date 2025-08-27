# Jira Integration

This document describes how to use the Jira integration in Chronicler to fetch and display project groups (epics) and their requirements.

## Setup

### 1. Install Dependencies

The Jira integration requires the `jira` and `python-dotenv` Python packages, which should already be installed if you're using the project dependencies.

### 2. Configure Authentication

You have multiple ways to provide authentication credentials:

#### Option A: .env File (Recommended)

Create a `.env` file in your project directory or home directory:

```bash
# Create .env file in project directory (preferred)
cat > .env << 'EOF'
JIRA_SERVER_URL=https://stadlerrailag.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token-here
EOF

# Or create it in your home directory
cat > ~/.env << 'EOF'
JIRA_SERVER_URL=https://stadlerrailag.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token-here
EOF
```

The CLI will automatically load `.env` from:
1. Current project directory (`./.env`) - **preferred**
2. Home directory (`~/.env`) - **fallback**

#### Option B: Environment Variables

```bash
export JIRA_SERVER_URL='https://stadlerrailag.atlassian.net'
export JIRA_EMAIL='your-email@company.com'
export JIRA_API_TOKEN='your-api-token-here'
```

#### Option C: Command Line Options

You can provide the credentials directly when running the command:

```bash
chronicler jira PPRX --server-url https://stadlerrailag.atlassian.net --email your-email@company.com --api-token your-token
```

**Priority Order:**
1. Command line options (highest priority)
2. Environment variables  
3. .env file values (lowest priority)

### 3. Generate API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a name (e.g., "Chronicler CLI")
4. Copy the generated token

## Usage

### Basic Usage

Fetch all groups and requirements from the PPRX project:

```bash
chronicler jira PPRX
```

### Output Formats

#### Table Format (Default)

Rich, colorized table output with panels for each group:

```bash
chronicler jira PPRX --format table
```

#### JSON Format

Machine-readable JSON output for scripting:

```bash
chronicler jira PPRX --format json
```

### Examples

```bash
# Using .env file (recommended)
# First create .env file with your credentials
cat > .env << 'EOF'
JIRA_SERVER_URL=https://stadlerrailag.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token
EOF

# Then just run the command
chronicler jira PPRX

# Using environment variables
export JIRA_SERVER_URL='https://stadlerrailag.atlassian.net'
export JIRA_EMAIL='your-email@company.com'  
export JIRA_API_TOKEN='your-api-token'
chronicler jira PPRX

# Using command line options (overrides .env and environment variables)
chronicler jira PPRX --server-url https://stadlerrailag.atlassian.net --email your-email@company.com --api-token your-token

# Get JSON output for further processing
chronicler jira PPRX --format json > requirements.json

# Verbose output (shows which .env file was loaded)
chronicler jira PPRX --verbose
```

## Understanding the Output

### Table Format

The table format displays:
- **Groups (Epics)**: Shown as green panels with group name, key, status, description, and requirement count
- **Requirements**: Displayed in a table under each group with:
  - Key: The Jira issue key (e.g., PPRX-123)
  - Summary: The requirement title/summary
  - Status: Current status (e.g., To Do, In Progress, Done)
  - Assignee: Who the requirement is assigned to

### JSON Format

The JSON format provides structured data with:
```json
{
  "project_key": "PPRX",
  "total_groups": 3,
  "groups": [
    {
      "key": "PPRX-1",
      "name": "Group Name",
      "summary": "Group Summary",
      "status": "In Progress",
      "description": "Detailed description...",
      "total_requirements": 5,
      "requirements": [
        {
          "key": "PPRX-2",
          "summary": "Requirement summary",
          "status": "To Do",
          "assignee": "John Doe",
          "description": "Requirement description..."
        }
      ]
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify your email and API token are correct
   - Make sure the API token has proper permissions
   - Check that the server URL is correct (including https://)

2. **No Groups Found**
   - The script tries to detect different issue types automatically
   - Check that your project actually has issues of type "Group" or "Epic"
   - Use `--verbose` flag to see debug information about available issue types

3. **No Requirements Found**
   - Verify that requirements are properly linked to their parent groups/epics
   - Check that the issue type is correctly named "Requirement"
   - The script tries multiple linking strategies (Epic Link, parent relationship)

### Debug Mode

Use the verbose flag to get more information about what's happening:

```bash
chronicler jira PPRX --verbose
```

This will show:
- Connection status
- Available issue types in the project
- Queries being executed
- Number of items found at each step

## Customization

The Jira client automatically adapts to different configurations:
- **Issue Types**: Tries "Group", "Epic", and other common epic types
- **Epic Name Fields**: Tests multiple custom fields commonly used for epic names
- **Linking**: Tests Epic Link, parent relationships, and other common linking methods

If your Jira setup uses different configurations, the script should still work but might need adjustments in the `jira_client.py` file.
