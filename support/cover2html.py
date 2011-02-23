#!/usr/bin/env python
#
# Convert coverage output to HTML table.
#
# Copyright (c) 2006  Michal Kwiatkowski <ruby@joker.linuxstuff.pl>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# * Neither the name of the author nor the names of his contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 

import re
import sys


def sort_by_cover(lines):
    def get_percent(obj):
        return int(obj[3][:-1])

    def compare(x, y):
        return cmp(get_percent(x), get_percent(y))

    lines.sort(compare)


def make_row(line, header=False, emphasis=False):
    result = []

    tag = 'td'
    if header:
        tag = 'th'

    result.append('<tr>\n')

    for field in line:
        if emphasis:
            result.append('<%(tag)s><strong>%(field)s</strong></%(tag)s>\n' % \
                          {'tag': tag, 'field': field})
        else:
            result.append('<%(tag)s>%(field)s</%(tag)s>\n' % \
                          {'tag': tag, 'field': field})

    result.append('</tr>\n')

    return ''.join(result)


def cover2html(text):
    text_lines = map(lambda x: re.split(r'\s+', x, 4), text.splitlines())
    text_lines = filter(lambda x: x[0].strip('-'), text_lines)

    title_line = text_lines.pop(0)
    summary_line = text_lines.pop()

    sort_by_cover(text_lines)

    result = []
    result.append('<table border="1">\n')
    result.append(make_row(title_line, header=True))

    for line in text_lines:
        result.append(make_row(line))

    result.append(make_row(summary_line, emphasis=True))
    result.append('</table>\n')

    return ''.join(result)


if __name__ == '__main__':
    print cover2html(sys.stdin.read())
