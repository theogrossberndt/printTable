from .chars import Chars

from .printableLines import HLine, StaticLines
from .expandableNode import ExpandableNode

class RootNode(ExpandableNode):
	def __init__(self, df, screenWidth):
		super().__init__('root', df, [], screenWidth, None)
		self.expanded = True
		self.lines = self.buildLines()


	def render(self):
		# TODO Figure this out better
		# Chop off 2 lines to get rid of the root output
		rendered = self.lines.render()[2:]

		# Add the bottom line by traversing rendered backwards until we find the last static line
		# Use the colWidths of this static line as the colcount for the last hline (full width)
		c = len(rendered)-1
		while c >= 0:
			if isinstance(rendered[c][0], StaticLines):
				rendered = rendered[:c+1]
				rendered.append((HLine(len(rendered[c][0].bottomColWidths), self.screenWidth), None))
				break
			c -= 1

		pendingHLine = None
		outputs = []
		for c in range(len(rendered)):
			if isinstance(rendered[c][0], HLine):
				# HLines absorb the bottom of the static line before and the top of the next static line
				# Set this hline to pending to be consolidated when we see the next static line (to remove duplicates)
				if pendingHLine is not None:
					pendingHLine.extend(rendered[c][0])
				else:
					pendingHLine = rendered[c][0].copy()
				continue
			elif not isinstance(rendered[c][0], StaticLines):
				continue

			# Otherwise, we have a static line. Add it to the outputs
			thisEl = rendered[c][0].copy()
#			thisEl = rendered[c]

			# First, if we have a pending hline it can be consolidated, then added to the outputs
			if pendingHLine is not None:
				pendingHLine.consolidate(outputs[-1][0] if len(outputs) > 0 else None, thisEl)
				outputs.append((pendingHLine, None))
				pendingHLine = None

			outputs.append((thisEl, rendered[c][1]))

		if pendingHLine is not None:
			pendingHLine.consolidate(outputs[-1][0] if len(outputs) > 0 else None, None)
			outputs.append((pendingHLine, None))

		# Each output element is an h line (one curses object), or a static lines object (list of curses objects)
		curses = []
		for output, node in outputs:
			if isinstance(output, HLine):
				curses.append((output.cursesRep, node))
			elif isinstance(output, StaticLines):
				for cursesRep in output.cursesReps:
					curses.append((cursesRep, node))

		return curses


	def getExpandables(self):
		return super().getExpandables()[1:]
