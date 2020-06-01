# -*- coding: utf-8 -*-

from odoo import models, fields, api
import random
from odoo import http
import json
from datetime import datetime


class AccountantSalesperson(models.Model):
    _name = 'accountant.salesperson'
    _description = 'this is Profit sales'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Date(string="开始期间", required=True)
    endDate = fields.Date(string="结束期间", required=True)
    fast_period = fields.Date(string="选取期间")
    salesperson = fields.Many2one('res.users', string='销售员', required=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    amount_a = fields.Monetary(default=0.0, string="主营业务收入",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_b = fields.Monetary(default=0.0, string="主营业务成本",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_c = fields.Monetary(default=0.0, string="主营业务利润",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_d = fields.Monetary(default=0.0, string="其他业务利润",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_e = fields.Monetary(default=0.0, string="销售费用",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_f = fields.Monetary(default=0.0, string="管理费用",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_g = fields.Monetary(default=0.0, string="财务费用",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_h = fields.Monetary(default=0.0, string="营业利润",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_i = fields.Monetary(default=0.0, string="营业外收入",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_j = fields.Monetary(default=0.0, string="营业外支出",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_k = fields.Monetary(default=0.0, string="税前利润",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_l = fields.Monetary(default=0.0, string="所得税",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_m = fields.Monetary(default=0.0, string="净利润",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_n = fields.Monetary(default=0.0, string="资产减值损失",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_o = fields.Monetary(default=0.0, string="投资收益",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_p = fields.Monetary(default=0.0, string="公允价值变动收益",
                               store=True, currency_field='company_currency_id', readonly=True)

    @api.multi
    def _sales_person(self):
        sales = self.salesperson.id
        person = self.env['res.partner'].search([('user_id', '=', sales)]).mapped('id')
        return person

    @api.multi
    def _mapped_debit(self, account_id):
        start_s = self.startDate
        start_e = self.endDate
        sales_person = self._sales_person()
        amount_mapped = self.env['account.move.line']
        debit = sum(amount_mapped.search([('date', '>=', start_s),
                                          ('date', '<=', start_e),
                                          ('account_id', '=', account_id),
                                          ('company_id', '=', self.company_id.id),
                                          ('partner_id', 'in', sales_person)]).mapped('debit'))
        credit = sum(amount_mapped.search([('date', '>=', start_s),
                                           ('date', '<=', start_e),
                                           ('account_id', '=', account_id),
                                           ('company_id', '=', self.company_id.id),
                                           ('partner_id', 'in', sales_person)]).mapped('credit'))
        balance = debit - credit
        return balance

    @api.multi
    def _mapped_credit(self, account_id):
        start_s = self.startDate
        start_e = self.endDate
        sales_person = self._sales_person()
        amount_mapped = self.env['account.move.line']
        debit = sum(amount_mapped.search([('date', '>=', start_s),
                                          ('date', '<=', start_e),
                                          ('account_id', '=', account_id),
                                          ('company_id', '=', self.company_id.id),
                                          ('partner_id', 'in', sales_person)]).mapped('debit'))
        credit = sum(amount_mapped.search([('date', '>=', start_s),
                                           ('date', '<=', start_e),
                                           ('account_id', '=', account_id),
                                           ('company_id', '=', self.company_id.id),
                                           ('partner_id', 'in', sales_person)]).mapped('credit'))
        balance = credit - debit
        return balance

    @api.multi
    def _profit_debit(self, account_s, account_e):
        currency_account = self.env['account.account'].search([('code', '>=', account_s),
                                                               ('code', '<=', account_e),
                                                               ('company_id', '=', self.company_id.id)]).mapped('id')
        currency = 0
        for currency_id in currency_account:
            currency_debit = self._mapped_debit(currency_id)
            currency += currency_debit
        return currency

    @api.multi
    def _profit_credit(self, account_s, account_e):
        currency_account = self.env['account.account'].search([('code', '>=', account_s),
                                                               ('code', '<=', account_e),
                                                               ('company_id', '=', self.company_id.id)]).mapped('id')
        currency = 0
        for currency_id in currency_account:
            currency_credit = self._mapped_credit(currency_id)
            currency += currency_credit
        return currency

    @api.multi
    def do_profit_sales(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')

        # 主营业务收入
        self.amount_a = self._profit_credit(600100, 600100)
        # 主营业务成本
        self.amount_b = self._profit_debit(640100, 640100)
        # 主营业务利润
        self.amount_c = self.amount_a - self.amount_b
        # 其他业务利润
        self.amount_d = self._profit_credit(605100, 605100) - self._profit_debit(640200, 640200)
        # 销售费用
        self.amount_e = self._profit_debit(660100, 660199)
        # 管理费用
        self.amount_f = self._profit_debit(660200, 660299)
        # 财务费用
        self.amount_g = self._profit_debit(660300, 660399)
        # 营业利润
        self.amount_h = self.amount_c + self.amount_d - self.amount_e - self.amount_f - self.amount_g - self.amount_n\
                        + self.amount_o + self.amount_p
        # 营业外收入
        self.amount_i = self._profit_credit(630100, 630100)
        # 营业外支出
        self.amount_j = self._profit_debit(671100, 671100)
        # 税前利润
        self.amount_k = self.amount_h + self.amount_i - self.amount_j
        # 所得税
        self.amount_l = self._profit_debit(680100, 690100)
        # 净利润
        self.amount_m = self.amount_k - self.amount_l
        # 资产减值损失
        self.amount_n = self._profit_debit(670100, 670100)
        # 投资收益
        self.amount_o = self._profit_credit(611100, 611100)
        # 公允价值变动收益
        self.amount_p = self._profit_credit(610100, 610100)