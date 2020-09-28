class MExceptions(Exception):
	pass

class SIGN_TOO_EARLY(MExceptions):
	def __init__(self, message='sign too early'):
		self.message = message
		self.ecode = 30101