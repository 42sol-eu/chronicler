#!/usr/bin/env python3
"""Main entry point for the Chronicler CLI."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text
from dotenv import load_dotenv

from . import __version__
from .docx_reader import DocxPropertiesReader, DocumentProperties

console = Console()

# Load environment variables from .env file at startup
# Prefer local .env over global ~/.env
env_loaded = False
if Path('.env').exists():
    load_dotenv('.env')
    env_loaded = Path('.env')
elif Path.home().joinpath('.env').exists():
    load_dotenv(Path.home() / '.env')
    env_loaded = Path.home() / '.env'


@click.group()
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output"
)
@click.version_option(version=__version__, prog_name="chronicler")
@click.pass_context
def cli(ctx, verbose):
    """Chronicler - A CLI application for managing text and office documents."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        click.echo(f"Chronicler v{__version__}")
        if env_loaded:
            console.print(f"[green]✓[/green] Loaded environment variables from {env_loaded}")
        else:
            console.print("[yellow]ℹ[/yellow] No .env file found (checked ~/.env and ./.env)")


@cli.command()
@click.argument("name")
@click.option(
    "--description",
    help="Description of the chronicle"
)
@click.pass_context
def create(ctx, name, description):
    """Create a new chronicle."""
    if ctx.obj['verbose']:
        click.echo(f"Creating chronicle: {name}")
    else:
        click.echo(f"Creating chronicle: {name}")
    
    if description:
        click.echo(f"Description: {description}")
    
    # TODO: Implement actual chronicle creation logic


@cli.command()
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (default: table)"
)
@click.pass_context
def list(ctx, format):
    """List all chronicles."""
    if ctx.obj['verbose']:
        click.echo(f"Listing chronicles (format: {format})")
    else:
        click.echo(f"Listing chronicles (format: {format})")
    
    # TODO: Implement actual chronicle listing logic


@cli.command()
@click.argument("name")
@click.pass_context
def show(ctx, name):
    """Show details of a chronicle."""
    if ctx.obj['verbose']:
        click.echo(f"Showing chronicle: {name}")
    else:
        click.echo(f"Showing chronicle: {name}")
    
    # TODO: Implement actual chronicle show logic


@cli.command("docx-check")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table", help="Output format")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def docx_check(file_path: str, output_format: str, verbose: bool):
    """Check for required document variables in a DOCX file.
    
    Validates the presence of standard document metadata fields:
    ID, Revision, Dokumententyp, Projekt, Freigeber, Freigabedatum, Status, Klassifizierung
    """
    try:
        reader = DocxPropertiesReader(file_path)
        
        # Define required variables
        required_vars = [
            "ID",
            "Revision", 
            "Dokumententyp",
            "Projekt",
            "Freigeber",
            "Freigabedatum", 
            "Status",
            "Klassifizierung"
        ]
        
        # Check each variable
        results = {}
        all_vars = reader.get_variable_values()
        
        for var_name in required_vars:
            if var_name in all_vars:
                value = all_vars[var_name]
                results[var_name] = {
                    "exists": True,
                    "value": value,
                    "status": "✓ Found"
                }
            else:
                results[var_name] = {
                    "exists": False,
                    "value": None,
                    "status": "✗ Missing"
                }
        
        # Calculate summary
        found_count = sum(1 for r in results.values() if r["exists"])
        total_count = len(required_vars)
        success_rate = (found_count / total_count) * 100
        
        if output_format == "json":
            output = {
                "file": file_path,
                "summary": {
                    "found": found_count,
                    "total": total_count,
                    "success_rate": round(success_rate, 1),
                    "all_found": found_count == total_count
                },
                "variables": {}
            }
            
            for var_name, result in results.items():
                if verbose or result["exists"]:
                    output["variables"][var_name] = {
                        "exists": result["exists"],
                        "value": result["value"]
                    }
                else:
                    output["variables"][var_name] = {
                        "exists": result["exists"]
                    }
            
            console.print_json(data=output)
        else:
            # Table format
            table = Table(title=f"Document Variable Check: {Path(file_path).name}")
            table.add_column("Variable", style="cyan", no_wrap=True)
            table.add_column("Status", justify="center")
            table.add_column("Value", style="dim")
            
            for var_name, result in results.items():
                status_style = "green" if result["exists"] else "red"
                value_display = str(result["value"]) if result["exists"] and verbose else ""
                if not verbose and result["exists"]:
                    value_display = "✓"
                elif not result["exists"]:
                    value_display = ""
                    
                table.add_row(
                    var_name,
                    f"[{status_style}]{result['status']}[/{status_style}]",
                    value_display
                )
            
            console.print(table)
            
            # Summary
            if found_count == total_count:
                console.print(f"\n[green]✓ All {total_count} required variables found![/green]")
            else:
                missing_count = total_count - found_count
                console.print(f"\n[yellow]⚠ {found_count}/{total_count} variables found. {missing_count} missing.[/yellow]")
                
                if not verbose:
                    console.print("[dim]Use --verbose to see variable values[/dim]")
    
    except FileNotFoundError:
        console.print(f"[red]Error: File '{file_path}' not found[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        raise click.Abort()


@cli.command("docx-add-vars")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output file path (default: overwrites input file)")
@click.option("--interactive/--batch", default=True, help="Interactive mode to prompt for values (default: interactive)")
@click.option("--force", is_flag=True, help="Add variables even if they already exist")
@click.option("--review-all", is_flag=True, help="Review and update all variables, not just missing ones")
def docx_add_vars(file_path: str, output: str, interactive: bool, force: bool, review_all: bool):
    """Add missing document variables to a DOCX file.
    
    Checks for required variables (ID, Revision, Dokumententyp, Projekt, 
    Freigeber, Freigabedatum, Status, Klassifizierung) and prompts the user 
    to add values for any that are missing.
    
    Use --review-all to interactively review and update all variables.
    """
    try:
        reader = DocxPropertiesReader(file_path)
        
        # Define required variables
        required_vars = [
            "ID",
            "Revision", 
            "Dokumententyp",
            "Projekt",
            "Freigeber",
            "Freigabedatum", 
            "Status",
            "Klassifizierung"
        ]
        
        # Get existing variables
        existing_vars = reader.get_variable_values()
        
        # Show current state
        console.print(f"\n[bold]Document:[/bold] {Path(file_path).name}")
        
        if review_all:
            # Review all mode - show all variables for interactive review
            console.print(f"[bold]Review Mode:[/bold] All {len(required_vars)} variables")
            
            if interactive:
                # Show current state table first
                console.print("\n[bold]Current Variable Status:[/bold]")
                status_table = Table(show_header=True)
                status_table.add_column("Variable", style="cyan")
                status_table.add_column("Current Value", style="green")
                status_table.add_column("Status", justify="center")
                
                for var_name in required_vars:
                    current_value = existing_vars.get(var_name, "")
                    status = "[green]✓ Set[/green]" if current_value else "[red]✗ Missing[/red]"
                    display_value = current_value if current_value else "[dim]Not set[/dim]"
                    status_table.add_row(var_name, display_value, status)
                
                console.print(status_table)
                
                # Interactive review mode
                new_properties = {}
                
                console.print("\n[bold cyan]Interactive Variable Review:[/bold cyan]")
                console.print("[dim]Press Enter to keep current value, or type new value to update[/dim]\n")
                
                for var_name in required_vars:
                    current_value = existing_vars.get(var_name, "")
                    
                    # Create prompt text
                    if current_value:
                        prompt_text = f"{var_name} [current: {current_value}]"
                        default_help = "Keep current"
                    else:
                        prompt_text = f"{var_name} [NOT SET]"
                        default_help = "Skip"
                    
                    # Prompt for value
                    value = click.prompt(
                        f"  {prompt_text}",
                        default="",
                        show_default=False,
                        prompt_suffix=f" ({default_help}): "
                    )
                    
                    if value.strip():
                        new_properties[var_name] = value.strip()
                        if current_value:
                            console.print(f"    [yellow]Will update: {current_value} → {value.strip()}[/yellow]")
                        else:
                            console.print(f"    [green]Will add: {value.strip()}[/green]")
                    else:
                        if current_value:
                            console.print(f"    [dim]Keeping current: {current_value}[/dim]")
                        else:
                            console.print(f"    [dim]Skipping {var_name}[/dim]")
            else:
                console.print("[red]Review all mode requires --interactive flag[/red]")
                raise click.Abort()
                
        else:
            # Original mode - only missing variables or force mode
            missing_vars = [var for var in required_vars if var not in existing_vars or force]
            
            if not missing_vars:
                console.print("[green]✓ All required variables are already present![/green]")
                if not force:
                    console.print("[dim]Use --review-all to review and update all variables[/dim]")
                    return
                else:
                    console.print("[yellow]--force specified, will prompt to update existing variables[/yellow]")
                    missing_vars = required_vars
            
            console.print(f"[bold]Missing variables:[/bold] {len(missing_vars)}")
            
            if interactive:
                # Interactive mode - prompt for each missing variable
                new_properties = {}
                
                console.print("\n[bold cyan]Please provide values for the missing variables:[/bold cyan]")
                console.print("[dim]Press Enter to skip a variable[/dim]\n")
                
                for var_name in missing_vars:
                    # Show current value if it exists
                    current_value = existing_vars.get(var_name, "")
                    prompt_text = f"{var_name}"
                    if current_value and force:
                        prompt_text += f" (current: {current_value})"
                    
                    # Prompt for value
                    value = click.prompt(
                        f"  {prompt_text}",
                        default="",
                        show_default=False,
                        prompt_suffix=": "
                    )
                    
                    if value.strip():
                        new_properties[var_name] = value.strip()
                    elif not current_value:
                        console.print(f"    [dim]Skipping {var_name}[/dim]")
            else:
                # Batch mode - would need to specify values via options or file
                console.print("[red]Batch mode not yet implemented. Use --interactive for now.[/red]")
                raise click.Abort()
        
        # Check if we have any changes to make
        if not new_properties:
            console.print("\n[yellow]No variables provided. No changes made.[/yellow]")
            return
        
        # Show summary of changes
        console.print("\n[bold]Variables to add/update:[/bold]")
        table = Table(show_header=True)
        table.add_column("Variable", style="cyan")
        table.add_column("Action", justify="center")
        table.add_column("New Value", style="green")
        if review_all:
            table.add_column("Previous Value", style="dim")
        
        for name, value in new_properties.items():
            current_value = existing_vars.get(name, "")
            if current_value:
                action = "[yellow]Update[/yellow]"
            else:
                action = "[green]Add[/green]"
            
            if review_all:
                prev_value = current_value if current_value else "[dim]Not set[/dim]"
                table.add_row(name, action, value, prev_value)
            else:
                table.add_row(name, action, value)
        
        console.print(table)
        
        if not click.confirm("\nProceed with these changes?"):
            console.print("[yellow]Operation cancelled.[/yellow]")
            return
        
        # Add the properties
        try:
            output_file = reader.add_custom_properties(new_properties, output)
            
            console.print(f"\n[green]✓ Successfully added {len(new_properties)} variables![/green]")
            console.print(f"[green]✓ File saved to: {output_file}[/green]")
            
            # Verify the changes
            if click.confirm("\nWould you like to verify the changes?"):
                # Re-read the file to show the updated properties
                updated_reader = DocxPropertiesReader(output_file)
                updated_vars = updated_reader.get_variable_values()
                
                console.print("\n[bold]Updated variables:[/bold]")
                verification_table = Table(show_header=True)
                verification_table.add_column("Variable", style="cyan")
                verification_table.add_column("Value", style="green")
                verification_table.add_column("Status", style="yellow")
                
                for var_name in required_vars:
                    if var_name in updated_vars:
                        status = "✓ Present"
                        if var_name in new_properties:
                            status = "✓ Added"
                        verification_table.add_row(var_name, updated_vars[var_name], status)
                    else:
                        verification_table.add_row(var_name, "[dim]Not set[/dim]", "✗ Missing")
                
                console.print(verification_table)
            
        except Exception as e:
            console.print(f"[red]Error adding properties: {e}[/red]")
            raise click.Abort()
    
    except FileNotFoundError:
        console.print(f"[red]Error: File '{file_path}' not found[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@cli.command("docx-props")
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (default: table)"
)
@click.option(
    "--variables-only",
    is_flag=True,
    help="Show only custom variables, not built-in properties"
)
@click.pass_context
def docx_properties(ctx, file_path: Path, format: str, variables_only: bool):
    """Read document properties and variables from a DOCX file."""
    console = Console()
    
    if ctx.obj['verbose']:
        click.echo(f"Reading properties from: {file_path}")
    
    try:
        reader = DocxPropertiesReader(file_path)
        props = reader.read_properties()
        
        if variables_only:
            # Show only custom variables
            data = props.custom_properties
            if format == "json":
                click.echo(json.dumps(data, indent=2, default=str))
            else:
                _display_variables_table(console, data)
        else:
            # Show all properties
            if format == "json":
                all_props = reader.get_all_properties_dict()
                click.echo(json.dumps(all_props, indent=2, default=str))
            else:
                _display_properties_table(console, props)
                
    except Exception as e:
        click.echo(f"Error reading DOCX file: {e}", err=True)
        raise click.Abort()


@cli.command("docx-vars")
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--names-only",
    is_flag=True,
    help="Show only variable names, not values"
)
@click.option(
    "--format",
    type=click.Choice(["list", "json"]),
    default="list",
    help="Output format (default: list)"
)
@click.pass_context
def docx_variables(ctx, file_path: Path, names_only: bool, format: str):
    """Read custom variables from a DOCX file."""
    if ctx.obj['verbose']:
        click.echo(f"Reading variables from: {file_path}")
    
    try:
        reader = DocxPropertiesReader(file_path)
        
        if names_only:
            var_names = reader.get_variable_names()
            if format == "json":
                click.echo(json.dumps(var_names, indent=2))
            else:
                for name in var_names:
                    click.echo(name)
        else:
            var_values = reader.get_variable_values()
            if format == "json":
                click.echo(json.dumps(var_values, indent=2, default=str))
            else:
                for name, value in var_values.items():
                    click.echo(f"{name}: {value}")
                    
    except Exception as e:
        click.echo(f"Error reading DOCX file: {e}", err=True)
        raise click.Abort()


def _display_properties_table(console: Console, props: DocumentProperties):
    """Display document properties in a rich table format."""
    table = Table(title="Document Properties", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="yellow")
    
    # Built-in properties
    built_in = [
        ("Title", props.title),
        ("Author", props.author),
        ("Subject", props.subject),
        ("Keywords", props.keywords),
        ("Comments", props.comments),
        ("Category", props.category),
        ("Created", props.created.isoformat() if props.created else None),
        ("Modified", props.modified.isoformat() if props.modified else None),
        ("Last Modified By", props.last_modified_by),
    ]
    
    for prop_name, prop_value in built_in:
        value_str = str(prop_value) if prop_value is not None else "[dim]None[/dim]"
        table.add_row(prop_name, value_str)
    
    # Add separator if there are custom properties
    if props.custom_properties:
        table.add_row("", "")  # Empty row as separator
        table.add_row("[bold]Custom Variables[/bold]", "")
        
        for name, value in props.custom_properties.items():
            value_str = str(value) if value is not None else "[dim]None[/dim]"
            table.add_row(f"  {name}", value_str)
    
    console.print(table)


def _display_variables_table(console: Console, variables: dict):
    """Display custom variables in a rich table format."""
    if not variables:
        console.print("[yellow]No custom variables found in the document.[/yellow]")
        return
        
    table = Table(title="Custom Variables", show_header=True, header_style="bold magenta")
    table.add_column("Variable Name", style="cyan", no_wrap=True)
    table.add_column("Value", style="yellow")
    table.add_column("Type", style="green")
    
    for name, value in variables.items():
        value_str = str(value) if value is not None else "[dim]None[/dim]"
        value_type = type(value).__name__
        table.add_row(name, value_str, value_type)
    
    console.print(table)


@cli.command("redmine")
@click.option(
    "--url",
    default="https://stap-software-redmine.stadlerrail.com/projects/linwqezmkvcypxhrbdoa/issues",
    help="Redmine project URL"
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (default: table)"
)
@click.pass_context
def redmine_list(ctx, url, format):
    """List all tickets from the Redmine project."""
    from .redmine_client import RedmineClient, load_credentials, extract_project_id_from_url
    
    try:
        if ctx.obj['verbose']:
            console.print(f"[blue]Loading credentials from ~/.env...[/blue]")
        
        # Load credentials
        username, password = load_credentials()
        
        # Extract project info from URL
        base_url = "/".join(url.split("/")[:3])  # Get base URL
        project_id = extract_project_id_from_url(url)
        
        if ctx.obj['verbose']:
            console.print(f"[blue]Connecting to Redmine at: {base_url}[/blue]")
            console.print(f"[blue]Project ID: {project_id}[/blue]")
        
        # Create client and fetch issues
        client = RedmineClient(base_url, username, password)
        issues = client.get_all_project_issues(project_id)
        
        if format == "json":
            # Output as JSON
            import json
            output = {
                "project_url": url,
                "project_id": project_id,
                "total_issues": len(issues),
                "issues": []
            }
            
            for issue in issues:
                issue_data = {
                    "id": issue.get("id"),
                    "subject": issue.get("subject"),
                    "status": issue.get("status", {}).get("name"),
                    "priority": issue.get("priority", {}).get("name"),
                    "assigned_to": issue.get("assigned_to", {}).get("name"),
                    "created_on": issue.get("created_on"),
                    "updated_on": issue.get("updated_on")
                }
                output["issues"].append(issue_data)
            
            click.echo(json.dumps(output, indent=2))
        else:
            # Display in table format
            client.display_issues_table(issues)
            
            if ctx.obj['verbose']:
                console.print(f"\n[green]Successfully retrieved {len(issues)} issues![/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@cli.command("jira")
@click.argument("project_key")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (default: table)"
)
@click.option(
    "--toc-only",
    is_flag=True,
    help="Show only the table of contents (overview of groups)"
)
@click.option(
    "--server-url",
    envvar="JIRA_SERVER_URL",
    help="Jira server URL (can be set via JIRA_SERVER_URL env var)"
)
@click.option(
    "--email",
    envvar="JIRA_EMAIL", 
    help="Jira email (can be set via JIRA_EMAIL env var)"
)
@click.option(
    "--api-token",
    envvar="JIRA_API_TOKEN",
    help="Jira API token (can be set via JIRA_API_TOKEN env var)"
)
@click.pass_context
def jira_command(ctx, project_key: str, format: str, toc_only: bool, server_url: str, email: str, api_token: str):
    """Retrieve and display Jira groups (epics) and their requirements from a project.
    
    PROJECT_KEY: The Jira project key (e.g., PPRX)
    
    Environment variables:
    - JIRA_SERVER_URL: Your Jira server URL (e.g., https://stadlerrailag.atlassian.net)
    - JIRA_EMAIL: Your Jira email address
    - JIRA_API_TOKEN: Your Jira API token
    """
    from .jira_client import JiraClient
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    import json
    
    try:
        # Create client from parameters or environment
        if server_url and email and api_token:
            client = JiraClient(server_url, email, api_token)
        else:
            client = JiraClient.from_env()
            if not client:
                console.print("[red]Error:[/red] Please provide Jira credentials either via options or environment variables")
                console.print("\nSet environment variables:")
                console.print("  export JIRA_SERVER_URL='https://stadlerrailag.atlassian.net'")
                console.print("  export JIRA_EMAIL='your-email@company.com'") 
                console.print("  export JIRA_API_TOKEN='your-api-token'")
                raise click.Abort()
        
        # Connect to Jira
        if not client.connect():
            raise click.Abort()
        
        console.print(f"[blue]Fetching groups and requirements for project:[/blue] {project_key}")
        
        # Get epics (groups) and their requirements
        epics = client.get_project_epics(project_key)
        
        if not epics:
            console.print(f"[yellow]No groups found in project {project_key}[/yellow]")
            return
        
        if toc_only:
            # Show only table of contents
            if format == "json":
                # JSON format for TOC only
                output = {
                    "project_key": project_key,
                    "total_groups": len(epics),
                    "table_of_contents": []
                }
                
                for epic in epics:
                    # Get unique Redmine IDs from requirements
                    redmine_ids = [req.redmine_id for req in epic.requirements if req.redmine_id is not None]
                    
                    toc_entry = {
                        "order": epic.order,
                        "redmine_ids": redmine_ids,
                        "redmine_id_count": len(redmine_ids),
                        "key": epic.key,
                        "name": epic.name,
                        "status": epic.status,
                        "total_requirements": len(epic.requirements)
                    }
                    output["table_of_contents"].append(toc_entry)
                
                click.echo(json.dumps(output, indent=2))
            else:
                # Rich table format for TOC only
                toc_table = Table(title="[bold blue]Table of Contents[/bold blue]", show_header=True, header_style="bold magenta")
                toc_table.add_column("Order", style="cyan", no_wrap=True, width=8)
                toc_table.add_column("Redmine_ID", style="bright_red", no_wrap=True, width=10)
                toc_table.add_column("Group Key", style="green", no_wrap=True)
                toc_table.add_column("Group Name", style="white")
                toc_table.add_column("Requirements", style="yellow", no_wrap=True, justify="center")
                toc_table.add_column("Status", style="blue", no_wrap=True)
                
                for epic in epics:
                    order_display = str(epic.order) if epic.order is not None else "—"
                    
                    # Get unique Redmine IDs from requirements
                    redmine_ids = [req.redmine_id for req in epic.requirements if req.redmine_id is not None]
                    redmine_id_display = f"{len(redmine_ids)} IDs" if redmine_ids else "—"
                    
                    toc_table.add_row(
                        order_display,
                        redmine_id_display,
                        epic.key,
                        epic.name[:50] + "..." if len(epic.name) > 50 else epic.name,
                        str(len(epic.requirements)),
                        epic.status
                    )
                
                console.print(toc_table)
                
                # Summary
                total_requirements = sum(len(epic.requirements) for epic in epics)
                summary_text = f"[bold green]Summary:[/bold green] {len(epics)} groups, {total_requirements} total requirements"
                console.print(Panel(summary_text, border_style="blue"))
        elif format == "json":
            # Output as JSON
            output = {
                "project_key": project_key,
                "total_groups": len(epics),
                "groups": []
            }
            
            for epic in epics:
                epic_data = {
                    "key": epic.key,
                    "name": epic.name,
                    "summary": epic.summary,
                    "status": epic.status,
                    "description": epic.description,
                    "order": epic.order,
                    "total_requirements": len(epic.requirements),
                    "requirements": []
                }
                
                for req in epic.requirements:
                    req_data = {
                        "key": req.key,
                        "summary": req.summary,
                        "status": req.status,
                        "assignee": req.assignee,
                        "description": req.description,
                        "order": req.order,
                        "redmine_id": req.redmine_id
                    }
                    epic_data["requirements"].append(req_data)
                
                output["groups"].append(epic_data)
            
            click.echo(json.dumps(output, indent=2))
        else:
            # Display in rich table format
            
            # Create table of contents first
            toc_table = Table(title="[bold blue]Table of Contents[/bold blue]", show_header=True, header_style="bold magenta")
            toc_table.add_column("Order", style="cyan", no_wrap=True, width=8)
            toc_table.add_column("Redmine_ID", style="bright_red", no_wrap=True, width=10)
            toc_table.add_column("Group Key", style="green", no_wrap=True)
            toc_table.add_column("Group Name", style="white")
            toc_table.add_column("Requirements", style="yellow", no_wrap=True, justify="center")
            toc_table.add_column("Status", style="blue", no_wrap=True)
            
            for epic in epics:
                order_display = str(epic.order) if epic.order is not None else "—"
                
                # Get unique Redmine IDs from requirements
                redmine_ids = [req.redmine_id for req in epic.requirements if req.redmine_id is not None]
                redmine_id_display = f"{len(redmine_ids)} IDs" if redmine_ids else "—"
                
                toc_table.add_row(
                    order_display,
                    redmine_id_display,
                    epic.key,
                    epic.name[:50] + "..." if len(epic.name) > 50 else epic.name,
                    str(len(epic.requirements)),
                    epic.status
                )
            
            console.print(toc_table)
            console.print()  # Empty line after TOC
            
            # Detailed view for each epic/group
            for epic in epics:
                # Create panel for each epic/group
                epic_info = Text()
                epic_info.append(f"Key: ", style="bold cyan")
                epic_info.append(f"{epic.key}\n")
                if epic.order is not None:
                    epic_info.append(f"Order: ", style="bold cyan")
                    epic_info.append(f"{epic.order}\n")
                epic_info.append(f"Status: ", style="bold cyan") 
                epic_info.append(f"{epic.status}\n")
                if epic.description:
                    epic_info.append(f"Description: ", style="bold cyan")
                    epic_info.append(f"{epic.description[:100]}{'...' if len(epic.description) > 100 else ''}\n")
                epic_info.append(f"Requirements: ", style="bold cyan")
                epic_info.append(f"{len(epic.requirements)}")
                
                # Create panel title with order if available
                order_prefix = f"[{epic.order}] " if epic.order is not None else ""
                panel_title = f"[bold green]Group: {order_prefix}{epic.name}[/bold green]"
                
                panel = Panel(
                    epic_info,
                    title=panel_title,
                    title_align="left",
                    border_style="green"
                )
                console.print(panel)
                
                # Create table for requirements
                if epic.requirements:
                    req_table = Table(show_header=True, header_style="bold magenta")
                    req_table.add_column("Key", style="cyan", no_wrap=True)
                    req_table.add_column("Order", style="cyan", no_wrap=True, width=8)
                    req_table.add_column("Redmine_ID", style="bright_red", no_wrap=True, width=10)
                    req_table.add_column("Summary", style="white")
                    req_table.add_column("Status", style="yellow", no_wrap=True)
                    req_table.add_column("Assignee", style="green", no_wrap=True)
                    
                    for req in epic.requirements:
                        order_display = str(req.order) if req.order is not None else "—"
                        redmine_id_display = str(req.redmine_id) if req.redmine_id is not None else "—"
                        req_table.add_row(
                            req.key,
                            order_display,
                            redmine_id_display,
                            req.summary[:60] + "..." if len(req.summary) > 60 else req.summary,
                            req.status,
                            req.assignee or "Unassigned"
                        )
                    
                    console.print(req_table)
                else:
                    console.print("[yellow]  No requirements found for this group[/yellow]")
                
                console.print()  # Empty line between groups
            
            # Summary
            total_requirements = sum(len(epic.requirements) for epic in epics)
            summary_text = f"[bold green]Summary:[/bold green] {len(epics)} groups, {total_requirements} total requirements"
            console.print(Panel(summary_text, border_style="blue"))
            
            if ctx.obj['verbose']:
                console.print(f"\n[green]Successfully retrieved {len(epics)} groups with {total_requirements} requirements![/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
