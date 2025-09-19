from typing import List
from .node import Node

class RootNode(Node):
	@staticmethod
	def promote(node: Node):
		if not isinstance(node, Node):
			raise TypeError("RootNode promotion expected Node but received " + str(type(node)))
		return RootNode(node._contentLine, node._childHeaderLine, node._colWidths, node._children, node.parent, node.depth, node.colSummary)
