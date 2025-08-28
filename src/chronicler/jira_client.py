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
    order: Optional[float] = None
    redmine_id: Optional[int] = None


@dataclass
class JiraEpic:
    """Represents a Jira epic (Group)."""
    key: str
    name: str
    summary: str
    status: str
    description: Optional[str]
    requirements: List[JiraIssue]
    order: Optional[float] = None


class JiraClient:
    """Client for interacting with Jira API."""
    
    def __init__(self, server_url: str, email: str, api_token: str):
        """Initialize Jira client."""
        self.server_url = server_url
        self.email = email
        self.api_token = api_token
        self.jira = None
        self._debug_fields_shown = False
        self._debug_req_fields_shown = False
        
    def connect(self) -> bool:
        """Test connection to Jira."""
        try:
            # Import jira here to avoid dependency issues
            from jira import JIRA
            
            # Create JIRA connection
            self.jira = JIRA(
                server=self.server_url,
                basic_auth=(self.email, self.api_token)
            )
            
            # Test connection by getting user info
            user = self.jira.current_user()
            console.print(f"[green]✓[/green] Connected to Jira as: {user}")
            return True
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to connect to Jira: {e}")
            return False
    
    def _extract_custom_field_value(self, issue, field_name: str, field_type: str = "string"):
        """Extract custom field value from issue, trying various possible field names."""
        # Define field-specific patterns
        if field_name.lower() in ["order"]:
            possible_fields = [
                'customfield_12268',  # Specific order field (Chapter.Subchapter format)
                'customfield_11649',  # Backup order fields
                'customfield_11650',
                'customfield_10019',
                'customfield_10018',
                'customfield_10020',
                'order',
                'orderfield',
            ]
        elif field_name.lower() in ["redmine_id", "redmineid"]:
            possible_fields = [
                'customfield_10020',  # Common Redmine ID field
                'customfield_10021',
                'customfield_10022',
                'customfield_10023',
                'customfield_10024',
                'redmine_id',
                'redmineid',
                'customfield_10018',
                'customfield_10019',
            ]
        else:
            # Generic field patterns
            possible_fields = [
                f'customfield_12268',  # Add the specific order field to generic search too
                f'customfield_10018',
                f'customfield_10019',
                f'customfield_10020',
                f'customfield_10021',
                f'customfield_10022',
                f'customfield_10023',
                f'customfield_10024',
                f'customfield_10025',
                field_name.lower(),
                field_name.lower().replace('_', ''),
                field_name.lower().replace(' ', ''),
                field_name.replace(' ', '_').lower(),
            ]
        
        for field_id in possible_fields:
            try:
                field_value = getattr(issue.fields, field_id, None)
                if field_value is not None:
                    # Handle different field types
                    if field_type == "int":
                        if isinstance(field_value, (int, float)):
                            return int(field_value)
                        elif isinstance(field_value, str) and field_value.strip().isdigit():
                            return int(field_value.strip())
                    elif field_type == "float":
                        if isinstance(field_value, (int, float)):
                            return float(field_value)
                        elif isinstance(field_value, str):
                            try:
                                return float(field_value.strip())
                            except ValueError:
                                continue
                    elif field_type == "string":
                        return str(field_value).strip() if field_value else None
                    else:
                        return field_value
            except (ValueError, AttributeError):
                continue
        
        return None
    
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
            # Get epic name
            epic_name = getattr(epic_issue.fields, 'customfield_10011', epic_issue.fields.summary)
            if not epic_name:
                epic_name = epic_issue.fields.summary
            
            # Extract order field for epic
            order = self._extract_custom_field_value(epic_issue, "Order", "float")
            
            # Get all requirements for this epic
            requirements = self._get_epic_requirements(project_key, epic_issue.key)
            
            # Skip epics with no requirements unless it's the first query result
            if not requirements and len(epics_issues) > 1:
                try:
                    # Double-check with a broader search for this specific epic
                    broader_search = self.jira.search_issues(
                        f'project = {project_key} AND "Epic Link" = {epic_issue.key}',
                        maxResults=50
                    )
                    if not broader_search:
                        continue
                except:
                    continue
            
            epic = JiraEpic(
                key=epic_issue.key,
                name=epic_name,
                summary=epic_issue.fields.summary,
                status=epic_issue.fields.status.name,
                description=getattr(epic_issue.fields, 'description', None),
                requirements=requirements,
                order=order
            )
            epics.append(epic)        # Sort epics by order field (if available), then by key as fallback
        epics.sort(key=lambda e: (e.order if e.order is not None else 999999.0, e.key))
                
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
                            
                            # Extract Order field for issue (used for both epics and issues)
                            order = self._extract_custom_field_value(req_issue, "Order", "float")
                            
                            # Extract Redmine ID field (only for issues)
                            redmine_id = self._extract_custom_field_value(req_issue, "Redmine_ID", "int")
                            
                            requirement = JiraIssue(
                                key=req_issue.key,
                                summary=req_issue.fields.summary,
                                issue_type=req_issue.fields.issuetype.name,
                                status=req_issue.fields.status.name,
                                assignee=req_issue.fields.assignee.displayName if req_issue.fields.assignee else None,
                                description=getattr(req_issue.fields, 'description', None),
                                epic_key=epic_key,
                                order=order,
                                redmine_id=redmine_id
                            )
                            requirements.append(requirement)
                    
                    break  # Stop trying other queries if we found something
                    
            except Exception as e:
                console.print(f"[yellow]Query failed:[/yellow] {jql} - {e}")
                continue
        
        if not requirements:
            console.print(f"[yellow]No requirements found for epic {epic_key}[/yellow]")
        else:
            # Sort requirements by order field (if available), then by key as fallback
            requirements.sort(key=lambda r: (r.order if r.order is not None else 999999.0, r.key))
                
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
