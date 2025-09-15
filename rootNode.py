import pandas as pd
from .node import Node
from .lineBuilder import LineBuilder
from .hline import HLine
from .config import Config

class RootNode(Node):
	def __init__(self, config: Config):
		super().__init__(config, 'root', [], 1, None)

		self.isExpanded = True
		self.focusedNode = self.children[0]
		self.focusedIdx = 0

		self._leafifyChildren()

	# This should only be called if the first child recursively calls it without knowing
	# In that case, return the top node
	def focusUp(self):
		return self.children[0]

	# Same thing as focus up, but with the bottom child
	# Return it
	def focusDown(self):
		return self.children[-1]


	def render(self):
		inLines = super().render()
#		return inLines

		# Merge neighboring hlines
		lines = []
		pendingHLine = None
		for line in inLines:
			if isinstance(line, HLine):
				if pendingHLine is None:
					pendingHLine = line
				else:
					pendingHLine = pendingHLine.merge(line)
			elif isinstance(line, LineBuilder):
				if pendingHLine is not None:
					lines.append(pendingHLine)
					pendingHLine = None
				lines.append(line)

		if pendingHLine is not None:
			lines.append(pendingHLine)

		return lines

	# Root node focus is special, because the focused idx cannot be 0
	def handleKey(self, keyCode):
		# Otherwise, left/right means focusing on the parent/child of the focused node
		if keyCode == Node.FOCUS_LEFT:
			if self.focusedNode.parent is not None and self.focusedNode.parent.depth > 1:
				self.focusedNode = self.focusedNode.parent
				self.focusedIdx -= 1
		if keyCode == Node.FOCUS_RIGHT:
			if len(self.focusedNode.children) > 0:
				self.focusedNode = self.focusedNode.children[0]
				self.focusedIdx += 1

		# If we have clicked and the focusedNode can collapse, flip its expansion
		if keyCode == Node.CLICK and self.focusedNode.canCollapse:
			self.focusedNode.isExpanded = not self.focusedNode.isExpanded
