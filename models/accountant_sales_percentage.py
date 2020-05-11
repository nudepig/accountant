# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountantSalesPercentage(models.Model):
    _description = 'this is sales'
    _name = 'accountant.sales.percentage'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Date(string="开始期间", required=True)
    endDate = fields.Date(string="结束期间", required=True)
    fast_period = fields.Datetime(string="选取期间")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    partner_id = fields.Char(string='合作伙伴', store=True, readonly=True, copy=False)
    partner_id_name = fields.Char(string='客户名称', store=True, copy=False)

    state = fields.Selection([
        ('draft', '草稿'),
        ('open', '打开'),
        ('in_payment', '正在付款'),
        ('paid', '已支付'),
        ('cancel', '取消'),
    ], string='发票状态', index=True, readonly=True,
        track_visibility='onchange', copy=False,)

    number = fields.Char(string='发票名称', store=True, readonly=True, copy=False)
    date = fields.Date(string='日期', copy=False, readonly=True)
    user_id = fields.Many2one('res.users', string='销售员', readonly=False, required=True, copy=False)
    user_id_name = fields.Char(string='销售员', store=True, readonly=True, copy=False)
    # team_id = fields.Many2one('crm.team', string='销售团队')
    team_id = fields.Char(string='销售团队', store=True, readonly=True, copy=False)
    origin = fields.Char(string='源文档', store=True, readonly=True, copy=False)
    # product_id = fields.Many2one('product.product', string='产品',
    #                              ondelete='restrict', index=True)
    product_id = fields.Char(string='产品名称', store=True, readonly=True, copy=False)
    brand = fields.Char(string='品牌', store=True, readonly=True, copy=False)
    # uom_id = fields.Many2one('uom.uom', string='计量单位',
    #                          ondelete='set null', index=True)
    uom_id = fields.Char(string='计量单位', store=True, readonly=True, copy=False)

    quantity = fields.Float(string='数量', digits=(10, 2))
    price_unit = fields.Float(string='单价', digits=(10, 2))
    price_subtotal_signed = fields.Float(string='小计', digits=(10, 2))
    receivable = fields.Monetary(string="应收", store=True,
                                 currency_field='company_currency_id', readonly=True)
    receivable_income = fields.Monetary(string="已收", store=True,
                                        currency_field='company_currency_id', readonly=True)
    discount_receivable = fields.Monetary(string="应收折让", store=True,
                                          currency_field='company_currency_id', readonly=True)
    balance = fields.Monetary(string="余额", store=True,
                              currency_field='company_currency_id', readonly=True)

    total = fields.Float(string='合计', digits=(10, 2))
    stock_picking = fields.Char(string='送货单号', store=True, copy=False)
    discount = fields.Float(string='折扣', digits=(10, 2))

    def accountant_sales(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
        payment_ids = self.env['account.payment'].search([('payment_date', '>=', self.startDate),
                                                               ('payment_date', '<=', self.endDate)]).ids

        sql = 'select invoice_id from account_invoice_payment_rel where payment_id in {}'.format(tuple(payment_ids))
        self.env.cr.execute(sql)
        result = self.env.cr.dictfetchall()
        invoice_ids = [x['invoice_id'] for x in result]
        invoice_list = self.env['account.invoice'].search([('id', 'in', invoice_ids),
                                                           ('user_id', '=', self.user_id.id)]).ids

        for invoice_id in invoice_list:
            partner_id = self.env['account.invoice'].search([('id', '=', invoice_id)]).partner_id.id
            partner_id_name = self.env['account.invoice'].search([('id', '=', invoice_id)]).partner_id.name
            state = self.env['account.invoice'].search([('id', '=', invoice_id)]).state
            number = self.env['account.invoice'].search([('id', '=', invoice_id)]).number
            date = self.env['account.invoice'].search([('id', '=', invoice_id)]).date_invoice
            user_id_name = self.env['account.invoice'].search([('id', '=', invoice_id)]).user_id.partner_id.name
            team_id = self.env['account.invoice'].search([('id', '=', invoice_id)]).team_id.name
            origin = self.env['account.invoice'].search([('id', '=', invoice_id)]).origin
            stock_picking_list = self.env['stock.picking'].search([('origin', '=', origin)]).mapped('name')
            stock_picking = ' '.join(stock_picking_list)  # 注意引号内有空格
            receivable = sum(self.env['account.move.line'].search([('invoice_id', '=', invoice_id),
                                                                  ('account_id', '=', 5)]).mapped('balance'))
            residual_signed = self.env['account.invoice'].search([('id', '=', invoice_id)]).residual_signed
            sql_pay = 'select payment_id from account_invoice_payment_rel where invoice_id = %s' % invoice_id
            self.env.cr.execute(sql_pay)
            result_pay = self.env.cr.dictfetchall()
            payment = [x['payment_id'] for x in result_pay]
            discount = sum(self.env['account.move.line'].search([('payment_id', 'in', payment),
                                                                 ('account_id', '=', 420)]).mapped('balance'))
            # receivable_income_s = sum(self.env['account.move.line'].search([('payment_id', 'in', payment_ids),
            #                                                                ('account_id', '=', 5)]).mapped('balance'))
            # receivable_income_e = sum(self.env['account.move.line'].search([('payment_id', 'in', payment_ids),
            #                                                               ('account_id', '=', 5)]).mapped('amount_residual'))
            # receivable_income = (receivable_income_s - receivable_income_e) * -1 - discount  # 用payment_id 找对应的应收
            receivable_income = sum(self.env['account.move.line'].search([('invoice_id', '=', invoice_id),
                                                                          ('account_id', '=', 5)]).mapped('balance_cash_basis'))
            vals = {
                'partner_id': partner_id,
                'partner_id_name': partner_id_name,
                'company_id': self.company_id.id,
                'state': state,
                'number': number,
                'date': date,
                'user_id_name': user_id_name,
                'user_id': self.user_id.id,
                'team_id': team_id,
                'origin': origin,
                'stock_picking': stock_picking,
                'receivable': receivable,
                'receivable_income': receivable_income,
                'balance': residual_signed,
                'discount': discount,
                'name': self.name,
                'startDate': self.startDate,
                'endDate': self.endDate,
            }
            self.create(vals)
            self._account_invoice_line(invoice_id, state, number, date, user_id_name, team_id, origin, partner_id, partner_id_name)

    def _account_invoice_line(self, invoice_id, state, number, date, user_id_name, team_id, origin, partner_id, partner_id_name):
        product_id_list = self.env['account.invoice.line'].search([('invoice_id', '=', invoice_id)]).mapped('product_id')
        for product_id in product_id_list:
            product_id = product_id.id

            brand_product = self.env['product.product'].search([('id', '=', product_id)]).mapped('product_tmpl_id').id
            brand_tmpl = self.env['product.template'].search([('id', '=', brand_product)]).mapped('categ_id').id
            brand_categ = self.env['product.category'].search([('id', '=', brand_tmpl)]).mapped('parent_id').id
            brand = self.env['product.category'].search([('id', '=', brand_categ)]).name

            product_name = self.env['product.template'].search([('id', '=', brand_product)]).name

            uom_id = self.env['account.invoice.line'].search([('invoice_id', '=', invoice_id),
                                                              ('product_id', '=', product_id)], limit=1).uom_id.name
            quantity = sum(self.env['account.invoice.line'].search([('invoice_id', '=', invoice_id),
                                                                   ('product_id', '=', product_id)]).mapped('quantity'))
            price_unit_list = self.env['account.invoice.line'].search([('invoice_id', '=', invoice_id),
                                                                      ('product_id', '=', product_id)]).mapped('price_unit')
            price_unit = sum(price_unit_list)/len(price_unit_list)
            price_subtotal_signed = sum(self.env['account.invoice.line'].search([('invoice_id', '=', invoice_id),
                                                                    ('product_id', '=', product_id)]).mapped('price_subtotal_signed'))

            total = quantity * price_unit
            values = {
                'partner_id': partner_id,
                'partner_id_name': partner_id_name,
                'company_id': self.company_id.id,
                'state': state,
                'number': number,
                'date': date,
                'user_id_name': user_id_name,
                'user_id': self.user_id.id,
                'team_id': team_id,
                'origin': origin,
                'product_id': product_name,
                'brand': brand,
                'uom_id': uom_id,
                'quantity': quantity,
                'price_unit': price_unit,
                'total': total,
                'price_subtotal_signed': price_subtotal_signed,
                # 'receivable_debit': receivable_debit,
                # 'receivable_credit': receivable_credit,
                # 'balance': balance,
                'name': self.name,
                'startDate': self.startDate,
                'endDate': self.endDate,
            }
            self.create(values)

    @api.model_create_multi
    def create(self, values):
        lines = super(AccountantSalesPercentage, self).create(values)
        return lines

    def remove_data(self):
        try:
            sql = "DELETE FROM accountant_sales_percentage"
            self.env.cr.execute(sql)
        except Exception:
            pass

