"""Construct a structured HTML tree from raw HTML text, 
Remove tag nodes with specific name or specific attributes."""
import re
from queue import LifoQueue
from html.parser import HTMLParser


class HTMLTreeParser(HTMLParser):
    """Find nodes (tags or data) from an HTML text and transform into a list of 
    node contents (tag names or data) content and a list of node types (start 
    tag, end tag, data, etc).

    Attributes
    ----------
    members : list of str
        The list of node contents, for a tag node, its tag name is stored, while for a data node, the data is stored.
    types : list of str
        The list of node types, like `starttag`, `endtag`, `data`.
    """
    members = []
    types = []

    def __init__(self):
        HTMLParser.__init__(self)
        self.members = []
        self.types = []

    def handle_starttag(self, tag, attrs):
        """Handler function of start tag node, append (tagname, attrs) to self.members and 'starttag' to self.types.
        """
        self.members.append((tag, attrs))
        self.types.append('starttag')

    def handle_endtag(self, tag):
        """Handler function of end tag node, append tagname to self.members and 'endtag' to self.types.
        """
        self.members.append(tag)
        self.types.append('endtag')

    def handle_data(self, data):
        """Handler function of data node, append data content to self.members and 'data' to self.types.
        """
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


class HTMLNode(object):
    """Nodes of HTML tree, super class of TagNode and DataNode.

    Attributes
    ----------
    tag : str
        The tag name of a tag node, or 'data' for a data node.
    level : int, default 0
        The level of node in HTML tree. The root node has level 0.
    closed : boolean, default False
        A tag node is closed when it has an correspondent end tag. A data node is always closed (always True).
    """

    def __init__(self, tag, level=0):
        self.tag = tag
        self.level = level
        self.closed = False


class TagNode(HTMLNode):
    """Tag node of HTML tree, inherited from HTMLNode class.

    Attributes
    ----------
    tag : str
        The tag name of the node.
    attrs : dict
        The dict of attributes and their values of the node.
    level : int, default 0
        The level of node in HTML tree. The root node has level 0.
    children : list of HTMLNode objects
        The tag nodes and data nodes under the node.
    closed : boolean, default False
        A tag node is closed when it has an correspondent end tag.
    """

    def __init__(self, tag, attrs=dict(), level=0):
        super().__init__(tag, level)
        self.attrs = {attr: set(attr_v.split()) for attr, attr_v in attrs}
        self.children = []

    def add_child(self, new_child):
        """Add a child node. Append the new child node to self.children.
        """
        self.children.append(new_child)

    def self_close(self):
        """Close the node with brute force for some self-closed tags.
        """
        self.closed = True

    def close(self, closing_tag):
        """Close the node if correspondent end tag found. If end tag doesn't match, raise an exception.
        """
        if closing_tag == self.tag:
            self.closed = True
        else:
            raise Exception("Closing tag doesn't match starting tag.")

    def clean(self,
              tags_delete=['script', 'noscript', 'style', 'aside',
                           'header', 'footer', 'nav', 'navigation'],
              attrs_delete=['menu', 'head', 'header', 'footer', 'foot', 'nav', 'navigation']):
        """Clean the node and its children nodes recursively if it's tag is to be deleted, or if it has an attribute value to be deleted.
        """
        if self.tag in tags_delete:
            return None
        elif self.attrs.get('id', set()) | self.attrs.get('class', set()) & set(attrs_delete):
            return None
        self.children = [c.clean(tags_delete, attrs_delete)
                         for c in self.children]
        self.children = [c for c in self.children if c]
        return self

    def pure_text(self):
        """Get pure text content of the node, including the pure text of its children nodes.
        """
        s = ' '.join([c.pure_text() for c in self.children])
        return s

    def __str__(self):
        s = '\t'*self.level + "<" + self.tag + "> : "
        s += ' | '.join([attr+' = "'+' '.join(attr_v) +
                         '"' for attr, attr_v in self.attrs.items()])
        if self.children:
            for c in self.children:
                s += '\n' + str(c)
        return s


class DataNode(HTMLNode):
    """Data node of HTML tree, inherited from HTMLNode class.

    Attributes
    ----------
    tag : str
        The tag name of data node, always `data`.
    level : int, default 0
        The level of node in HTML tree. The root node has level 0.
    data : str
        The text data of the data node.
    closed : boolean, default True
        A data node is always closed (always True).
    """

    def __init__(self, data, level=0):
        super().__init__('data', level)
        self.data = data
        self.closed = True

    def clean(self, *args):
        """A data node is always clean, return self without doing anything.
        """
        return self

    def pure_text(self):
        """A data node's data is pure text.
        """
        return self.data

    def __str__(self):
        s = '\t'*self.level + "<" + self.tag + "> : " + self.data
        return s


class HTMLTree(object):
    """HTML tree stucture.

    Attributes
    ----------
    root : HTMLNode object
        The root node of the tree.
    pointer : HTMLNode object
        The node which is currently under operation.
    path : LifoQueue
        The path of nodes under operation, a node in the path is always the child node of the node at its previous position in the queue.
    """

    def __init__(self):
        self.root = TagNode('root')
        self.path = LifoQueue()
        self.pointer = self.root

    def add_node(self, node):
        """Add a tag node to the tree.
        """
        # the added tag node's level increments by 1
        node.level = self.pointer.level + 1
        self.pointer.add_child(node)
        # add the new tag node to the path
        self.path.put(self.pointer)
        # move the pointer to the newly added node
        self.pointer = self.pointer.children[-1]

    def add_data(self, data_node):
        """Add a data node to the tree.
        """
        # the added data node's level increments by 1
        data_node.level = self.pointer.level + 1
        self.pointer.add_child(data_node)
        # no need to put data node to the path, nor move the pointer downward

    def close_node(self, closing_tag):
        """Close the node currently under operation if the end tag matches.
        Parameters
        ----------
        closing_tag : str
            The name of the end tag.
        """
        if self.pointer.closed:
            raise Exception("More closing tags than starting tags.")
        self.pointer.close(closing_tag)
        self.pointer = self.path.get()

    def self_close(self):
        """Close the node with brute force for some self-closed tags.
        """
        if self.pointer.closed:
            raise Exception("More closing tags than starting tags.")
        self.pointer.self_close()
        if self.pointer.tag == 'root':
            return
        if self.path.empty():
            raise Exception("More closing tags than starting tags.")
        self.pointer = self.path.get()

    def clean(self,
              tags_delete=['script', 'noscript', 'style', 'aside',
                           'header', 'footer', 'nav', 'navigation'],
              attrs_delete=['menu', 'head', 'header', 'footer', 'foot', 'nav', 'navigation']):
        """Clean the tree by removing nodes with tag to be deleted, or with an attribute value to be deleted.
        """
        self.root.clean(tags_delete, attrs_delete)
        # TODO: remove the root node and upgrade its only child when the root node has only one child
        # if len(self.root.children) == 1:
        #     self.root = self.root.children[0]

    def check_sanity(self):
        """Check if a tree is totally closed. If not, some end tags are missed.
        """
        if not self.root.closed:
            raise Exception("Tree root node not closed.")

    def pure_text(self):
        """Get the pure text of the tree.
        """
        text = self.root.pure_text()
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def __str__(self):
        return str(self.root)

    @staticmethod
    def html_to_tree(html_text):
        """Transform a raw HTML text to a tree.

        Paramters
        ---------
        html_text : str
            The HTML text to be transformed.

        Returns
        -------
        HTMLTree object : The HTML tree built from the HTML text.
        """
        SELF_CLOSING_TAGS = ['img', 'area', 'base', 'br', 'col', 'command', 'embed',
                             'hr', 'input', 'keygen', 'link', 'menuitem', 'meta', 'param', 'source', 'wbr']
        parser = HTMLTreeParser()
        html_text = re.sub(r'< +', '<', html_text)
        html_text = re.sub(r'\\/', '/', html_text)
        html_text = re.sub(r'\\"', '/', html_text)
        parser.feed(html_text)
        parser.close()
        tree = HTMLTree()
        for t, p in zip(parser.types, parser.members):
            if t == 'starttag':
                new_node = TagNode(p[0], attrs=p[1])
                tree.add_node(new_node)
                if p[0] in SELF_CLOSING_TAGS:
                    tree.self_close()
            if t == 'data':
                data_node = DataNode(data=p)
                tree.add_data(data_node)
            if t == 'endtag':
                if p not in SELF_CLOSING_TAGS:
                    tree.close_node(p)
        tree.self_close()
        tree.check_sanity()
        return tree


def unit_test():
    t = "<div>This is a test text.</div>"
    print('-'*10+"Original HTML text:"+'-'*10+'\n', t)
    tree = HTMLTree.html_to_tree(t)
    print('-'*10+"Tree structure:"+'-'*10+'\n', tree)
    tree.clean()
    print('-'*10+"Pure text:"+'-'*10+'\n', tree.pure_text())
    print()
    t = "<div id = \"menu head\" class = \"menu\">\n<div>in header<\/div>\t<\/div><div>\ntext1<div>text2<\/div><footer>footer text<\/footer>text3<\/div>"
    print('-'*10+"Original HTML text:"+'-'*10+'\n', t)
    tree = HTMLTree.html_to_tree(t)
    print('-'*10+"Tree structure:"+'-'*10+'\n', tree)
    tree.clean()
    print('-'*10+"Pure text:"+'-'*10+'\n', tree.pure_text())


if __name__ == '__main__':
    unit_test()
