import frappe
from frappe.utils.__init__ import get_fullname


customer =  get_fullname(frappe.session.user)
# sales_inv = None

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

	if si:
		context.item_list = get_items(si)
	# print(item_list)
	# print([ item_list[x]['quantity'] for x in item_list ], [ item_list[x]['total'] for x in item_list ])
	context.final_total = dict(
		quantity = sum([ context.item_list[x]['quantity'] for x in context.item_list ]),
		total = sum([ context.item_list[x]['total'] for x in context.item_list ])
	)

	sales_inv = si_doc
	# print(sales_inv)
		

def check_customer(customer):
	c = frappe.db.sql(''' Select name,first_name,last_name from tabCustomer''', as_dict=True)
	# print(c)
	cust_list = { x.first_name +' '+x.last_name : x.name for x in c}
	return None if customer not in cust_list else cust_list[customer]

def find_drafted_si(customer):
	si = frappe.db.sql(f'''
		SELECT * from `tabSales Invoice`
		WHERE customer = '{customer}'
		AND docstatus = 0
	''', as_dict=True)

	si_doc = frappe.get_doc('Sales Invoice', si[0]['name'])
	
	return si[0],si_doc if si else None



def update_cart_item(item,d):
	
	new_item = {}
	for x in item:
		new_item[x] = float(item[x]) + float(d[x])
	return new_item



def get_items(si):
	items = frappe.db.sql(f''' SELECT name, item_name, rate, quantity, total from `tabSales Invoice Item` 
	WHERE parent = "{si.name}" ''', as_dict=True)
	names =  [x['item_name'] for x in items]

	item_names = frappe.db.sql(''' SELECT  name,item_name from `tabItem` 
									WHERE name in {names} '''.format(names=tuple(names)), as_dict=True)
	item_list = {x['item_name']:{'rate':0.0, 'quantity':0.0, 'total':0.0} for x in item_names}

	for x in item_names:
		for y in items:
			if x['name'] == y['item_name']:
				d = {}
				key = x['item_name']
				d[key] = {'rate':y['rate'], 'quantity':y['quantity'], 'total':y['total']}
				item_list[key] = update_cart_item(item_list[key],d[key])
	# print(item_names,items,item_list)
	return item_list

@frappe.whitelist()
def submit_si():
	cust_name = check_customer(customer)
	si,sales_inv = find_drafted_si(cust_name)
	print(si,sales_inv)
	try:
		# sales_inv.insert()
		sales_inv.submit()
	# return 1
	except:
		return 'error'
	
	return 1
