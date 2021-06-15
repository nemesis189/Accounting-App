# -*- coding: utf-8 -*-
# Copyright (c) 2021, subin and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

class TestSalesInvoice(unittest.TestCase):
	def setUp(self):
		if not frappe.db.exists('Item',{'item_code':'cont111'}):
			create_test_item(item_code='cont111',item_name='Container1',rate='10',def_uom='units')

		if not frappe.db.exists('Customer', {'customer_id':'test123'}):
			create_test_customer(cust_id='test123', fname='Test', lname='Customer')
		self.customer = frappe.db.get_value('Customer', {'customer_id':'test123'}, 'name')


	def test_sales_invoice_total_quantity_and_rate(self):
		item = [
			{'item_name': 'Container1', 'rate': '10', 'quantity':'100', 'total':'1000'},
		]
		si_doc = create_si(item,self.customer)

		self.assertEqual(frappe.get_value("Sales Invoice",si_doc.name,"total_quantity"),100.0)
		self.assertEqual(frappe.get_value("Sales Invoice",si_doc.name,"total_rate"),1000.0)

	
	def tearDown(self):
		delete_test_doc('Sales Invoice','customer',self.customer)
		delete_test_doc('Item','item_code','cont111')
		delete_test_doc('Customer','customer_id','test123')


def create_si(item,name):
	doc = frappe.get_doc({
		'doctype' : 'Sales Invoice',
		'series' : 'ACC-SINV-.YYYY.-',
		'item' : item,
		'customer' : name,
	})
	doc.save()
	return doc

def create_test_item(**args):
	args = frappe._dict(args)
	doc = frappe.get_doc({
		'doctype': 'Item',
		'item_name': args.item_name,
		'item_code':args.item_code,
		'rate':args.rate,
		'def_uom':args.def_uom
	}).insert()

def create_test_customer(**args):
	args = frappe._dict(args)
	doc = frappe.get_doc({
		'doctype': 'Customer',
		'customer_id': args.cust_id,
		'first_name':args.fname,
		'last_name':args.lname
	}).insert()




def delete_test_doc(dt, id_name, id):
	if frappe.db.exists(dt, {id_name:id}):
		name = frappe.db.get_value(dt,{id_name:id},"name")
		frappe.delete_doc(dt,name)