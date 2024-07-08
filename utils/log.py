import adafruit_logging as logging
from gc import collect, mem_free
log = logging.getLogger()

def log_exception(e: any):
	if isinstance(e, Exception):
		from traceback import print_exception
		print_exception(e)
		log.error(e)

def log_memory_usage(label: str):
	collect()
	log.debug(f'--> Free memory: {mem_free():,} @ {label}')