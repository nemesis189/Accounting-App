# -*- coding: utf-8 -*-
# Copyright (c) 2021, subin and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
import json
from frappe.utils import flt, cint


@frappe.whitelist()
def clickmethod(customer,quantity,item):
	item_dict = json.loads(item)
	item_name = get_item_name(item_dict)
	q = float(quantity)
	total = q * flt(item_dict['rate'])
	customer = check_customer(customer)
	
	if customer is None:
		return 'error'

	si = find_drafted_si(customer)

	cart = {'item_name': item_name['name'], 'rate': item_dict['rate'], 'quantity':quantity, 'total':total}

	try:
		if not si:
			doc = frappe.get_doc({
				'doctype' : 'Sales Invoice',
				'series' : 'ACC-SINV-.YYYY.-',
				'item' : [ cart ],
				'customer' : customer
			})
			doc.save()

		else:
			si_item_fields = {
				'doctype': 'Sales Invoice Item',
				'docstatus' : si.docstatus,
				'parent' : si.name,
				'parentfield' : 'item',
				'parenttype' : 'Sales Invoice',
			}

			si_item_fields.update(cart)
			si_item = frappe.get_doc(si_item_fields)
			si_item.save()
	
	except:
		return 'trans_error'


	return 'success'

@frappe.whitelist()
def check_customer(customer):
	c = frappe.db.sql(''' Select name,first_name,last_name from tabCustomer''', as_dict=True)
	# print(c)
	cust_list = { x.first_name +' '+x.last_name : x.name for x in c}
	if customer not in cust_list:
		return None
	else:
		return cust_list[customer]


@frappe.whitelist()
def insert_customer(fname,lname,cid):
	print(fname,lname,cid)
	customer = frappe.get_doc({
		'doctype':'Customer',
		'first_name':fname,
		'last_name':lname,
		'customer_id':cid
	})
	# customer.save()
	customer.insert()
	return 1


	
@frappe.whitelist()
def find_drafted_si(customer):
	si = frappe.db.sql(f'''
		SELECT * from `tabSales Invoice`
		WHERE customer = '{customer}'
		AND docstatus = 0
	''', as_dict=True)
	return si[0] if si else None

	

def get_item_name(item_dict):
	query = f'''  
		SELECT name FROM tabItem
		WHERE item_code = '{item_dict['code']}'
	'''
	item_name = frappe.db.sql(query, as_dict=True)
	return item_name[0]

def get_customer_name(item_dict):
	query = f'''  
		SELECT name FROM tabCustomer
		WHERE customer_name = '{item_dict['code']}'
	'''
	item_name = frappe.db.sql(query, as_dict=True)
	return item_name[0]


class Item(WebsiteGenerator):
	pass
