import os

from .rootNode import RootNode

class DataModel:
	def __init__(self, df, countableCols, hiddenCols, screenWidth):
		self.df = df

		self.root = RootNode(self.df, countableCols, hiddenCols, screenWidth)
		expandables = self.root.getExpandables()
		self.focused = expandables[0] if len(expandables) > 0 else None
		if self.focused is not None:
			self.focused.isFocused = True


	def click(self):
		if self.focused is None:
			return
		self.focused.expanded = not self.focused.expanded


	def focusNext(self, direction):
		if self.focused is None:
			return None

		expandables = self.root.getExpandables()

		# Focus should be properly managed to never hold a reference to an unfocusable node
		# If that is the case, the while loop will only ever run once
		# However, if it does happen go up the tree from self.focused until we find a parent that is still focusable, and use that as the focus idx
		focus = self.focused
		focusIdx = -1
		while focus is not None and focusIdx < 0:
			try:
				focusIdx = expandables.index(focus)
			except ValueError:
				pass
			focus = focus.parent

		# If focusIdx is still -1 here, we have big problems
		if focusIdx < 0:
			print("This is bad")
			focusIdx = 0

		# Otherwise, unfocus the old element and focus the next element (with wrapping)
		self.focused.isFocused = False
		self.focused = expandables[(focusIdx + direction + len(expandables)) % len(expandables)]
		self.focused.isFocused = True
		return self.focused


	def render(self):
		return self.root.render()
