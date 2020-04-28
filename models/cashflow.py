# -*- coding: utf-8 -*-
from odoo import models, fields, api
import random
from odoo import http
import json
from datetime import datetime


class AccountantCash(models.Model):
    _name = 'accountant.cash'
    _description = 'this is cash flow statement'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Date(string="开始期间", required=True)
    endDate = fields.Date(string="结束期间", required=True)
    fast_period = fields.Date(string="选取期间")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司', store=True, index=True, readonly=False, required=True)
    amount_a = fields.Monetary(default=0.0, store=True, currency_field='company_currency_id', readonly=True)
    amount_b = fields.Monetary(default=0.0, store=True, currency_field='company_currency_id', readonly=True)
    amount_c = fields.Monetary(default=0.0, store=True, currency_field='company_currency_id', readonly=True)
    amount_d = fields.Monetary(default=0.0, store=True, currency_field='company_currency_id', readonly=True)
    amount_e = fields.Monetary(default=0.0, store=True, currency_field='company_currency_id', readonly=True)
    amount_f = fields.Monetary(default=0.0, store=True, currency_field='company_currency_id', readonly=True)
    amount_g = fields.Monetary(default=0.0, store=True, currency_field='company_currency_id', readonly=True)
    amount_h = fields.Monetary(default=0.0, store=True, currency_field='company_currency_id', readonly=True)
    amount_i = fields.Monetary(default=0.0, store=True, currency_field='company_currency_id', readonly=True)

    @api.multi
    def _cash_sale(self, account_s, account_e):
        ids = self.env['account.account'].search(
            [('code', '>=', account_s),
             ('code', '<=', account_e),
             ('company_id', '=', self.company_id.id)]).mapped('id')
        return ids

    @api.multi
    def _cash_journal(self):
        journal = self.env['account.journal'].search(['|', ('type', '=', 'bank'),
                                                      ('type', '=', 'cash'),
                                                      ('company_id', '=', self.company_id.id)]).mapped('id')
        return journal

    @api.multi
    def _cash_journal_account(self):
        journal_ids = self.env['account.journal'].search(['|', ('type', '=', 'bank'),
                                                          ('type', '=', 'cash'),
                                                          ('company_id', '=', self.company_id.id)
                                                          ]).mapped('default_credit_account_id')
        return journal_ids

    @api.multi
    def _cash_account_debit(self, journal_id, account_id):
        account = sum(self.env['account.move.line'].search([('date', '>=', self.startDate),
                                                            ('date', '<=', self.endDate),
                                                            ('journal_id', '=', journal_id),
                                                            ('account_id', '=', account_id),
                                                            ('company_id', '=', self.company_id.id)]).mapped('debit'))
        return account

    @api.multi
    def _cash_account_credit(self, journal_id, account_id):
        account = sum(self.env['account.move.line'].search([('date', '>=', self.startDate),
                                                            ('date', '<=', self.endDate),
                                                            ('journal_id', '=', journal_id),
                                                            ('account_id', '=', account_id),
                                                            ('company_id', '=', self.company_id.id)]).mapped('credit'))
        return account

    @api.multi
    def _cash_del(self, journal_id):
        cash_del = self.env['account.journal'].search([('id', '=', journal_id),
                                                       ('company_id', '=', self.company_id.id)
                                                       ], limit=1).default_credit_account_id
        return cash_del

    @api.multi
    def _cash_bank_debit(self, journal_id):
        account_ids = self._cash_sale(660100, 660399)
        account_ids.append(5)
        journal_ids = []
        journal_obj = self._cash_journal_account()
        for journal in journal_obj:
            journal_ids.append(journal.id)

        cash_del = self._cash_del(journal_id)
        journal_ids.remove(cash_del.id)  # 核算自己的日记账


        account = sum(self.env['account.move.line'].search([('date', '>=', self.startDate),
                                                            ('date', '<=', self.endDate),
                                                            ('journal_id', '=', journal_id),
                                                            ('account_id', 'not in', account_ids),
                                                            ('account_id', 'not in', journal_ids),
                                                            ('reconciled', '=', False),
                                                            ('company_id', '=', self.company_id.id)
                                                            ]).mapped('debit'))
        return account

    @api.multi
    def _cash_bank_credit(self, journal_id):
        account_ids = self._cash_sale(660100, 690100)
        account_ids.append(5)
        journal_ids = []
        journal_obj = self._cash_journal_account()
        for journal in journal_obj:
            journal_ids.append(journal.id)

        cash_del = self._cash_del(journal_id)
        journal_ids.remove(cash_del.id)  # 核算自己的日记账
        account = sum(self.env['account.move.line'].search([('date', '>=', self.startDate),
                                                            ('date', '<=', self.endDate),
                                                            ('journal_id', '=', journal_id),
                                                            ('account_id', 'not in', account_ids),
                                                            ('account_id', 'not in', journal_ids),
                                                            ('reconciled', '=', False),
                                                            ('company_id', '=', self.company_id.id)
                                                            ]).mapped('credit'))
        return account

    @api.multi
    def _cash_usual_debit(self, journal_id, account_s, account_d):
        account_ids = self._cash_sale(account_s, account_d)
        account = sum(self.env['account.move.line'].search([('date', '>=', self.startDate),
                                                            ('date', '<=', self.endDate),
                                                            ('journal_id', '=', journal_id),
                                                            ('account_id', 'in', account_ids),
                                                            ('company_id', '=', self.company_id.id)]).mapped('debit'))
        return account

    @api.multi
    def _cash_usual_credit(self, journal_id, account_s, account_d):
        account_ids = self._cash_sale(account_s, account_d)
        account = sum(self.env['account.move.line'].search([('date', '>=', self.startDate),
                                                            ('date', '<=', self.endDate),
                                                            ('journal_id', '=', journal_id),
                                                            ('account_id', 'in', account_ids),
                                                            ('company_id', '=', self.company_id.id)]).mapped('credit'))
        return account

    @api.multi
    def do_cash(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
        # 销售商品、提供劳务收到的现金
        account_id = 5  # 应收账款
        journal_a = self._cash_journal()
        sum_amount_a_credit = 0
        sum_amount_a_debit = 0
        sum_amount_b_debit = 0
        sum_amount_b_credit = 0
        sum_amount_d_debit = 0
        sum_amount_d_credit = 0
        sum_amount_e_debit = 0
        sum_amount_e_credit = 0
        sum_amount_f_debit = 0
        sum_amount_f_credit = 0
        sum_amount_g_debit = 0
        sum_amount_g_credit = 0
        for journal_id in journal_a:
            sum_amount_a_credit += self._cash_account_credit(journal_id, account_id)
            sum_amount_a_debit += self._cash_account_debit(journal_id, account_id)

            sum_amount_b_debit += self._cash_bank_debit(journal_id)
            sum_amount_b_credit += self._cash_bank_credit(journal_id)

            sum_amount_d_debit += self._cash_account_debit(journal_id, 40)
            sum_amount_d_credit += self._cash_account_credit(journal_id, 40)

            sum_amount_e_debit += self._cash_usual_debit(journal_id, 660111, 660111)
            sum_amount_e_credit += self._cash_usual_credit(journal_id, 660111, 660111)

            sum_amount_f_debit += self._cash_usual_debit(journal_id, 680100, 680100)
            sum_amount_f_credit += self._cash_usual_credit(journal_id, 680100, 680100)

            sum_amount_g_debit += self._cash_usual_debit(journal_id, 660100, 660110)\
                                  + self._cash_usual_debit(journal_id, 660112, 68099)\
                                  + self._cash_usual_debit(journal_id, 680101, 690100)
            sum_amount_g_credit += self._cash_usual_credit(journal_id, 660100, 660110)\
                                   + self._cash_usual_credit(journal_id, 660112, 68099)\
                                   + self._cash_usual_credit(journal_id, 680101, 690100)
        self.amount_a = sum_amount_a_credit - sum_amount_a_debit
        # 收到的其他与经营活动有关的现金
        self.amount_b = sum_amount_b_debit - sum_amount_b_credit
        # 现金流入小计
        self.amount_c = self.amount_a + self.amount_b
        # 购买商品、接受劳务支付的现金
        self.amount_d = sum_amount_d_debit - sum_amount_d_credit
        # 支付给职工以及为职工支付的现金
        self.amount_e = sum_amount_e_debit - sum_amount_e_credit
        # 支付的各项税费
        self.amount_f = sum_amount_f_debit - sum_amount_f_credit
        # 支付的其他与经营活动有关的费用
        self.amount_g = sum_amount_g_debit - sum_amount_g_credit
        # 现金流出小计
        self.amount_h = self.amount_d + self.amount_e + self.amount_f + self.amount_g
        # 经营活动产生的现金流量净额
        self.amount_i = self.amount_c - self.amount_h
















