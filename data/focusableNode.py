from .node import Node
from ..drawing import Line

class FocusableNode(Node):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.isFocused = False
		self.focusedIdx = 0

	def click(self):
		# If i'm collapsed, dont allow clicks on the last possible focusedIdx
		if self.isCollapsed and self.focusedIdx == len(self.contentLine)-1:
			return
		super().click()


	@property
	def contentDecorators(self):
		dec = [Line.NORMAL for c in range(len(self.contentLine))]
		if self.isFocused and self.focusedIdx < len(dec):
			dec[self.focusedIdx] = Line.FOCUSED
		return dec


	def focusUp(self, sourceNode = None):
		# If this is the root (no parent) focus up means nothing, don't let it happen
		if self.parent is None:
			return sourceNode

		sourceNode = self if sourceNode is None else sourceNode

		childIdx = self.parent.children.index(self)
		# If I am the first child in my parent, let my parent focus up (recursive case)
		if childIdx <= 0:
			return self.parent.focusUp(sourceNode)

		# Otherwise, focus on the previous child in the parent (base case)
		depth = sourceNode.focusOut()
		return self.parent.children[childIdx-1].focusIn(depth, -1)


	def focusDown(self, sourceNode = None):
		# If this is the root (no parent) focus down means nothing, don't let it happen
		if self.parent is None:
			return sourceNode

		sourceNode = self if sourceNode is None else sourceNode

		childIdx = self.parent.children.index(self)
		# If I am the last child in my parent, let my parent focus down (recursive case)
		if childIdx+1 >= len(self.parent.children):
			return self.parent.focusDown(sourceNode)

		# Otherwise, focus on the next child in the parent (base case)
		depth = sourceNode.focusOut()
		return self.parent.children[childIdx+1].focusIn(depth, 0)


	def focusLeft(self):
		if self.focusedIdx-1 >= 0:
			self.focusedIdx -= 1
			return self

		# If i have a grandparent, focus on my parent (to avoid focusing on the root)
		if self.parent is not None and self.parent.parent is not None:
			self.focusOut()
			return self.parent.focusIn()
		return self


	def focusRight(self):
		# Attempt to focus on the next content cell
		if self.focusedIdx+1 < len(self.contentLine):
			self.focusedIdx += 1
			return self

		# If im not collapsed and have children, focus on the first one
		if not self.isCollapsed and len(self.children) > 0:
			self.focusOut()
			return self.children[0].focusIn()

		return self


	def focusIn(self, depth = -1, idx = 0):
		# If the goal depth is deeper than the current node and this node is not collapsed, attempt to focus deeper
		if depth > self.depth and not self.isCollapsed and len(self.children) > 0:
			return self.children[idx].focusIn(depth, idx)
		# Otherwise focus on me and attempt to send remaining depth into focusedIdx
		self.isFocused = True
		self.focusedIdx = max(0, min(depth - self.depth, len(self.contentLine)-1))
		return self


	def focusOut(self):
		self.isFocused = False
		return self.depth + self.focusedIdx


	def __str__(self):
		if self.focusedIdx < len(self.statusLine):
			return str(self.statusLine[self.focusedIdx])
		return ''
