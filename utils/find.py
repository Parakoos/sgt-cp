def find_thing(i: iter[any], default: any) -> any:
	try:
		return next(i)
	except StopIteration:
		return default

def find_int(i: iter[int], default: int) -> int:
	try:
		return next(i)
	except StopIteration:
		return default

def find_string(i: iter[str], default: str = None) -> str|None:
	try:
		return next(i)
	except StopIteration:
		return default

def find_color(i: iter[tuple[int, int, int]], default: tuple[int, int, int]) -> tuple[int, int, int]:
	try:
		return next(i)
	except StopIteration:
		return default
