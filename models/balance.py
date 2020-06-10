# -*- coding: utf-8 -*-
from odoo import models, fields, api
import random
from odoo import http
import json
from datetime import datetime


class AccountantBalance(models.Model):
    _name = 'accountant.balance'
    _description = 'this is Balance sheet'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Date(string="开始期间", required=True, store=True)
    endDate = fields.Date(string="结束期间", required=True, store=True)
    fast_period = fields.Date(string="选取期间")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    amount_b = fields.Monetary(default=0.0, string="货币资金",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_c = fields.Monetary(default=0.0, string="交易性金融资产",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_d = fields.Monetary(default=0.0, string="应收票据",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_e = fields.Monetary(default=0.0, string="应收账款",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_f = fields.Monetary(default=0.0, string="预付款项",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_g = fields.Monetary(default=0.0, string="应收股利",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_h = fields.Monetary(default=0.0, string="其他应收款",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_i = fields.Monetary(default=0.0, string="存货",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_j = fields.Monetary(default=0.0, string="一年内到期的非流动资产",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_k = fields.Monetary(default=0.0, string="其他流动资产",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_l = fields.Monetary(default=0.0, string="流动资产合计",
                               store=True, currency_field='company_currency_id', readonly=True)

    @api.multi
    def profit_mapped_debit(self, account_id):
        start_s = self.startDate
        start_e = self.endDate
        amount_mapped = self.env['account.move.line']
        debit = sum(amount_mapped.search([('date', '>=', start_s),
                                          ('date', '<=', start_e),
                                          ('account_id', '=', account_id),
                                          ('company_id', '=', self.company_id.id)]).mapped('debit'))
        credit = sum(amount_mapped.search([('date', '>=', start_s),
                                           ('date', '<=', start_e),
                                           ('account_id', '=', account_id),
                                           ('company_id', '=', self.company_id.id)]).mapped('credit'))
        balance = debit - credit
        return balance

    @api.multi
    def profit_mapped_credit(self, account_id):
        start_s = self.startDate
        start_e = self.endDate
        amount_mapped = self.env['account.move.line']
        debit = sum(amount_mapped.search([('date', '>=', start_s),
                                          ('date', '<=', start_e),
                                          ('account_id', '=', account_id),
                                          ('company_id', '=', self.company_id.id)]).mapped('debit'))
        credit = sum(amount_mapped.search([('date', '>=', start_s),
                                           ('date', '<=', start_e),
                                           ('account_id', '=', account_id),
                                           ('company_id', '=', self.company_id.id)]).mapped('credit'))
        balance = credit - debit
        return balance

    @api.multi
    def _account_debit(self, account_s, account_e):
        currency_account = self.env['account.account'].search([('code', '>=', account_s),
                                                               ('code', '<=', account_e),
                                                               ('company_id', '=', self.company_id.id)]).mapped('id')
        currency = 0
        for currency_id in currency_account:
            currency_debit = self.profit_mapped_debit(currency_id)
            currency += currency_debit
        return currency

    @api.multi
    def _account_credit(self, account_s, account_e):
        currency_account = self.env['account.account'].search([('code', '>=', account_s),
                                                               ('code', '<=', account_e),
                                                               ('company_id', '=', self.company_id.id)]).mapped('id')
        currency = 0
        for currency_id in currency_account:
            currency_credit = self.profit_mapped_credit(currency_id)
            currency += currency_credit
        return currency


    def _amount_get(self, amount):
        result = self.env['accountant.balance.set'].search([('company_id', '=', self.company_id.id)], limit=1).mapped(amount)[0]
        amount_sum = 0.0
        for L_dir in result.split(';'):
            s_dir = eval(L_dir)
            if s_dir == 0:
                break
            p_dir = s_dir.get('+')
            r_dir = s_dir.get('-')
            if p_dir:
                p_b, p_s, p_e = p_dir.split(',')
                if p_b == 'debit':
                    amount_sum += self._account_debit(int(p_s), int(p_e))
                elif p_b == 'credit':
                    amount_sum += self._account_credit(int(p_s), int(p_e))
                else:
                    raise UserError("计算失败！原因:余额方向填写错误")

            elif r_dir:
                r_b, r_s, r_e = r_dir.split(',')
                if r_b == 'debit':
                    amount_sum -= self._account_debit(int(r_s), int(r_e))
                elif r_b == 'credit':
                    amount_sum -= self._account_credit(int(r_s), int(r_e))
                else:
                    raise UserError("计算失败！原因:余额方向填写错误")
            else:
                raise UserError("计算失败！原因:+或—填写错误")

        return amount_sum



    @api.multi
    def do_current_assets(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
        # 货币资金

        # current_eight = self._account_debit(1002010, 1002016)
        self.amount_b = self._amount_get('amount_b')
        # 交易性金融资产
        # self.amount_c = self._account_debit(150300, 150300)
        self.amount_c = self._amount_get('amount_c')
        # 应收票据
        self.amount_d = self._amount_get('amount_d')
        # 应收账款
        # self.amount_e = self._account_debit(112200, 112200) \
        #                 + self._account_debit(11230001, 11230001)\
        #                 - self._account_credit(123100, 123100)
        self.amount_e = self._amount_get('amount_e')
        # # 预付款项
        # self.amount_f = self._account_debit(220200, 220200) + self._account_debit(112300, 112300)
        # 预付款项
        self.amount_f = self._amount_get('amount_f')
        # 应收股利
        self.amount_g = self._amount_get('amount_g')
        # 其他应收款
        self.amount_h = self._amount_get('amount_h')
        # 存货
        self.amount_i = self._amount_get('amount_i')
        # 一年内到期的非流动资产
        self.amount_j = self._amount_get('amount_j')
        # 其他流动资产
        self.amount_k = self._amount_get('amount_k')
        # 流动资产合计
        self.amount_l = self.amount_b + self.amount_c + self.amount_d + self.amount_e + self.amount_f + self.amount_g\
                        + self.amount_h + self.amount_i + self.amount_j + self.amount_k
        return self.do_fixed_assets()

    amount_m = fields.Monetary(default=0.0, string="可供出售金融资产",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_n = fields.Monetary(default=0.0, string="持有至到期投资",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_o = fields.Monetary(default=0.0, string="长期应收款",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_p = fields.Monetary(default=0.0, string="长期股权投资",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_q = fields.Monetary(default=0.0, string="投资性房地产",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_r = fields.Monetary(default=0.0, string="固定资产",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_s = fields.Monetary(default=0.0, string="在建工程",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_t = fields.Monetary(default=0.0, string="工程物资",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_v = fields.Monetary(default=0.0, string="固定资产清理",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_u = fields.Monetary(default=0.0, string="生产线生物资产",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_w = fields.Monetary(default=0.0, string="油气资产",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_x = fields.Monetary(default=0.0, string="无形资产",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_y = fields.Monetary(default=0.0, string="开发支出",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_z = fields.Monetary(default=0.0, string="商誉",
                               store=True, currency_field='company_currency_id', readonly=True)
    amount_aa = fields.Monetary(default=0.0, string="长期待摊费用",
                                store=True, currency_field='company_currency_id', readonly=True)
    amount_bb = fields.Monetary(default=0.0, string="递延所得税资产",
                                store=True, currency_field='company_currency_id', readonly=True)
    amount_cc = fields.Monetary(default=0.0, string="其他非流动资产",
                                store=True, currency_field='company_currency_id', readonly=True)
    amount_dd = fields.Monetary(default=0.0, string="非流动资产合计",
                                store=True, currency_field='company_currency_id', readonly=True)
    amount_ee = fields.Monetary(default=0.0, string="资产总计",
                                store=True, currency_field='company_currency_id', readonly=True)

    @api.multi
    def do_fixed_assets(self):
        # 可供出售金融资产
        self.amount_m = self._amount_get('amount_m')
        # 持有至到期投资
        self.amount_n = self._amount_get('amount_n')
        # 长期应收款
        self.amount_o = self._amount_get('amount_o')
        # 长期股权投资
        self.amount_p = self._amount_get('amount_p')
        # 投资性房地产
        self.amount_q = self._amount_get('amount_q')
        # 固定资产
        self.amount_r = self._amount_get('amount_r')
        # 在建工程
        self.amount_s = self._amount_get('amount_s')
        # 工程物资
        self.amount_t = self._amount_get('amount_t')
        # 固定资产清理
        self.amount_v = self._amount_get('amount_v')
        # 生产线生物资产
        self.amount_u = self._amount_get('amount_u')
        # 油气资产
        self.amount_w = self._amount_get('amount_w')
        # 无形资产
        self.amount_x = self._amount_get('amount_x')
        # 开发支出
        self.amount_y = self._amount_get('amount_y')
        # 商誉
        self.amount_z = self._amount_get('amount_z')
        # 长期待摊费用
        self.amount_aa = self._amount_get('amount_aa')
        # 递延所得税资产
        self.amount_bb = self._amount_get('amount_bb')
        # 其他非流动资产
        self.amount_cc = self._amount_get('amount_cc')
        # 非流动资产合计
        self.amount_dd = self.amount_m + self.amount_n + self.amount_o + self.amount_p + self.amount_q + self.amount_r\
                         + self.amount_s + self.amount_t + self.amount_u + self.amount_v + self.amount_w\
                         + self.amount_x + self.amount_y + self.amount_z + self.amount_aa + self.amount_bb\
                         + self.amount_cc
        # 资产总计
        self.amount_ee = self.amount_l + self.amount_dd
        return self.do_current_liabilities()

    debt_a = fields.Monetary(default=0.0, string="短期借款",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_b = fields.Monetary(default=0.0, string="交易性金融负债",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_c = fields.Monetary(default=0.0, string="应付票据",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_d = fields.Monetary(default=0.0, string="应付账款",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_e = fields.Monetary(default=0.0, string="预收款项",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_f = fields.Monetary(default=0.0, string="应付职工薪酬",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_g = fields.Monetary(default=0.0, string="应交税费",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_h = fields.Monetary(default=0.0, string="应付利息",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_i = fields.Monetary(default=0.0, string="应付股利",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_j = fields.Monetary(default=0.0, string="其他应付款",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_k = fields.Monetary(default=0.0, string="一年内到期的非流动负债",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_l = fields.Monetary(default=0.0, string="其他流动负债",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_m = fields.Monetary(default=0.0, string="流动负债合计",
                             store=True, currency_field='company_currency_id', readonly=True)

    @api.multi
    def do_current_liabilities(self):
        # 短期借款
        self.debt_a = self._amount_get('debt_a')
        # 交易性金融负债
        self.debt_b = self._amount_get('debt_b')
        # 应付票据
        self.debt_c = self._amount_get('debt_c')
        # 应付账款
        self.debt_d = self._amount_get('debt_d')
        # 预收帐款
        self.debt_e = self._amount_get('debt_e')
        # 应付职工薪酬
        self.debt_f = self._amount_get('debt_f')
        # 应交税费
        self.debt_g = self._amount_get('debt_g')
        # 应付利息
        self.debt_h = self._amount_get('debt_h')
        # 应付股利
        self.debt_i = self._amount_get('debt_i')
        # 其他应付款
        self.debt_j = self._amount_get('debt_j')
        # 一年内到期的非流动负债
        self.debt_k = self._amount_get('debt_k')
        # 其他流动负债
        self.debt_l = self._amount_get('debt_l')
        # 流动负债合计
        self.debt_m = self.debt_a + self.debt_b + self.debt_c + self.debt_d + self.debt_e + self.debt_f + self.debt_g\
                      + self.debt_h + self.debt_i + self.debt_j + self.debt_k + self.debt_l
        return self.do_fixed_liabilities()

    debt_n = fields.Monetary(default=0.0, string="长期借款",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_o = fields.Monetary(default=0.0, string="应付债券",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_p = fields.Monetary(default=0.0, string="长期应付款",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_q = fields.Monetary(default=0.0, string="专项应付款",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_r = fields.Monetary(default=0.0, string="预计负债",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_s = fields.Monetary(default=0.0, string="递延所得税负债",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_t = fields.Monetary(default=0.0, string="其他非流动负债",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_u = fields.Monetary(default=0.0, string="非流动负债合计",
                             store=True, currency_field='company_currency_id', readonly=True)
    debt_v = fields.Monetary(default=0.0, string="负债合计",
                             store=True, currency_field='company_currency_id', readonly=True)

    @api.multi
    def do_fixed_liabilities(self):
        # 长期借款
        self.debt_n = self._amount_get('debt_n')
        # 应付债券
        self.debt_o = self._amount_get('debt_o')
        # 长期应付款
        self.debt_p = self._amount_get('debt_p')
        # 专项应付款
        self.debt_q = self._amount_get('debt_q')
        # 预计负债
        self.debt_r = self._amount_get('debt_r')
        # 递延所得税负债
        self.debt_s = self._amount_get('debt_s')
        # 其他非流动负债
        self.debt_t = self._amount_get('debt_t')
        # 非流动负债合计
        self.debt_u = self.debt_n + self.debt_o + self.debt_p + self.debt_q + self.debt_r + self.debt_s + self.debt_t
        # 负债合计
        self.debt_v = self.debt_m + self.debt_u
        return self.do_equity()

    equity_a = fields.Monetary(default=0.0, string="实收资本",
                               store=True, currency_field='company_currency_id', readonly=True)
    equity_b = fields.Monetary(default=0.0, string="资本公积",
                               store=True, currency_field='company_currency_id', readonly=True)
    equity_c = fields.Monetary(default=0.0, string="盈余公积",
                               store=True, currency_field='company_currency_id', readonly=True)
    equity_d = fields.Monetary(default=0.0, string="未分配利润",
                               store=True, currency_field='company_currency_id', readonly=True)
    equity_e = fields.Monetary(default=0.0, string="所有者权益合计",
                               store=True, currency_field='company_currency_id', readonly=True)
    equity_f = fields.Monetary(default=0.0, string="负债和所有者权益总计",
                               store=True, currency_field='company_currency_id', readonly=True)

    @api.multi
    def do_equity(self):
        # 实收资本
        self.equity_a = self._amount_get('equity_a')
        # 资本公积
        self.equity_b = self._amount_get('equity_b')
        # 盈余公积
        self.equity_c = self._amount_get('equity_c')
        # 未分配利润
        self.equity_d = self._amount_get('equity_d')
        # 所有者权益合计
        self.equity_e = self.equity_a + self.equity_b + self.equity_c + self.equity_d
        # 负债和所有者权益总计
        self.equity_f = self.debt_v + self.equity_e



class AccountantBalanceSet(models.Model):
    _name = 'accountant.balance.set'
    _description = 'this is balance set'

    name = fields.Char(string='名称', store=True, required=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    amount_b = fields.Char(string='货币资金', store=True, required=True)
    amount_c = fields.Char(string='交易性金融资产',store=True, required=True)
    amount_d = fields.Char(string='应收票据',store=True, required=True)
    amount_e = fields.Char(string='应收账款',store=True, required=True)
    amount_f = fields.Char(string='预付款项',store=True, required=True)
    amount_g = fields.Char(string='应收股利',store=True, required=True)
    amount_h = fields.Char(string='其他应收款',store=True, required=True)
    amount_i = fields.Char(string='存货',store=True, required=True)
    amount_j = fields.Char(string='一年内到期的非流动资产',store=True, required=True)
    amount_k = fields.Char(string='其他流动资产',store=True, required=True)

    amount_m = fields.Char(string='可供出售金融资产', store=True, required=True)
    amount_n = fields.Char(string='持有至到期投资', store=True, required=True)
    amount_o = fields.Char(string='长期应收款', store=True, required=True)
    amount_p = fields.Char(string='长期股权投资', store=True, required=True)
    amount_q = fields.Char(string='投资性房地产', store=True, required=True)
    amount_r = fields.Char(string='固定资产', store=True, required=True)
    amount_s = fields.Char(string='在建工程', store=True, required=True)
    amount_t = fields.Char(string='工程物资', store=True, required=True)
    amount_v = fields.Char(string='固定资产清理', store=True, required=True)
    amount_u = fields.Char(string='生产线生物资产', store=True, required=True)
    amount_w = fields.Char(string='油气资产', store=True, required=True)
    amount_x = fields.Char(string='无形资产', store=True, required=True)
    amount_y = fields.Char(string='开发支出', store=True, required=True)
    amount_z = fields.Char(string='商誉', store=True, required=True)
    amount_aa = fields.Char(string='长期待摊费用', store=True, required=True)
    amount_bb = fields.Char(string='递延所得税资产', store=True, required=True)
    amount_cc = fields.Char(string='其他非流动资产', store=True, required=True)

    debt_a = fields.Char(string='短期借款', store=True, required=True)
    debt_b = fields.Char(string='交易性金融负债', store=True, required=True)
    debt_c = fields.Char(string='应付票据', store=True, required=True)
    debt_d = fields.Char(string='应付账款', store=True, required=True)
    debt_e = fields.Char(string='预收帐款', store=True, required=True)
    debt_f = fields.Char(string='应付职工薪酬', store=True, required=True)
    debt_g = fields.Char(string='应交税费', store=True, required=True)
    debt_h = fields.Char(string='应付利息', store=True, required=True)
    debt_i = fields.Char(string='应付股利', store=True, required=True)
    debt_j = fields.Char(string='其他应付款', store=True, required=True)
    debt_k = fields.Char(string='一年内到期的非流动负债', store=True, required=True)
    debt_l = fields.Char(string='其他流动负债', store=True, required=True)

    debt_n = fields.Char(string='长期借款', store=True, required=True)
    debt_o = fields.Char(string='应付债券', store=True, required=True)
    debt_p = fields.Char(string='长期应付款', store=True, required=True)
    debt_q = fields.Char(string='专项应付款', store=True, required=True)
    debt_r = fields.Char(string='预计负债', store=True, required=True)
    debt_s = fields.Char(string='递延所得税负债', store=True, required=True)
    debt_t = fields.Char(string='其他非流动负债', store=True, required=True)

    equity_a = fields.Char(string='实收资本', store=True, required=True)
    equity_b = fields.Char(string='资本公积', store=True, required=True)
    equity_c = fields.Char(string='盈余公积', store=True, required=True)
    equity_d = fields.Char(string='未分配利润', store=True, required=True)







