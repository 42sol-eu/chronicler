#!/usr/bin/env python3
"""Main entry point for the Chronicler CLI."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from . import __version__
from .docx_reader import DocxPropertiesReader, DocumentProperties

console = Console()


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


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
