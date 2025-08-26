#!/usr/bin/env python3
"""
Debug script to examine the actual HTML response we're getting.
"""

import urllib.request
import urllib.error
from rich.console import Console
from rich.syntax import Syntax

console = Console()

def examine_response():
    """Examine the HTML response to understand the authentication flow."""
    
    url = "https://stap-software-redmine.stadlerrail.com"
    
    try:
        request = urllib.request.Request(url)
        request.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
            
            console.print(f"[blue]Response Status: {response.status}[/blue]")
            console.print(f"[blue]Content-Type: {response.headers.get('content-type')}[/blue]")
            console.print(f"[blue]Content Length: {len(content)} chars[/blue]")
            
            # Show the first part of the response
            console.print("\n[bold]First 2000 characters of response:[/bold]")
            syntax = Syntax(content[:2000], "html", theme="monokai", line_numbers=True)
            console.print(syntax)
            
            # Look for specific patterns
            console.print("\n[bold]Analysis:[/bold]")
            
            if "netscaler" in content.lower():
                console.print("[yellow]✓ NetScaler detected[/yellow]")
            
            if "login" in content.lower():
                console.print("[yellow]✓ Login form detected[/yellow]")
            
            # Look for form elements
            import re
            forms = re.findall(r'<form[^>]*>', content, re.IGNORECASE)
            if forms:
                console.print(f"[cyan]Found {len(forms)} form(s):[/cyan]")
                for i, form in enumerate(forms):
                    console.print(f"  {i+1}: {form}")
            
            # Look for input fields
            inputs = re.findall(r'<input[^>]*>', content, re.IGNORECASE)
            if inputs:
                console.print(f"\n[cyan]Found {len(inputs)} input field(s):[/cyan]")
                for i, inp in enumerate(inputs[:10]):  # Show first 10
                    console.print(f"  {i+1}: {inp}")
                if len(inputs) > 10:
                    console.print(f"  ... and {len(inputs) - 10} more")
            
            # Look for JavaScript redirects or meta refreshes
            if "location.href" in content or "window.location" in content:
                console.print("[yellow]✓ JavaScript redirect detected[/yellow]")
            
            if "<meta" in content and "refresh" in content.lower():
                console.print("[yellow]✓ Meta refresh detected[/yellow]")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    examine_response()
