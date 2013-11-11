from json import dumps

def toJSON(o):
	return dumps(o.data)

FILTER_FIELD_LIST = [
	# , ("field_name", function_to_be_applied_on_unserialize)
	("min_price", int)
	, ("max_price", int)
	, ("min_price_for_alert", int)
	, ("max_price_for_alert", int)
	, ("alert_enabled", None)
	, ("auto_contact_sms", None)
	, ("auto_contact_email", None)
	, ("auto_contact_sms_template", None)
	, ("auto_contact_mail_template", None)
	, ("sms_device_name", None)
	, ("mail_auto_contact_from_email", None)
	, ("mail_auto_contact_from_name", None)
	, ("mail_auto_contact_from_phone", None)
	, ("name", None)
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
		self.name = data["name"]
	
	def satisfies(self, item):
		if ((self.data["min_price"] is None or item["price"] >= self.data["min_price"]) and
			(self.data["max_price"] is None or item["price"] <= self.data["max_price"])):
			return True
		return False

	def __repr__(self):
		return "Filter(" + self.name + ")"

	def satisfies_alert(self, item):
		if self.data["alert_enabled"] is not True:
			return False

		if not self.satisfies(item):
			return False

		if ((self.data["min_price_for_alert"] is None or item["price"] >= self.data["min_price_for_alert"]) and
			(self.data["max_price_for_alert"] is None or item["price"] <= self.data["max_price_for_alert"])):
			return True
		return False

	def satisfies_auto_contact_sms(self, item):
		return (self.satisfies_alert(item) and self.data["auto_contact_sms"])

	def satisfies_auto_contact_email(self, item):
		return (self.satisfies_alert(item) and self.data["auto_contact_email"])

	def get_auto_contact_sms_message(self, item):
		if self.data["auto_contact_sms_template"]:
			return self.data["auto_contact_sms_template"] % (item["title"], item["price"])
		else:
			return None

	def get_auto_contact_mail_message(self, item):
		return self.data["auto_contact_mail_template"] % (item["title"], item["price"])
