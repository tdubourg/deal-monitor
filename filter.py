from json import dumps

def toJSON(o):
	return dumps(o.data)

FILTER_FIELD_LIST = [
	("min_price", int)
	, ("max_price", int)
	, ("min_price_for_alert", int)
	, ("max_price_for_alert", int)
	, ("alert_enabled", None)
]
def fromJSON(data):
	for field in FILTER_FIELD_LIST:
		try:
			if field[1] is not None:
				data[field[0]] = field[1](data[field[0]])
			else:
				data[field[0]] = data[field[0]]
		except KeyError:
			data[field[0]] = None
	return Filter(data)

class Filter(object):
	"""docstring for Filter"""
	def __init__(self, data):
		super(Filter, self).__init__()
		self.data = data
	
	def satisfies(self, item):
		if ((self.data["min_price"] is None or item["price"] >= self.data["min_price"]) and
			(self.data["max_price"] is None or item["price"] <= self.data["max_price"])):
			return True
		return False

	def __repr__(self):
		return "(min=%s, max=%s, min_al=%s, max_al=%s)" % (
			self.data["min_price"],
			self.data["max_price"],
			self.data["min_price_for_alert"],
			self.data["max_price_for_alert"]
		)

	def satisfies_alert(self, item):
		if self.data["alert_enabled"] is not True:
			return False

		if not self.satisfies(item):
			return False

		if ((self.data["min_price_for_alert"] is None or item["price"] >= self.data["min_price_for_alert"]) and
			(self.data["max_price_for_alert"] is None or item["price"] <= self.data["max_price_for_alert"])):
			return True
		return False
