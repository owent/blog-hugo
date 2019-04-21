#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import glob
import re

os.chdir(os.path.dirname(__file__))

SUMMARY_FILE = open('SUMMARY.md', mode='w', encoding='utf8')

SUMMARY_FILE.write('# Summary\r\n\r\n')

SUMMARY_FILE.write('* [About Me](source/about/_index.md)\r\n')

TITLE_PATTERN = re.compile('title: ([^\r\n]*)')
ID_PATTERN = re.compile('id:\\s*(\\d*)')

REPLACE_PATTERN = re.compile('([\\[\\]\\(\\)])')

def walk_dir(parent_dir, *, ident=''):
    print('[INFO] Analysis for directory {0}'.format(parent_dir))
    all_files = glob.glob(os.path.join(parent_dir, '*'))
    if all_files is None or len(all_files) == 0:
        return
    all_files.sort(reverse=True)
    readme_file = None
    def get_readme_file(parent_dir, ident):
        title_name = os.path.basename(parent_dir)
        title_name = REPLACE_PATTERN.sub('\\\\\\g<0>', title_name)
        title_md = '{0}* [{1}]({2}/README.md)'.format(
            ident, title_name,
            REPLACE_PATTERN.sub('\\\\\\g<0>', parent_dir.replace('\\', '/'))
        )
        SUMMARY_FILE.write(title_md)
        SUMMARY_FILE.write('\r\n')
        readme_file = open('{0}/README.md'.format(parent_dir), mode='w', encoding='utf8')
        readme_file.write('# {0}\r\n\r\n'.format(title_name))
        return readme_file

    for file in filter(lambda f: f[-9:].upper() != 'README.MD', all_files):
        if os.path.isdir(file):
            if readme_file is None:
                readme_file = get_readme_file(parent_dir, ident)
            title_file = os.path.basename(file)
            readme_file.write('  * [{0}]({1}/README.md)\r\n'.format(
                title_file, REPLACE_PATTERN.sub('\\\\\\g<0>', os.path.relpath(file, parent_dir).replace('\\', '/'))))
            walk_dir(file, ident=ident + ' ')
        elif file[-3:].lower() == '.md':
            if readme_file is None:
                readme_file = get_readme_file(parent_dir, ident)
            title_match = TITLE_PATTERN.search(open(file, mode='r', encoding='utf8').read())
            if title_match is not None:
                title_file = title_match.group(1)
                if title_file[0:1] == '"' or title_file[0:1] == "'":
                    if title_file[0:1] == title_file[-1:]:
                        title_file = title_file[1:-1]
            else:
                title_file = os.path.basename(file)[0:-3]
            title_file = REPLACE_PATTERN.sub('\\\\\\g<0>', title_file)
            SUMMARY_FILE.write('{0}  * [{1}]({2})\r\n'.format(
                ident, title_file, REPLACE_PATTERN.sub('\\\\\\g<0>', file.replace('\\', '/'))))
            readme_file.write('  * [{0}]({1})\r\n'.format(
                title_file, REPLACE_PATTERN.sub('\\\\\\g<0>', os.path.relpath(file, parent_dir).replace('\\', '/'))))


if __name__ == "__main__":
    dirs = glob.glob(os.path.join('source', 'post', '*'))
    dirs.sort(reverse=True)
    for root_dir in dirs:
        if os.path.isdir(root_dir):
            walk_dir(root_dir, ident='')
