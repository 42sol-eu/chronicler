#!/usr/bin/env python3
"""
Redmine API client for accessing project tickets.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import urllib.request
import urllib.parse
import urllib.error
import base64
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn


class RedmineClient:
    """Client for accessing Redmine API."""
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize the Redmine client.
        
        Args:
            base_url: Base URL of the Redmine instance
            username: Redmine username
            password: Redmine password
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.console = Console()
        
        # Create authentication header
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an authenticated request to the Redmine API.
        
        Args:
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            Exception: If the request fails
        """
        # Build URL - ensure we're using the API endpoint
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        
        # Make sure we're hitting the API endpoint
        if not endpoint.startswith('/issues.json'):
            endpoint = endpoint.replace('/issues', '/issues.json')
        
        url = f"{self.base_url}{endpoint}"
        
        if params:
            query_string = urllib.parse.urlencode(params)
            url += f"?{query_string}"
        
        # Create request
        request = urllib.request.Request(url)
        request.add_header("Authorization", self.auth_header)
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")
        request.add_header("User-Agent", "chronicler-redmine-client/1.0")
        
        try:
            if self.console:
                self.console.print(f"[dim]Making request to: {url}[/dim]")
            
            with urllib.request.urlopen(request, timeout=30) as response:
                response_data = response.read().decode('utf-8')
                
                if self.console:
                    self.console.print(f"[dim]Response status: {response.status}[/dim]")
                    self.console.print(f"[dim]Response length: {len(response_data)} chars[/dim]")
                
                if response.status == 200:
                    if not response_data.strip():
                        raise Exception("Empty response from server")
                    
                    try:
                        return json.loads(response_data)
                    except json.JSONDecodeError as e:
                        # Log the response for debugging
                        if self.console:
                            self.console.print(f"[dim]Raw response: {response_data[:500]}...[/dim]")
                        raise Exception(f"JSON decode error: {e}")
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                    
        except urllib.error.HTTPError as e:
            error_data = ""
            try:
                error_data = e.read().decode('utf-8')
            except:
                pass
            
            if self.console:
                self.console.print(f"[dim]HTTP Error response: {error_data[:500]}[/dim]")
            raise Exception(f"HTTP {e.code}: {e.reason} - {error_data}")
        except urllib.error.URLError as e:
            raise Exception(f"URL Error: {e.reason}")
        except Exception as e:
            raise Exception(f"Request failed: {e}")
    
    def get_project_issues(self, project_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Get issues for a specific project.
        
        Args:
            project_id: Project identifier
            limit: Maximum number of issues to return per request
            offset: Number of issues to skip
            
        Returns:
            Dictionary containing issues and metadata
        """
        params = {
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
            "status_id": "*",  # Include all statuses
            "sort": "id:desc"  # Sort by ID descending (newest first)
        }
        
        return self._make_request("issues.json", params)
    
    def get_all_project_issues(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all issues for a project (handles pagination).
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of all issues
        """
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
        """
        Display issues in a formatted table.
        
        Args:
            issues: List of issue dictionaries
        """
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
            created_on = issue.get("created_on", "")[:10]  # Just the date part
            updated_on = issue.get("updated_on", "")[:10]  # Just the date part
            
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


def load_credentials() -> tuple[str, str]:
    """
    Load Redmine credentials from ~/.env file.
    
    Returns:
        Tuple of (username, password)
        
    Raises:
        Exception: If credentials are not found or file doesn't exist
    """
    env_file = Path.home() / ".env"
    
    if not env_file.exists():
        raise Exception(f"Environment file not found: {env_file}")
    
    username = None
    password = None
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'').strip()
                
                if key in ['redmine_user_name', 'redmine_user']:
                    username = value
                elif key in ['redmine_password']:
                    password = value
    
    if not username:
        raise Exception("redmine_user_name or redmine_user must be set in ~/.env")
    if not password:
        raise Exception("redmine_password must be set in ~/.env")
    
    return username, password


def extract_project_id_from_url(url: str) -> str:
    """
    Extract project ID from Redmine project URL.
    
    Args:
        url: Full Redmine project URL
        
    Returns:
        Project identifier
    """
    # Extract project ID from URL like:
    # https://stap-software-redmine.stadlerrail.com/projects/linwqezmkvcypxhrbdoa/issues
    parts = url.rstrip('/').split('/')
    for i, part in enumerate(parts):
        if part == 'projects' and i + 1 < len(parts):
            return parts[i + 1]
    
    raise Exception(f"Could not extract project ID from URL: {url}")


def main():
    """Main function to list all tickets in the Redmine project."""
    console = Console()
    
    try:
        # Load credentials
        console.print("[blue]Loading credentials from ~/.env...[/blue]")
        username, password = load_credentials()
        
        # Extract project info from URL
        project_url = "https://stap-software-redmine.stadlerrail.com/projects/linwqezmkvcypxhrbdoa/issues"
        base_url = "https://stap-software-redmine.stadlerrail.com"
        project_id = extract_project_id_from_url(project_url)
        
        console.print(f"[blue]Connecting to Redmine at: {base_url}[/blue]")
        console.print(f"[blue]Project ID: {project_id}[/blue]")
        
        # First, let's try to check if we can access the main page
        console.print("[yellow]Checking Redmine access...[/yellow]")
        
        # Create client and fetch issues
        client = RedmineClient(base_url, username, password)
        
        # Try to access the issues
        issues = client.get_all_project_issues(project_id)
        
        # Display results
        client.display_issues_table(issues)
        
        console.print(f"\n[green]Successfully retrieved {len(issues)} issues![/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("\n[yellow]Troubleshooting tips:[/yellow]")
        console.print("1. Verify that you can access the Redmine URL in a web browser")
        console.print("2. Check if you need to be connected to VPN")
        console.print("3. Verify that your credentials in ~/.env are correct")
        console.print("4. The Redmine instance might require API key authentication instead of username/password")
        console.print(f"5. Try accessing: {base_url}/my/api_key to get an API key")
        sys.exit(1)


if __name__ == "__main__":
    main()
