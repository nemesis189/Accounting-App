import frappe
from frappe.utils.__init__ import get_fullname


customer =  get_fullname(frappe.session.user)

def is_user_logged_in():
	if  frappe.session.user != "Guest":
		return True
	else: return False


def get_context(context):
	context.logged_in = True
	if not is_user_logged_in():
		context.logged_in = False
	cust_name = check_customer(customer)
	
	si,si_doc = find_drafted_si(cust_name)

	context.item_list = get_items(si)

	context.final_total = dict(
		quantity = sum([ context.item_list[x]['quantity'] for x in context.item_list ]) if si else 0.0,
		total = sum([ context.item_list[x]['total'] for x in context.item_list ]) if si else 0.0
	)


def check_customer(customer):
	c = frappe.db.sql(''' Select name,first_name,last_name from tabCustomer''', as_dict=True)
	cust_list = { x.first_name +' '+x.last_name : x.name for x in c}
	return None if customer not in cust_list else cust_list[customer]


def find_drafted_si(customer):
	si = frappe.db.sql(f'''
		SELECT * from `tabSales Invoice`
		WHERE customer = '{customer}'
		AND docstatus = 0 '''
		, as_dict=True)
	if si:
		si_doc = frappe.get_doc('Sales Invoice', si[0]['name'])
		return si[0],si_doc 
	return None



def update_cart_item(item,d):
	new_item = {}
	for x in item:
		if x  in ['quantity','total']:
			new_item[x] =  float(item[x]) + float(d[x]) 
		else:
			new_item[x] = d[x]
	return new_item



def get_items(si):
	items = frappe.db.sql(f''' SELECT name, item_name, rate, quantity, total from `tabSales Invoice Item` 
	WHERE parent = "{si.name}" ''', as_dict=True)
	n =  [ x['item_name'] for x in items ]
	names = str(n).replace('[','(').replace(']',')')

	item_names = frappe.db.sql(''' SELECT  name,item_name, item_image from `tabItem` 
									WHERE name in {names} '''
								.format(names=names), as_dict=True)
	item_list = {x['item_name']:{'rate':0.0, 'quantity':0.0, 'total':0.0, 'image':''} for x in item_names}

	for x in item_names:
		for y in items:
			if x['name'] == y['item_name']:
				d = {}
				key = x['item_name']
				d[key] = {'rate':y['rate'], 'quantity':y['quantity'], 'total':y['total'], 'image':x['item_image']}
				item_list[key] = update_cart_item(item_list[key],d[key])
	return item_list

@frappe.whitelist()
def submit_si():
	cust_name = check_customer(customer)
	si,sales_inv = find_drafted_si(cust_name)
	try:
		sales_inv.submit()
	except:
		return 'error'
	
	return 'submitted'
