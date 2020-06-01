odoo.define("accountant.fast_picker", ['web.AbstractField', 'web.field_registry', 'web.time', 'accountant.period_tool'], function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    var time = require('web.time');
    var Perod_tool = require('accountant.period_tool');
    var ac_fast_picker = AbstractField.extend({
        supportedFieldTypes: ['date'],
        template: 'accountant.fast_picker',
        attributes: {
            style: "background-color:white;border: 1px solid grey;"
        },
        events: _.extend({}, AbstractField.prototype.events, {
            'click button': '_onClick',
        }),
        _onClick: function (e) {
            var self = this;
            var btn = $(e.target);
            var periodScop = self._getPeriod(btn.text());
            var startDate = $("[name='startDate'] input");
            var endDate = $("[name='endDate'] input");
            startDate.val(time.date_to_str(periodScop.startDate)).trigger('change');
            endDate.val(time.date_to_str(periodScop.endDate)).trigger('change');
        },
        _getPeriod: function (periodName) {
            var dt = new Date();
            var voucherPeriod = new Perod_tool.VoucherPeriod(dt);
            switch (periodName) {
                case '本月':
                    return voucherPeriod.getCurrentMonth();
                case '上月':
                    return voucherPeriod.getPreMonth();
                case '本年':
                    return voucherPeriod.getCurrentYear();
                case '去年':
                    return voucherPeriod.getPreYear();
                case '本季':
                    return voucherPeriod.getCurrentSeason();
                case '上季':
                    return voucherPeriod.getPreSeason();
                case '今年上半年':
                    return voucherPeriod.getFirstHalfYear()
                case '去年上半年':
                    return voucherPeriod.getFirstHalfPreYear();
                case '去年下半年':
                    return voucherPeriod.getSecondHalfPreYear()
                default:
                    return voucherPeriod.getCurrentMonth();

            };
        },
    });
    var fieldRegistry = require('web.field_registry');
    fieldRegistry.add('ac_fast_picker', ac_fast_picker);
    return {
        ac_fast_picker: ac_fast_picker,
    };

});
//期间处理工具
odoo.define('accountant.period_tool', function (require) {
    var Class = require('web.Class');
    //日期范围
    var PeriodScop = Class.extend({
        init: function (startDate, endDate) {
            this.startDate = startDate;
            this.endDate = endDate;
        },
    });
    // 一个会计期间（一个月）
    var VoucherPeriod = Class.extend({
        init: function (date) {
            this.date = date;
            this.year = date.getFullYear();
            this.month = date.getMonth() + 1;
            this.days = this.getDaysOf(this.year, this.month);
            this.firstDate = new Date(this.year, this.month - 1, 1)
            this.endDate = new Date(this.year, this.month - 1, this.days)
        },
        // 当月
        getCurrentMonth: function () {
            return new PeriodScop(this.firstDate, this.endDate);
        },
        // 上月
        getPreMonth: function () {
            var month = this.month - 1;
            var year = this.year;
            if (this.month == 1) {
                month = 12;
                year = year - 1;
            };
            var days = this.getDaysOf(year, month);
            var firstDate = new Date(year, month - 1, 1);
            var endDate = new Date(year, month - 1, days);
            return new PeriodScop(firstDate, endDate);
        },
        getCurrentYear: function () {
            var year = this.year
            var firstDate = new Date(year, 0, 1);
            var days = this.getDaysOf(year, 12);
            var endDate = new Date(year, 11, days);
            return new PeriodScop(firstDate, endDate);

        },
        getPreYear: function () {
            var year = this.year - 1
            var firstDate = new Date(year, 0, 1);
            var days = this.getDaysOf(year, 12);
            var endDate = new Date(year, 11, days);
            return new PeriodScop(firstDate, endDate);
        },
        // 本季
        getCurrentSeason: function () {
            var month = this.month;
            var year = this.year;
            var firstMonth = 10;
            var endMonth = 12;
            if (1 <= month && month <= 3) {
                firstMonth = 1;
                endMonth = 3;
            } else if (4 <= month && month <= 6) {
                firstMonth = 4;
                endMonth = 6;
            } else if (7 <= month && month <= 9) {
                firstMonth = 7;
                endMonth = 9;
            };
            var days = this.getDaysOf(year, endMonth)
            var firstDate = new Date(year, firstMonth - 1, 1);
            var endDate = new Date(year, endMonth - 1, days);
            return new PeriodScop(firstDate, endDate);

        },
        //上季
        getPreSeason: function () {
            var month = this.month;
            var year = this.year;
            var firstMonth = 10;
            var endMonth = 12;
            if (1 <= month && month <= 3) {
                year = this.year - 1
            } else if (4 <= month && month <= 6) {
                firstMonth = 1;
                endMonth = 3;
            } else if (7 <= month && month <= 9) {
                firstMonth = 4;
                endMonth = 6;
             } else if (10 <= month && month <= 12) {
                firstMonth = 7;
                endMonth = 9;
            };
            var days = this.getDaysOf(year, endMonth)
            var firstDate = new Date(year, firstMonth - 1, 1);
            var endDate = new Date(year, endMonth - 1, days);
            return new PeriodScop(firstDate, endDate);
        },
        // 上半年
        getFirstHalfYear: function () {
            var year = this.year
            var firstDate = new Date(year, 0, 1);
            var days = this.getDaysOf(year, 6);
            var endDate = new Date(year, 5, days);
            return new PeriodScop(firstDate, endDate);
        },
        getFirstHalfPreYear: function () {
            var year = this.year - 1
            var firstDate = new Date(year, 0, 1);
            var days = this.getDaysOf(year, 6);
            var endDate = new Date(year, 5, days);
            return new PeriodScop(firstDate, endDate);
        },
        getSecondHalfPreYear: function () {
            var year = this.year - 1
            var firstDate = new Date(year, 6, 1);
            var days = this.getDaysOf(year + 1, 0);
            var endDate = new Date(year, 11, days);
            return new PeriodScop(firstDate, endDate);
        },
        getDaysOf: function (year, month) {
            if (month == 12) {
                year = year + 1;
                month = 0;
            }
            return (new Date(year, month, 0)).getDate();
        },
    });




    return {
        'VoucherPeriod': VoucherPeriod,
        'PeriodScop': PeriodScop,
    };
});