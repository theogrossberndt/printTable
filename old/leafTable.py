from .chars import Chars
from .printableLines import StaticLines
import pandas as pd

class LeafTable:
	# Left col widths also includes the first column of the df for prettier printing with the other rows
	def __init__(self, df, leftColWidths, countableCols, hiddenCols, screenWidth):
		self.df = df.astype(str)[df.notna()]

		self.colWidths = [*leftColWidths]
		for col in self.df.columns[1:]:
			self.colWidths.append(int(max(len(col), self.df[col].str.len().max())))

		for col in self.df.columns:
			if col in hiddenCols:
				self.df.drop(columns=col, inplace=True)
			elif col in countableCols:
				self.df[col] = pd.to_numeric(self.df[col], downcast='integer')

		cleanCols = Chars.colNameCleanup(self.df.columns)
		self.df.rename(columns = {self.df.columns[c]: cleanCols[c] for c in range(len(cleanCols))}, inplace = True)
		self.screenWidth = screenWidth

	# Returns a static lines object representing the whole table
	def buildLines(self, firstLineModifier = None, modDecorator = None, headerDecorator = None, addHeader = True):
		# The first column is always drawn by the parent
		effCols = [*self.df.columns]
		effCols[0] = ''

		effHeaderDecorator = headerDecorator if headerDecorator is not None else Chars.headerDecorator

		# If we have a first line modifier, that should be prepended to the header
		effHeader = effCols if firstLineModifier is None else [firstLineModifier, *effCols]

		# This element should have the supplied decorator, so we have to use elementwise decorators for the header
		headerDecorators = [modDecorator, *[effHeaderDecorator for _ in effCols]] if firstLineModifier is not None else effHeaderDecorator

		if addHeader:
			headerLine = StaticLines(effHeader, self.colWidths, self.screenWidth, decorator = headerDecorators)
		else:
			headerLine = None

		tableLines = self.df.apply(lambda row: StaticLines(row, self.colWidths, self.screenWidth), axis=1)

		for line in tableLines:
			if headerLine is not None:
				headerLine.extend(line)
			else:
				headerLine = line

		return headerLine
