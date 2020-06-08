# -*- coding: utf-8 -*-

from odoo import models, fields, api
import random
from odoo import http
import json
from datetime import datetime


class AccountantTeam(models.Model):
    _name = 'accountant.team'
    _description = 'this is Profit team'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Date(string="开始期间", required=True)
    endDate = fields.Date(string="结束期间", required=True)
    fast_period = fields.Date(string="选取期间")
    team = fields.Many2one('crm.team', string='销售团队', required=True)
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
    def _sales_team_id(self):
        sales = self.team.id
        team = self.env['res.users'].search([('sale_team_id', '=', sales)]).mapped('id')
        return team

    @api.multi
    def _sales_team(self):
        sales = self._sales_team_id()
        team = self.env['res.partner'].search([('user_id', 'in', sales)]).mapped('id')
        return team

    @api.multi
    def _mapped_debit(self, account_id):
        start_s = self.startDate
        start_e = self.endDate
        sales_team = self._sales_team()
        amount_mapped = self.env['account.move.line']
        debit = sum(amount_mapped.search([('date', '>=', start_s),
                                          ('date', '<=', start_e),
                                          ('account_id', '=', account_id),
                                          ('company_id', '=', self.company_id.id),
                                          ('partner_id', 'in', sales_team)]).mapped('debit'))
        credit = sum(amount_mapped.search([('date', '>=', start_s),
                                           ('date', '<=', start_e),
                                           ('account_id', '=', account_id),
                                           ('company_id', '=', self.company_id.id),
                                           ('partner_id', 'in', sales_team)]).mapped('credit'))
        balance = debit - credit
        return balance

    @api.multi
    def _mapped_credit(self, account_id):
        start_s = self.startDate
        start_e = self.endDate
        sales_team = self._sales_team()
        amount_mapped = self.env['account.move.line']
        debit = sum(amount_mapped.search([('date', '>=', start_s),
                                          ('date', '<=', start_e),
                                          ('account_id', '=', account_id),
                                          ('company_id', '=', self.company_id.id),
                                          ('partner_id', 'in', sales_team)]).mapped('debit'))
        credit = sum(amount_mapped.search([('date', '>=', start_s),
                                           ('date', '<=', start_e),
                                           ('account_id', '=', account_id),
                                           ('company_id', '=', self.company_id.id),
                                           ('partner_id', 'in', sales_team)]).mapped('credit'))
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

    def _amount_get(self, amount):
        result = self.env['accountant.profit.set'].search([('company_id', '=', self.company_id.id)], limit=1).mapped(amount)[0]
        amount_sum = 0.0
        for L_dir in result.split(';'):
            s_dir= eval(L_dir)
            if s_dir == 0:
                break
            p_dir = s_dir.get('+')
            r_dir = s_dir.get('-')
            if p_dir:
                p_b, p_s, p_e = p_dir.split(',')
                if p_b == 'debit':
                    amount_sum += self._profit_debit(int(p_s), int(p_e))
                elif p_b == 'credit':
                    amount_sum += self._profit_credit(int(p_s), int(p_e))
                else:
                    raise UserError("计算失败！原因:余额方向填写错误")

            elif r_dir:
                r_b, r_s, r_e = r_dir.split(',')
                if r_b == 'debit':
                    amount_sum -= self._profit_debit(int(r_s), int(r_e))
                elif r_b == 'credit':
                    amount_sum -= self._profit_credit(int(r_s), int(r_e))
                else:
                    raise UserError("计算失败！原因:余额方向填写错误")
            else:
                raise UserError("计算失败！原因:+或—填写错误")

        return amount_sum

    @api.multi
    def do_profit_team(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')

        # 主营业务收入
        self.amount_a = self._amount_get('amount_a')
        # 主营业务成本
        self.amount_b = self._amount_get('amount_b')
        # 主营业务利润
        self.amount_c = self.amount_a - self.amount_b
        # 其他业务利润
        self.amount_d = self._amount_get('amount_d')
        # 销售费用
        self.amount_e = self._amount_get('amount_e')
        # 管理费用
        self.amount_f = self._amount_get('amount_f')
        # 财务费用
        self.amount_g = self._amount_get('amount_g')
        # 资产减值损失
        self.amount_n = self._amount_get('amount_n')
        # 投资收益
        self.amount_o = self._amount_get('amount_o')
        # 公允价值变动收益
        self.amount_p = self._amount_get('amount_p')
        # 营业利润
        self.amount_h = self.amount_c + self.amount_d - self.amount_e - self.amount_f - self.amount_g - self.amount_n \
                        + self.amount_o + self.amount_p
        # 营业外收入
        self.amount_i = self._amount_get('amount_i')
        # 营业外支出
        self.amount_j = self._amount_get('amount_j')
        # 税前利润
        self.amount_k = self.amount_h + self.amount_i - self.amount_j
        # 所得税
        self.amount_l = self._amount_get('amount_l')
        # 净利润
        self.amount_m = self.amount_k - self.amount_l