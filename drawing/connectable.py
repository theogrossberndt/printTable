# Connectable defines the required methods for an object that can connect to an hline
# This provides the necessary methods for getting top and bottom column definitions, and what is and is not content
class Connectable:
	def getTopColWidths(self):
		pass

	def getTopContentLen(self):
		pass

	def getBottomColWidths(self):
		pass

	def getBottomContentLen(self):
		pass
