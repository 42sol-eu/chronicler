#!/usr/bin/env python3
"""
Alternative Redmine API client using API key authentication.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import urllib.request
import urllib.parse
import urllib.error
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn


class RedmineAPIKeyClient:
    """Redmine client using API key authentication."""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the Redmine client with API key.
        
        Args:
            base_url: Base URL of the Redmine instance
            api_key: Redmine API key
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.console = Console()
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an authenticated request to the Redmine API using API key.
        
        Args:
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        # Build URL
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        
        url = f"{self.base_url}{endpoint}"
        
        # Add API key to parameters
        if params is None:
            params = {}
        params['key'] = self.api_key
        
        query_string = urllib.parse.urlencode(params)
        url += f"?{query_string}"
        
        # Create request
        request = urllib.request.Request(url)
        request.add_header("Accept", "application/json")
        request.add_header("User-Agent", "chronicler-redmine-client/1.0")
        
        try:
            self.console.print(f"[dim]Making request to: {url.replace(self.api_key, 'XXX')}[/dim]")
            
            with urllib.request.urlopen(request, timeout=30) as response:
                response_data = response.read().decode('utf-8')
                
                self.console.print(f"[dim]Response status: {response.status}[/dim]")
                
                if response.status == 200:
                    if not response_data.strip():
                        raise Exception("Empty response from server")
                    
                    # Check if response is HTML (indicating login page)
                    if response_data.strip().startswith('<!DOCTYPE html>') or response_data.strip().startswith('<html'):
                        raise Exception("Received HTML response instead of JSON - authentication may have failed")
                    
                    return json.loads(response_data)
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                    
        except urllib.error.HTTPError as e:
            error_data = ""
            try:
                error_data = e.read().decode('utf-8')
            except:
                pass
            raise Exception(f"HTTP {e.code}: {e.reason} - {error_data}")
        except urllib.error.URLError as e:
            raise Exception(f"URL Error: {e.reason}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON decode error: {e}")
    
    def get_project_issues(self, project_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get issues for a specific project."""
        params = {
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
            "status_id": "*",
            "sort": "id:desc"
        }
        
        return self._make_request("/issues.json", params)
    
    def get_all_project_issues(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all issues for a project (handles pagination)."""
        all_issues = []
        offset = 0
        limit = 100
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Fetching issues...", total=None)
            
            while True:
                try:
                    response = self.get_project_issues(project_id, limit=limit, offset=offset)
                    issues = response.get("issues", [])
                    
                    if not issues:
                        break
                    
                    all_issues.extend(issues)
                    offset += limit
                    
                    progress.update(task, description=f"Fetched {len(all_issues)} issues...")
                    
                    # Check if we've got all issues
                    total_count = response.get("total_count", 0)
                    if len(all_issues) >= total_count:
                        break
                        
                except Exception as e:
                    self.console.print(f"[red]Error fetching issues: {e}[/red]")
                    break
            
            progress.update(task, description=f"Completed: {len(all_issues)} issues fetched")
        
        return all_issues
    
    def display_issues_table(self, issues: List[Dict[str, Any]]) -> None:
        """Display issues in a formatted table."""
        if not issues:
            self.console.print("[yellow]No issues found.[/yellow]")
            return
        
        table = Table(title=f"Project Issues ({len(issues)} total)")
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
            
            table.add_row(
                issue_id,
                subject,
                status,
                priority,
                assigned_to,
                created_on,
                updated_on
            )
        
        self.console.print(table)


def load_api_key() -> str:
    """Load Redmine API key from ~/.env file."""
    env_file = Path.home() / ".env"
    
    if not env_file.exists():
        raise Exception(f"Environment file not found: {env_file}")
    
    api_key = None
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'').strip()
                
                # Check for various possible key names (including typos)
                if key in ['redmine_api_key', 'redmine_api_leu']:
                    api_key = value
                    break
    
    if not api_key:
        raise Exception("redmine_api_key must be set in ~/.env. Get it from: https://stap-software-redmine.stadlerrail.com/my/api_key")
    
    return api_key


def main():
    """Main function using API key authentication."""
    console = Console()
    
    try:
        # Load API key
        console.print("[blue]Loading API key from ~/.env...[/blue]")
        api_key = load_api_key()
        
        # Setup
        base_url = "https://stap-software-redmine.stadlerrail.com"
        project_id = "linwqezmkvcypxhrbdoa"
        
        console.print(f"[blue]Connecting to Redmine at: {base_url}[/blue]")
        console.print(f"[blue]Project ID: {project_id}[/blue]")
        
        # Create client and fetch issues
        client = RedmineAPIKeyClient(base_url, api_key)
        issues = client.get_all_project_issues(project_id)
        
        # Display results
        client.display_issues_table(issues)
        
        console.print(f"\n[green]Successfully retrieved {len(issues)} issues![/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("\n[yellow]Troubleshooting tips:[/yellow]")
        console.print("1. Get your API key from: https://stap-software-redmine.stadlerrail.com/my/api_key")
        console.print("2. Add 'redmine_api_key=YOUR_API_KEY' to ~/.env")
        console.print("3. Make sure you can access the Redmine instance (VPN may be required)")
        sys.exit(1)


if __name__ == "__main__":
    main()
