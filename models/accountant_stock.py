from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, pycompat
from odoo.addons import decimal_precision as dp
import xlrd
import xlwt
import datetime


# class AccountantStock(models.Model):
#     _description = 'this is stock'
#     _name = 'accountant.stock'
#     name = fields.Char(string="报表名称", required=True)
#     startDate = fields.Date(string="开始期间", required=True)
#     endDate = fields.Date(string="结束期间", required=True)
#     fast_period = fields.Date(string="选取期间")
#     company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
#                                           string="Company Currency", readonly=True, store=True)
#     company_id = fields.Many2one('res.company', string='公司',
#                                  store=True, index=True, readonly=False, required=True)
#     line_ids = fields.One2many('accountant.stock.line', 'move_id', string='库存周转率',
#                                copy=True, readonly=True, ondelete="Cascade")
#
#     def _accountant_stock_category(self, product_c, product_category):
#         stock_s = sum(self.env['account.move.line'].search([('date', '<=', self.startDate),
#                                           ('account_id', '=', 15),
#                                           ('product_id', 'in', product_c),
#                                           ('company_id', '=', self.company_id.id)]).mapped('balance'))
#         stock_e = sum(self.env['account.move.line'].search([('date', '<=', self.endDate),
#                                           ('account_id', '=', 15),
#                                           ('product_id', 'in', product_c),
#                                           ('company_id', '=', self.company_id.id)]).mapped('balance'))
#         stock_cost = sum(self.env['account.move.line'].search([('date', '>=', self.startDate),
#                                           ('date', '<=', self.endDate),
#                                           ('account_id', '=', 67),
#                                           ('product_id', 'in', product_c),
#                                           ('company_id', '=', self.company_id.id)]).mapped('balance'))
#         if stock_cost and stock_e and stock_s:
#             stock_rate = stock_cost/((stock_s + stock_e)/2)
#         else:
#             stock_rate = None
#         values = {
#             'stock_s': stock_s,
#             'stock_e': stock_e,
#             'stock_cost': stock_cost,
#             'stock_rate': stock_rate,
#             'company_id': self.company_id.id,
#             'move_id': self.id,
#             'category': product_category
#         }
#         self.env['accountant.stock.line'].create(values)
#
#     def accountant_open_table(self):
#         if self.startDate > self.endDate:
#             raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
#         test = ['0']
#         category_for = self.env['product.category'].search([('name', 'not in', test)]).mapped('id')
#         for product in category_for:
#             product_c = self.env['product.template'].search([('categ_id', '=', product),
#                                                              ('company_id', '=', self.company_id.id)]).mapped('id')
#             product_category = self.env['product.category'].search([('id', '=', product)]).complete_name
#             self._accountant_stock_category(product_c, product_category)
#
#
# class AccountantStockLine(models.Model):
#     _description = 'this is stock line'
#     _name = 'accountant.stock.line'
#     move_id = fields.Many2one('accountant.stock', string='库存周转', ondelete="Cascade",
#                               help="The move of this entry line.", index=True, auto_join=True)
#     company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
#                                           string="Company Currency", store=True)
#     company_id = fields.Many2one('res.company', string='公司',
#                                  store=True, index=True, readonly=False)
#     category = fields.Char(string="产品分类", store=True, readonly=True)
#     stock_s = fields.Monetary(default=0.0, string="期初库存",
#                               store=True, currency_field='company_currency_id', readonly=True)
#     stock_e = fields.Monetary(default=0.0, string="期末库存",
#                               store=True, currency_field='company_currency_id', readonly=True)
#     stock_cost = fields.Monetary(default=0.0, string="出库成本",
#                                  store=True, currency_field='company_currency_id', readonly=True)
#     stock_rate = fields.Monetary(default=0.0, string="库存周转率",
#                                  store=True, currency_field='company_currency_id', readonly=True)
#
#     @api.model_create_multi
#     def create(self, values):
#         lines = super(AccountantStockLine, self).create(values)
#         return lines  #
# 上述是从account.move.line中按照分类查询库存周转率

#按分类库存周转率
class AccountantStockMove(models.Model):
    _description = 'this is stock move'
    _name = 'accountant.stock.move'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Datetime(string="开始期间", required=True)
    endDate = fields.Datetime(string="结束期间", required=True)
    fast_period = fields.Datetime(string="选取期间")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    line_ids = fields.One2many('accountant.stock.move.line', 'move_id', string='库存周转率',
                               copy=True, readonly=True, ondelete="Cascade")

    def _date_range(self, begindate, enddate):
        dates = []
        dt = datetime.datetime.strptime(begindate, "%Y-%m-%d")
        date = begindate[:]
        while date <= enddate:
            dates.append(date)
            dt = dt + datetime.timedelta(1)
            date = dt.strftime("%Y-%m-%d")
        return len(dates)

    def _accountant_stock_category(self, product_template, product_category):
        # product.product的id和product_tmpl_id不完全一致，有错位
        product_product = self.env['product.product'].search([('product_tmpl_id', 'in', product_template)]).mapped('id')

        location = self.env['stock.location'].search([('company_id', '=', self.company_id.id),
                                                              ('active', '=', True)]).mapped('id')

        start_s = sum(self.env['stock.move.line'].search([('date', '<=', self.startDate),
                                                                 ('location_id', 'in', location),
                                                                 ('product_id', 'in', product_product)]).mapped('qty_done'))

        start_e = sum(self.env['stock.move.line'].search([('date', '<=', self.startDate),
                                                                 ('location_dest_id', 'in', location),
                                                                 ('product_id', 'in', product_product)]).mapped('qty_done'))
        start = start_e - start_s

        end_s = sum(self.env['stock.move.line'].search([('date', '<=', self.endDate),
                                                                  ('location_id', 'in', location),
                                                                  ('product_id', 'in', product_product)]).mapped('qty_done'))

        end_e = sum(self.env['stock.move.line'].search([('date', '<=', self.endDate),
                                                                  ('location_dest_id', 'in', location),
                                                                  ('product_id', 'in', product_product)]).mapped('qty_done'))
        end = end_e - end_s

        # stock_cost = sum(self.env['account.move.line'].search([('date', '>=', self.startDate.date()),
        #                                   ('date', '<=', self.endDate.date()),
        #                                   ('account_id', '=', 67),
        #                                   ('product_id', 'in', product_product),
        #                                   ('company_id', '=', self.company_id.id)]).mapped('quantity'))
        # stock_cost = stock_cost * -1

        stock_cost_out = sum(self.env['stock.move.line'].search([('date', '>=', self.startDate),
                                                                 ('date', '<=', self.endDate),
                                                                 ('product_id', 'in', product_product),
                                                                 ('location_dest_id', '=', 9)]).mapped('qty_done'))

        stock_cost_in = sum(self.env['stock.move.line'].search([('date', '>=', self.startDate),
                                                                ('date', '<=', self.endDate),
                                                                ('product_id', 'in', product_product),
                                                                ('location_id', '=', 9)]).mapped('qty_done'))

        stock_cost = stock_cost_out - stock_cost_in

        # begindate = str(self.startDate.date())
        # enddate = str(self.endDate.date())
        # duration = self._date_range(begindate, enddate)

        if stock_cost:
            stock_rate = (start + end) * 0.5
            if stock_rate:
                stock_rate = (stock_cost/stock_rate) * 100
                # stock_rate = '%.2f' % stock_rate
                # stock_rate = str(stock_rate) + '%'
        else:
            stock_rate = None
        if stock_rate:
            values = {
                'stock_s': start,
                'stock_e': end,
                'stock_cost': stock_cost,
                'stock_rate': stock_rate,
                'company_id': self.company_id.id,
                'move_id': self.id,
                'category': product_category
            }
            self.env['accountant.stock.move.line'].create(values)

    def accountant_move_open_table(self):  # 按产品分类计算库存周转率
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
        category_for = self.env['product.category'].search([]).mapped('id')
        for product in category_for:
            product_template = self.env['product.template'].search([('categ_id', '=', product),
                                                             ('company_id', '=', self.company_id.id)]).mapped('id')
            product_category = self.env['product.category'].search([('id', '=', product)]).complete_name
            self._accountant_stock_category(product_template, product_category)

#按分类库存周转率明细
class AccountantStockMoveLine(models.Model):
    _description = 'this is stock move line'
    _name = 'accountant.stock.move.line'
    move_id = fields.Many2one('accountant.stock.move', string='库存周转', ondelete="Cascade",
                              help="The move of this entry line.", index=True, auto_join=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False)
    category = fields.Char(string="产品分类", store=True, readonly=True)
    stock_s = fields.Float(default=0.00, string="期初库存数量",
                           store=True, digits=(10, 2), readonly=True)
    stock_e = fields.Float(default=0.0, string="期末库存数量",
                           store=True, digits=(10, 2), readonly=True)
    stock_cost = fields.Float(default=0.0, string="出库数量",
                              store=True, digits=(10, 2), readonly=True)
    stock_rate = fields.Monetary(default=0.0, string="库存周转率(%)", currency_field='company_currency_id', readonly=True, store=True)

    @api.model_create_multi
    def create(self, values):
        lines = super(AccountantStockMoveLine, self).create(values)
        return lines
# 上述是从stock.move.line中按照分类查询库存周转率

## 按分类库存毛利率
class AccountantStockGross(models.Model):
    _description = 'this is stock gross'
    _name = 'accountant.stock.gross'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Date(string="开始期间", required=True)
    endDate = fields.Date(string="结束期间", required=True)
    fast_period = fields.Date(string="选取期间")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    line_ids = fields.One2many('accountant.stock.gross.line', 'move_id', string='库存周转率',
                               copy=True, readonly=True, ondelete="Cascade")

    def accountant_income_rate(self):  # 按产品分类计算分类毛利率
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
        category_for = self.env['product.category'].search([]).mapped('id')
        for product in category_for:
            product_template = self.env['product.template'].search([('categ_id', '=', product),
                                                             ('company_id', '=', self.company_id.id)]).mapped('id')
            product_category = self.env['product.category'].search([('id', '=', product)]).complete_name
            self._income_rate(product_template, product_category)

    def _income_rate(self, product_template, product_category):
        product_product = self.env['product.product'].search([('product_tmpl_id', 'in', product_template)]).mapped('id')

        income = sum(self.env['account.move.line'].search([('company_id', '=', self.company_id.id),
                                                             ('date', '>=', self.startDate),
                                                             ('date', '<=', self.endDate),
                                                             ('product_id', 'in', product_product),
                                                             ('account_id', '=', 62)]).mapped('balance'))
        income = income * -1

        cost = sum(self.env['account.move.line'].search([('company_id', '=', self.company_id.id),
                                                        ('date', '>=', self.startDate),
                                                        ('date', '<=', self.endDate),
                                                        ('product_id', 'in', product_product),
                                                        ('account_id', '=', 67)]).mapped('balance'))
        gross_profit = income - cost
        if gross_profit and income:
            gross_rate = (gross_profit/income) * 100
            # gross_rate = '%.2f' % gross_rate
        else:
            gross_rate = None
        if gross_rate:
            values = {
                'income': income,
                'cost': cost,
                'gross_profit': gross_profit,
                'gross_rate': gross_rate,
                'company_id': self.company_id.id,
                'move_id': self.id,
                'category': product_category
            }
            self.env['accountant.stock.gross.line'].create(values)

## 按分类库存毛利率明细
class AccountantStockGrossLine(models.Model):
    _description = 'this is stock gross line'
    _name = 'accountant.stock.gross.line'
    move_id = fields.Many2one('accountant.stock.gross', string='库存周转', ondelete="Cascade",
                              help="The move of this entry line.", index=True, auto_join=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False)
    category = fields.Char(string="产品分类", store=True, readonly=True)
    income = fields.Monetary(default=0.0, string="收入",
                             store=True, currency_field='company_currency_id', readonly=True)
    cost = fields.Monetary(default=0.0, string="成本",
                           store=True, currency_field='company_currency_id', readonly=True)
    gross_profit = fields.Monetary(default=0.0, string="毛利额",
                                   store=True, currency_field='company_currency_id', readonly=True)
    gross_rate = fields.Monetary(default=0.0, string="毛利率(%)", currency_field='company_currency_id', readonly=True, store=True)

    @api.model_create_multi
    def create(self, values):
        lines = super(AccountantStockGrossLine, self).create(values)
        return lines
# 上述是从stock.gross.line中按照分类查询毛利率

# 按品牌库存周转率
class AccountantStockBrand(models.Model):
    _description = 'this is stock brand'
    _name = 'accountant.stock.brand'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Datetime(string="开始期间", required=True)
    endDate = fields.Datetime(string="结束期间", required=True)
    fast_period = fields.Datetime(string="选取期间")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    line_ids = fields.One2many('accountant.stock.brand.line', 'move_id', string='库存周转率',
                               copy=True, readonly=True, ondelete="Cascade")

    def _accountant_stock_category(self, product_template, product_category):
        # product.product的id和product_tmpl_id不完全一致，有错位
        product_product = self.env['product.product'].search([('product_tmpl_id', 'in', product_template)]).mapped('id')

        location = self.env['stock.location'].search([('company_id', '=', self.company_id.id),
                                                              ('active', '=', True)]).mapped('id')

        start_s = sum(self.env['stock.move.line'].search([('date', '<=', self.startDate),
                                                                 ('location_id', 'in', location),
                                                                 ('product_id', 'in', product_product)]).mapped('qty_done'))

        start_e = sum(self.env['stock.move.line'].search([('date', '<=', self.startDate),
                                                                 ('location_dest_id', 'in', location),
                                                                 ('product_id', 'in', product_product)]).mapped('qty_done'))
        start = start_e - start_s

        end_s = sum(self.env['stock.move.line'].search([('date', '<=', self.endDate),
                                                                  ('location_id', 'in', location),
                                                                  ('product_id', 'in', product_product)]).mapped('qty_done'))

        end_e = sum(self.env['stock.move.line'].search([('date', '<=', self.endDate),
                                                                  ('location_dest_id', 'in', location),
                                                                  ('product_id', 'in', product_product)]).mapped('qty_done'))
        end = end_e - end_s

        # stock_cost = sum(self.env['account.move.line'].search([('date', '>=', self.startDate.date()),
        #                                   ('date', '<=', self.endDate.date()),
        #                                   ('account_id', '=', 67),
        #                                   ('product_id', 'in', product_product),
        #                                   ('company_id', '=', self.company_id.id)]).mapped('quantity'))
        # stock_cost = stock_cost * -1

        stock_cost_out = sum(self.env['stock.move.line'].search([('date', '>=', self.startDate),
                                           ('date', '<=', self.endDate),
                                           ('product_id', 'in', product_product),
                                           ('location_dest_id', '=', 9)]).mapped('qty_done'))

        stock_cost_in = sum(self.env['stock.move.line'].search([('date', '>=', self.startDate),
                                           ('date', '<=', self.endDate),
                                           ('product_id', 'in', product_product),
                                           ('location_id', '=', 9)]).mapped('qty_done'))

        stock_cost = stock_cost_out - stock_cost_in

        if stock_cost:
            stock_rate = (start + end) * 0.5
            if stock_rate:
                stock_rate = (stock_cost/stock_rate) * 100
                # stock_rate = '%.2f' % stock_rate
                # stock_rate = str(stock_rate) + '%'
        else:
            stock_rate = None
        if stock_rate:
            values = {
                'stock_s': start,
                'stock_e': end,
                'stock_cost': stock_cost,
                'stock_rate': stock_rate,
                'company_id': self.company_id.id,
                'move_id': self.id,
                'category': product_category
            }
            self.env['accountant.stock.brand.line'].create(values)

    def brand_open_table(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
        brand_for = [1, 5, 6, 9, 10, 78, 92, 96, 101, 104, 114, 115, 116, 120, 121,
                     126, 128, 129, 130, 131, 132, 137, 138, 149, 150]
        for brand in brand_for:
            category_for = self.env['product.category'].search(["|", ('parent_id', '=', brand),
                                                                ('id', '=', brand)]).mapped('id')
            product_c = self.env['product.template'].search([('categ_id', 'in', category_for),
                                                             ('company_id', '=', self.company_id.id)]).mapped('id')
            product_category = self.env['product.category'].search([('id', '=', brand)]).name
            self._accountant_stock_category(product_c, product_category)

# 按品牌库存周转率明细
class AccountantStockBrandLine(models.Model):
    _description = 'this is stock move brand'
    _name = 'accountant.stock.brand.line'
    move_id = fields.Many2one('accountant.stock.brand', string='库存周转', ondelete="Cascade",
                              help="The move of this entry line.", index=True, auto_join=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False)
    category = fields.Char(string="品牌", store=True, readonly=True)
    stock_s = fields.Float(default=0.00, string="期初库存数量",
                           store=True, digits=(10, 2), readonly=True)
    stock_e = fields.Float(default=0.0, string="期末库存数量",
                           store=True, digits=(10, 2), readonly=True)
    stock_cost = fields.Float(default=0.0, string="出库数量",
                              store=True, digits=(10, 2), readonly=True)
    stock_rate = fields.Monetary(default=0.0, string="库存周转率(%)",
                                   store=True, currency_field='company_currency_id', readonly=True)

    @api.model_create_multi
    def create(self, values):
        lines = super(AccountantStockBrandLine, self).create(values)
        return lines

#按品牌毛利率
class AccountantStockBrandGross(models.Model):
    _description = 'this is stock brand gross'
    _name = 'accountant.stock.brand.gross'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Date(string="开始期间", required=True)
    endDate = fields.Date(string="结束期间", required=True)
    fast_period = fields.Datetime(string="选取期间")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    line_ids = fields.One2many('accountant.stock.brand.gross.line', 'move_id', string='库存毛利率',
                               copy=True, readonly=True, ondelete="Cascade")

    def _accountant_stock_category(self, product_template, product_category):
        # product.product的id和product_tmpl_id不完全一致，有错位
        product_product = self.env['product.product'].search([('product_tmpl_id', 'in', product_template)]).mapped('id')

        income = sum(self.env['account.move.line'].search([('company_id', '=', self.company_id.id),
                                                           ('date', '>=', self.startDate),
                                                           ('date', '<=', self.endDate),
                                                           ('product_id', 'in', product_product),
                                                           ('account_id', '=', 62)]).mapped('balance'))
        income = income * -1

        cost = sum(self.env['account.move.line'].search([('company_id', '=', self.company_id.id),
                                                         ('date', '>=', self.startDate),
                                                         ('date', '<=', self.endDate),
                                                         ('product_id', 'in', product_product),
                                                         ('account_id', '=', 67)]).mapped('balance'))
        gross_profit = income - cost
        if gross_profit and income:
            gross_rate = (gross_profit / income) * 100
            # gross_rate = '%.2f' % gross_rate + "%"
        else:
            gross_rate = None
        if gross_rate:
            values = {
                'income': income,
                'cost': cost,
                'gross_profit': gross_profit,
                'gross_rate': gross_rate,
                'company_id': self.company_id.id,
                'move_id': self.id,
                'category': product_category
            }
            self.env['accountant.stock.brand.gross.line'].create(values)

    def brand_gross_open_table(self):
            if self.startDate > self.endDate:
                raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
            brand_for = [1, 5, 6, 9, 10, 78, 92, 96, 101, 104, 114, 115, 116, 120, 121,
                         126, 128, 129, 130, 131, 132, 137, 138, 149, 150]
            for brand in brand_for:
                category_for = self.env['product.category'].search(["|", ('parent_id', '=', brand),
                                                                    ('id', '=', brand)]).mapped('id')
                product_template = self.env['product.template'].search([('categ_id', 'in', category_for),
                                                                 ('company_id', '=', self.company_id.id)]).mapped('id')
                product_category = self.env['product.category'].search([('id', '=', brand)]).name
                self._accountant_stock_category(product_template, product_category)

#按品牌毛利率明细
class AccountantStockBrandGrossLine(models.Model):
    _description = 'this is stock move brand gross'
    _name = 'accountant.stock.brand.gross.line'
    move_id = fields.Many2one('accountant.stock.brand.gross', string='库存周转', ondelete="Cascade",
                              help="The move of this entry line.", index=True, auto_join=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False)
    category = fields.Char(string="品牌", store=True, readonly=True)
    income = fields.Monetary(default=0.0, string="收入",
                             store=True, currency_field='company_currency_id', readonly=True)
    cost = fields.Monetary(default=0.0, string="成本",
                           store=True, currency_field='company_currency_id', readonly=True)
    gross_profit = fields.Monetary(default=0.0, string="毛利额",
                                   store=True, currency_field='company_currency_id', readonly=True)
    gross_rate = fields.Monetary(default=0.0, string="毛利率(%)",
                                   store=True, currency_field='company_currency_id', readonly=True)

    @api.model_create_multi
    def create(self, values):
        lines = super(AccountantStockBrandGrossLine, self).create(values)
        return lines
