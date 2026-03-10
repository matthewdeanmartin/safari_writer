import sys
import re
import os
import json
import threading
import time
from pathlib import Path
from typing import Optional, TextIO, List
from safari_basic.interpreter import SafariBasic, BasicError

# Directory containing bundled example programs
_EXAMPLES_DIR = Path(__file__).parent / "examples"

# Keywords for tab completion
BASIC_KEYWORDS = [
    "ABS", "ASC", "CHR$", "CLR", "CLOSE", "CONT", "COS", "DIM", "END",
    "EXP", "FOR", "GOSUB", "GOTO", "IF", "INPUT", "INT", "LEN", "LET",
    "LIST", "LOG", "NEXT", "NEW", "OPEN", "PRINT", "READ", "REM",
    "RENUMBER", "RESTORE", "RETURN", "RND", "RUN", "SAVE", "LOAD",
    "SGN", "SIN", "SQR", "STEP", "STOP", "STR$", "TAN", "THEN",
    "TO", "TRON", "TROFF", "UNDO", "REDO", "VAL", "VARS",
    "BYE", "EXIT", "QUIT", "HELP", "EDIT", "DELETE", "FIND",
    "REPLACE", "FILES", "DIR", "PWD", "CD", "AUTOSAVE", "EXAMPLES",
]

# Per-topic help entries
HELP_TOPICS = {
    "LIST": "LIST [n[,m]]\n  List program lines. LIST alone shows all.\n  LIST 10 shows line 10. LIST 10,50 shows lines 10 through 50.",
    "RUN": "RUN [n]\n  Run the program from the beginning, or from line n.",
    "NEW": "NEW\n  Clear the current program from memory.\n  Warns if there are unsaved changes.",
    "LOAD": 'LOAD "filename"\n  Load a BASIC program from disk.\n  Warns if there are unsaved changes.',
    "SAVE": 'SAVE "filename"\n  Save the current program to disk.',
    "REN": "REN [start[,step[,from]]]\n  Renumber program lines.\n  Default: REN 10,10,0 (start at 10, step 10, from line 0).\n  Alias: RENUMBER",
    "RENUMBER": "See: HELP REN",
    "UNDO": "UNDO\n  Undo the last program edit (up to 100 levels).",
    "REDO": "REDO\n  Redo a previously undone edit.",
    "VARS": "VARS\n  List all current variables and their values.",
    "CLR": "CLR\n  Clear all variables, arrays, and stacks.",
    "CONT": "CONT\n  Continue execution after a STOP statement.",
    "TRON": "TRON [VARS]\n  Enable execution tracing. Shows line numbers as they execute.\n  TRON VARS also shows variable changes after each statement.",
    "TROFF": "TROFF\n  Disable execution tracing.",
    "EDIT": "EDIT <line>\n  Retrieve a stored line into the output for review/copying.\n  The line text is displayed so you can re-enter it with modifications.",
    "DELETE": "DELETE <start>[,<end>]\n  Delete a single line or a range of lines.\n  DELETE 100 deletes line 100. DELETE 100,200 deletes lines 100-200.",
    "FIND": 'FIND "text"\n  Search for a string in the program source.\n  Shows all lines containing the text (case-insensitive).',
    "REPLACE": 'REPLACE "old","new"\n  Replace all occurrences of old with new in the program source.\n  Shows count of replacements made.',
    "FILES": "FILES [pattern]\n  List files in the current directory.\n  Optional glob pattern filters results (e.g., FILES *.bas).\n  Alias: DIR",
    "DIR": "See: HELP FILES",
    "PWD": "PWD\n  Print the current working directory.",
    "CD": 'CD "path"\n  Change the current working directory.',
    "AUTOSAVE": "AUTOSAVE ON / AUTOSAVE OFF\n  Enable or disable automatic saving every 15 seconds.\n  Requires a filename (use SAVE first).",
    "PRINT": 'PRINT expr[;expr...]\n  Output values. Use ; to suppress newline, , for tab.\n  Shorthand: ? expr',
    "INPUT": 'INPUT ["prompt";] var\n  Read a value from the user into a variable.',
    "IF": "IF expr THEN statement\nIF expr THEN line_number\n  Conditional execution. No ELSE clause.",
    "FOR": "FOR var = start TO end [STEP step]\n  Begin a counted loop. Must be closed with NEXT var.",
    "NEXT": "NEXT [var]\n  End of a FOR loop. Increments the variable and loops if not done.",
    "GOTO": "GOTO line_number\n  Jump execution to the specified line.",
    "GOSUB": "GOSUB line_number\n  Call a subroutine. Use RETURN to come back.",
    "RETURN": "RETURN\n  Return from a GOSUB call.",
    "DIM": "DIM var(size)[, var2(size2)]\n  Dimension arrays or string variables.\n  DIM A(100) creates a numeric array.\n  DIM N$(50) creates a string that can hold 50 characters.",
    "END": "END\n  Halt program execution.",
    "STOP": "STOP\n  Pause execution. Use CONT to resume.",
    "REM": "REM comment\n  A remark/comment. Also: ' comment",
    "OPEN": 'OPEN #fd, "filename", "mode"\n  Open a file. Mode is "r" for read or "w" for write.',
    "CLOSE": "CLOSE #fd\n  Close an open file.",
    "BYE": "BYE\n  Exit the REPL. Also: EXIT, QUIT",
    "HELP": "HELP [topic]\n  Show help. HELP alone lists commands.\n  HELP PRINT shows details for PRINT.",
    "EXAMPLES": 'EXAMPLES\n  List bundled demo programs.\n  Use EXAMPLES <name> to load one, e.g. EXAMPLES HELLO',
}


class SafariREPL:
    HISTORY_FILE = ".safari_history"
    MAX_HISTORY = 500

    def __init__(self, out_stream: Optional[TextIO] = None, in_stream: Optional[TextIO] = None):
        self.interpreter = SafariBasic(out_stream=out_stream, in_stream=in_stream)
        self.out_stream = self.interpreter.out_stream
        self.in_stream = self.interpreter.in_stream
        self.current_filename: Optional[str] = None
        self.modified = False
        self.history: List[str] = []
        self._autosave_enabled = False
        self._autosave_timer: Optional[threading.Timer] = None
        self._load_history()

    def _load_history(self):
        try:
            path = os.path.join(os.path.expanduser("~"), self.HISTORY_FILE)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self.history = [l.rstrip('\n') for l in f.readlines()][-self.MAX_HISTORY:]
        except Exception:
            pass

    def _save_history(self):
        try:
            path = os.path.join(os.path.expanduser("~"), self.HISTORY_FILE)
            with open(path, 'w', encoding='utf-8') as f:
                for entry in self.history[-self.MAX_HISTORY:]:
                    f.write(entry + '\n')
        except Exception:
            pass

    def _add_history(self, line: str):
        if line and (not self.history or self.history[-1] != line):
            self.history.append(line)

    def print_out(self, text: str, end: str = '\n'):
        self.out_stream.write(text + end)
        self.out_stream.flush()

    def _warn_unsaved(self) -> bool:
        """Returns True if there are unsaved changes (caller should warn)."""
        return self.modified

    def complete(self, prefix: str) -> List[str]:
        """Return tab-completion candidates for the given prefix."""
        upper = prefix.upper()
        results = []
        # Keyword completion
        for kw in BASIC_KEYWORDS:
            if kw.startswith(upper):
                results.append(kw)
        # Line number completion (contextual)
        if prefix.isdigit():
            for num in self.interpreter.line_order:
                s = str(num)
                if s.startswith(prefix):
                    results.append(s)
        # Filename completion
        try:
            directory = '.'
            file_prefix = prefix
            if '/' in prefix or '\\' in prefix:
                directory = os.path.dirname(prefix)
                file_prefix = os.path.basename(prefix)
            for entry in os.listdir(directory):
                if entry.upper().startswith(file_prefix.upper()):
                    full = os.path.join(directory, entry) if directory != '.' else entry
                    results.append(full)
        except Exception:
            pass
        return results

    def process_line(self, raw_line: str) -> bool:
        """
        Processes a single REPL line.
        Returns True if the REPL should continue, False if it should exit.
        """
        line = raw_line.strip()
        if not line:
            return True

        self._add_history(line)

        # Check for line number (Program Mode)
        match = re.match(r'^(\d+)\s*(.*)', line)
        if match:
            num = int(match.group(1))
            text = match.group(2).strip()
            self.interpreter._save_undo()
            if not text:
                if num in self.interpreter.lines:
                    del self.interpreter.lines[num]
            else:
                self.interpreter.lines[num] = text
            self.interpreter.line_order = sorted(self.interpreter.lines.keys())
            self.modified = True
            return True

        # Immediate Mode
        upper_line = line.upper()

        # Core REPL Commands
        if upper_line == "NEW":
            if self.modified:
                self.print_out("WARNING: UNSAVED CHANGES WILL BE LOST")
            self.interpreter.reset()
            self.current_filename = None
            self.modified = False
            self._stop_autosave()
            self.print_out("READY")
            return True

        if upper_line.startswith("LIST"):
            self._do_list(line)
            return True

        if upper_line.startswith("RUN"):
            try:
                # Check for RUN <line>
                parts = line.split()
                start_line = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                self.interpreter.run_program(start_line)
            except BasicError:
                pass # Already printed
            except Exception as e:
                self.print_out(f"INTERNAL ERROR: {e}")
            return True

        if upper_line.startswith("LOAD"):
            if self.modified:
                self.print_out("WARNING: UNSAVED CHANGES WILL BE LOST")
            self._do_load(line)
            return True

        if upper_line.startswith("SAVE"):
            self._do_save(line)
            return True

        if upper_line.startswith("REN") or upper_line.startswith("RENUMBER"):
            self._do_renumber(line)
            return True

        if upper_line == "UNDO":
            if self.interpreter.undo():
                self.print_out("UNDONE")
            else:
                self.print_out("NOTHING TO UNDO")
            return True

        if upper_line == "REDO":
            if self.interpreter.redo():
                self.print_out("REDONE")
            else:
                self.print_out("NOTHING TO REDO")
            return True

        if upper_line == "CLR":
            self.interpreter._clear_vars()
            return True

        if upper_line == "CONT":
            if self.interpreter.stopped and self.interpreter.pc_idx >= 0:
                self.interpreter.stopped = False
                self.interpreter._run_loop()
            else:
                self.print_out("CANNOT CONTINUE")
            return True

        if upper_line in ("BYE", "EXIT", "QUIT"):
            if self.modified:
                self.print_out("WARNING: UNSAVED CHANGES WILL BE LOST")
            self._stop_autosave()
            self._save_history()
            return False

        if upper_line == "VARS":
            self._do_vars()
            return True

        if upper_line.startswith("HELP"):
            self._do_help(line)
            return True

        if upper_line.startswith("EDIT"):
            self._do_edit(line)
            return True

        if upper_line.startswith("DELETE"):
            self._do_delete(line)
            return True

        if upper_line.startswith("FIND"):
            self._do_find(line)
            return True

        if upper_line.startswith("REPLACE"):
            self._do_replace(line)
            return True

        if upper_line in ("FILES", "DIR") or upper_line.startswith("FILES ") or upper_line.startswith("DIR "):
            self._do_files(line)
            return True

        if upper_line == "PWD":
            self.print_out(os.getcwd())
            return True

        if upper_line.startswith("CD"):
            self._do_cd(line)
            return True

        if upper_line.startswith("AUTOSAVE"):
            self._do_autosave(line)
            return True

        if upper_line.startswith("EXAMPLES"):
            self._do_examples(line)
            return True

        # If not a REPL command, it's a BASIC statement to execute immediately
        try:
            self.interpreter.execute_immediate(line)
        except BasicError:
            pass # Already printed
        except Exception as e:
            self.print_out(f"INTERNAL ERROR: {e}")

        return True

    def _do_list(self, line: str):
        parts = line.upper().replace("LIST", "").strip().split(",")
        start = 0
        end = float('inf')

        if parts[0].strip():
            try:
                start = int(parts[0].strip())
                end = start
            except ValueError:
                pass

        if len(parts) > 1:
            if parts[1].strip():
                try:
                    end = int(parts[1].strip())
                except ValueError:
                    pass
            else:
                end = float('inf')

        for num in self.interpreter.line_order:
            if start <= num <= end:
                self.print_out(f"{num} {self.interpreter.lines[num]}")

    def _do_load(self, line: str):
        match = re.search(r'["\'](.*?)["\']', line)
        filename = match.group(1) if match else line.split()[-1] if len(line.split()) > 1 else self.current_filename

        if not filename:
            self.print_out("LOAD REQUIRES FILENAME")
            return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.interpreter.reset()
                for l in f:
                    self.process_line(l.strip())
                self.current_filename = filename
                self.modified = False
                self.print_out(f"LOADED {filename}")
        except Exception as e:
            self.print_out(f"ERROR LOADING {filename}: {e}")

    def _do_save(self, line: str):
        match = re.search(r'["\'](.*?)["\']', line)
        filename = match.group(1) if match else line.split()[-1] if len(line.split()) > 1 else self.current_filename

        if not filename:
            self.print_out("SAVE REQUIRES FILENAME")
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for num in self.interpreter.line_order:
                    f.write(f"{num} {self.interpreter.lines[num]}\n")
                self.current_filename = filename
                self.modified = False
                self.print_out(f"SAVED {filename}")
        except Exception as e:
            self.print_out(f"ERROR SAVING {filename}: {e}")

    def _do_renumber(self, line: str):
        # REN start,step,from
        params = line.upper().replace("RENUMBER", "").replace("REN", "").strip().split(",")
        start = 10
        step = 10
        from_line = 0

        try:
            if len(params) >= 1 and params[0].strip():
                start = int(params[0].strip())
            if len(params) >= 2 and params[1].strip():
                step = int(params[1].strip())
            if len(params) >= 3 and params[2].strip():
                from_line = int(params[2].strip())
        except ValueError:
            self.print_out("INVALID PARAMETERS FOR RENUMBER")
            return

        count = self.interpreter.renumber(start, step, from_line)
        self.print_out(f"RENUMBERED {count} LINES")

    def _do_vars(self):
        if not self.interpreter.vars and not self.interpreter.arrays:
            self.print_out("NO VARIABLES")
            return
        for name, val in sorted(self.interpreter.vars.items()):
            if isinstance(val, str):
                self.print_out(f'{name} = "{val}"')
            else:
                self.print_out(f'{name} = {val}')
        for name, arr in sorted(self.interpreter.arrays.items()):
            self.print_out(f"{name}({len(arr)-1}) = [ARRAY]")

    def _do_edit(self, line: str):
        parts = line.split()
        if len(parts) < 2 or not parts[1].isdigit():
            self.print_out("EDIT REQUIRES LINE NUMBER")
            return
        num = int(parts[1])
        if num not in self.interpreter.lines:
            self.print_out(f"LINE {num} NOT FOUND")
            return
        self.print_out(f"{num} {self.interpreter.lines[num]}")

    def _do_delete(self, line: str):
        args = line.upper().replace("DELETE", "").strip()
        if not args:
            self.print_out("DELETE REQUIRES LINE NUMBER(S)")
            return
        parts = args.split(",")
        try:
            start = int(parts[0].strip())
            end = int(parts[1].strip()) if len(parts) > 1 else start
        except ValueError:
            self.print_out("INVALID LINE NUMBER")
            return
        self.interpreter._save_undo()
        count = 0
        for num in list(self.interpreter.line_order):
            if start <= num <= end:
                del self.interpreter.lines[num]
                count += 1
        self.interpreter.line_order = sorted(self.interpreter.lines.keys())
        if count:
            self.modified = True
            self.print_out(f"DELETED {count} LINE{'S' if count != 1 else ''}")
        else:
            self.print_out("NO LINES IN RANGE")

    def _do_find(self, line: str):
        match = re.search(r'["\'](.*?)["\']', line)
        if not match:
            self.print_out('FIND REQUIRES "TEXT"')
            return
        needle = match.group(1).upper()
        found = 0
        for num in self.interpreter.line_order:
            source = self.interpreter.lines[num]
            upper_source = source.upper()
            if needle in upper_source:
                # Highlight by showing pointer
                idx = upper_source.index(needle)
                self.print_out(f"{num} {source}")
                pointer = " " * (len(str(num)) + 1 + idx) + "^" * len(needle)
                self.print_out(pointer)
                found += 1
        if found == 0:
            self.print_out("NOT FOUND")
        else:
            self.print_out(f"{found} LINE{'S' if found != 1 else ''} FOUND")

    def _do_replace(self, line: str):
        # REPLACE "old","new"
        matches = re.findall(r'["\'](.*?)["\']', line)
        if len(matches) < 2:
            self.print_out('REPLACE REQUIRES "OLD","NEW"')
            return
        old_text, new_text = matches[0], matches[1]
        if not old_text:
            self.print_out("SEARCH TEXT CANNOT BE EMPTY")
            return
        self.interpreter._save_undo()
        count = 0
        for num in self.interpreter.line_order:
            source = self.interpreter.lines[num]
            # Case-insensitive replace
            new_source = re.sub(re.escape(old_text), new_text, source, flags=re.IGNORECASE)
            if new_source != source:
                self.interpreter.lines[num] = new_source
                count += 1
                self.print_out(f"{num} {new_source}")
        if count:
            self.modified = True
            self.print_out(f"REPLACED IN {count} LINE{'S' if count != 1 else ''}")
        else:
            self.print_out("NOT FOUND")

    def _do_files(self, line: str):
        parts = line.split(maxsplit=1)
        pattern = parts[1].strip() if len(parts) > 1 else None
        try:
            entries = sorted(os.listdir('.'))
            if pattern:
                import fnmatch
                entries = [e for e in entries if fnmatch.fnmatch(e.upper(), pattern.upper())]
            for entry in entries:
                if os.path.isdir(entry):
                    self.print_out(f"  <DIR>  {entry}")
                else:
                    size = os.path.getsize(entry)
                    self.print_out(f"  {size:>7}  {entry}")
            self.print_out(f"{len(entries)} FILE{'S' if len(entries) != 1 else ''}")
        except Exception as e:
            self.print_out(f"ERROR: {e}")

    def _do_cd(self, line: str):
        match = re.search(r'["\'](.*?)["\']', line)
        if match:
            path = match.group(1)
        else:
            parts = line.split(maxsplit=1)
            path = parts[1].strip() if len(parts) > 1 else os.path.expanduser("~")
        try:
            os.chdir(path)
            self.print_out(os.getcwd())
        except Exception as e:
            self.print_out(f"ERROR: {e}")

    def _do_autosave(self, line: str):
        upper = line.upper().strip()
        if "ON" in upper:
            if not self.current_filename:
                self.print_out("SAVE FILE FIRST (USE SAVE COMMAND)")
                return
            self._autosave_enabled = True
            self._schedule_autosave()
            self.print_out("AUTOSAVE ON")
        elif "OFF" in upper:
            self._stop_autosave()
            self.print_out("AUTOSAVE OFF")
        else:
            state = "ON" if self._autosave_enabled else "OFF"
            self.print_out(f"AUTOSAVE IS {state}")

    def _schedule_autosave(self):
        if not self._autosave_enabled:
            return
        self._autosave_timer = threading.Timer(15.0, self._do_autosave_tick)
        self._autosave_timer.daemon = True
        self._autosave_timer.start()

    def _do_autosave_tick(self):
        if self._autosave_enabled and self.current_filename and self.modified:
            try:
                with open(self.current_filename, 'w', encoding='utf-8') as f:
                    for num in self.interpreter.line_order:
                        f.write(f"{num} {self.interpreter.lines[num]}\n")
                self.modified = False
            except Exception:
                pass
        if self._autosave_enabled:
            self._schedule_autosave()

    def _stop_autosave(self):
        self._autosave_enabled = False
        if self._autosave_timer:
            self._autosave_timer.cancel()
            self._autosave_timer = None

    def _do_help(self, line: str):
        parts = line.split(maxsplit=1)
        if len(parts) > 1:
            topic = parts[1].strip().upper()
            if topic in HELP_TOPICS:
                self.print_out(HELP_TOPICS[topic])
            else:
                self.print_out(f"NO HELP FOR '{topic}'")
                # Suggest close matches
                suggestions = [k for k in HELP_TOPICS if k.startswith(topic[:2])]
                if suggestions:
                    self.print_out(f"TRY: {', '.join(suggestions)}")
            return
        self.print_out("SAFARI BASIC REPL COMMANDS:")
        self.print_out("LIST [n[,m]]       - List program lines")
        self.print_out("RUN [n]            - Run program [from line n]")
        self.print_out("NEW                - Clear program")
        self.print_out('LOAD "file"        - Load program from disk')
        self.print_out('SAVE "file"        - Save program to disk')
        self.print_out("REN [s[,i[,f]]]    - Renumber lines")
        self.print_out("EDIT <line>        - Show line for editing")
        self.print_out("DELETE <n>[,<m>]   - Delete line(s)")
        self.print_out('FIND "text"        - Search program source')
        self.print_out('REPLACE "old","new"- Search and replace')
        self.print_out("UNDO / REDO        - Undo/redo program changes")
        self.print_out("VARS               - List variables")
        self.print_out("CLR                - Clear variables")
        self.print_out("CONT               - Continue after STOP")
        self.print_out("TRON [VARS] / TROFF- Trace execution")
        self.print_out("FILES [pattern]    - List directory (alias: DIR)")
        self.print_out("PWD / CD           - Show/change directory")
        self.print_out("AUTOSAVE ON/OFF    - Toggle autosave")
        self.print_out("EXAMPLES [name]    - List/load demo programs")
        self.print_out("BYE / EXIT         - Exit REPL")
        self.print_out("HELP <topic>       - Detailed help on a command")

    def _do_examples(self, line: str):
        parts = line.split(maxsplit=1)
        if len(parts) > 1:
            # Load a specific example
            name = parts[1].strip()
            if not name.lower().endswith(".bas"):
                name += ".bas"
            example_path = _EXAMPLES_DIR / name.lower()
            if not example_path.exists():
                self.print_out(f"EXAMPLE '{name}' NOT FOUND")
                self.print_out("TYPE EXAMPLES TO SEE AVAILABLE DEMOS")
                return
            if self.modified:
                self.print_out("WARNING: UNSAVED CHANGES WILL BE LOST")
            self._do_load(f'LOAD "{example_path}"')
            return
        # List available examples
        if not _EXAMPLES_DIR.exists():
            self.print_out("NO EXAMPLES DIRECTORY FOUND")
            return
        examples = sorted(_EXAMPLES_DIR.glob("*.bas"))
        if not examples:
            self.print_out("NO EXAMPLE PROGRAMS FOUND")
            return
        self.print_out("DEMO PROGRAMS:")
        for ex in examples:
            # Read first line to get description from REM
            desc = ""
            try:
                first_line = ex.read_text(encoding="utf-8").split("\n", 1)[0]
                rem_match = re.match(r'^\d+\s+REM\s+[-—]*\s*(.*?)\s*[-—]*\s*$', first_line, re.IGNORECASE)
                if rem_match:
                    desc = f"  - {rem_match.group(1)}"
            except Exception:
                pass
            self.print_out(f"  {ex.stem.upper()}{desc}")
        self.print_out(f"\nTYPE EXAMPLES <NAME> TO LOAD ONE")

def main():
    repl = SafariREPL()
    print("Safari Basic REPL")
    print("READY")
    while True:
        try:
            line = input("> ")
            if not repl.process_line(line):
                break
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nBREAK")
            repl.interpreter.stopped = True

if __name__ == "__main__":
    main()
