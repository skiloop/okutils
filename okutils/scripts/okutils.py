#!/bin/env python
# -*- coding:utf8 -*-

import argparse
import asyncio
from okutils.sdm import Reader,AsyncReader

async def async_list_docs(args):
    """
    list documents in bin file
    """
    async with AsyncReader(args.file) as reader:
        i = 1
        await reader.fd.seek(args.offset)
        while True:
            pos = await reader.fd.tell()
            key, value = await reader.readone(key_only=args.key_only, pattern=args.pattern)
            if key is None:
                break
            key = key.decode()
            if args.key_only:
                print(f"[{i:10d}]{pos:10d}\t{key:20s}")
            else:
                try:
                    value = value.decode()
                except UnicodeDecodeError:
                    pass
                print(f"[{i:10d}]{pos:10d}\t{key:20s}\t{value[:30]}... {len(value)}")
            if args.limit > 0 and i >= args.limit:
                break
            i += 1

def read_doc(args):
    """
    read document at specified position
    """
    reader = Reader(args.file)
    key, value = reader.readone_at(args.pos)
    print(key, value)

def list_docs(args):
    """
    list documents in bin file
    """
    if args.async_mode:
        asyncio.run(async_list_docs(args))
        return
    reader = Reader(args.file)
    i = 1
    reader.fd.seek(args.offset)
    while True:
        pos = reader.fd.tell()
        key, value = reader.readone(key_only=args.key_only, pattern=args.pattern)
        if key is None:
            break
        key = key.decode()
        if args.key_only:
            print(f"[{i:10d}]{pos:10d}\t{key:20s}")
        else:
            try:
                value = value.decode()
            except UnicodeDecodeError:
                pass
            print(f"[{i:10d}]{pos:10d}\t{key:20s}\t{value[:30]}... {len(value)}")
        if args.limit > 0 and i >= args.limit:
            break
        i += 1


def main():
    """
    okutils command line tool for bin-file
    """
    parser = argparse.ArgumentParser(description='okutils')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    parser.add_argument('--verbose', action='store_true', help='verbose output')
    parser.add_argument('-a','--async-mode', action='store_true', help='use async mode')
    subparsers = parser.add_subparsers(help="sub-command help")
    list_docs_cmd = subparsers.add_parser('list',aliases=['l'], help='list documents')
    list_docs_cmd.add_argument('file', help='bin file to list')
    list_docs_cmd.add_argument('-k','--key-only', action='store_true', help='list keys only')
    list_docs_cmd.add_argument('-o','--offset', type=int, default=0, help='offset to start list')
    list_docs_cmd.add_argument('-l','--limit', type=int, default=0, help='limit the number of documents to list')
    list_docs_cmd.add_argument('-p','--pattern', type=str, default=None, help='pattern to match key')
    list_docs_cmd.set_defaults(func=list_docs)
    read_doc_cmd = subparsers.add_parser('read',aliases=['r'], help='read document')
    read_doc_cmd.add_argument('file', help='bin file to read')
    read_doc_cmd.add_argument('pos', type=int, help='position of document to read')
    read_doc_cmd.set_defaults(func=read_doc)
    _args = parser.parse_args()
    if _args.verbose:
        Reader.VERBOSE = True
    _args.func(_args)


if __name__ == '__main__':
    main()