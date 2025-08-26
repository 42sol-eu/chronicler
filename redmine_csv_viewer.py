#!/usr/bin/env python3
"""
Rich CSV Viewer for Redmine Issues
Displays German CSV exports from Redmine with proper formatting and German character support.
"""

import csv
import sys
from datetime import datetime
from typing import Any, Dict, List

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt
from rich.table import Table

def fix_german_encoding(text: str) -> str:
    """Fix common German character encoding issues."""
    if not isinstance(text, str):
        return text
    
    # Common encoding fixes for German characters
    replacements = {
        'Ã¤': 'ä',  # a umlaut
        'Ã¶': 'ö',  # o umlaut  
        'Ã¼': 'ü',  # u umlaut
        'ÃŸ': 'ß',  # eszett
        'Ã„': 'Ä',  # A umlaut
        'Ã–': 'Ö',  # O umlaut
        'Ãœ': 'Ü',  # U umlaut
        'â‚¬': '€',  # Euro symbol
        'â€œ': '"',  # left double quote
        'â€': '"',   # right double quote
        'â€™': "'",  # right single quote
        'â€˜': "'",  # left single quote
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def get_combined_order_number(issue: Dict[str, Any]) -> str:
    """Combine Auftragsnummer/-name and FIS Auftragsnummer/-name into one field."""
    order = fix_german_encoding(str(issue.get('Auftragsnummer/-name', ''))).strip()
    fis_order = fix_german_encoding(str(issue.get('FIS Auftragsnummer/-name', ''))).strip()
    
    # Combine both fields, removing duplicates and empty values
    combined_parts = []
    if order:
        combined_parts.append(order)
    if fis_order and fis_order != order:  # Avoid duplicates
        combined_parts.append(fis_order)
    
    return ' | '.join(combined_parts) if combined_parts else 'No Order'

def filter_by_order(data: List[Dict[str, Any]], order_filter: str) -> List[Dict[str, Any]]:
    """Filter issues by order number (case-insensitive partial match)."""
    if not order_filter:
        return data
    
    order_filter_lower = order_filter.lower()
    filtered = []
    
    for issue in data:
        combined_order = get_combined_order_number(issue).lower()
        if order_filter_lower in combined_order:
            filtered.append(issue)
    
    return filtered

def group_by_order(data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group issues by combined order number."""
    groups = {}
    
    for issue in data:
        order = get_combined_order_number(issue)
        if order not in groups:
            groups[order] = []
        groups[order].append(issue)
    
    return groups

console = Console()

def load_csv_data(filename: str) -> List[Dict[str, Any]]:
    """Load CSV data with automatic encoding detection and German umlaut support."""
    console = Console()
    
    # Try different encodings, prioritizing ones that handle German umlauts well
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
    
    for encoding in encodings:
        try:
            console.print(f"Trying encoding: {encoding}")
            with open(filename, 'r', encoding=encoding) as file:
                # Detect delimiter
                sample = file.read(1024)
                file.seek(0)
                
                delimiter = ';' if sample.count(';') > sample.count(',') else ','
                console.print(f"Using delimiter: '{delimiter}'")
                
                # Use progress bar for loading
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("Loading issues...", total=None)
                    
                    reader = csv.DictReader(file, delimiter=delimiter)
                    data = []
                    
                    for row in reader:
                        # Clean up any encoding artifacts and normalize data
                        cleaned_row = {}
                        for key, value in row.items():
                            if key and value:
                                # Fix German encoding issues
                                clean_key = fix_german_encoding(key)
                                clean_value = fix_german_encoding(str(value))
                                cleaned_row[clean_key] = clean_value
                            else:
                                cleaned_row[key] = value
                        data.append(cleaned_row)
                    
                    progress.update(task, completed=True)
                
                console.print(f"[green]Successfully loaded with {encoding} encoding![/green]")
                return data
                
        except UnicodeDecodeError:
            console.print(f"Encoding {encoding} failed, trying next...")
            continue
        except Exception as e:
            console.print(f"Error with {encoding}: {e}")
            continue
    
    console.print("[red]Failed to load CSV with any encoding[/red]")
    return []

def get_status_style(status: str) -> str:
    """Get color style based on issue status."""
    status_lower = status.lower()
    if 'new' in status_lower or 'open' in status_lower:
        return "red"
    elif 'progress' in status_lower or 'assigned' in status_lower:
        return "yellow"
    elif 'resolved' in status_lower or 'closed' in status_lower or 'done' in status_lower:
        return "green"
    elif 'feedback' in status_lower or 'review' in status_lower:
        return "blue"
    else:
        return "white"

def get_priority_style(priority: str) -> str:
    """Get color style based on priority."""
    priority_lower = priority.lower()
    if 'urgent' in priority_lower or 'immediate' in priority_lower or 'critical' in priority_lower:
        return "bold red"
    elif 'high' in priority_lower:
        return "red"
    elif 'normal' in priority_lower or 'medium' in priority_lower:
        return "yellow"
    elif 'low' in priority_lower:
        return "green"
    else:
        return "white"

def format_date(date_str: str) -> str:
    """Format date string for display."""
    if not date_str:
        return ""
    
    try:
        # Try different date formats
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%d.%m.%Y']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        return date_str[:10]  # Fallback to first 10 chars
    except:
        return date_str

def create_summary_panel(data: List[Dict[str, Any]]) -> Panel:
    """Create a summary panel with statistics."""
    if not data:
        return Panel("No data loaded", title="Summary")
    
    total_issues = len(data)
    
    # Get unique values for key fields
    statuses = {}
    priorities = {}
    assignees = set()
    
    for issue in data:
        status = fix_german_encoding(issue.get('Status', '')).strip()
        priority = fix_german_encoding(issue.get('Priorität', '')).strip()  # Fixed umlaut
        assignee = fix_german_encoding(issue.get('Zugewiesen an', '')).strip()  # German column name
        
        if status:
            statuses[status] = statuses.get(status, 0) + 1
        if priority:
            priorities[priority] = priorities.get(priority, 0) + 1
        if assignee and assignee != 'Unassigned':
            assignees.add(assignee)
    
    # Create summary text
    summary_lines = [
        f"[bold cyan]Total Issues:[/bold cyan] {total_issues}",
        f"[bold cyan]Unique Assignees:[/bold cyan] {len(assignees)}",
        "",
        "[bold yellow]Status Distribution:[/bold yellow]"
    ]
    
    for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True):
        style = get_status_style(status)
        percentage = (count / total_issues) * 100
        summary_lines.append(f"  [{style}]{status}[/{style}]: {count} ({percentage:.1f}%)")
    
    summary_lines.extend(["", "[bold yellow]Priority Distribution:[/bold yellow]"])
    
    for priority, count in sorted(priorities.items(), key=lambda x: x[1], reverse=True):
        style = get_priority_style(priority)
        percentage = (count / total_issues) * 100
        summary_lines.append(f"  [{style}]{priority}[/{style}]: {count} ({percentage:.1f}%)")
    
    return Panel("\n".join(summary_lines), title="📊 Issue Summary", box=box.ROUNDED)

def display_issues_table(filtered_issues, max_rows=None, filter_status=None, filter_assignee=None, filter_order=None, group_by_orders=False):
    """Display issues in a rich table with German column mapping"""
    console = Console()
    
    # Apply filters
    if filter_status:
        filtered_issues = [issue for issue in filtered_issues 
                          if filter_status.lower() in str(issue.get('Status', '')).lower()]
    
    if filter_assignee:
        filtered_issues = [issue for issue in filtered_issues 
                          if filter_assignee.lower() in str(issue.get('Zugewiesen an', '')).lower()]
    
    if filter_order:
        filtered_issues = filter_by_order(filtered_issues, filter_order)
    
    if max_rows:
        filtered_issues = filtered_issues[:max_rows]
    
    if group_by_orders:
        # Display grouped by order numbers
        groups = group_by_order(filtered_issues)
        
        for order, issues in sorted(groups.items()):
            console.print(f"\n[bold blue]═══ Order: {order} ({len(issues)} issues) ═══[/bold blue]")
            _display_table_for_issues(issues, console)
    else:
        # Display normal table
        _display_table_for_issues(filtered_issues, console)

def _display_table_for_issues(issues, console):
    """Helper function to display a table for a list of issues."""
    if not issues:
        console.print("[yellow]No issues to display[/yellow]")
        return
    
def _display_table_for_issues(issues, console):
    """Helper function to display a table for a list of issues."""
    if not issues:
        console.print("[yellow]No issues to display[/yellow]")
        return
    
    # German column mapping - use actual column names from CSV with proper umlauts
    column_mapping = {
        'Thema': 'Thema',  # Column 8
        'Status': 'Status',  # Column 6
        'Priorität': 'Priorität',  # Column 7 (now with proper umlaut)
        'Zugewiesen an': 'Zugewiesen an',  # Column 10
        'Aktualisiert': 'Aktualisiert',  # Column 11
        'Tracker': 'Tracker',  # Column 3
        'Projekt': 'Projekt'  # Column 2
    }
    
    # Create table
    table = Table(title=f"🎫 Redmine Issues ({len(issues)} shown)")
    
    # Add columns with specific widths
    table.add_column("ID", style="cyan", width=8)
    table.add_column("Req-ID", style="bright_cyan", width=16)
    table.add_column("Order", style="yellow", width=20)
    table.add_column("Subject", style="bright_white", width=30)
    table.add_column("Status", style="green", width=14)
    table.add_column("Priority", style="yellow", width=10)
    table.add_column("Assigned", style="blue", width=15)
    table.add_column("Updated", style="magenta", width=12)
    
    # Add rows
    for issue in issues[:100]:  # Limit to first 100 for readability
        # Extract data with fallback to original column names
        issue_id = str(issue.get('#', ''))
        subject = fix_german_encoding(str(issue.get('Thema', '')))
        
        # Extract Req-ID from subject (everything before the colon)
        req_id = ""
        if ':' in subject:
            req_id = subject.split(':', 1)[0].strip()
            # Remove req_id from subject to avoid duplication
            subject = subject.split(':', 1)[1].strip()
        
        # Get combined order number
        order = get_combined_order_number(issue)
        
        status = fix_german_encoding(str(issue.get('Status', '')))
        priority = fix_german_encoding(str(issue.get('Priorität', '')))  # Now with proper umlaut
        assigned = fix_german_encoding(str(issue.get('Zugewiesen an', '')))
        updated = fix_german_encoding(str(issue.get('Aktualisiert', '')))
        
        # Truncate long text
        subject = (subject[:27] + '...') if len(subject) > 30 else subject
        order = (order[:17] + '...') if len(order) > 20 else order
        status = (status[:11] + '...') if len(status) > 14 else status
        assigned = (assigned[:12] + '...') if len(assigned) > 15 else assigned
        
        table.add_row(
            issue_id, req_id, order, subject, status, priority, assigned, updated
        )
    
    # Display count information
    hidden_columns = len(issues[0].keys()) - 8 if issues else 0  # Updated to account for new column
    console.print(table)
    console.print(f"\n[dim]Showing 8 of {len(issues[0].keys()) if issues else 0} columns[/dim]")
    if hidden_columns > 0:
        console.print(f"[dim]Hidden columns: Type, Project, Übergeordnetes Ticket, Autor, Kategorie, Zielversion...[/dim]")

def interactive_mode(data: List[Dict[str, Any]]) -> None:
    """Run interactive mode for exploring the data."""
    while True:
        console.print("\n[bold blue]Interactive Mode[/bold blue]")
        console.print("Commands:")
        console.print("  [cyan]all[/cyan] - Show all issues")
        console.print("  [cyan]summary[/cyan] - Show summary statistics")
        console.print("  [cyan]status <status>[/cyan] - Filter by status")
        console.print("  [cyan]assignee <name>[/cyan] - Filter by assignee")
        console.print("  [cyan]limit <number>[/cyan] - Limit number of rows")
        console.print("  [cyan]export <filename>[/cyan] - Export filtered data")
        console.print("  [cyan]quit[/cyan] - Exit")
        
        command = Prompt.ask("\n[yellow]Enter command[/yellow]", default="all").strip().lower()
        
        if command == "quit" or command == "q":
            break
        elif command == "all":
            display_issues_table(data)
        elif command == "summary":
            console.print(create_summary_panel(data))
        elif command.startswith("status "):
            status_filter = command[7:].strip()
            display_issues_table(data, filter_status=status_filter)
        elif command.startswith("assignee "):
            assignee_filter = command[9:].strip()
            display_issues_table(data, filter_assignee=assignee_filter)
        elif command.startswith("limit "):
            try:
                limit = int(command[6:].strip())
                display_issues_table(data, max_rows=limit)
            except ValueError:
                console.print("[red]Invalid limit number[/red]")
        elif command.startswith("export "):
            filename = command[7:].strip()
            # Implementation for export would go here
            console.print(f"[yellow]Export to {filename} not implemented yet[/yellow]")
        else:
            console.print("[red]Unknown command[/red]")

@click.command()
@click.argument('csv_file', default='trains_issues.csv')
@click.option('--limit', '-l', type=int, help='Limit number of rows to display')
@click.option('--status', '-s', help='Filter by status')
@click.option('--assignee', '-a', help='Filter by assignee')
@click.option('--order', '-o', help='Filter by order number (Auftragsnummer or FIS Auftragsnummer)')
@click.option('--group-by-order', '-g', is_flag=True, help='Group issues by order number')
@click.option('--summary', is_flag=True, help='Show only summary statistics')
@click.option('--interactive', '-i', is_flag=True, help='Run in interactive mode')
def main(csv_file, limit, status, assignee, order, group_by_order, summary, interactive):
    """Rich CSV viewer for Redmine issues.
    
    CSV_FILE: Path to the CSV file to display (default: trains_issues.csv)
    """
    console = Console()
    
    # Load data
    console.print(f"[blue]Loading data from {csv_file}...[/blue]")
    data = load_csv_data(csv_file)
    
    if not data:
        console.print("[red]No data loaded. Exiting.[/red]")
        sys.exit(1)
    
    console.print(f"[green]Successfully loaded {len(data)} issues![/green]\n")
    
    # Show summary panel
    console.print(create_summary_panel(data))
    
    if summary:
        return
    
    if interactive:
        interactive_mode(data)
    else:
        # Display table with filters
        display_issues_table(
            data, 
            max_rows=limit, 
            filter_status=status, 
            filter_assignee=assignee,
            filter_order=order,
            group_by_orders=group_by_order
        )

if __name__ == "__main__":
    main()
