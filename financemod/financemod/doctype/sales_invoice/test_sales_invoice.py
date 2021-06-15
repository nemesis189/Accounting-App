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


	def test_sales_invoice_total_quantity_and_rate(self):
		item = [
			{'item_name': 'Container1', 'rate': '10', 'quantity':'100', 'total':'1000'},
		]
		customer = frappe.db.get_value('Customer', {'customer_id':'test123'}, 'name')
		si_doc = create_si(item,name)

		self.assertEqual(frappe.get_value("Sales Invoice",si_doc.name,"total_quantity"),"100")
		self.assertEqual(frappe.get_value("Sales Invoice",si_doc.name,"total_rate"),"1000")


	def create_si(item):
		doc = frappe.get_doc({
			'doctype' : 'Sales Invoice',
			'series' : 'ACC-SINV-.YYYY.-',
			'item' : item,
			'customer' : name,
		})
		# doc.insert()
		doc.submit
		return doc

	def create_test_item(**args):
		doc = frappe.get_doc({
			'item_name': args.item_name,
			'item_code':args.item_code,
			'rate':args.rate,
			'def_uom':args.def_uom
		}).insert()

	def create_test_customer(**args):
		doc = frappe.get_doc({
			'customer_id': args.cust_id,
			'first_name':args.first_name,
			'last_name':args.last_name
		}).insert()

	def tearDown(self):
		delete_test_doc('Item','item_code','cont111')
		delete_test_doc('Customer','customer_id','test123')

	
	def delete_test_doc(dt, id_name, id):
		if frappe.db.exists(dt, {id_name:id}):
			name = frappe.db.get_value(dt,{id_name:id},"name")
			frappe.delete_doc(dt,name)