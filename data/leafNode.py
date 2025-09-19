from .node import Node
from .mergableNode import MergableNode
from .focusableNode import FocusableNode
from typing import Union

class ILeafNode:
	pass

class LeafNode(MergableNode):
	def __init__(self, derivedNode: Node, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.derivedNode = derivedNode

	@staticmethod
	def isLeaf(node: Node) -> bool:
		firstChild = None
		for child in node.children:
			# More than one child is a collapsible node
			if firstChild is not None:
				return False
			firstChild = child
		# No children is definitely a leaf
		if firstChild is None:
			return True
		# Otherwise, traverse down to make sure all desendants are also leaves
		return LeafNode.isLeaf(firstChild)


	@staticmethod
	def promote(node: Node) -> ILeafNode:
		if not isinstance(node, Node):
			raise TypeError("LeafNode promotion expected Node but received " + str(type(node)))

		# Use all private accessors for building the node EXCEPT for children (hidden children stay hidden)
		headerLine = []
		contentLine: List[str] = []

		deepestChild = node
		while len(deepestChild.children) > 0:
			headerLine.extend(deepestChild._childHeaderLine)
			contentLine.extend(deepestChild._contentLine)
			deepestChild = deepestChild.children[0]

		headerLine.extend(deepestChild._childHeaderLine)
		contentLine.extend(deepestChild._contentLine)

		return LeafNode(node, contentLine, headerLine, deepestChild._colWidths, [], node.parent, node.depth)


	def __eq__(self, other):
		if isinstance(other, LeafNode):
			return self.derivedNode == other.derivedNode
		return self.derivedNode == other
