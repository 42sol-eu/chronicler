#!/usr/bin/env python3
"""
Redmine connection diagnostic script.
Tests various ways to connect to the Redmine instance.
"""

import sys
from pathlib import Path
import urllib.request
import urllib.error
from rich.console import Console
from rich.table import Table

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

console = Console()

def test_basic_connection(url: str) -> bool:
    """Test basic HTTP connection to URL."""
    try:
        request = urllib.request.Request(url)
        request.add_header("User-Agent", "chronicler-test/1.0")
        
        with urllib.request.urlopen(request, timeout=10) as response:
            content = response.read().decode('utf-8')
            
            console.print(f"[green]✓[/green] Basic connection successful")
            console.print(f"  Status: {response.status}")
            console.print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
            console.print(f"  Content length: {len(content)} chars")
            
            if content.strip().startswith('<!DOCTYPE html>') or content.strip().startswith('<html'):
                console.print(f"  [yellow]⚠[/yellow] Received HTML content (may be login page)")
                return False
            elif content.strip().startswith('{'):
                console.print(f"  [green]✓[/green] Received JSON content")
                return True
            else:
                console.print(f"  [yellow]⚠[/yellow] Received unexpected content type")
                return False
                
    except urllib.error.HTTPError as e:
        console.print(f"[red]✗[/red] HTTP Error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        console.print(f"[red]✗[/red] URL Error: {e.reason}")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        return False

def test_api_endpoint(base_url: str, api_key: str = None) -> bool:
    """Test API endpoint access."""
    url = f"{base_url}/issues.json?limit=1"
    if api_key:
        url += f"&key={api_key}"
    
    console.print(f"Testing API endpoint: {url.replace(api_key or '', 'XXX')}")
    return test_basic_connection(url)

def load_env_vars() -> dict:
    """Load environment variables from ~/.env."""
    env_file = Path.home() / ".env"
    vars_dict = {}
    
    if not env_file.exists():
        console.print(f"[yellow]⚠[/yellow] No .env file found at {env_file}")
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

def main():
    """Run connection diagnostics."""
    console.print("[bold blue]Redmine Connection Diagnostic Tool[/bold blue]\n")
    
    base_url = "https://stap-software-redmine.stadlerrail.com"
    project_url = "https://stap-software-redmine.stadlerrail.com/projects/linwqezmkvcypxhrbdoa/issues"
    
    # Load environment variables
    console.print("[bold]1. Checking environment variables[/bold]")
    env_vars = load_env_vars()
    
    table = Table(title="Environment Variables")
    table.add_column("Variable", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Value", style="dim")
    
    required_vars = [
        "redmine_user_name", "redmine_user", "redmine_password", 
        "redmine_api_key", "redmine_api_leu"
    ]
    
    for var in required_vars:
        if var in env_vars:
            value_display = env_vars[var][:10] + "..." if len(env_vars[var]) > 10 else env_vars[var]
            table.add_row(var, "✓ Found", value_display)
        else:
            table.add_row(var, "✗ Missing", "")
    
    console.print(table)
    console.print()
    
    # Test basic connectivity
    console.print("[bold]2. Testing basic connectivity[/bold]")
    console.print("Testing main Redmine URL...")
    test_basic_connection(base_url)
    console.print()
    
    console.print("Testing project URL...")
    test_basic_connection(project_url)
    console.print()
    
    # Test API endpoints
    console.print("[bold]3. Testing API endpoints[/bold]")
    
    # Without authentication
    console.print("Testing API without authentication...")
    test_api_endpoint(base_url)
    console.print()
    
    # With API key if available
    api_key = env_vars.get('redmine_api_key') or env_vars.get('redmine_api_leu')
    if api_key:
        console.print("Testing API with API key...")
        test_api_endpoint(base_url, api_key)
    else:
        console.print("[yellow]No API key found - skipping authenticated API test[/yellow]")
    
    console.print()
    
    # Recommendations
    console.print("[bold]4. Recommendations[/bold]")
    
    if api_key:
        console.print("[green]✓[/green] API key found - try using the API key authentication method")
    else:
        console.print("[yellow]⚠[/yellow] No API key found - get one from: https://stap-software-redmine.stadlerrail.com/my/api_key")
    
    username = env_vars.get('redmine_user_name') or env_vars.get('redmine_user')
    password = env_vars.get('redmine_password')
    
    if username and password:
        console.print("[green]✓[/green] Username and password found")
    else:
        console.print("[yellow]⚠[/yellow] Username or password missing")
    
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. If you're getting HTML responses, check if you need VPN access")
    console.print("2. Try accessing the Redmine URL in a web browser first")
    console.print("3. If browser access works, the issue may be with API authentication")
    console.print("4. Consider using the API key method instead of username/password")


if __name__ == "__main__":
    main()
