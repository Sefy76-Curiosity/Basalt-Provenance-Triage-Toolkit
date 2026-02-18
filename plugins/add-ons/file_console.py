"""
File Operations Console - Safe file management using Python
"""
import tkinter as tk
from tkinter import ttk, filedialog
import os
import shutil
import glob
import zipfile
from datetime import datetime
import subprocess

PLUGIN_INFO = {
    'id': 'file_console',
    'name': 'File Operations',
    'category': 'console',
    'icon': '📁',
    'version': '1.0',
    'description': 'Manage files safely across all platforms'
}

class FileConsolePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.history = []
        self.history_index = -1
        self.current_dir = os.getcwd()

    def create_tab(self, parent):
        """Create file operations console UI"""
        # Top bar with current directory
        dir_frame = ttk.Frame(parent)
        dir_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(dir_frame, text="📁 Current:").pack(side=tk.LEFT)
        self.dir_label = tk.Label(dir_frame, text=self.current_dir,
                                   font=('Consolas', 8), bg='#2d2d2d', fg='white',
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Button(dir_frame, text="Browse", command=self._browse_folder).pack(side=tk.RIGHT)

        # Output area
        output_frame = ttk.Frame(parent)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.output = tk.Text(
            output_frame,
            bg='#1e1e1e',
            fg='#d4d4d4',
            font=('Consolas', 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL,
                                  command=self.output.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.configure(yscrollcommand=scrollbar.set)

        # Quick commands bar
        quick_frame = ttk.Frame(parent)
        quick_frame.pack(fill=tk.X, padx=5, pady=2)

        commands = [
            ("📋 List CSV", lambda: self.execute("list_files('*.csv')")),
            ("📋 List XLSX", lambda: self.execute("list_files('*.xlsx')")),
            ("📁 PWD", lambda: self.execute("pwd()")),
            ("📊 Size", lambda: self.execute("file_sizes()")),
            ("🗜️ Backup", lambda: self.execute("backup('*.csv')")),
            ("🔍 Find", self._show_find_dialog)
        ]

        for text, cmd in commands:
            ttk.Button(quick_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

        # Input area
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text=">>>", font=('Consolas', 10, 'bold')).pack(side=tk.LEFT, padx=2)

        self.input = tk.Text(
            input_frame,
            height=2,
            bg='#2d2d2d',
            fg='#ffffff',
            font=('Consolas', 10),
            insertbackground='white',
            wrap=tk.WORD
        )
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Bind keys
        self.input.bind('<Return>', self._on_enter)
        self.input.bind('<Shift-Return>', self._insert_newline)
        self.input.bind('<Up>', self._history_up)
        self.input.bind('<Down>', self._history_down)

        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Run", command=self.execute_input).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear", command=self._clear_screen).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Help", command=self._show_help).pack(side=tk.LEFT, padx=2)

        self._print_welcome()

    def _print_welcome(self):
        """Print welcome message"""
        welcome = f"""
╔══════════════════════════════════════════════════════════╗
║               File Operations Console                    ║
╠══════════════════════════════════════════════════════════╣
║  Current Directory:                                      ║
║  {self.current_dir:<50}      ║
║                                                          ║
║  Available commands:                                     ║
║    list_files(pattern='*')   - List files                ║
║    file_sizes()              - Show file sizes           ║
║    pwd()                     - Show current directory    ║
║    cd(path)                  - Change directory          ║
║    mkdir(name)               - Create directory          ║
║    copy(src, dst)            - Copy file(s)              ║
║    move(src, dst)            - Move/rename file(s)       ║
║    delete(path)              - Delete file/directory     ║
║    backup(pattern)           - Backup matching files     ║
║    zip(name, pattern)        - Create zip archive        ║
║    unzip(zipfile, dest)      - Extract zip               ║
║    grep(pattern, file)       - Search in file            ║
║                                                          ║
║  Examples:                                               ║
║    >>> list_files('*.csv')                               ║
║    >>> backup('samples_*.csv')                           ║
║    >>> grep('SINAI', 'samples.csv')                      ║
║    >>> zip('data.zip', '*.csv')                          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
        self._print_output(welcome)

    def _show_help(self):
        """Show detailed help"""
        help_text = """
📁 FILE OPERATIONS GUIDE
═══════════════════════════════════════════════════════════

LISTING FILES:
  list_files()           - List all files
  list_files('*.csv')    - List CSV files only
  list_files('*.xlsx')   - List Excel files
  file_sizes()           - Show files with sizes

DIRECTORY OPERATIONS:
  pwd()                  - Show current directory
  cd('folder')           - Change to folder
  cd('..')               - Go up one level
  mkdir('newfolder')     - Create new folder

FILE OPERATIONS:
  copy('file.csv', 'backup.csv')     - Copy file
  move('old.csv', 'new.csv')         - Rename/move
  delete('file.csv')                 - Delete file
  delete('folder', recursive=True)   - Delete folder

BACKUP & ARCHIVE:
  backup('*.csv')                    - Backup CSVs to folder
  zip('archive.zip', '*.csv')        - Create zip
  unzip('archive.zip', 'extracted/') - Extract zip

SEARCH:
  grep('SINAI', 'samples.csv')       - Search in file
  grep('Zr_ppm', '*.csv')            - Search in multiple files

💡 TIPS:
  • All commands work the same on Windows/Mac/Linux
  • Use quotes around patterns: '*.csv'
  • Paths can be relative or absolute
"""
        self._print_output(help_text)

    def execute_input(self):
        """Execute command from input"""
        code = self.input.get("1.0", tk.END).strip()
        if code:
            self.execute(code)

    def execute(self, command):
        """Execute a file operation command"""
        if not command:
            return

        self.history.append(command)
        self.history_index = len(self.history)

        self._print_output(f">>> {command}\n")
        self.input.delete("1.0", tk.END)

        try:
            # Parse command
            if command.startswith('list_files') or command == 'list_files()':
                result = self._list_files(command)
            elif command.startswith('file_sizes') or command == 'file_sizes()':
                result = self._file_sizes()
            elif command.startswith('pwd') or command == 'pwd()':
                result = f"{self.current_dir}\n"
            elif command.startswith('cd'):
                result = self._change_dir(command)
            elif command.startswith('mkdir'):
                result = self._make_dir(command)
            elif command.startswith('copy'):
                result = self._copy_files(command)
            elif command.startswith('move'):
                result = self._move_files(command)
            elif command.startswith('delete'):
                result = self._delete_files(command)
            elif command.startswith('backup'):
                result = self._backup_files(command)
            elif command.startswith('zip'):
                result = self._create_zip(command)
            elif command.startswith('unzip'):
                result = self._extract_zip(command)
            elif command.startswith('grep'):
                result = self._grep(command)
            else:
                result = f"Unknown command: {command}\nTry 'help()'\n"

            self._print_output(result)

        except Exception as e:
            self._print_output(f"Error: {str(e)}\n", error=True)

        self._print_output("\n")
        self._update_dir_display()

    def _list_files(self, command):
        """List files matching pattern"""
        # Parse pattern from command
        if '(' in command and ')' in command:
            pattern = command.split('(')[1].split(')')[0].strip('\'"')
        else:
            pattern = '*'

        files = glob.glob(os.path.join(self.current_dir, pattern))

        if not files:
            return f"No files matching '{pattern}'\n"

        result = f"\n📋 Files matching '{pattern}':\n"
        for f in sorted(files):
            name = os.path.basename(f)
            if os.path.isdir(f):
                result += f"  📁 {name}/\n"
            else:
                size = os.path.getsize(f)
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024*1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size/(1024*1024):.1f} MB"
                result += f"  📄 {name} ({size_str})\n"

        return result

    def _file_sizes(self):
        """Show file sizes"""
        files = glob.glob(os.path.join(self.current_dir, '*'))

        result = "\n📊 File sizes:\n"
        total = 0
        for f in sorted(files):
            if os.path.isfile(f):
                size = os.path.getsize(f)
                name = os.path.basename(f)
                result += f"  {size:10d} B  {name}\n"
                total += size

        if total < 1024:
            total_str = f"{total} B"
        elif total < 1024*1024:
            total_str = f"{total/1024:.2f} KB"
        else:
            total_str = f"{total/(1024*1024):.2f} MB"

        result += f"\n  Total: {total_str}\n"
        return result

    def _change_dir(self, command):
        """Change directory"""
        # Parse path from command
        if '(' in command and ')' in command:
            path = command.split('(')[1].split(')')[0].strip('\'"')
        else:
            return "Usage: cd('path')\n"

        if path == '..':
            new_dir = os.path.dirname(self.current_dir)
        else:
            if os.path.isabs(path):
                new_dir = path
            else:
                new_dir = os.path.join(self.current_dir, path)

        if os.path.exists(new_dir) and os.path.isdir(new_dir):
            self.current_dir = os.path.abspath(new_dir)
            return f"Changed to: {self.current_dir}\n"
        else:
            return f"Directory not found: {path}\n"

    def _make_dir(self, command):
        """Create directory"""
        if '(' in command and ')' in command:
            name = command.split('(')[1].split(')')[0].strip('\'"')
        else:
            return "Usage: mkdir('name')\n"

        path = os.path.join(self.current_dir, name)
        os.makedirs(path, exist_ok=True)
        return f"Created directory: {name}\n"

    def _copy_files(self, command):
        """Copy files"""
        import re
        match = re.match(r"copy\(['\"](.+?)['\"],\s*['\"](.+?)['\"]\)", command)
        if not match:
            return "Usage: copy('source', 'destination')\n"

        src, dst = match.groups()
        src_path = os.path.join(self.current_dir, src)
        dst_path = os.path.join(self.current_dir, dst)

        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
            return f"Copied directory {src} -> {dst}\n"
        else:
            shutil.copy2(src_path, dst_path)
            return f"Copied file {src} -> {dst}\n"

    def _move_files(self, command):
        """Move/rename files"""
        import re
        match = re.match(r"move\(['\"](.+?)['\"],\s*['\"](.+?)['\"]\)", command)
        if not match:
            return "Usage: move('source', 'destination')\n"

        src, dst = match.groups()
        src_path = os.path.join(self.current_dir, src)
        dst_path = os.path.join(self.current_dir, dst)

        shutil.move(src_path, dst_path)
        return f"Moved {src} -> {dst}\n"

    def _delete_files(self, command):
        """Delete files/directories"""
        import re
        recursive = False
        if 'recursive=True' in command:
            recursive = True
            match = re.match(r"delete\(['\"](.+?)['\"]", command)
        else:
            match = re.match(r"delete\(['\"](.+?)['\"]\)", command)

        if not match:
            return "Usage: delete('path') or delete('path', recursive=True)\n"

        path = match.group(1)
        full_path = os.path.join(self.current_dir, path)

        if os.path.isfile(full_path):
            os.remove(full_path)
            return f"Deleted file: {path}\n"
        elif os.path.isdir(full_path):
            if recursive:
                shutil.rmtree(full_path)
                return f"Deleted directory: {path}\n"
            else:
                return f"Use recursive=True to delete directory: {path}\n"
        else:
            return f"Not found: {path}\n"

    def _backup_files(self, command):
        """Backup matching files to timestamped folder"""
        import re
        match = re.match(r"backup\(['\"](.+?)['\"]\)", command)
        if not match:
            return "Usage: backup('*.csv')\n"

        pattern = match.group(1)

        # Create backup folder with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.current_dir, f"backup_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        # Copy matching files
        files = glob.glob(os.path.join(self.current_dir, pattern))
        count = 0
        for f in files:
            if os.path.isfile(f):
                shutil.copy2(f, backup_dir)
                count += 1

        return f"Backed up {count} files to: backup_{timestamp}/\n"

    def _create_zip(self, command):
        """Create zip archive"""
        import re
        match = re.match(r"zip\(['\"](.+?)['\"],\s*['\"](.+?)['\"]\)", command)
        if not match:
            return "Usage: zip('archive.zip', '*.csv')\n"

        zip_name, pattern = match.groups()
        zip_path = os.path.join(self.current_dir, zip_name)

        files = glob.glob(os.path.join(self.current_dir, pattern))

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for f in files:
                if os.path.isfile(f):
                    zipf.write(f, os.path.basename(f))

        size = os.path.getsize(zip_path)
        size_str = f"{size/(1024*1024):.1f} MB" if size > 1024*1024 else f"{size/1024:.1f} KB"

        return f"Created {zip_name} ({size_str}) with {len(files)} files\n"

    def _extract_zip(self, command):
        """Extract zip archive"""
        import re
        match = re.match(r"unzip\(['\"](.+?)['\"],\s*['\"](.+?)['\"]\)", command)
        if not match:
            return "Usage: unzip('archive.zip', 'destination/')\n"

        zip_name, dest = match.groups()
        zip_path = os.path.join(self.current_dir, zip_name)
        dest_path = os.path.join(self.current_dir, dest)

        os.makedirs(dest_path, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(dest_path)

        return f"Extracted {zip_name} to {dest}\n"

    def _grep(self, command):
        """Search in files"""
        import re
        match = re.match(r"grep\(['\"](.+?)['\"],\s*['\"](.+?)['\"]\)", command)
        if not match:
            return "Usage: grep('text', 'file.csv')\n"

        search_text, pattern = match.groups()

        files = glob.glob(os.path.join(self.current_dir, pattern))
        results = []

        for f in files:
            if os.path.isfile(f):
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        for i, line in enumerate(file, 1):
                            if search_text.lower() in line.lower():
                                results.append(f"{os.path.basename(f)}:{i}: {line.strip()}")
                except:
                    pass

        if results:
            return "\n".join(results) + "\n"
        else:
            return f"No matches for '{search_text}' in {pattern}\n"

    def _browse_folder(self):
        """Open folder browser dialog"""
        folder = filedialog.askdirectory(initialdir=self.current_dir)
        if folder:
            self.current_dir = folder
            self._update_dir_display()
            self._print_output(f"Changed to: {self.current_dir}\n")

    def _update_dir_display(self):
        """Update the directory display"""
        self.dir_label.config(text=self.current_dir)

    def _show_find_dialog(self):
        """Show dialog for finding files"""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Find Files")
        dialog.geometry("400x200")
        dialog.transient(self.app.root)

        main = ttk.Frame(dialog, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Search for:").pack(anchor=tk.W)
        search_var = tk.StringVar()
        ttk.Entry(main, textvariable=search_var, width=40).pack(fill=tk.X, pady=5)

        ttk.Label(main, text="In files:").pack(anchor=tk.W, pady=(10,0))
        pattern_var = tk.StringVar(value="*.csv")
        ttk.Entry(main, textvariable=pattern_var, width=40).pack(fill=tk.X, pady=5)

        def do_find():
            cmd = f"grep('{search_var.get()}', '{pattern_var.get()}')"
            dialog.destroy()
            self.execute(cmd)

        ttk.Button(main, text="Find", command=do_find).pack(pady=10)

    def _print_output(self, text, error=False):
        """Print to output"""
        self.output.config(state=tk.NORMAL)
        if error:
            self.output.insert(tk.END, text, 'error')
            self.output.tag_config('error', foreground='#f48771')
        else:
            self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def _on_enter(self, event):
        """Handle Enter key"""
        if not (event.state & 0x1):  # Not Shift
            self.execute_input()
            return "break"
        return None

    def _insert_newline(self, event):
        """Insert newline on Shift+Enter"""
        self.input.insert(tk.INSERT, "\n")
        return "break"

    def _history_up(self, event):
        """Navigate history up"""
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.input.delete("1.0", tk.END)
            self.input.insert("1.0", self.history[self.history_index])
        return "break"

    def _history_down(self, event):
        """Navigate history down"""
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.input.delete("1.0", tk.END)
            self.input.insert("1.0", self.history[self.history_index])
        elif self.history_index == len(self.history) - 1:
            self.history_index = len(self.history)
            self.input.delete("1.0", tk.END)
        return "break"

    def _clear_screen(self):
        """Clear output"""
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)
        self._print_welcome()

def register_plugin(main_app):
    """Register this plugin"""
    plugin = FileConsolePlugin(main_app)
    if hasattr(main_app.center, 'add_console_plugin'):
        main_app.center.add_console_plugin(
            console_name="File Ops",
            console_icon="📁",
            console_instance=plugin
        )
    return None
