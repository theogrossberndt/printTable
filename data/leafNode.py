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
		if not isinstance(node, FocusableNode):
			raise TypeError("LeafNode promotion expected FocusableNode but received " + str(type(node)))

		# Use all private accessors for building the node EXCEPT for children (hidden children stay hidden)
		headerLine = []
		contentLine: List[str] = []

		deepestChild = node
		focusedIdx = 0
		isFocused = False
		while len(deepestChild.children) > 0:
			if deepestChild.isFocused:
				isFocused = True
			headerLine.extend(deepestChild._childHeaderLine)
			contentLine.extend(deepestChild._contentLine)
			deepestChild = deepestChild.children[0]
			if not isFocused:
				focusedIdx += 1

		headerLine.extend(deepestChild._childHeaderLine)
		contentLine.extend(deepestChild._contentLine)

		leaf = LeafNode(node, contentLine, headerLine, deepestChild._colWidths, [], node.parent, node.depth, isFocused = isFocused, focusedIdx = focusedIdx)
		# Somewhat hacky way of adding hide functionality to a leaf node
		# Could be fixed by extracting hide into its own subclass of node, but why bother tbh
		leaf.hide = node.hide
		leaf.isHidden = node.isHidden
		return leaf


	# Saves everything back to the derived node
	# The derived node should be a ChildCondensingNode, so copy every variable that has
	def saveState(self):
#		self.derivedNode.isHidden = self.isHidden
		# For focus, we have to iterate through children to focus the proper node, unless I'm not focused at all
		if not self.isFocused:
			self.derivedNode.isFocused = self.isFocused
			self.derivedNode.focusedIdx = 0
		else:
			focusedIdx = self.focusedIdx
			child = self.derivedNode
			while focusedIdx > 0:
				if len(child.children) == 0:
					break
				child = child.children[0]
				focusedIdx -= 1
			child.isFocused = True
			child.focusedIdx = focusedIdx


	def __eq__(self, other):
		if isinstance(other, LeafNode):
			return self.derivedNode == other.derivedNode
		return self.derivedNode == other
