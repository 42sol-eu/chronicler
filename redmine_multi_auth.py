#!/usr/bin/env python3
"""
Multi-method Redmine client that tries various authentication approaches.
"""

import sys
from pathlib import Path
import json
import urllib.request
import urllib.parse
import urllib.error
import base64
from rich.console import Console
from rich.table import Table

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

console = Console()


def load_env_vars():
    """Load environment variables from ~/.env."""
    env_file = Path.home() / ".env"
    vars_dict = {}
    
    if not env_file.exists():
        return vars_dict
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'').strip()
                vars_dict[key] = value
    
    return vars_dict


def try_api_key_auth(base_url: str, project_id: str, api_key: str) -> dict:
    """Try API key authentication with various methods."""
    methods = [
        # Method 1: API key as URL parameter
        f"{base_url}/issues.json?key={api_key}&project_id={project_id}&limit=5",
        
        # Method 2: API key as header
        f"{base_url}/issues.json?project_id={project_id}&limit=5",
        
        # Method 3: Different API key parameter name
        f"{base_url}/issues.json?api_key={api_key}&project_id={project_id}&limit=5",
    ]
    
    headers_variants = [
        {"X-Redmine-API-Key": api_key},
        {"X-API-Key": api_key},
        {"Authorization": f"Bearer {api_key}"},
        {"API-Key": api_key},
    ]
    
    for i, url in enumerate(methods):
        console.print(f"[blue]Trying method {i+1}: API key authentication...[/blue]")
        
        try:
            request = urllib.request.Request(url)
            request.add_header("Accept", "application/json")
            request.add_header("User-Agent", "chronicler-redmine/1.0")
            
            # For method 2, add API key as header
            if i == 1:
                for headers in headers_variants:
                    try:
                        req = urllib.request.Request(url)
                        req.add_header("Accept", "application/json")
                        req.add_header("User-Agent", "chronicler-redmine/1.0")
                        for key, value in headers.items():
                            req.add_header(key, value)
                        
                        with urllib.request.urlopen(req, timeout=30) as response:
                            content = response.read().decode('utf-8')
                            if content.strip().startswith('{'):
                                data = json.loads(content)
                                if 'issues' in data:
                                    console.print(f"[green]✓ Success with headers: {headers}[/green]")
                                    return data
                    except:
                        continue
            else:
                with urllib.request.urlopen(request, timeout=30) as response:
                    content = response.read().decode('utf-8')
                    
                    console.print(f"[dim]Response length: {len(content)} chars[/dim]")
                    
                    if content.strip().startswith('{'):
                        data = json.loads(content)
                        if 'issues' in data:
                            console.print(f"[green]✓ Success with method {i+1}![/green]")
                            return data
                    elif content.strip().startswith('<'):
                        console.print(f"[yellow]⚠ Method {i+1}: Got HTML response[/yellow]")
                    else:
                        console.print(f"[yellow]⚠ Method {i+1}: Unexpected response format[/yellow]")
                        
        except urllib.error.HTTPError as e:
            console.print(f"[red]✗ Method {i+1}: HTTP {e.code} - {e.reason}[/red]")
        except Exception as e:
            console.print(f"[red]✗ Method {i+1}: {e}[/red]")
    
    return None


def try_basic_auth(base_url: str, project_id: str, username: str, password: str) -> dict:
    """Try basic HTTP authentication."""
    console.print("[blue]Trying basic HTTP authentication...[/blue]")
    
    try:
        url = f"{base_url}/issues.json?project_id={project_id}&limit=5"
        
        # Create basic auth header
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        auth_header = f"Basic {encoded_credentials}"
        
        request = urllib.request.Request(url)
        request.add_header("Authorization", auth_header)
        request.add_header("Accept", "application/json")
        request.add_header("User-Agent", "chronicler-redmine/1.0")
        
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read().decode('utf-8')
            
            if content.strip().startswith('{'):
                data = json.loads(content)
                if 'issues' in data:
                    console.print("[green]✓ Basic auth successful![/green]")
                    return data
            else:
                console.print("[yellow]⚠ Basic auth: Got HTML response[/yellow]")
                
    except urllib.error.HTTPError as e:
        console.print(f"[red]✗ Basic auth: HTTP {e.code} - {e.reason}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Basic auth: {e}[/red]")
    
    return None


def try_direct_project_access(base_url: str, project_id: str) -> dict:
    """Try accessing project directly without authentication."""
    console.print("[blue]Trying direct access without authentication...[/blue]")
    
    try:
        url = f"{base_url}/projects/{project_id}/issues.json?limit=5"
        
        request = urllib.request.Request(url)
        request.add_header("Accept", "application/json")
        request.add_header("User-Agent", "chronicler-redmine/1.0")
        
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read().decode('utf-8')
            
            if content.strip().startswith('{'):
                data = json.loads(content)
                if 'issues' in data:
                    console.print("[green]✓ Direct access successful![/green]")
                    return data
            else:
                console.print("[yellow]⚠ Direct access: Got HTML response[/yellow]")
                
    except urllib.error.HTTPError as e:
        console.print(f"[red]✗ Direct access: HTTP {e.code} - {e.reason}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Direct access: {e}[/red]")
    
    return None


def get_all_issues(base_url: str, project_id: str, auth_method: str, auth_data: dict) -> list:
    """Get all issues using the successful authentication method."""
    all_issues = []
    offset = 0
    limit = 100
    
    console.print(f"[blue]Fetching all issues using {auth_method}...[/blue]")
    
    while True:
        try:
            if auth_method == "api_key_param":
                url = f"{base_url}/issues.json?key={auth_data['api_key']}&project_id={project_id}&limit={limit}&offset={offset}&status_id=*"
            elif auth_method == "api_key_header":
                url = f"{base_url}/issues.json?project_id={project_id}&limit={limit}&offset={offset}&status_id=*"
            elif auth_method == "basic_auth":
                url = f"{base_url}/issues.json?project_id={project_id}&limit={limit}&offset={offset}&status_id=*"
            elif auth_method == "direct":
                url = f"{base_url}/projects/{project_id}/issues.json?limit={limit}&offset={offset}&status_id=*"
            
            request = urllib.request.Request(url)
            request.add_header("Accept", "application/json")
            request.add_header("User-Agent", "chronicler-redmine/1.0")
            
            if auth_method == "api_key_header":
                request.add_header("X-Redmine-API-Key", auth_data['api_key'])
            elif auth_method == "basic_auth":
                credentials = f"{auth_data['username']}:{auth_data['password']}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                request.add_header("Authorization", f"Basic {encoded_credentials}")
            
            with urllib.request.urlopen(request, timeout=30) as response:
                content = response.read().decode('utf-8')
                data = json.loads(content)
                
                issues = data.get('issues', [])
                if not issues:
                    break
                
                all_issues.extend(issues)
                offset += limit
                
                console.print(f"[dim]Fetched {len(all_issues)} issues so far...[/dim]")
                
                total_count = data.get('total_count', 0)
                if len(all_issues) >= total_count:
                    break
                    
        except Exception as e:
            console.print(f"[red]Error fetching more issues: {e}[/red]")
            break
    
    return all_issues


def display_issues(issues: list):
    """Display issues in a table."""
    if not issues:
        console.print("[yellow]No issues found.[/yellow]")
        return
    
    table = Table(title=f"Redmine Issues ({len(issues)} total)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Subject", style="white", max_width=50)
    table.add_column("Status", style="green")
    table.add_column("Priority", style="yellow")
    table.add_column("Assigned To", style="blue")
    table.add_column("Created", style="magenta")
    
    for issue in issues:
        issue_id = str(issue.get("id", ""))
        subject = issue.get("subject", "")
        status = issue.get("status", {}).get("name", "")
        priority = issue.get("priority", {}).get("name", "")
        assigned_to = issue.get("assigned_to", {}).get("name", "Unassigned")
        created_on = issue.get("created_on", "")[:10]
        
        table.add_row(issue_id, subject, status, priority, assigned_to, created_on)
    
    console.print(table)


def main():
    """Try multiple authentication methods to access Redmine."""
    console.print("[bold blue]Multi-Method Redmine Client[/bold blue]\n")
    
    # Load environment variables
    env_vars = load_env_vars()
    
    base_url = "https://stap-software-redmine.stadlerrail.com"
    project_id = "linwqezmkvcypxhrbdoa"
    
    console.print(f"[blue]Target: {base_url}[/blue]")
    console.print(f"[blue]Project: {project_id}[/blue]\n")
    
    # Try different authentication methods
    result = None
    auth_method = None
    auth_data = {}
    
    # Method 1: API Key
    api_key = env_vars.get('redmine_api_key') or env_vars.get('redmine_api_leu')
    if api_key:
        console.print("[bold]1. Trying API Key Authentication[/bold]")
        result = try_api_key_auth(base_url, project_id, api_key)
        if result:
            auth_method = "api_key_param"  # or determine which method worked
            auth_data = {"api_key": api_key}
    
    # Method 2: Basic Auth
    if not result:
        username = env_vars.get('redmine_user_name') or env_vars.get('redmine_user')
        password = env_vars.get('redmine_password')
        
        if username and password:
            console.print("\n[bold]2. Trying Basic Authentication[/bold]")
            result = try_basic_auth(base_url, project_id, username, password)
            if result:
                auth_method = "basic_auth"
                auth_data = {"username": username, "password": password}
    
    # Method 3: Direct Access
    if not result:
        console.print("\n[bold]3. Trying Direct Access[/bold]")
        result = try_direct_project_access(base_url, project_id)
        if result:
            auth_method = "direct"
    
    if result:
        console.print(f"\n[green]✓ Successfully connected using {auth_method}![/green]")
        console.print(f"[green]Found {len(result.get('issues', []))} issues in sample[/green]\n")
        
        # Get all issues
        all_issues = get_all_issues(base_url, project_id, auth_method, auth_data)
        
        # Display results
        display_issues(all_issues)
        
        console.print(f"\n[green]Successfully retrieved {len(all_issues)} total issues![/green]")
        
    else:
        console.print("\n[red]✗ All authentication methods failed![/red]")
        console.print("\n[yellow]Possible issues:[/yellow]")
        console.print("1. Network connectivity or VPN required")
        console.print("2. Incorrect credentials")
        console.print("3. API access disabled")
        console.print("4. Project access restrictions")
        console.print("5. Corporate firewall blocking access")


if __name__ == "__main__":
    main()
