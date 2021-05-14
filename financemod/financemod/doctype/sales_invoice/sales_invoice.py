# -*- coding: utf-8 -*-
# Copyright (c) 2021, subin and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class SalesInvoice(Document):
	def create_gl_entry(self):
		acct = self.debit_to
		acct_against = self.credit_to
		cred_amount = 0
		debt_amount = self.total_rate
		for i in range(2):
			doc = frappe.get_doc({
				'doctype': 'GL Entry',
				'posting_date':self.date,
				'account': acct,
				'debit_amount': debt_amount,
				'credit_amount': cred_amount,
				'against':acct_against,
				'voucher_type':self.doctype
			})
			doc.insert()
			if i == 1: break
			acct = self.credit_to
			acct_against = self.debit_to
			cred_amount = self.total_rate
			debt_amount = 0


			

	def on_submit(self):
		self.create_gl_entry()
		
 