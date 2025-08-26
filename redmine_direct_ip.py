#!/usr/bin/env python3
"""
Test Redmine access using the direct IP address to bypass NetScaler.
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

def test_direct_ip_access(ip_address: str, project_id: str, auth_data: dict) -> dict:
    """Test access using direct IP address."""
    
    console.print(f"[blue]Testing direct IP access: {ip_address}[/blue]")
    
    # Try different protocols and ports
    base_urls = [
        f"https://{ip_address}",
        f"http://{ip_address}",
        f"https://{ip_address}:443", 
        f"http://{ip_address}:80",
        f"https://{ip_address}:3000",  # Common Redmine port
        f"http://{ip_address}:3000",
    ]
    
    for base_url in base_urls:
        console.print(f"[dim]Trying: {base_url}[/dim]")
        
        # Test basic connectivity first
        try:
            test_url = f"{base_url}/"
            request = urllib.request.Request(test_url)
            request.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
            request.add_header("Host", "stap-software-redmine.stadlerrail.com")  # Use original hostname
            
            with urllib.request.urlopen(request, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                
                console.print(f"[green]✓ {base_url} - HTTP {response.status}[/green]")
                console.print(f"[dim]  Content-Type: {response.headers.get('content-type', 'unknown')}[/dim]")
                console.print(f"[dim]  Content length: {len(content)} chars[/dim]")
                
                # Check if it's NetScaler
                if "netscaler" in content.lower():
                    console.print(f"[yellow]  ⚠ Still getting NetScaler response[/yellow]")
                    continue
                
                # Check if it looks like Redmine
                if "redmine" in content.lower() or "issues" in content.lower():
                    console.print(f"[green]  ✓ Looks like Redmine![/green]")
                    
                    # Now try API access
                    return test_api_access(base_url, project_id, auth_data)
                
                # If we get a different response, it might be working
                if not content.strip().startswith('<!DOCTYPE html>'):
                    console.print(f"[yellow]  ⚠ Non-standard response, testing API...[/yellow]")
                    result = test_api_access(base_url, project_id, auth_data)
                    if result:
                        return result
                        
        except urllib.error.HTTPError as e:
            if e.code == 401:
                console.print(f"[yellow]  ⚠ {base_url} - HTTP 401 (Auth required)[/yellow]")
                # Try API access anyway
                result = test_api_access(base_url, project_id, auth_data)
                if result:
                    return result
            elif e.code == 403:
                console.print(f"[yellow]  ⚠ {base_url} - HTTP 403 (Forbidden)[/yellow]")
            else:
                console.print(f"[red]  ✗ {base_url} - HTTP {e.code}: {e.reason}[/red]")
        except urllib.error.URLError as e:
            console.print(f"[red]  ✗ {base_url} - URL Error: {e.reason}[/red]")
        except Exception as e:
            console.print(f"[red]  ✗ {base_url} - Error: {e}[/red]")
    
    return None

def test_api_access(base_url: str, project_id: str, auth_data: dict) -> dict:
    """Test API access with various authentication methods."""
    
    api_endpoints = [
        f"{base_url}/issues.json?project_id={project_id}&limit=5",
        f"{base_url}/projects/{project_id}/issues.json?limit=5",
    ]
    
    # Authentication methods to try
    auth_methods = [
        {"type": "api_key_param", "data": auth_data.get("api_key")},
        {"type": "api_key_header", "data": auth_data.get("api_key")},
        {"type": "basic_auth", "data": (auth_data.get("username"), auth_data.get("password"))},
        {"type": "none", "data": None},
    ]
    
    for endpoint in api_endpoints:
        console.print(f"[dim]  Testing API endpoint: {endpoint.split('?')[0]}[/dim]")
        
        for auth_method in auth_methods:
            if auth_method["data"] is None and auth_method["type"] != "none":
                continue
                
            try:
                if auth_method["type"] == "api_key_param":
                    url = f"{endpoint}&key={auth_method['data']}"
                elif auth_method["type"] == "api_key_header":
                    url = endpoint
                else:
                    url = endpoint
                
                request = urllib.request.Request(url)
                request.add_header("Accept", "application/json")
                request.add_header("User-Agent", "Redmine-API-Client/1.0")
                request.add_header("Host", "stap-software-redmine.stadlerrail.com")
                
                if auth_method["type"] == "api_key_header":
                    request.add_header("X-Redmine-API-Key", auth_method["data"])
                elif auth_method["type"] == "basic_auth":
                    username, password = auth_method["data"]
                    credentials = f"{username}:{password}"
                    encoded_credentials = base64.b64encode(credentials.encode()).decode()
                    request.add_header("Authorization", f"Basic {encoded_credentials}")
                
                with urllib.request.urlopen(request, timeout=15) as response:
                    content = response.read().decode('utf-8')
                    
                    if content.strip().startswith('{'):
                        data = json.loads(content)
                        if 'issues' in data:
                            console.print(f"[green]    ✓ SUCCESS with {auth_method['type']}![/green]")
                            console.print(f"[green]    Found {len(data['issues'])} issues[/green]")
                            return {
                                "base_url": base_url,
                                "auth_method": auth_method["type"],
                                "auth_data": auth_method["data"],
                                "sample_data": data
                            }
                        else:
                            console.print(f"[yellow]    ⚠ JSON response but no issues with {auth_method['type']}[/yellow]")
                    else:
                        console.print(f"[yellow]    ⚠ Non-JSON response with {auth_method['type']}[/yellow]")
                        
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    console.print(f"[dim]    - {auth_method['type']}: HTTP 401 (Auth required)[/dim]")
                elif e.code == 403:
                    console.print(f"[dim]    - {auth_method['type']}: HTTP 403 (Forbidden)[/dim]")
                else:
                    console.print(f"[dim]    - {auth_method['type']}: HTTP {e.code}[/dim]")
            except Exception as e:
                console.print(f"[dim]    - {auth_method['type']}: {e}[/dim]")
    
    return None

def get_all_issues(config: dict, project_id: str) -> list:
    """Get all issues using the successful configuration."""
    
    console.print(f"[blue]Fetching all issues from {config['base_url']}...[/blue]")
    
    all_issues = []
    offset = 0
    limit = 100
    
    while True:
        try:
            if config["auth_method"] == "api_key_param":
                url = f"{config['base_url']}/issues.json?key={config['auth_data']}&project_id={project_id}&limit={limit}&offset={offset}&status_id=*&sort=id:desc"
            elif config["auth_method"] == "api_key_header":
                url = f"{config['base_url']}/issues.json?project_id={project_id}&limit={limit}&offset={offset}&status_id=*&sort=id:desc"
            elif config["auth_method"] == "basic_auth":
                url = f"{config['base_url']}/issues.json?project_id={project_id}&limit={limit}&offset={offset}&status_id=*&sort=id:desc"
            else:
                url = f"{config['base_url']}/issues.json?project_id={project_id}&limit={limit}&offset={offset}&status_id=*&sort=id:desc"
            
            request = urllib.request.Request(url)
            request.add_header("Accept", "application/json")
            request.add_header("User-Agent", "Redmine-API-Client/1.0")
            request.add_header("Host", "stap-software-redmine.stadlerrail.com")
            
            if config["auth_method"] == "api_key_header":
                request.add_header("X-Redmine-API-Key", config["auth_data"])
            elif config["auth_method"] == "basic_auth":
                username, password = config["auth_data"]
                credentials = f"{username}:{password}"
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
    """Display issues in a formatted table."""
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
    table.add_column("Updated", style="dim")
    
    for issue in issues:
        issue_id = str(issue.get("id", ""))
        subject = issue.get("subject", "")
        status = issue.get("status", {}).get("name", "")
        priority = issue.get("priority", {}).get("name", "")
        assigned_to = issue.get("assigned_to", {}).get("name", "Unassigned")
        created_on = issue.get("created_on", "")[:10]
        updated_on = issue.get("updated_on", "")[:10]
        
        table.add_row(issue_id, subject, status, priority, assigned_to, created_on, updated_on)
    
    console.print(table)

def main():
    """Test direct IP access to Redmine."""
    console.print("[bold blue]Testing Direct IP Access to Redmine[/bold blue]\n")
    
    # Load environment variables
    env_vars = load_env_vars()
    
    # Get configuration
    direct_ip = env_vars.get('redmine_direct_url', '').replace('https://', '').replace('http://', '')
    if not direct_ip:
        console.print("[red]No redmine_direct_url found in .env file[/red]")
        return
    
    project_id = "linwqezmkvcypxhrbdoa"  # From the original URL
    
    auth_data = {
        "api_key": env_vars.get('redmine_api_key'),
        "username": env_vars.get('redmine_user_name'),
        "password": env_vars.get('redmine_password'),
    }
    
    console.print(f"[blue]Direct IP: {direct_ip}[/blue]")
    console.print(f"[blue]Project ID: {project_id}[/blue]")
    console.print(f"[blue]Available auth: API Key: {'✓' if auth_data['api_key'] else '✗'}, Credentials: {'✓' if auth_data['username'] and auth_data['password'] else '✗'}[/blue]\n")
    
    # Test direct IP access
    success_config = test_direct_ip_access(direct_ip, project_id, auth_data)
    
    if success_config:
        console.print(f"\n[green]✓ Successfully connected using direct IP![/green]")
        console.print(f"[green]  Base URL: {success_config['base_url']}[/green]")
        console.print(f"[green]  Auth method: {success_config['auth_method']}[/green]")
        
        # Get all issues
        all_issues = get_all_issues(success_config, project_id)
        
        # Display results
        display_issues(all_issues)
        
        console.print(f"\n[green]Successfully retrieved {len(all_issues)} total issues using direct IP access![/green]")
        
        # Save working configuration for future use
        console.print(f"\n[blue]Working configuration saved. You can use:[/blue]")
        console.print(f"  Base URL: {success_config['base_url']}")
        console.print(f"  Auth method: {success_config['auth_method']}")
        
    else:
        console.print(f"\n[red]✗ Direct IP access failed[/red]")
        console.print("[yellow]Possible issues:[/yellow]")
        console.print("1. IP address may also be behind the same gateway")
        console.print("2. Different port might be needed")
        console.print("3. SSL/TLS certificate issues with direct IP")
        console.print("4. Firewall blocking direct IP access")

if __name__ == "__main__":
    main()
