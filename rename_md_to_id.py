#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import glob
import re
from urllib.parse import quote, unquote

os.chdir(os.path.dirname(__file__))

ID_PATTERN = re.compile('id:\\s*(\\d*)\\s*[\\r\\n]')

def walk_dir(parent_dir):
    print('[INFO] Analysis for directory {0}'.format(parent_dir))
    all_files = glob.glob(os.path.join(parent_dir, '*'), recursive=False)

    # check directory name
    dir_base_name = os.path.basename(parent_dir)
    if quote(unquote(dir_base_name)) != dir_base_name:
        target_dir_name = os.path.join(os.path.dirname(parent_dir), quote(unquote(dir_base_name)))
        print('[INFO] Rename directory from {0} to {1}'.format(parent_dir, target_dir_name))
        os.rename(parent_dir, target_dir_name)
        parent_dir = target_dir_name

    for file in filter(lambda f: f[-9:].upper() != 'README.MD', all_files):
        if os.path.isdir(file):
            walk_dir(file)
        elif file[-3:].lower() == '.md':
            file_inst = open(file, mode='r', encoding='utf8')
            id_match = ID_PATTERN.search(file_inst.read())
            file_inst.close()
            if id_match is not None:
                id_file = id_match.group(1)
                basename = os.path.basename(file)
                if id_file != basename[0:-3]:
                    target_file_name = os.path.join(os.path.dirname(file), '{0}.md'.format(id_file))
                    print('[INFO] Rename file from {0} to {1}'.format(file, target_file_name))
                    os.rename(file, target_file_name)
            else:
                basename = os.path.basename(file)
                if quote(unquote(basename)) != basename:
                    target_file_name = os.path.join(os.path.dirname(file), quote(unquote(basename)))
                    print('[INFO] Rename directory from {0} to {1}'.format(file, target_file_name))
                    os.rename(file, target_file_name)


if __name__ == "__main__":
    for root_dir in glob.glob(os.path.join('source', '_*', '*')):
        if os.path.isdir(root_dir):
            walk_dir(root_dir)
