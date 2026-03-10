import sys
import re
import os
from typing import Optional, TextIO
from safari_basic.interpreter import SafariBasic, BasicError

class SafariREPL:
    def __init__(self, out_stream: Optional[TextIO] = None, in_stream: Optional[TextIO] = None):
        self.interpreter = SafariBasic(out_stream=out_stream, in_stream=in_stream)
        self.out_stream = self.interpreter.out_stream
        self.in_stream = self.interpreter.in_stream
        self.current_filename: Optional[str] = None
        self.modified = False

    def print_out(self, text: str, end: str = '\n'):
        self.out_stream.write(text + end)
        self.out_stream.flush()

    def process_line(self, raw_line: str) -> bool:
        """
        Processes a single REPL line. 
        Returns True if the REPL should continue, False if it should exit.
        """
        line = raw_line.strip()
        if not line:
            return True

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
                # In a real app we'd ask for confirmation, but for now just NEW.
                pass
            self.interpreter.reset()
            self.current_filename = None
            self.modified = False
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
            return False

        if upper_line == "VARS":
            self._do_vars()
            return True

        if upper_line == "HELP":
            self._do_help()
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

    def _do_help(self):
        self.print_out("SAFARI BASIC REPL COMMANDS:")
        self.print_out("LIST [n[,m]] - List program lines")
        self.print_out("RUN [n]      - Run program [from line n]")
        self.print_out("NEW          - Clear program")
        self.print_out("LOAD \"file\"  - Load program from disk")
        self.print_out("SAVE \"file\"  - Save program to disk")
        self.print_out("REN [s[,i[,f]]] - Renumber lines")
        self.print_out("UNDO / REDO  - Undo/redo program changes")
        self.print_out("VARS         - List variables")
        self.print_out("CLR          - Clear variables")
        self.print_out("CONT         - Continue after STOP")
        self.print_out("TRON / TROFF - Trace execution")
        self.print_out("BYE / EXIT   - Exit REPL")
        self.print_out("HELP         - This message")

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
