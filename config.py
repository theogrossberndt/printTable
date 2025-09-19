import pandas as pd
from typing import Set

class Config:
	def __init__(self, countableCols: Set[str], hiddenCols: Set[str], summarize = None, colNameCleanup = None):
		self.countableCols = countableCols
		self.hiddenCols = hiddenCols
		self.sumFunc = summarize if summarize is not None else Config.defaultSummary
		self.colNameCleanupFunc = colNameCleanup if colNameCleanup is not None else Config.defaultColCleanup


	def summarize(self, df: pd.DataFrame, colName: str, long: bool = False):
		return self.sumFunc(self, df, colName, long)


	@staticmethod
	def defaultSummary(self, df: pd.DataFrame, colName: str, long: bool):
		sums = []
		summary = 0
		for col in df.columns:
			if col in self.countableCols:
				sum = pd.to_numeric(df[col].fillna(0), downcast='integer').sum()
				summary += sum
				sums.append(self.colNameCleanup(col) + ': ' + str(sum))
		if not long:
			return 'Total: ' + str(summary)
		else:
			return ', '.join(sums)


	def colNameCleanup(self, v):
		return self.colNameCleanupFunc(self, v)

	@staticmethod
	def defaultColCleanup(self, v):
		if isinstance(v, str):
			subIdx = v.find('_')
			if subIdx > 0:
				return v[subIdx+1:]
			return v

		return [self.colNameCleanup(val) for val in v]
