# -*- coding: utf-8 -*-
{
    'name': "accountant",

    'summary': """
    会计报表
    """,

    'description': """
        管理财务和分析会计
    """,

    'author': "aaron",
    'website': "http://www.nudepig.cn",
    'application': True,
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'accountant',
    'version': '0.2',
    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'account'],
    'images': ['static/description/icon.png'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/accountant_move_line_view.xml',
        'views/assetsAdd_templates.xml',

        'views/accountant_menuitem.xml',
        'views/accountant_overview.xml',
        'views/accountant_profit.xml',
        'views/accountant_profit_team.xml',
        'views/accountant_profit_sales.xml',

        'views/accountant_sun.xml',
        'views/accountant_assets.xml',
        'views/accountant_cash.xml',
        'views/accountant_stock_move.xml',
        'views/accountant_stock_brand.xml',
        'views/accountant_stock_gross_rate.xml',
        'views/accountant_stock_brand_rate.xml',

        'views/accountant_statement_customer.xml',
        'views/accountant_invoice_statement.xml',
        'views/accountant_sales_percentage.xml',
        'views/accountant_set_profit.xml',

        'report/accountant_profit_report.xml',
        'report/accountant_balance_report.xml',
        'report/accountant_cash_report.xml',
        'report/accountant_stock_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/accountant_overview.xml',
    ],
    'css': [
        'static/css/accountant.css',
        'static/css/jexcel.css',
        'static/css/jsuites.css',
        'static/css/bootstrap-grid.css',
        'static/css/bootstrap-grid.min.css',
        'static/css/bootstrap-reboot.css',
        'static/css/bootstrap-reboot.min.css',
        'static/css/bootstrap.css',
        'static/css/bootstrap.min.css',
        'static/css/style.css',


    ],
    'qweb': [
        'views/btn_templates.xml',
    ],
}
