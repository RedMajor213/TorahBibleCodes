#!/usr/bin/env python3
"""
TorahBibleCodes GUI - A graphical user interface for Torah Bible Codes search software.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import sys
import io
import os
import subprocess

## Set working directory to script location
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class TorahBibleCodesGUI:
    """Main GUI Application for Torah Bible Codes Search"""
    
    CODICES = {
        1: ("Koren Codex", "[Torah: 304805]"),
        2: ("Leningrad Codex", "[Torah: 304850; Tanach: 1197042]"),
        3: ("MAM Collection", "[Torah: 304801; Tanach: 1196839]")
    }
    
    TEXTS = {
        1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
        6: "Joshua", 7: "Judges", 8: "I Samuel", 9: "II Samuel", 10: "I Kings",
        11: "II Kings", 12: "Isaiah", 13: "Jeremiah", 14: "Ezekiel", 15: "Hosea",
        16: "Joel", 17: "Amos", 18: "Obadiah", 19: "Jonah", 20: "Micah",
        21: "Nahum", 22: "Habakkuk", 23: "Zephaniah", 24: "Haggai", 25: "Zechariah",
        26: "Malachi", 27: "Psalms", 28: "Proverbs", 29: "Job", 30: "Song of Songs",
        31: "Ruth", 32: "Lamentations", 33: "Ecclesiastes", 34: "Esther", 35: "Daniel",
        36: "Ezra", 37: "Nehemiah", 38: "I Chronicles", 39: "II Chronicles",
        40: "Pentateuch (Torah)", 41: "Prophets (Nevi'im)", 42: "Writings (K'tuvim)",
        43: "Hebrew Bible (Tanach)", 44: "Samuel (Combined)", 45: "Kings (Combined)",
        46: "Ezra-Nehemiah", 47: "Chronicles (Combined)"
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("Torah Bible Codes - ELS Search Software")
        self.root.geometry("1000x750")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.codex_var = tk.IntVar(value=2)
        self.text_var = tk.IntVar(value=1)
        self.matrix_var = tk.StringVar(value="50")
        self.skip_min_var = tk.StringVar(value="1")
        self.skip_max_var = tk.StringVar(value="100")
        self.is_running = False
        self.process = None
        
        self._build_ui()
        
    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        ## Left panel
        left = ttk.LabelFrame(main, text="Search Configuration", padding=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0,5))
        
        ## Codex selection
        ttk.Label(left, text="1. Select Codex:", font=('Helvetica', 11, 'bold')).pack(anchor=tk.W, pady=(0,5))
        for num, (name, desc) in self.CODICES.items():
            ttk.Radiobutton(left, text=f"{name} {desc}", variable=self.codex_var, 
                          value=num, command=self._on_codex_change).pack(anchor=tk.W)
        
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ## Text selection
        ttk.Label(left, text="2. Select Text:", font=('Helvetica', 11, 'bold')).pack(anchor=tk.W, pady=(0,5))
        
        text_frame = ttk.Frame(left)
        text_frame.pack(fill=tk.X)
        
        self.text_listbox = tk.Listbox(text_frame, height=10, exportselection=False)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_listbox.yview)
        self.text_listbox.config(yscrollcommand=scrollbar.set)
        self.text_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._populate_texts()
        self.text_listbox.selection_set(0)
        
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ## Matrix size
        ttk.Label(left, text="3. 2D Matrix Columns:", font=('Helvetica', 11, 'bold')).pack(anchor=tk.W, pady=(0,5))
        ttk.Entry(left, textvariable=self.matrix_var, width=15).pack(anchor=tk.W)
        ttk.Label(left, text="(Number of columns for output matrix)", font=('Helvetica', 9)).pack(anchor=tk.W)
        
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ## Skip distances
        ttk.Label(left, text="4. Skip Distances (d):", font=('Helvetica', 11, 'bold')).pack(anchor=tk.W, pady=(0,5))
        skip_frame = ttk.Frame(left)
        skip_frame.pack(fill=tk.X)
        ttk.Label(skip_frame, text="Min:").pack(side=tk.LEFT)
        ttk.Entry(skip_frame, textvariable=self.skip_min_var, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(skip_frame, text="Max:").pack(side=tk.LEFT, padx=(10,0))
        ttk.Entry(skip_frame, textvariable=self.skip_max_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ## Search terms
        ttk.Label(left, text="5. ELS Search Terms (Hebrew):", font=('Helvetica', 11, 'bold')).pack(anchor=tk.W, pady=(0,5))
        ttk.Label(left, text="Enter each term on a new line:", font=('Helvetica', 9)).pack(anchor=tk.W)
        
        self.terms_text = scrolledtext.ScrolledText(left, height=6, width=35, font=('Arial', 12))
        self.terms_text.pack(fill=tk.X, pady=5)
        self.terms_text.insert('1.0', "קיאן\nשחלה")  ## Default example terms
        
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ## Buttons
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.run_btn = ttk.Button(btn_frame, text="▶ Run Search", command=self._run_search)
        self.run_btn.pack(side=tk.LEFT, padx=(0,5))
        
        self.stop_btn = ttk.Button(btn_frame, text="■ Stop", command=self._stop_search, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="📂 Open Output", command=self._open_output).pack(side=tk.RIGHT)
        
        ## Help button
        btn_frame2 = ttk.Frame(left)
        btn_frame2.pack(fill=tk.X, pady=(10,5))
        
        ttk.Button(btn_frame2, text="❓ How to Use", command=self._show_help).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ## Right panel - Output
        right = ttk.LabelFrame(main, text="Output Log", padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(right, height=30, width=60, font=('Courier', 10))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.insert('1.0', "Welcome to Torah Bible Codes!\n\nConfigure your search on the left and click 'Run Search'.\n\nOutput files will be saved to: USER_GENERATED_FILES/\n")
        
        ## Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _populate_texts(self):
        self.text_listbox.delete(0, tk.END)
        codex = self.codex_var.get()
        max_text = 5 if codex == 1 else 47
        for num in range(1, max_text + 1):
            self.text_listbox.insert(tk.END, f"{num}. {self.TEXTS.get(num, 'Unknown')}")
            
    def _on_codex_change(self):
        self._populate_texts()
        self.text_listbox.selection_set(0)
        
    def _get_selected_text(self):
        sel = self.text_listbox.curselection()
        return sel[0] + 1 if sel else 1
        
    def _log(self, msg):
        self.output_text.insert(tk.END, msg)
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
    def _run_search(self):
        if self.is_running:
            return
            
        ## Get parameters
        codex = self.codex_var.get()
        text_num = self._get_selected_text()
        matrix_cols = self.matrix_var.get()
        skip_min = self.skip_min_var.get()
        skip_max = self.skip_max_var.get()
        terms = self.terms_text.get('1.0', tk.END).strip().split('\n')
        terms = [t.strip() for t in terms if t.strip()]
        
        if not terms:
            messagebox.showerror("Error", "Please enter at least one search term.")
            return
            
        self.is_running = True
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Running search...")
        
        self.output_text.delete('1.0', tk.END)
        self._log(f"Starting ELS Search...\n")
        self._log(f"Codex: {self.CODICES[codex][0]}\n")
        self._log(f"Text: {self.TEXTS.get(text_num, 'Unknown')}\n")
        self._log(f"Matrix columns: {matrix_cols}\n")
        self._log(f"Skip distances: {skip_min} to {skip_max}\n")
        self._log(f"Search terms: {terms}\n")
        self._log("-" * 50 + "\n\n")
        
        ## Create input script for automated execution
        thread = threading.Thread(target=self._execute_search, 
                                 args=(codex, text_num, matrix_cols, skip_min, skip_max, terms))
        thread.daemon = True
        thread.start()
        
    def _execute_search(self, codex, text_num, matrix_cols, skip_min, skip_max, terms):
        try:
            ## Build input sequence for p.py
            inputs = [
                str(codex),      ## Codex selection
                str(text_num),   ## Text selection  
                matrix_cols,     ## Matrix columns
                "1",             ## Manual input type
                str(len(terms)), ## Number of search terms
            ]
            inputs.extend(terms)  ## Add each search term
            inputs.extend([skip_min, skip_max])  ## Skip distances
            
            input_str = '\n'.join(inputs) + '\n'
            
            ## Run p.py with piped input
            self.process = subprocess.Popen(
                [sys.executable, 'p.py'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            ## Send all inputs
            self.process.stdin.write(input_str)
            self.process.stdin.flush()
            self.process.stdin.close()
            
            ## Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                if not self.is_running:
                    break
                self.root.after(0, self._log, line)
                
            self.process.wait()
            
            self.root.after(0, self._log, "\n" + "=" * 50 + "\n")
            self.root.after(0, self._log, "Search completed! Check USER_GENERATED_FILES/ for results.\n")
            
        except Exception as e:
            self.root.after(0, self._log, f"\nError: {str(e)}\n")
        finally:
            self.root.after(0, self._search_finished)
            
    def _search_finished(self):
        self.is_running = False
        self.process = None
        self.run_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Ready")
        
    def _stop_search(self):
        if self.process:
            self.process.terminate()
        self.is_running = False
        self._log("\n\nSearch stopped by user.\n")
        self._search_finished()
        
    def _open_output(self):
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "USER_GENERATED_FILES")
        if os.path.exists(output_dir):
            if sys.platform == 'darwin':
                subprocess.run(['open', output_dir])
            elif sys.platform == 'win32':
                subprocess.run(['explorer', output_dir])
            else:
                subprocess.run(['xdg-open', output_dir])
        else:
            messagebox.showinfo("Info", "Output folder does not exist yet. Run a search first.")
            
    def _show_help(self):
        """Display the How to Use help dialog"""
        help_window = tk.Toplevel(self.root)
        help_window.title("How to Use - Torah Bible Codes")
        help_window.geometry("700x650")
        help_window.transient(self.root)
        
        ## Main container with scrollbar
        container = ttk.Frame(help_window, padding=15)
        container.pack(fill=tk.BOTH, expand=True)
        
        ## Create canvas with scrollbar for long content
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        ## Help content
        help_text = scrollable_frame
        
        ## Title
        ttk.Label(help_text, text="How to Use Torah Bible Codes", 
                 font=('Helvetica', 16, 'bold')).pack(anchor=tk.W, pady=(0,15))
        
        ## Overview
        ttk.Label(help_text, text="Overview", font=('Helvetica', 13, 'bold')).pack(anchor=tk.W, pady=(10,5))
        overview = """This software searches for Equidistant Letter Sequences (ELS) in Hebrew Bible texts. 
An ELS is a sequence of letters found at regular intervals (skip distances) within the text. 
For example, finding the letters of a word by skipping every 50 letters."""
        ttk.Label(help_text, text=overview, wraplength=650, justify=tk.LEFT).pack(anchor=tk.W, pady=(0,10))
        
        ## Step 1: Codex
        ttk.Label(help_text, text="1. Select Codex", font=('Helvetica', 13, 'bold')).pack(anchor=tk.W, pady=(10,5))
        codex_text = """Choose which manuscript collection to search:

• Koren Codex - Based on the Claremont Michigan Transliteration. Contains only the Torah (5 books of Moses). Best for focused Torah-only searches.

• Leningrad Codex - The oldest complete Hebrew Bible manuscript (c. 1008 CE). Contains the complete Tanach (Torah, Prophets, and Writings). Most commonly used for research.

• MAM (Miqra According to the Masorah) - Based on the Aleppo Codex, considered the most authoritative Masoretic text. Contains the complete Tanach.

Recommendation: Start with Leningrad Codex for the most comprehensive searches."""
        ttk.Label(help_text, text=codex_text, wraplength=650, justify=tk.LEFT).pack(anchor=tk.W, pady=(0,10))
        
        ## Step 2: Text
        ttk.Label(help_text, text="2. Select Text", font=('Helvetica', 13, 'bold')).pack(anchor=tk.W, pady=(10,5))
        text_text = """Choose which book(s) of the Hebrew Bible to search:

• Individual Books (1-39): Search within a single book (Genesis, Exodus, Isaiah, Psalms, etc.)

• Combined Collections:
   - Pentateuch/Torah (40): All 5 books of Moses combined
   - Prophets/Nevi'im (41): All prophetic books combined
   - Writings/K'tuvim (42): All writings combined
   - Hebrew Bible/Tanach (43): The entire Hebrew Bible
   - Combined books (44-47): Samuel, Kings, Ezra-Nehemiah, Chronicles as single texts

Recommendation: For beginners, start with Genesis or the Torah. Larger texts take longer to search but may reveal more patterns."""
        ttk.Label(help_text, text=text_text, wraplength=650, justify=tk.LEFT).pack(anchor=tk.W, pady=(0,10))
        
        ## Step 3: 2D Matrix
        ttk.Label(help_text, text="3. 2D Matrix Columns", font=('Helvetica', 13, 'bold')).pack(anchor=tk.W, pady=(10,5))
        matrix_text = """This controls how the text is displayed in the output CSV file as a 2D grid.

What it means:
• The entire text is arranged into a grid with X columns and Y rows
• The number you enter is the number of COLUMNS (width) of this grid
• The rows are calculated automatically based on the text length

How to choose:
• Common values: 50, 100, 200, 500
• Smaller numbers (50-100): Easier to view in Excel, good for visual inspection
• The program will show you a list of "factors" (exact divisors) of the text length
• Using a factor creates a perfectly rectangular matrix
• You can use ANY number - the program will add padding if needed

Example: For Genesis (78,069 letters), entering 50 creates a grid of 50 columns × 1,562 rows.

Recommendation: Start with 50 or 100 for easy viewing in spreadsheet software. Values over 800 may exceed Excel's column limit."""
        ttk.Label(help_text, text=matrix_text, wraplength=650, justify=tk.LEFT).pack(anchor=tk.W, pady=(0,10))
        
        ## Step 4: Skip Distances
        ttk.Label(help_text, text="4. Skip Distances (d)", font=('Helvetica', 13, 'bold')).pack(anchor=tk.W, pady=(10,5))
        skip_text = """The skip distance (d) is the number of letters between each letter of an ELS.

How ELS works:
If searching for "תורה" (Torah) with skip distance d=50:
• Find first letter "ת" at position n
• Look for "ו" at position n+50
• Look for "ר" at position n+100
• Look for "ה" at position n+150

Min and Max values:
• Min: The smallest skip distance to search (e.g., 1)
• Max: The largest skip distance to search (e.g., 100)
• The program searches ALL skip distances from Min to Max

Positive vs Negative:
• Positive d: Searches forward through the text
• Negative d: Searches backward through the text
• To search both directions, use negative Min (e.g., -100) and positive Max (e.g., 100)

Recommendation:
• For quick searches: Min=1, Max=100
• For thorough searches: Min=-1000, Max=1000
• Larger ranges take longer but find more results
• Skip distance of 1 finds consecutive letters (normal spelling)"""
        ttk.Label(help_text, text=skip_text, wraplength=650, justify=tk.LEFT).pack(anchor=tk.W, pady=(0,10))
        
        ## Step 5: Search Terms
        ttk.Label(help_text, text="5. ELS Search Terms", font=('Helvetica', 13, 'bold')).pack(anchor=tk.W, pady=(10,5))
        terms_text = """Enter the Hebrew words or phrases you want to search for.

How to enter:
• Type or paste Hebrew text directly
• Enter ONE search term per line
• Spaces within terms are automatically removed
• You can search for multiple terms at once

Examples:
   משיח        (Messiah)
   ישראל       (Israel)
   תורה        (Torah)
   בראשית      (Genesis/In the beginning)

Tips:
• Hebrew is read right-to-left, but you can type/paste normally
• Names, words, and short phrases work best
• Longer terms are less likely to be found but more statistically significant
• The program searches for each term independently

Recommendation: Start with 2-4 letter words to verify the search is working, then try longer terms."""
        ttk.Label(help_text, text=terms_text, wraplength=650, justify=tk.LEFT).pack(anchor=tk.W, pady=(0,10))
        
        ## Output Files
        ttk.Label(help_text, text="Understanding Output Files", font=('Helvetica', 13, 'bold')).pack(anchor=tk.W, pady=(10,5))
        output_text = """Results are saved to the USER_GENERATED_FILES folder:

• 2D Matrix CSV: The text arranged in a grid format
• Letter Statistics: Count and percentage of each Hebrew letter
• Gematria Values: Numerical values for each word
• ELS Matches: All found ELS sequences with their positions
• Individual ELS files: Detailed data for each search term

Each file is named with the codex, text, matrix size, and search parameters for easy identification."""
        ttk.Label(help_text, text=output_text, wraplength=650, justify=tk.LEFT).pack(anchor=tk.W, pady=(0,10))
        
        ## Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ## Close button
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)
        
        ## Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        ## Focus the help window
        help_window.focus_set()


def main():
    root = tk.Tk()
    app = TorahBibleCodesGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
