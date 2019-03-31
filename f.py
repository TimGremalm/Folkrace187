#IP 192.168.0.134

print('Hello')


def reload():
	import sys
	del sys.modules['f']
	import f
