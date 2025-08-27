#!/usr/bin/env python3
"""Jira client for interacting with Atlassian Jira API."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from jira import JIRA
from rich.console import Console

console = Console()


@dataclass
class JiraIssue:
    """Represents a Jira issue."""
    key: str
    summary: str
    issue_type: str
    status: str
    assignee: Optional[str]
    description: Optional[str]
    epic_key: Optional[str] = None
    epic_name: Optional[str] = None


@dataclass
class JiraEpic:
    """Represents a Jira epic (Group)."""
    key: str
    name: str
    summary: str
    status: str
    description: Optional[str]
    requirements: List[JiraIssue]
    order: Optional[int] = None


class JiraClient:
    """Client for interacting with Jira API."""
    
    def __init__(self, server_url: str, email: str, api_token: str):
        """Initialize Jira client."""
        self.server_url = server_url
        self.email = email
        self.api_token = api_token
        self.jira = None
        
    def connect(self) -> bool:
        """Connect to Jira instance."""
        try:
            self.jira = JIRA(
                server=self.server_url,
                basic_auth=(self.email, self.api_token)
            )
            # Test connection
            self.jira.myself()
            console.print("[green]✓[/green] Successfully connected to Jira")
            return True
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to connect to Jira: {e}")
            return False
    
    def get_project_epics(self, project_key: str) -> List[JiraEpic]:
        """Get all epics (Groups) from a project."""
        if not self.jira:
            raise RuntimeError("Not connected to Jira")
        
        # First, let's try to get all issue types to understand the structure
        try:
            project = self.jira.project(project_key)
            console.print(f"[blue]Project:[/blue] {project.name}")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not fetch project details: {e}[/yellow]")
        
        # Query for epics/groups in the project
        # Try multiple potential names for the epic work type
        epic_type_queries = [
            f'project = {project_key} AND type = "Group"',
            f'project = {project_key} AND type = "Epic"',
            f'project = {project_key} AND type in ("Group", "Epic")'
        ]
        
        epics_issues = []
        successful_query = None
        
        for jql in epic_type_queries:
            try:
                issues = self.jira.search_issues(f'{jql} ORDER BY key', maxResults=100)
                if issues:
                    epics_issues = issues
                    successful_query = jql
                    console.print(f"[green]Found {len(issues)} epics using query:[/green] {jql}")
                    break
            except Exception as e:
                console.print(f"[yellow]Query failed:[/yellow] {jql} - {e}")
                continue
        
        if not epics_issues and not successful_query:
            # Fallback: try to get all issues and filter by type
            console.print("[yellow]Trying fallback approach...[/yellow]")
            try:
                all_issues = self.jira.search_issues(f'project = {project_key} ORDER BY key', maxResults=500)
                console.print(f"[blue]Found {len(all_issues)} total issues in project[/blue]")
                
                # Show available issue types
                issue_types = set()
                for issue in all_issues:
                    issue_types.add(issue.fields.issuetype.name)
                
                console.print(f"[blue]Available issue types:[/blue] {', '.join(sorted(issue_types))}")
                
                # Filter for potential epic types
                epic_types = [t for t in issue_types if any(keyword in t.lower() for keyword in ['epic', 'group', 'initiative'])]
                if epic_types:
                    console.print(f"[green]Potential epic types found:[/green] {', '.join(epic_types)}")
                    epics_issues = [issue for issue in all_issues if issue.fields.issuetype.name in epic_types]
                else:
                    console.print("[yellow]No obvious epic types found. Using all issues as potential epics.[/yellow]")
                    epics_issues = all_issues[:10]  # Limit to first 10 to avoid too much output
                    
            except Exception as e:
                console.print(f"[red]Fallback approach failed:[/red] {e}")
                return []
        
        epics = []
        
        for epic_issue in epics_issues:
            # Get requirements for this epic
            requirements = self._get_epic_requirements(project_key, epic_issue.key)
            
            # Try to get epic name from various possible fields
            epic_name = epic_issue.fields.summary  # Default to summary
            
            # Common epic name fields to try
            epic_name_fields = ['customfield_10011', 'customfield_10014', 'customfield_10004']
            for field_name in epic_name_fields:
                try:
                    field_value = getattr(epic_issue.fields, field_name, None)
                    if field_value and isinstance(field_value, str):
                        epic_name = field_value
                        break
                except:
                    continue
            
            epic = JiraEpic(
                key=epic_issue.key,
                name=epic_name,
                summary=epic_issue.fields.summary,
                status=epic_issue.fields.status.name,
                description=getattr(epic_issue.fields, 'description', None),
                requirements=requirements
            )
            epics.append(epic)
                
        return epics
    
    def _get_epic_requirements(self, project_key: str, epic_key: str) -> List[JiraIssue]:
        """Get all requirements for a specific epic."""
        # Try multiple ways to find requirements linked to this epic
        requirement_queries = [
            f'project = {project_key} AND type = "Requirement" AND "Epic Link" = {epic_key}',
            f'project = {project_key} AND issuetype = "Requirement" AND "Epic Link" = {epic_key}',
            f'project = {project_key} AND "Epic Link" = {epic_key}',  # Get all linked issues
            f'project = {project_key} AND parent = {epic_key}',  # For hierarchical relationships
        ]
        
        requirements = []
        
        for jql in requirement_queries:
            try:
                requirement_issues = self.jira.search_issues(f'{jql} ORDER BY key', maxResults=100)
                
                if requirement_issues:
                    console.print(f"[green]Found {len(requirement_issues)} linked issues for {epic_key}[/green]")
                    
                    for req_issue in requirement_issues:
                        # Filter for actual requirements if we got all linked issues
                        if 'requirement' in req_issue.fields.issuetype.name.lower() or len(requirement_queries) == 1:
                            requirement = JiraIssue(
                                key=req_issue.key,
                                summary=req_issue.fields.summary,
                                issue_type=req_issue.fields.issuetype.name,
                                status=req_issue.fields.status.name,
                                assignee=req_issue.fields.assignee.displayName if req_issue.fields.assignee else None,
                                description=getattr(req_issue.fields, 'description', None),
                                epic_key=epic_key
                            )
                            requirements.append(requirement)
                    
                    break  # Stop trying other queries if we found something
                    
            except Exception as e:
                console.print(f"[yellow]Query failed:[/yellow] {jql} - {e}")
                continue
        
        if not requirements:
            console.print(f"[yellow]No requirements found for epic {epic_key}[/yellow]")
                
        return requirements
    
    @staticmethod
    def from_env() -> Optional['JiraClient']:
        """Create JiraClient from environment variables."""
        server_url = os.getenv('JIRA_SERVER_URL')
        email = os.getenv('JIRA_EMAIL')
        api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([server_url, email, api_token]):
            missing = [var for var, val in [
                ('JIRA_SERVER_URL', server_url),
                ('JIRA_EMAIL', email),
                ('JIRA_API_TOKEN', api_token)
            ] if not val]
            console.print(f"[red]Missing environment variables:[/red] {', '.join(missing)}")
            return None
            
        return JiraClient(server_url, email, api_token)
