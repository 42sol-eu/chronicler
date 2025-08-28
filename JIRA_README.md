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

Show only the table of contents (overview):

```bash
chronicler jira PPRX --toc-only
```

### Output Formats

#### Table Format (Default)

Rich, colorized table output with panels for each group:

```bash
chronicler jira PPRX --format table
```

This format now includes:
- **Table of Contents**: Overview of all groups with order, key, name, requirement count, and status
- **Detailed Groups**: Full information for each group including requirements

#### Table of Contents Only

Show only an overview of all groups:

```bash
chronicler jira PPRX --toc-only
```

#### JSON Format

Machine-readable JSON output for scripting:

```bash
chronicler jira PPRX --format json
```

JSON output now includes the `order` field for proper sorting.

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

# Show only table of contents
chronicler jira PPRX --toc-only

# Table of contents in JSON format
chronicler jira PPRX --toc-only --format json

# Verbose output (shows which .env file was loaded)
chronicler jira PPRX --verbose
```

## Understanding the Output

### Ordering

Groups are automatically sorted by their `order` field (if available), then by key as a fallback. This ensures a consistent and logical presentation of requirements groups.

### Field Extraction

The CLI automatically detects and extracts custom fields:

- **Order**: Extracted from both epics and issues for sorting purposes
- **Redmine_ID**: Extracted from issues only (simple integer counter)

The system tries multiple common custom field IDs to find these fields:
- `customfield_10018` through `customfield_10025`
- Variations of the field name (lowercase, without spaces/underscores)

If a field is not found, it will display as "—" in tables and `null` in JSON output.

### Table Format

The table format displays:
- **Table of Contents**: Overview showing order, Redmine ID count, group key, name, requirement count, and status
- **Groups (Epics)**: Shown as green panels with group name (including order prefix), key, order, status, description, and requirement count
- **Requirements**: Displayed in a table under each group with:
  - Key: The Jira issue key (e.g., PPRX-123)
  - Order: The order/sequence number of the requirement within the group
  - Redmine_ID: The Redmine ID associated with this requirement
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
      "order": 1,
      "total_requirements": 5,
      "requirements": [
        {
          "key": "PPRX-2",
          "summary": "Requirement summary",
          "status": "To Do",
          "assignee": "John Doe",
          "description": "Requirement description...",
          "order": 2,
          "redmine_id": 456
        }
      ]
    }
  ]
}
```

### Table of Contents JSON Format

When using `--toc-only --format json`:
```json
{
  "project_key": "PPRX",
  "total_groups": 3,
  "table_of_contents": [
    {
      "order": 1,
      "redmine_ids": [456, 789],
      "redmine_id_count": 2,
      "key": "PPRX-1",
      "name": "Group Name",
      "status": "In Progress",
      "total_requirements": 5
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
