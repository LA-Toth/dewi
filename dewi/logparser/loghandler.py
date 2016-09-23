# Copyright 2016 Laszlo Attila Toth
# Distributed under the terms of the GNU General Public License v3

import os
import re
import time
import typing

from dewi.logparser.syslog import Parser
from dewi.module_framework.config import Config
from dewi.module_framework.messages import Messages, Level, CORE_CATEGORY
from dewi.module_framework.module import Module


class LogParserModule:
    def __init__(self, config: Config, messages: Messages):
        self._config = config
        self._messages = messages

    def set(self, entry: str, value):
        self._config.set(entry, value)

    def get(self, entry: str):
        return self._config.get(entry)

    def add_message(self, level: Level, category, message: str):
        self._messages.add(level, category, message)

    def get_registration(self) -> typing.List[typing.Dict[str, typing.Union[str, callable]]]:
        return []

    def start(self):
        pass

    def finish(self):
        pass


class _Pattern:
    def __init__(self, config: typing.Dict[str, typing.Union[str, callable]]):
        self.program = config.get('program', '')
        self.message_substring = config.get('message_substring', '')
        self.callback = config['callback']
        regex = config.get('message_regex', '')

        if regex:
            self.message_regex = re.compile(regex)
            self.process = self.process_regex
        else:
            self.message_regex = ''
            if self.message_substring:
                self.process = self.process_substring
            else:
                self.process = self.callback

    def process_regex(self, matched_line):
        m = self.message_regex.match(matched_line.group('msg'))

        if m:
            self.callback(matched_line)

    def process_substring(self, matched_line):
        if self.message_substring in matched_line.group('msg'):
            self.callback(matched_line)


class LogHandlerModule(Module):
    """
    @type modules typing.List[LogParserModule]
    """

    def __init__(self, config: Config, messages: Messages, base_path: str):
        """
        base_path: which contains the directory of log messages
        It can be e.g. '/var'
        """
        super().__init__(config, messages)
        self._log_dir = os.path.join(base_path, 'logs')
        if not os.path.exists(self._log_dir):
            self._log_dir = os.path.join(base_path, 'log')
        if not os.path.exists(self._log_dir):
            self._log_dir = os.path.join(base_path, 'var_log')

        self.parser = Parser()
        self.modules = list()
        self._program_parsers = dict()
        self._other_parsers = set()

    def provide(self):
        return 'log'

    def register_module(self, m: type):
        self.modules.append(m(self._config, self._messages))

    def run(self):
        self._init_parsers()
        files = self._collect_files()
        self._process_files(files)
        self._finalize_parsers()

    def _init_parsers(self):
        for module in self.modules:
            registrations = module.get_registration()
            for reg in registrations:
                if 'program' in reg:
                    self._add_to_map(self._program_parsers, reg['program'], _Pattern(reg))
                else:
                    self._other_parsers.add(_Pattern(reg))
            module.start()

    @staticmethod
    def _add_to_map(dictionary, key, value):
        if key not in dictionary:
            dictionary[key] = set()

        dictionary[key].add(value)

    def _get_program_modules(self, program: str):
        return self._program_parsers[program] if program in self._program_parsers else set()

    def _finalize_parsers(self):
        for module in self.modules:
            module.finish()

    def _collect_files(self):
        date_file_map = dict()
        files = os.listdir(self._log_dir)
        for file in files:
            if not file.startswith('messages-') and not file.startswith('syslog-'):
                continue

            filename = os.path.join(self._log_dir, file)
            with open(filename) as f:
                line = f.readline()
                parsed = self.parser.parse_date(line)
                date_file_map[parsed.group('date')] = filename

        return [date_file_map[k] for k in sorted(date_file_map.keys())]

    def _process_files(self, files: typing.List[str]):
        start = time.clock()
        cnt = 0
        for fn in files:
            with open(fn) as f:
                line = 'non-empty'
                while line:
                    line = f.readline()
                    cnt += 1
                    self._process_line(line)

        end = time.clock()
        diff = end - start
        self.add_message(
            Level.DEBUG, CORE_CATEGORY,
            "Run time: {} line(s) in {} s ({}/s)".format(cnt, diff, int(cnt / diff)))

    def _process_line(self, line: str):
        line_match = self.parser.parse(line)
        if not line_match:
            return

        for module in self._get_program_modules(line_match.group('app')):
            module.process(line_match)

        for module in self._other_parsers:
            module.process(line_match)
