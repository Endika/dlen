"""Dlen class."""
import argparse
import io
import os
import re


class DefLen(object):
    """Def count lines."""

    def_name = None
    count = 0
    def_tab = 0
    blank_lines = 2
    warn_line_per_def = 12
    error_line_per_def = 20
    line = ''
    filename = ''

    def _print_def_resume(self):
        number = self.warn_line_per_def
        if self.def_name and self.count > number:
            status = 'WARN'
            if self.count > self.error_line_per_def:
                number = self.error_line_per_def
                status = 'ERROR'
            print('[{}] \'{}\' {} function too long ({} > {} lines)'.format(
                status, self.filename, self.def_name, self.count, number))

    def _reset_count(self):
        self.def_name = None
        self.count = 0
        self.blank_lines = 2

    def detect_def(self):
        """Detect def."""
        result_lts = re.findall(re.compile(br'def(.*?)\('), self.line)
        if ((result_lts) or
                (self.def_name and self.blank_lines == 0)):
            self._print_def_resume()
            self._reset_count()
            if 'def' in self.line:
                self.def_tab = self.line.index('def')
                if result_lts:
                    self.def_name = result_lts[0].strip()
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

    def __init__(self):
        """Init."""
        data = self.create_parser()
        for file in self.iter_source_code(data['files']):
            self.filename = file
            with io.open(file, 'rb') as f:
                for line_number, line in enumerate(f, 1):
                    self.line = line
                    current_tab = self.get_current_tab()
                    if not self.detect_def():
                        if self.def_tab < current_tab:
                            self.count += 1
                            self.blank_lines = 2
                        elif self.def_name:
                            self.blank_lines -= 1


def main():
    """Run in command line."""
    DefLen()
