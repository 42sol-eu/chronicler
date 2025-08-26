#!/usr/bin/env python3
"""
Enhanced Redmine client that handles redirects and authentication flows.
This version can work with NetScaler AAA and other authentication gateways.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn


class RedmineSessionClient:
    """Redmine client that handles authentication sessions and redirects."""
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize the Redmine client with session handling.
        
        Args:
            base_url: Base URL of the Redmine instance
            username: Username for authentication
            password: Password for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.console = Console()
        
        # Set up cookie jar for session management
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            urllib.request.HTTPRedirectHandler()
        )
        
        # Set default headers
        self.opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Accept-Encoding', 'gzip, deflate'),
            ('Connection', 'keep-alive'),
            ('Upgrade-Insecure-Requests', '1'),
        ]
        
        urllib.request.install_opener(self.opener)
        
    def authenticate(self) -> bool:
        """
        Authenticate with the Redmine instance, handling redirects.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.console.print("[blue]Attempting to authenticate...[/blue]")
            
            # First, try to access the main page to see what we get
            main_response = self._make_request_raw(self.base_url)
            
            if "netscaler" in main_response.lower() or "aaa" in main_response.lower():
                self.console.print("[yellow]Detected NetScaler AAA gateway, attempting form-based auth...[/yellow]")
                return self._handle_netscaler_auth(main_response)
            elif "login" in main_response.lower():
                self.console.print("[yellow]Detected Redmine login form, attempting direct auth...[/yellow]")
                return self._handle_redmine_auth(main_response)
            else:
                # Try to access API directly
                return self._test_api_access()
                
        except Exception as e:
            self.console.print(f"[red]Authentication failed: {e}[/red]")
            return False
    
    def _make_request_raw(self, url: str, data: bytes = None, headers: Dict[str, str] = None) -> str:
        """Make a raw HTTP request and return the response text."""
        request = urllib.request.Request(url, data=data)
        
        if headers:
            for key, value in headers.items():
                request.add_header(key, value)
        
        try:
            with self.opener.open(request, timeout=30) as response:
                # Handle gzip encoding
                import gzip
                content = response.read()
                if response.headers.get('content-encoding') == 'gzip':
                    content = gzip.decompress(content)
                return content.decode('utf-8', errors='ignore')
        except Exception as e:
            raise Exception(f"Request failed: {e}")
    
    def _handle_netscaler_auth(self, login_page_content: str) -> bool:
        """Handle NetScaler AAA authentication."""
        try:
            # Look for login form in the NetScaler page
            import re
            
            # Find the form action
            form_action_match = re.search(r'<form[^>]*action="([^"]*)"', login_page_content, re.IGNORECASE)
            if not form_action_match:
                raise Exception("Could not find login form action")
            
            form_action = form_action_match.group(1)
            if form_action.startswith('/'):
                form_action = self.base_url + form_action
            
            # Find form fields
            username_field = "Login"  # Common NetScaler field name
            password_field = "passwd"  # Common NetScaler field name
            
            # Look for actual field names in the form
            username_match = re.search(r'<input[^>]*name="([^"]*)"[^>]*(?:placeholder="[^"]*username|type="text")', login_page_content, re.IGNORECASE)
            password_match = re.search(r'<input[^>]*name="([^"]*)"[^>]*type="password"', login_page_content, re.IGNORECASE)
            
            if username_match:
                username_field = username_match.group(1)
            if password_match:
                password_field = password_match.group(1)
            
            self.console.print(f"[dim]Submitting to: {form_action}[/dim]")
            self.console.print(f"[dim]Username field: {username_field}, Password field: {password_field}[/dim]")
            
            # Prepare form data
            form_data = {
                username_field: self.username,
                password_field: self.password,
                'NSC_USER': self.username,  # Additional NetScaler field
                'NSC_PASSWD': self.password,  # Additional NetScaler field
            }
            
            # Submit login form
            post_data = urllib.parse.urlencode(form_data).encode('utf-8')
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self.base_url,
            }
            
            response = self._make_request_raw(form_action, data=post_data, headers=headers)
            
            # Check if authentication was successful
            if "error" in response.lower() or "invalid" in response.lower():
                return False
            
            # Try to access Redmine after authentication
            return self._test_api_access()
            
        except Exception as e:
            self.console.print(f"[red]NetScaler authentication failed: {e}[/red]")
            return False
    
    def _handle_redmine_auth(self, login_page_content: str) -> bool:
        """Handle direct Redmine authentication."""
        try:
            import re
            
            # Look for Redmine login form
            form_action_match = re.search(r'<form[^>]*action="([^"]*login[^"]*)"', login_page_content, re.IGNORECASE)
            if not form_action_match:
                form_action = f"{self.base_url}/login"
            else:
                form_action = form_action_match.group(1)
                if form_action.startswith('/'):
                    form_action = self.base_url + form_action
            
            # Find authenticity token if present
            token_match = re.search(r'<input[^>]*name="authenticity_token"[^>]*value="([^"]*)"', login_page_content)
            
            form_data = {
                'username': self.username,
                'password': self.password,
                'back_url': f"{self.base_url}/",
            }
            
            if token_match:
                form_data['authenticity_token'] = token_match.group(1)
            
            post_data = urllib.parse.urlencode(form_data).encode('utf-8')
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self.base_url,
            }
            
            response = self._make_request_raw(form_action, data=post_data, headers=headers)
            
            return self._test_api_access()
            
        except Exception as e:
            self.console.print(f"[red]Redmine authentication failed: {e}[/red]")
            return False
    
    def _test_api_access(self) -> bool:
        """Test if we can access the API after authentication."""
        try:
            # Try to access a simple API endpoint
            api_url = f"{self.base_url}/issues.json?limit=1"
            
            request = urllib.request.Request(api_url)
            request.add_header('Accept', 'application/json')
            
            with self.opener.open(request, timeout=30) as response:
                content = response.read().decode('utf-8')
                
                # Check if we got JSON
                if content.strip().startswith('{'):
                    data = json.loads(content)
                    if 'issues' in data or 'total_count' in data:
                        self.console.print("[green]✓ API access successful![/green]")
                        return True
                
                # If we got HTML, authentication probably failed
                if content.strip().startswith('<'):
                    self.console.print("[yellow]Still getting HTML response - authentication may have failed[/yellow]")
                    return False
                
                return False
                
        except Exception as e:
            self.console.print(f"[red]API test failed: {e}[/red]")
            return False
    
    def get_project_issues(self, project_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get issues for a specific project."""
        params = {
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
            "status_id": "*",
            "sort": "id:desc"
        }
        
        query_string = urllib.parse.urlencode(params)
        url = f"{self.base_url}/issues.json?{query_string}"
        
        request = urllib.request.Request(url)
        request.add_header('Accept', 'application/json')
        
        try:
            with self.opener.open(request, timeout=30) as response:
                content = response.read().decode('utf-8')
                
                if not content.strip().startswith('{'):
                    raise Exception("Received non-JSON response - authentication may have expired")
                
                return json.loads(content)
                
        except Exception as e:
            raise Exception(f"Failed to get issues: {e}")
    
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


def load_credentials() -> tuple[str, str]:
    """Load credentials from ~/.env file."""
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


def main():
    """Main function using session-based authentication."""
    console = Console()
    
    try:
        # Load credentials
        console.print("[blue]Loading credentials from ~/.env...[/blue]")
        username, password = load_credentials()
        
        # Setup
        base_url = "https://stap-software-redmine.stadlerrail.com"
        project_id = "linwqezmkvcypxhrbdoa"
        
        console.print(f"[blue]Connecting to Redmine at: {base_url}[/blue]")
        console.print(f"[blue]Project ID: {project_id}[/blue]")
        
        # Create client and authenticate
        client = RedmineSessionClient(base_url, username, password)
        
        if not client.authenticate():
            raise Exception("Authentication failed - check your credentials and network connection")
        
        # Fetch issues
        issues = client.get_all_project_issues(project_id)
        
        # Display results
        client.display_issues_table(issues)
        
        console.print(f"\n[green]Successfully retrieved {len(issues)} issues![/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("\n[yellow]Troubleshooting tips:[/yellow]")
        console.print("1. Make sure you have the correct username and password in ~/.env")
        console.print("2. Try accessing the Redmine URL in a web browser first")
        console.print("3. If you're behind a corporate firewall, you may need VPN access")
        console.print("4. Check if there are any proxy settings required")
        sys.exit(1)


if __name__ == "__main__":
    main()
