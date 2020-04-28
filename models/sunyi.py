from odoo import models, fields, api
import json


class AccountantSun(models.Model):
    _name = 'accountant.sun'
    _description = 'this is Carry over gains and losses'
    startDate = fields.Date(string="开始期间", required=True)
    endDate = fields.Date(string="结束期间", required=True)
    fast_period = fields.Date(string="选取期间")
    ref = fields.Char(string='摘要', copy=False, required=True)
    date = fields.Date(required=True, index=True,
                       default=fields.Date.context_today, readonly=True)
    journal_id = fields.Many2one('account.journal',
                                 string='Journal', readonly=False, index=True, store=True)
    company_id = fields.Many2one('res.company',
                                 string='公司', store=True, index=True, readonly=False, required=True)
    account_id = fields.Many2one('account.account', string='Account', index=True, store=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    debit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    move_id = fields.Many2one('account.move', string='Journal Entry', ondelete="cascade",
                              help="The move of this entry line.", index=True, auto_join=True)

    @api.multi
    def sun_entry(self):
        sun_write = {
            'state': 'draft',
            'name': 'JZSY',
            'date': self.date,
            'journal_id': '3',
            'ref': self.ref,
            'company_id': self.company_id.id
        }
        self.env(user=2)['account.move'].create(sun_write)
        return self.sun_entry_line()

    @api.multi
    def sun_mapped(self, account_id):
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
    def _sun_entry_line(self, account_id, debit, credit):
        move_id = self.env['account.move'].search([('date', '=', fields.Date.today()),
                                                   ('name', '=', 'JZSY'),
                                                   ('company_id', '=', self.company_id.id)], limit=1).id
        sun_line = {
            'account_id': account_id,
            'move_id': move_id,
            'date_maturity': self.date,
            'debit': debit,
            'credit': credit,
            'company_id': self.company_id.id,
            'name': '结转损益',
        }
        return sun_line

    @api.multi
    def _get_balance(self, balance, account):
        if balance >= 0:
            debit = 0
            credit = balance
            account_id = account
            result = self._sun_entry_line(account_id, debit, credit)
            return result
        else:
            debit = -balance
            credit = 0
            account_id = account
            result = self._sun_entry_line(account_id, debit, credit)
            return result

    @api.multi
    def _get_balance_sun(self, balance, account):
        if balance >= 0:
            debit = balance
            credit = 0
            account_id = account
            result = self._sun_entry_line(account_id, debit, credit)
            return result
        else:
            debit = 0
            credit = -balance
            account_id = account
            result = self._sun_entry_line(account_id, debit, credit)
            return result

    @api.multi
    def sun_entry_line(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')

        account_s = 440100
        account_e = 690100
        account = self.env['account.account'].search([('code', '>=', account_s),
                                                      ('code', '<=', account_e),
                                                      ('company_id', '=', self.company_id.id)]).mapped('id')
        sun_line_create = []
        profit = 0
        for account_id in account:
            debit = self.sun_mapped(account_id)
            if debit != 0:
                income = self._get_balance(debit, account_id)
                sun_line_create.append(income)
            profit += debit
        if profit != 0:
            profit_this_year = self._get_balance_sun(profit, 56)
            sun_line_create.append(profit_this_year)
        self.env(user=2)['account.move.line'].create(sun_line_create)








