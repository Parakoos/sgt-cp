
from os import getenv

class SettingInvalidError(Exception):
    def __init__(self, key: str):
        super().__init__(f"Setting not formatted OK. Settings must be integers or strings wrapped in \"double quotes\": {key}")

class SettingMissingError(Exception):
    def __init__(self, key: str):
        super().__init__(f"Mandatory setting missing: {key}")

class SettingTypeError(Exception):
    def __init__(self, key: str, type: str):
        super().__init__(f"Failed to convert the setting to {type}: {key}")

def get_setting(key: str, default: None|str|int = None) -> str|int:
	try:
		val = getenv(key)
		if val != None:
			return val
		elif default != None:
			return default
		else:
			raise SettingMissingError(key)
	except ValueError as e:
		raise SettingInvalidError(key) from e
	except SettingMissingError as e:
		raise e
	except Exception as e:
		raise SettingMissingError(key) from e

def get_string(key: str, default: None|str = None) -> str:
	val = get_setting(key, default)
	try:
		return str(val)
	except Exception as e:
		raise SettingTypeError(key, 'string') from e

def get_int(key: str, default: None|int = None) -> int:
	val = get_setting(key, default)
	try:
		return int(val)
	except Exception as e:
		raise SettingTypeError(key, 'integer') from e

def get_float(key: str, default: None|float = None) -> float:
	val = get_setting(key, default)
	try:
		return float(val)
	except Exception as e:
		raise SettingTypeError(key, 'float') from e
