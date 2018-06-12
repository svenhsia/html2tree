# -*- coding: utf-8 -*-
# author: Shiwen XIA
# date: 2018/06/12
"""Construct a the tree structure from a raw HTML text.
"""
from queue import LifoQueue
from html.parser import HTMLParser
from html.entities import name2codepoint
from pprint import pprint
import re


class MyHTMLParser(HTMLParser):
    members = []
    types = []

    def __init__(self):
        HTMLParser.__init__(self)
        self.members = []
        self.types = []

    def reset(self):
        HTMLParser.reset(self)
        self.members = []
        self.types = []

    def handle_starttag(self, tag, attrs):
        self.members.append((tag, attrs))
        self.types.append('starttag')

    def handle_endtag(self, tag):
        self.members.append(tag)
        self.types.append('endtag')

    def handle_data(self, data):
        data_stripped = data.strip()
        if data_stripped:
            self.members.append(data_stripped)
            self.types.append('data')

    def handle_comment(self, data):
        # print("Comment  :", data)
        pass

    def handle_entityref(self, name):
        # c = chr(name2codepoint[name])
        # print("Named ent:", c)
        pass

    def handle_charref(self, name):
        # if name.startswith('x'):
        #     c = chr(int(name[1:], 16))
        # else:
        #     c = chr(int(name))
        # print("Num ent  :", c)
        pass

    def handle_decl(self, data):
        # print("Decl     :", data)
        pass


class Node(object):

    def __init__(self, tag, attrs=[], level=0):
        self.tag = tag
        self.attrs = attrs
        self.data = ''
        self.children = []
        self.closed = False
        self.level = level

    def add_data(self, new_data):
        self.data += ' ' + new_data

    def add_child(self, new_child):
        self.children.append(new_child)

    def self_close(self):
        self.closed = True

    def close(self, closing_tag):
        if closing_tag == self.tag:
            self.closed = True
        else:
            raise Exception("Closing tag doesn't match starting tag.")

    def clean(self):
        self.children = [c for c in self.children if c]
        for c in self.children:
            c.clean

    def get_pure_text(self):
        s = ' '.join([self.data]+[c.get_pure_text() for c in self.children])
        return s

    def __str__(self):
        s = '\t'*self.level + self.tag + ' : ' + self.data
        # s += ' '.join([str(tup) for tup in self.attrs])
        if self.children:
            for c in self.children:
                s += '\n' + str(c)
        return s


class Tree(object):

    def __init__(self):
        self.root = Node('root')
        self.path = LifoQueue()
        self.pointer = self.root

    def add_node(self, node):
        node.level = self.pointer.level + 1
        self.pointer.add_child(node)
        self.path.put(self.pointer)
        self.pointer = self.pointer.children[-1]

    def add_data(self, data):
        self.pointer.add_data(data)

    def close_node(self, closing_tag):
        if self.pointer.closed:
            raise Exception("More closing tags than starting tags.")
        self.pointer.close(closing_tag)
        self.pointer = self.path.get()

    def self_close(self):
        if self.pointer.closed:
            raise Exception("More closing tags than starting tags.")
        self.pointer.self_close()
        if self.pointer.tag == 'root':
            return
        if self.path.empty():
            raise Exception("More closing tags than starting tags.")
        self.pointer = self.path.get()

    def clean_tree(self):
        self.root.clean()

    def check_sanity(self):
        if not self.root.closed:
            raise Exception("Tree root node not closed.")

    def get_pure_text(self):
        text = self.root.get_pure_text()
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def __str__(self):
        return str(self.root)


def html_to_tree(html_text):
    SELF_CLOSING_TAGS = ['img', 'area', 'base', 'br', 'col', 'command', 'embed',
                         'hr', 'input', 'keygen', 'link', 'menuitem', 'meta', 'param', 'source', 'wbr']
    parser = MyHTMLParser()
    parser.feed(html_text)
    parser.close()
    tree = Tree()
    for t, p in zip(parser.types, parser.members):
        if t == 'starttag':
            new_node = Node(p[0], p[1])
            tree.add_node(new_node)
            if p[0] in SELF_CLOSING_TAGS:
                tree.self_close()
        if t == 'data':
            tree.add_data(p)
        if t == 'endtag':
            if p not in SELF_CLOSING_TAGS:
                tree.close_node(p)
    tree.self_close()
    tree.check_sanity()
    return tree


def deep_cleaning(node):
    if node.tag in ['script', 'noscript', 'style', 'aside', 'header', 'footer', 'nav', 'navigation']:
        return None
    elif set(['menu', 'head', 'header', 'footer', 'foot', 'social', 'sub-social']) & set([t for tup in node.attrs for t in tup[1].split()]):
        return None
    else:
        kept_children = []
        for c in node.children:
            new_c = deep_cleaning(c)
            if new_c:
                kept_children.append(new_c)
        node.children = kept_children
    return node
