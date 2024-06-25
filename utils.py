def find(i: iter, default=None):
	try:
		return next(i)
	except StopIteration:
		return default
