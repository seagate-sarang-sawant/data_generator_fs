# !/usr/bin/python
import random
import time
import signal
import os
import sys
import argparse
import re
import logging
from typing import Protocol
from collections import deque
from math import ceil
from argparse import ArgumentParser

KB = 1024
MB = KB * KB
LOGGER = logging.getLogger("DataGenerator")
UNITS = {'KB': KB, 'MB': MB}


def init_logger(log, opts):
    log.setLevel(opts.log_level)
    fh = logging.FileHandler('data_generator.log', mode='w')
    fh.setLevel(opts.log_level)
    console = logging.StreamHandler()
    console.setLevel(opts.log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s'
                                  ' - %(message)s')
    fh.setFormatter(formatter)
    console.setFormatter(formatter)
    log.addHandler(fh)
    log.addHandler(console)


def signal_handler(signum, frame):
    print('SIGINT handler called with signal ', signum)
    LOGGER.info('Signal handler called with signal {},'
                ' exiting process'.format(signum))
    sys.exit(0)


class PDirGenerator(Protocol):
    """Interface Dir Generator interface spec."""
    def create_dir_structure(self) -> None:
        ...


class IterativeDirGenerator(PDirGenerator):
    """Constructs directory tree iteratively, with options from user."""
    def __init__(self, opts):
        self.opts = opts
        self.ndirs = self.opts.get('dirs')
        self.depth = self.opts.get('depth')
        self.root_mount_point = self.opts.get('rootdir')
        self.dq = deque()

    def create_dir_structure(self):
        """
        Creates a directory structure as per script specifications.
        E.g.
        /root_mount_point
        ├── dir1
        │   ├── dir1_1
        │   │   ├── dir1_1_1
        │   │   │   ├── dir1_1_1_1
        │   │   │   │   ├── dir1_1_1_1_1
        │   │   │   │   ├── dir1_1_1_1_2
        │   │   │   │   ├── dir1_1_1_1_3
        │   │   │   │   ├── ...
        │   │   │   │   └── dir1_1_1_1_10
        │   │   │   ├── dir1_1_1_2
        │   │   │   ├── dir1_1_1_3
        │   │   │   ├── ...
        │   │   │   └── dir1_1_1_10
        │   │   ├── dir1_1_2
        │   │   ├── dir1_1_3
        │   │   ├── ....
        │   │   └── dir1_1_10
        │   ├── dir1_2
        │   ├── dir1_3
        │   ├── ...
        │   └── dir1_10
        ├── dir2
        │   ├── dir2_1
        │   ├── dir2_2
        │   ├── dir2_3
        │   ├── ...
        │   └── dir2_10
        ├── ...
        └── dir10
            ├── dir10_1
            ├── dir10_2
            ├── dir10_3
            ├── ...
            └── dir10_10

        :return: None
        """
        prefix = 'dir'
        suffix = '_'
        level = 1
        if not os.path.exists(self.root_mount_point):
            os.mkdir(self.root_mount_point)
        for ix in range(1, self.ndirs + 1):
            t_path = prefix + str(ix)
            os.makedirs(os.path.join(self.root_mount_point, t_path),
                        exist_ok=True)
            self.dq.append((t_path, self.root_mount_point))
        self.dq.append(None)  # marks level 1
        self._create_dir_structure(suffix, self.ndirs, level=level + 1)

    def _create_dir_structure(self, suffix: str, dir_count: int, level: int):
        """Iterative method to generate the directory structure."""
        root_dir = self.root_mount_point
        while len(self.dq) > 1 and level <= self.depth:
            item = self.dq.popleft()
            if item is None:
                self.dq.append(None)
                level += 1
            else:
                root_dir = os.path.join(item[1], item[0])
                for ix in range(1, dir_count + 1):
                    t_path = item[0] + suffix + str(ix)
                    os.makedirs(os.path.join(root_dir, t_path), exist_ok=True)
                    self.dq.append((t_path, root_dir))


class DFSDirGenerator(PDirGenerator):
    """Constructs Recursive directory tree with options from user."""
    def __init__(self, opts):
        self.opts = opts
        self.ndirs = self.opts.get('dirs')
        self.depth = self.opts.get('depth')
        self.root_mount_point = self.opts.get('rootdir')

    def create_dir_structure(self):
        """
        Depth of directory should be 5 levels and each directory
        (including root mount point)
        should have 10 sub-directories.
        :return: bool
        """
        prefix = 'dir'
        suffix = '_'
        level = 0
        if not os.path.exists(self.root_mount_point):
            os.mkdir(self.root_mount_point)
        for ix in range(1, self.ndirs + 1):
            t_path = prefix + str(ix)
            base_path = os.path.join(self.root_mount_point, t_path)
            os.makedirs(base_path, exist_ok=True)
            self._create_dir_structure(base_path, t_path, suffix,
                                       self.ndirs, level=level + 1)

    def _create_dir_structure(self, base_path: str, prefix: str, suffix: str,
                              dir_count: int, level: int):
        if level == self.depth:
            return
        for ix in range(1, dir_count + 1):
            t_path = prefix + suffix + str(ix)
            new_base_path = os.path.join(base_path, t_path)
            os.makedirs(new_base_path, exist_ok=True)
            self._create_dir_structure(new_base_path, t_path, suffix,
                                       dir_count, level=level + 1)


class DataGenerator:
    unc_buf = os.urandom(MB)  # Random buffer of 1 MB

    def __init__(self, opts):
        self.opts = opts
        self.total_files_created = 0
        self.root_mount_point = self.opts.get('rootdir')

    @staticmethod
    def generate_dir_structure(default_gen: PDirGenerator):
        default_gen.create_dir_structure()

    def generate_data(self):
        """Generates data within root mount point FS hierarchy."""
        root_dir = self.root_mount_point
        files = self.opts.get('files')
        depth = self.opts.get('depth')
        dirs = self.opts.get('dirs')
        min_sz, max_sz = self.opts.get('size').split('-')  # 4KB-8KB
        match = re.match(r'(\d+?)([\w]+)', min_sz)
        min_s, min_unit = (int(match.groups()[0]), match.groups()[1])
        min_s = min_s * UNITS[min_unit]
        match = re.match(r'(\d+?)([\w]+)', max_sz)
        max_s, max_unit = (int(match.groups()[0]), match.groups()[1])
        max_s = max_s * UNITS[max_unit]
        total_dirs = sum(pow(dirs, i) for i in range(depth, 0, -1))
        # approx calc if the total files are not divisible by total dirs
        files_per_dir = ceil(files / total_dirs)
        LOGGER.info('Starting walk ...' + root_dir)
        root_dir = os.path.abspath(root_dir)
        LOGGER.info('Absolute path of root dir is ' + root_dir)
        skip_level = 1
        prefix = 'file'
        for root, subdirs, files in os.walk(root_dir):
            if skip_level == 1:
                LOGGER.info(f'Skipping level {skip_level} files creation')
                skip_level += 1
                continue
            stats = dict()
            for ix in range(1, files_per_dir + 1):
                name = os.path.join(root, prefix + str(ix))
                stats[name] = random.randint(min_s, max_s)
            self.save_to_disk(stats)

    @staticmethod
    def save_to_disk(st):
        """
        Constructs files from stats dict items
        with pre allocated buffer."""
        ts = str(time.time())
        for k, v in st.items():
            with open(f'{k}_{ts}', mode='wb') as fd:
                try:
                    fd.write(DataGenerator.unc_buf[:v + 1])
                    LOGGER.info(f'Written file {k}_{ts}')
                except Exception as fault:
                    LOGGER.exception("Exception {}".
                                     format(str(sys.exc_info())))
                    LOGGER.exception("Exception occurred in writing the"
                                     " file.", fault)


def parse_args(parser: ArgumentParser):
    parser.add_argument("-d", "--depth", type=int, default=5,
                        help="Depth of directory structure. e.g. 5 "
                             "level depth under var dir /var/a/b/c/d/e")
    parser.add_argument("-n", "--dirs", type=int,
                        help="Number of directories to be created within"
                             " a dir at any level.")
    parser.add_argument("-r", "--rootdir", type=str,
                        help="Root dir in which the data is to be created")
    parser.add_argument("-s", "--size", type=str, default='4KB-8KB',
                        help="Size range of the file to be created"
                             " e.g. 4KB-8KB, 4KB-1MB")
    parser.add_argument("-t", "--files", type=int, default=10000,
                        help="Number of files to be created in "
                             "the directory structure.")
    parser.add_argument("-c", "--content", type=str,
                        default='random', help="Content type Random or else.")
    parser.add_argument("-l", "--log_level", type=int, default=logging.DEBUG,
                        help="log level value as defined below" +
                             "CRITICAL = 50" +
                             "FATAL = CRITICAL" +
                             "ERROR = 40" +
                             "WARNING = 30 WARN = WARNING" +
                             "INFO = 20 DEBUG = 10"
                        )
    parser.add_argument("-p", dest="benchmark", action='store_false',
                        help="Time the run.")
    return parser.parse_args()


def main():
    parser = argparse.ArgumentParser()
    opts = parse_args(parser)
    level = opts.log_level
    level = logging.getLevelName(level)
    opts.log_level = level
    init_logger(LOGGER, opts)
    # Set the signal handler
    signal.signal(signal.SIGINT, signal_handler)
    dir_gen = DFSDirGenerator(vars(opts))
    # dir_gen = IterativeDirGenerator(vars(opts))
    data_gen = DataGenerator(vars(opts))
    data_gen.generate_dir_structure(dir_gen)
    data_gen.generate_data()


if __name__ == "__main__":
    main()
    # Comments to be removed
    # tested both dir generators and data generators due to disk space
    # limitations of my machine.
    # TC1: --files=200 --depth=3 --dirs=5 --rootdir="/Users/sarangsawant" -l=10
    # TC2: --files=2000 --depth=3 --dirs=5  \
    # --rootdir="/Users/sarangsawant" -l=10
