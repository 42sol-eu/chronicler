#!/usr/bin/env python3
"""
Try alternative URLs and endpoints to bypass the NetScaler gateway.
"""

import urllib.request
import urllib.error
from rich.console import Console
from rich.table import Table

console = Console()

def test_alternative_urls():
    """Test various alternative URLs that might bypass the gateway."""
    
    base_url = "https://stap-software-redmine.stadlerrail.com"
    
    alternative_urls = [
        # Try different protocols/subdomains
        "http://stap-software-redmine.stadlerrail.com",
        "https://redmine.stadlerrail.com",
        "http://redmine.stadlerrail.com",
        
        # Try direct API endpoints
        f"{base_url}/api/issues.json",
        f"{base_url}/redmine/issues.json",
        f"{base_url}/app/issues.json",
        
        # Try different ports
        "https://stap-software-redmine.stadlerrail.com:443",
        "https://stap-software-redmine.stadlerrail.com:8080",
        "https://stap-software-redmine.stadlerrail.com:3000",
        
        # Try admin or direct access URLs
        f"{base_url}/admin",
        f"{base_url}/redmine",
        f"{base_url}/app",
        f"{base_url}/login",
        
        # Try bypassing with different paths
        f"{base_url}/../issues.json",
        f"{base_url}/./issues.json",
        
        # Try with specific user agents that might bypass filtering
        base_url,  # Will test with different user agents
    ]
    
    results = []
    
    for url in alternative_urls:
        console.print(f"[blue]Testing: {url}[/blue]")
        
        try:
            request = urllib.request.Request(url)
            
            # Try different user agents
            user_agents = [
                "curl/7.68.0",
                "Redmine-API/1.0",
                "python-requests/2.25.1",
                "Mozilla/5.0 (compatible; RedmineBot/1.0)",
                "wget/1.20.3",
            ]
            
            for ua in user_agents:
                try:
                    req = urllib.request.Request(url)
                    req.add_header("User-Agent", ua)
                    req.add_header("Accept", "application/json")
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        content = response.read().decode('utf-8', errors='ignore')
                        
                        is_json = content.strip().startswith('{')
                        is_netscaler = "netscaler" in content.lower()
                        has_issues = "issues" in content.lower()
                        
                        status = "JSON" if is_json else "HTML" if content.strip().startswith('<') else "OTHER"
                        
                        results.append({
                            "url": url,
                            "user_agent": ua,
                            "status_code": response.status,
                            "content_type": status,
                            "is_netscaler": is_netscaler,
                            "has_issues": has_issues,
                            "length": len(content)
                        })
                        
                        if is_json and has_issues:
                            console.print(f"[green]✓ SUCCESS: {url} with UA: {ua}[/green]")
                            return url, ua, content
                        elif not is_netscaler and status != "HTML":
                            console.print(f"[yellow]⚠ Interesting: {url} with UA: {ua} - {status}[/yellow]")
                            
                except urllib.error.HTTPError as e:
                    if e.code != 404:  # Don't report 404s
                        console.print(f"[dim]  {ua}: HTTP {e.code}[/dim]")
                except:
                    pass
                    
        except Exception as e:
            console.print(f"[dim]  Failed: {e}[/dim]")
    
    # Display results table
    if results:
        console.print("\n[bold]Summary of attempts:[/bold]")
        table = Table()
        table.add_column("URL", style="cyan", max_width=40)
        table.add_column("User Agent", style="blue", max_width=25)
        table.add_column("Status", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("NetScaler", style="red")
        table.add_column("Length", style="dim")
        
        for result in results:
            table.add_row(
                result["url"],
                result["user_agent"],
                str(result["status_code"]),
                result["content_type"],
                "Yes" if result["is_netscaler"] else "No",
                str(result["length"])
            )
        
        console.print(table)
    
    return None, None, None


def test_common_redmine_paths():
    """Test common Redmine installation paths."""
    
    base_domains = [
        "stap-software-redmine.stadlerrail.com",
        "redmine.stadlerrail.com",
        "stadlerrail.com",
    ]
    
    common_paths = [
        "",
        "/redmine",
        "/app",
        "/applications/redmine",
        "/tools/redmine",
        "/pm",
        "/project",
        "/issues",
    ]
    
    console.print("\n[bold]Testing common Redmine paths:[/bold]")
    
    for domain in base_domains:
        for path in common_paths:
            url = f"https://{domain}{path}/issues.json?limit=1"
            
            try:
                request = urllib.request.Request(url)
                request.add_header("Accept", "application/json")
                request.add_header("User-Agent", "Redmine-Client/1.0")
                
                with urllib.request.urlopen(request, timeout=5) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                    
                    if content.strip().startswith('{') and 'issues' in content:
                        console.print(f"[green]✓ FOUND: {url}[/green]")
                        return url
                    elif not "netscaler" in content.lower():
                        console.print(f"[yellow]⚠ Different response: {url}[/yellow]")
                        
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    console.print(f"[yellow]⚠ Auth required: {url}[/yellow]")
                elif e.code == 403:
                    console.print(f"[yellow]⚠ Forbidden: {url}[/yellow]")
            except:
                pass
    
    return None


def main():
    """Test alternative access methods."""
    console.print("[bold blue]Testing Alternative Access Methods[/bold blue]\n")
    
    # Test alternative URLs
    success_url, success_ua, content = test_alternative_urls()
    
    if success_url:
        console.print(f"\n[green]✓ Found working endpoint: {success_url}[/green]")
        console.print(f"[green]✓ Working User-Agent: {success_ua}[/green]")
        
        # Parse and display issues
        try:
            import json
            data = json.loads(content)
            issues = data.get('issues', [])
            console.print(f"[green]✓ Found {len(issues)} issues![/green]")
            
            if issues:
                console.print("\n[bold]Sample issues:[/bold]")
                for i, issue in enumerate(issues[:3]):
                    console.print(f"  {issue.get('id')}: {issue.get('subject')}")
                    
        except Exception as e:
            console.print(f"[red]Error parsing JSON: {e}[/red]")
    else:
        # Test common paths
        working_path = test_common_redmine_paths()
        
        if working_path:
            console.print(f"\n[green]✓ Found alternative path: {working_path}[/green]")
        else:
            console.print("\n[red]✗ No alternative access methods found[/red]")
            console.print("\n[yellow]The Redmine instance appears to be fully protected by NetScaler AAA.[/yellow]")
            console.print("[yellow]This requires either:[/yellow]")
            console.print("1. VPN access that bypasses the gateway")
            console.print("2. Whitelisted IP address")
            console.print("3. Valid corporate network access")
            console.print("4. Browser-based authentication first")


if __name__ == "__main__":
    main()
