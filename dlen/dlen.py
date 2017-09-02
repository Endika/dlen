"""Dlen class."""
import argparse
import io
import os
import re


class DefLen(object):
    """Def count lines."""

    function_name = None
    class_name = None
    class_count = 0
    count = 0
    function_tab = 0
    class_tab = 0
    class_blank_lines = 2
    blank_lines = 2
    warn_line_per_function = 12
    error_line_per_function = 20
    error_line_per_class = 500
    line = ''
    filename = ''
    output = []
    show_console = False

    def _process_print(self, status, number, function=True):
        type_msg = 'function' if function else 'class'
        name_msg = self.function_name if function else self.class_name
        count = self.count if function else self.class_count
        filename = ' \'{}\''.format(self.filename) if self.filename else ''
        msg = '[{}]{} {} {} too long ({} > {} lines)'.format(
            status, filename, name_msg, type_msg, count, number)
        self.output.append(msg)
        if self.show_console:
            print(msg)

    def _print_def_resume(self):
        number = self.warn_line_per_function
        if self.function_name and self.count > number:
            status = 'WARN'
            if self.count > self.error_line_per_function:
                number = self.error_line_per_function
                status = 'ERROR'
            self._process_print(status, number)

    def _print_class_resume(self):
        number = self.error_line_per_class
        if self.class_name and self.class_count > number:
            status = 'ERROR'
            self._process_print(status, number, function=False)

    def _reset_count(self, function=True):
        if function:
            self.function_name = None
            self.count = 0
            self.blank_lines = 2
        else:
            self.class_name = None
            self.class_count = 0
            self.class_blank_lines = 2

    def detect_function(self):
        """Detect def."""
        result_lts = re.findall(re.compile(br'def(.*?)\('), self.line)
        if ((result_lts) or
                (self.function_name and self.blank_lines == 0)):
            self._print_def_resume()
            self._reset_count()
            if 'def' in self.line:
                self.function_tab = self.line.index('def')
                if result_lts:
                    self.function_name = result_lts[0].strip()
                return True
        return False

    def detect_class(self):
        """Detect def."""
        result_lts = re.findall(re.compile(br'class(.*?)\('), self.line)
        if ((result_lts) or
                (self.class_name and self.class_blank_lines == 0)):
            self._print_class_resume()
            self._reset_count(function=False)
            if 'class' in self.line:
                self.class_tab = self.line.index('class')
                if result_lts:
                    self.class_name = result_lts[0].strip()
                return True
        return False

    def get_current_tab(self):
        """Get current tab."""
        current_tab = 0
        for i in self.line:
            if i in [' ', '\t']:
                current_tab += 1
            else:
                break
        return current_tab

    def create_parser(self):
        """Simple parser argument."""
        parser = argparse.ArgumentParser(
            description='Dlen checks the length of the functions')
        parser.add_argument(
            'files', nargs='*',
            help=('One or more Python source files that need their '
                  'functions checks.'))
        return vars(parser.parse_args())

    def iter_source_code(self, paths, file_lts=[]):
        """Iterate over all Python source files defined in paths."""
        for path in paths:
            if os.path.isdir(path):
                for dirpath, dirnames, filenames in os.walk(
                        path, topdown=True):
                    for filename in filenames:
                        if filename.endswith('.py'):
                            file_lts.append(os.path.join(dirpath, filename))
            else:
                file_lts.append(path)
        return file_lts

    def check_function(self, current_tab):
        """Check function."""
        if not self.detect_function():
            if self.function_tab < current_tab:
                self.count += 1
                self.blank_lines = 2
            elif self.function_name:
                self.blank_lines -= 1

    def check_class(self, current_tab):
        """Check class."""
        if not self.detect_class():
            if self.class_tab < current_tab:
                self.class_count += 1
                self.class_blank_lines = 2
            elif self.class_name:
                self.class_blank_lines -= 1

    def process_line(self, line):
        """Process line."""
        self.line = line
        current_tab = self.get_current_tab()
        self.check_function(current_tab)
        self.check_class(current_tab)

    def _run_import_mode(self, files_content):
        for file_txt in files_content:
            for line in file_txt.split('\n'):
                self.process_line(line)

    def _run_cli_mode(self, files_content):
        self.show_console = True
        data = self.create_parser()
        for file in self.iter_source_code(data['files']):
            self.filename = file
            with io.open(file, 'rb') as f:
                for line_number, line in enumerate(f, 1):
                    self.process_line(line)

    def __init__(self, files_content=None):
        """Init."""
        if files_content:
            self._run_import_mode(files_content)
        else:
            self._run_cli_mode(files_content)


def main():
    """Run in command line."""
    return DefLen()
