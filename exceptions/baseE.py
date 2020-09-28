

class fenluE(BaseException):

	def __init__(self, module, *args, **kwargs):
		self.mod = module
		super(fenluE, self).__init__(*args, **kwargs)
