from json import dumps

def toJSON(o):
	return dumps(o.data)

def fromJSON(data):
	try:
		data["min_price"] = int(data["min_price"])
	except KeyError:
		data["min_price"] = None

	try:
		data["max_price"] = int(data["max_price"])
	except KeyError:
		data["max_price"] = None
	
	try:
		data["min_price_for_alert"] = int(data["min_price_for_alert"])
	except KeyError:
		data["min_price_for_alert"] = None
	
	try:
		data["max_price_for_alert"] = int(data["max_price_for_alert"])
	except KeyError:
		data["max_price_for_alert"] = None

	try:
		data["alert_enabled"] = data["alert_enabled"]
	except KeyError:
		data["alert_enabled"] = None
	
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
