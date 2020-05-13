// 凭证借贷方金额
odoo.define('accountant.accountantListRenderer', function (require) {
    "use strict";
    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        events: _.extend({}, ListRenderer.prototype.events, {
            'change table td.voucher_d_amount': '_entryamountChange',
            'change table td.voucher_c_amount': '_entryamountChange',
        }),
        _entryamountChange: function (event) {
            // table td.voucher_c_amount 的元素改变事件处理
        },
        init: function (parent, state, params) {
            var self = this;
            this._super.apply(this, arguments);
        },
        _renderBodyCell: function (record, node, colIndex, options) {
            var self = this;
            var newTd = this._super.apply(this, arguments);
            // 如果给字段添加了class="amountColor"属性,那么这个字段为金额字段显示的值改变颜色
            var name = node.attrs.name;
            var amount = record.data[name];
            if (_hasClass(newTd, 'amountColor')) {
                _changeNodeColor(newTd, amount);
            };
            return newTd;
        }
    });
    //改变金额节点颜色
    function _changeNodeColor(node, amount) {
        switch (true) {
            case (amount - 0 > 0):
                break;
            case (amount - 0 == 0):
                node.addClass('amount-zero');
                // css定义在 server\addons\accountant\static\css\accountant.css
                break;
            case (amount - 0 < 0):
                node.addClass('amount-negative');
                break;
            default:
                break;
        }
        return node;
    };

    //含有类
    function _hasClass(td, className) {
        if (td.hasClass(className)) {
            return true;
        };
        return false;
    };
    return ListRenderer;
});
//凭证的核算项目字段,自动继承摘要，借贷自动平衡等
odoo.define('web.accountantExtend', ['web.basic_fields', 'web.relational_fields', 'accountant.accountantVoucher', 'web.field_registry'], function (require) {
    "use strict";
    var relational_fields = require('web.relational_fields');
    var fieldMany2ManyTags = relational_fields.FieldMany2ManyTags;
    var accountantVoucher = require('accountant.accountantVoucher');
    var FieldChar = require('web.basic_fields').FieldChar;
    var tiger_accountItems_m2m = fieldMany2ManyTags.extend({

        activate: function () {
            return this.choiceItemsModel ? this.choiceItemsModel.activate() : false;
        },
        getFocusableElement: function () {
            return this.choiceItemsModel ? this.choiceItemsModel.getFocusableElement() : $();
        },

        /**
         * @private
         */
        _renderEdit: function () {
            var self = this;
            var newAccountId = 0;
            var preAccountId = 0;
            if (this.record.data.account && this.record.data.account.data.id) {
                newAccountId = this.record.data.account.data.id;
            };
            if (this.choiceItemsModel) {
                preAccountId = this.choiceItemsModel.ac_accountId;
                if (preAccountId == newAccountId) {
                    return;
                }
                this.choiceItemsModel.destroy();
            };
            this.choiceItemsModel = new accountantVoucher.choiceItemsModel(this, this.name, this.record, {
                mode: 'edit',
                noOpen: true,
                viewType: this.viewType,
                attrs: this.attrs,
            }, newAccountId);
            this.choiceItemsModel.value = false;
            return this.choiceItemsModel.appendTo(this.$el);
        },
        willStart: function () {
            return this._super.apply(this, arguments);
        },
        _onFieldChanged: function (ev) {
            if ($.inArray(ev.target, this.choiceItemsModel.ac_choiceItemsMany2ones) == -1) {
                return;
            };
            ev.stopPropagation();
            var newValue = ev.data.changes[this.name];
            if (newValue) {
                //改变了核算项目,例如:以前是A,现在选择了B
                this._addTag(newValue);
                var id = ev.target.ac_itemId;
                if (id && id > 0 && id != newValue.id) {
                    this._removeTag(id);
                }

                ev.target.ac_itemId = newValue.id;
                ev.target.ac_itemName = newValue.display_name;
                //重要覆写
                ev.stopPropagation();
                return;
            };
            //没有选择,或删除了核算项目,以前是A现在删除了A,没有选择其他的
            if (ev.target.ac_itemId) {
                this._removeTag(ev.target.ac_itemId);
            }
            ev.target.ac_itemId = null;
            ev.target.ac_itemName = null;

            //重要覆写
            ev.stopPropagation();
        },

    });
    var FieldChar_voucher_explain = FieldChar.extend({
        events: _.extend({}, FieldChar.prototype.events, {
            'focusin': '_onBlur',
        }),
        // 分录说明获得焦点时触发
        _onBlur: function (e) {
            var self = $(e.target)
            var self_tr = self.parentsUntil('tr').parent('tr')
            var pr_tr = self_tr.prev('tr');
            var explain = self.val();
            if ($.trim(explain) == '') {
                this._autoExplain(self, pr_tr);
            };
            this._autoBalance(self_tr);
        },
        // 自动继承上条分录说明
        _autoExplain: function (self, pr_tr) {
            var pr_explain = pr_tr.find('span.oe_ac_explain');
            self.val(pr_explain.text());
            self.trigger('input');
        },
        // 借贷自动平衡
        _autoBalance: function (self_tr) {
            var damount_input = self_tr.find("[name='damount']").find("input");
            var camount_input = self_tr.find("[name='camount']").find("input");
            // var dsum = $("[title='ac_dsum']");
            // var csum = $("[title='ac_csum']");
            var amount = $("[name='sum_amount']span").text().replace(/,/gi, '');
            // var amount = dsum.text().replace(/,/gi, '') - csum.text().replace(/,/gi, '');
            var old_amount = damount_input.val().replace(/,/gi, '') - camount_input.val().replace(/,/gi, '');
            if (old_amount == 0) {
                if (amount > 0) {
                    camount_input.val(amount);
                    camount_input.trigger('input');
                } else if (amount < 0) {
                    damount_input.val(-amount);
                    damount_input.trigger('input');
                };
            };

        },
    });

    var FieldMany2ManyCheckBoxes = relational_fields.FieldMany2ManyCheckBoxes;
    var FieldMany2ManyCheckBoxes_flowToLeft = FieldMany2ManyCheckBoxes.extend({


        template: 'FieldMany2ManyCheckBoxes_flowToLeft',
    });
    var fieldRegistry = require('web.field_registry');
    fieldRegistry.add('tiger_accountItems_m2m', tiger_accountItems_m2m);
    // 继承many2many_checkboxes向左浮动
    fieldRegistry.add('many2many_checkboxes_floatleft', FieldMany2ManyCheckBoxes_flowToLeft);
    fieldRegistry.add('FieldChar_voucher_explain', FieldChar_voucher_explain);

    return {
        tiger_accountItems_m2m: tiger_accountItems_m2m,
        fieldMany2ManyCheckBoxes_flowToLeft: FieldMany2ManyCheckBoxes_flowToLeft,
        FieldChar_voucher_explain: FieldChar_voucher_explain,
    };
});
//凭证的核算项目字段选择
odoo.define('accountant.accountantVoucher', ['web.AbstractField', 'web.relational_fields', 'web.field_registry', 'web.core', 'web.field_utils'], function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    var relational_fields = require('web.relational_fields');
    var FieldMany2One = relational_fields.FieldMany2One;
    var core = require('web.core');
    var qweb = core.qweb;
    var field_utils = require('web.field_utils');
    var _t = core._t;
    var ChoiceItemsMany2one = FieldMany2One.extend({
        events: _.extend({}, FieldMany2One.prototype.events, {
            'blur input': '_onBlur',
            'keydown input': '_onKeydown',

        }),
        _onBlur: function (e) {},

        /**输入时按tab键,跳到下一个项目
         * @param  {} e
         */
        _onKeydown: function (e) {
            self = this;
            e.stopImmediatePropagation();
            switch (e.which) {
                case $.ui.keyCode.TAB:
                    $('.itemChoice').nextUntil('.o_input').first().focus();
                    break;
                default:
                    self._super.apply(self, arguments);
            }
        },
        init: function (parent, name, record, options, typeId, itemName, itemId) {
            this.ac_itemTypeId = typeId;
            this.ac_itemName = itemName;
            this.ac_itemId = itemId;
            // this.ac_valueItemId = itemId;
            this.ac_newItemName = itemName;
            this.ac_newItemId = itemId;
            this.ac_lastSetValueItemId = undefined;
            this._super.apply(this, arguments);
            if (itemName) {
                this.m2o_value = itemName;
            } else {
                this.m2o_value = "";
            };

        },
        start: function () {
            this._super.apply(this, arguments);

        },
        _formatValue: function (value) {

            if (this.ac_itemName) {
                return this.ac_itemName;
            };
            return "";

        },
        _search: function (search_val) {
            var self = this;
            var def = $.Deferred();
            this.orderer.add(def);
            var context = this.record.getContext(this.recordParams);
            var domain = this.record.getDomain(this.recordParams);
            _.extend(context, this.additionalContext);

            var blacklisted_ids = this._getSearchBlacklist();
            if (blacklisted_ids.length > 0) {
                // domain.push(['id', 'not in', blacklisted_ids]);

            }
            //使核算项目下拉列表只选择对应类别
            domain.push(['itemClass', '=', this.ac_itemTypeId]);
            this._rpc({
                    model: this.field.relation,
                    method: "name_search",
                    kwargs: {
                        name: search_val,
                        args: domain,
                        operator: "ilike",
                        limit: this.limit + 1,
                        context: context,
                    }
                })
                .then(function (result) {
                    var values = _.map(result, function (x) {
                        x[1] = self._getDisplayName(x[1]);
                        return {
                            label: _.str.escapeHTML(x[1].trim()) || data.noDisplayContent,
                            value: x[1],
                            name: x[1],
                            id: x[0],
                        };
                    });

                    // search more... if more results than limit
                    if (values.length > self.limit) {
                        values = values.slice(0, self.limit);
                        values.push({
                            label: _t("Search More..."),
                            action: function () {
                                self._rpc({
                                        model: self.field.relation,
                                        method: 'name_search',
                                        kwargs: {
                                            name: search_val,
                                            args: domain,
                                            operator: "ilike",
                                            limit: 160,
                                            context: context,
                                        },
                                    })
                                    .then(self._searchCreatePopup.bind(self, "search"));
                            },
                            classname: 'o_m2o_dropdown_option',
                        });
                    }
                    var create_enabled = self.can_create && !self.nodeOptions.no_create;
                    // quick create
                    var raw_result = _.map(result, function (x) {
                        return x[1];
                    });
                    if (create_enabled && !self.nodeOptions.no_quick_create &&
                        search_val.length > 0 && !_.contains(raw_result, search_val)) {
                        values.push({
                            label: _.str.sprintf(_t('Create "<strong>%s</strong>"'),
                                $('<span />').text(search_val).html()),
                            action: self._quickCreate.bind(self, search_val),
                            classname: 'o_m2o_dropdown_option'
                        });
                    }
                    // create and edit ...
                    if (create_enabled && !self.nodeOptions.no_create_edit) {
                        var createAndEditAction = function () {
                            // Clear the value in case the user clicks on discard
                            self.$('input').val('');
                            return self._searchCreatePopup("form", false, self._createContext(search_val));
                        };
                        values.push({
                            label: _t("Create and Edit..."),
                            action: createAndEditAction,
                            classname: 'o_m2o_dropdown_option',
                        });
                    } else if (values.length === 0) {
                        values.push({
                            label: _t("No results to show..."),
                        });
                    }

                    def.resolve(values);
                });

            return def;
        },

        _onFieldChanged: function (event) {
            this.lastChangeEvent = event; //test
            var newItem = event.data.changes.items;
            this.ac_newItemName = newItem.display_name;
            this.ac_newItemId = newItem.id;
            this.$input.val(this.ac_newItemName);
        },

    });
    var choiceItemsModel = AbstractField.extend({
        //凭证中的选择核算项目
        supportedFieldTypes: ['many2many'],
        template: 'accountant_voucher_choice_items',

        custom_events: _.extend({}, AbstractField.prototype.custom_events, {

        }),
        events: _.extend({}, AbstractField.prototype.events, {

        }),

        init: function (parent, name, record, options, accountId) {
            this._super.apply(this, arguments);
            this.limit = 8;
            this.ac_items = []; //分录已有的核算项目
            this.ac_accountId = accountId;
            this.ac_choiceItemsMany2ones = [];
        },


        /**
         * 加载和设置分录核算项目
         * @returns {Deferred}
         */
        _initItems: function () {
            var self = this;
            return $.when(this._getEntryItems()).then(function (items) {
                self.ac_items = items;
            });
        },
        start: function () {
            var self = this;
            self.itemChoiceContainer = this.$el;
            return this._super.apply(this, arguments);

        },

        reinitialize: function (value) {
            this.isDirty = false;
            this.floating = false;
            return this._setValue(value);
        },
        /**获得对应核算项目类别的核算项目
         * @return {string} 项目名称
         */
        _getItem: function (items, typeId) {
            var item = {};
            $.each(items, function (i, n) {
                if (items[i].itemClass == typeId) {
                    item.name = items[i].name;
                    item.id = items[i].id;
                    return false;
                };
            });
            return item;
        },
        /**核算项目栏插入一个many2one部件
         * @param  {object} itemType 核算项目对象
         * @param  {object} container 凭证分录中的核算项目栏
         */
        _insertItemChoice: function (itemType, container) {
            var self = this;
            var typeName = itemType.name;
            var typeId = 'itemType_' + itemType.id;
            var attrs = this.attrs;
            var item = self._getItem(self.ac_items, itemType.id);

            var oneItemChoice = new ChoiceItemsMany2one(self, self.name, self.record, {
                mode: 'edit',
                noOpen: true,
                viewType: self.viewType,
                attrs: attrs,
            }, itemType.id, item.name, item.id);

            var itemsIds = $.map(self.ac_items, function (i) {
                return i.id;
            });
            oneItemChoice._getSearchBlacklist = function () {
                return itemsIds || [];
            };
            var itemRow = $(self._createItemChoiceHtml(typeName));
            itemRow.appendTo(container);
            var seletiontag = itemRow.find('.ac-item-selection').first();
            oneItemChoice.appendTo(seletiontag);
            self.ac_choiceItemsMany2ones.push(oneItemChoice);
            oneItemChoice.$el.find('input').attr('id', typeId);
        },
        /**获取科目下挂的核算项目类别
         * @param  {integer} accountId 科目ID
         * @returns {object} 核算项目类别列表[{'id':,'name':}]
         */
        _getItemTypes: function (accountId) {
            return this._rpc({
                model: 'accountant.account',
                method: 'get_itemClasses',
                args: [accountId]
            });

        },
        /**构建核算项目类别标签
         * @param  {string} itemTypeName 核算项目类别名称
         */
        _createItemChoiceHtml: function (itemTypeName) {
            var htmlstr = "<div class='row itemChoice'><div class='col-3 ac-item-type-name'>" + itemTypeName + "</div><div class='ac-item-selection'></div></div>";
            return htmlstr;
        },
        _removeTag: function (id) {
            var record = _.findWhere(this.value.data, {
                res_id: id
            });
            this._setValue({
                operation: 'FORGET',
                ids: [record.id],
            });
        },
        _renderEdit: function () {
            var self = this;
            $.each(self.itemTypes, function (i) {
                self._insertItemChoice(self.itemTypes[i], self.itemChoiceContainer);
            });
        },
        willStart: function () {
            var self = this;
            var def1 = self._super.apply(this, arguments);
            var def2 = self._getItemTypes(self.record.data.account.res_id);
            var def3 = def2.then(function (param) {
                self.itemTypes = param;
            });
            var def4 = self._initItems();
            return $.when(def1, def2, def3, def4);
        },
        _getRenderTagsContext: function () {
            return {
                itemTypes: this.itemTypes,
            };
        },
        /**获得分录的核算项目列表
         * @param  {integer} entryId 分录ID
         * @return {obj} 核算项目列表{id:,name:,itemClass:}
         */
        _getEntryItems: function () {
            var entryId = this.record.data.items.res_ids;
            return this._rpc({
                model: 'accountant.item',
                method: 'getEntryItems',
                args: [entryId]
            });
        },
        getFocusableElement: function () {
            return this.mode === 'edit' && this.$('input').first() || this.$el;
        },
    });
    var fieldRegistry = require('web.field_registry');
    fieldRegistry.add('choiceItemsModel', choiceItemsModel);
    return {
        ChoiceItemsMany2one: ChoiceItemsMany2one,
        choiceItemsModel: choiceItemsModel,

    }
});
//给凭证列表视图添加按钮
odoo.define('accountant.accountantVoucheListButton', function (require) {
    "use strict";
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var ListController = require('web.ListController');
    var voucherListController = ListController.extend({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var btns = this.$buttons;
                var ac_voucher_number_sort_btn = btns.find('.ac_voucher_number_sort'); //凭证编号排序按钮
                ac_voucher_number_sort_btn.on('click', this.proxy('vouchersSortByNumber'));
                var ac_voucher_filter_btn = btns.find('.ac_voucher_filter'); //查询按钮
                ac_voucher_filter_btn.on('click', this.proxy('voucher_filter'));
            };
        },
        /**依据凭证编号对凭证列表进行排序
         */
        vouchersSortByNumber: function () {
            var tbody = this.$el.find('tbody').first();
            var trs = this.$el.find('tr.o_data_row');
            trs.detach();
            trs.sort(this._voucherNumbersort);
            tbody.append(trs);

        },
        _voucherNumbersort: function (a, b) {
            return $(a).find('.voucherNumber').text() - $(b).find('.voucherNumber').text();
        },
        //查询凭证
        voucher_filter: function () {
            alert('暂未实现');
        },
    });
    var voucherListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: voucherListController,
        }),
    });
    viewRegistry.add('voucherListView', voucherListView);
    return voucherListView;
});
//启用期初列表视图
odoo.define('accountant.balanceListView', function (require) {
    "use strict";
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var ListController = require('web.ListController');
    var CheckBalance = require('accountant.begin_balance_check');
    var balanceListController = ListController.extend({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var btns = this.$buttons;
                var check_balance_btn = new CheckBalance(this);
                check_balance_btn.appendTo(btns);
            };
        },

    });
    var balanceListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: balanceListController,
        }),
    });
    viewRegistry.add('balanceListView', balanceListView);
    return balanceListView;
});
//启用期初平衡检查按钮
odoo.define("accountant.begin_balance_check", function (require) {
    "use strict";
    var Widget = require('web.Widget');
    var framework = require('web.framework');
    var CheckBalance = Widget.extend({
        template: 'accountant.check_balance',
        events: {
            'click': '_do_check',
        },
        _do_check: function () {
            var self = this;
            this.do_action({
                name: '启用期初平衡检查',
                type: 'ir.actions.act_window',
                res_model: 'accountant.begin_balance_check',
                views: [
                    [false, 'form']
                ],
                target: 'new'
            });
            // framework.blockUI();
            // alert('开始试算平衡');
            // this._rpc({
            //     model: 'accountant.account',
            //     method: 'get_itemClasses',
            //     args: [176],
            // }).then(function (items) {
            //     // _.map(items,function(){
            //     //     s=s+self.name;
            //     //   });

            //     console.log('over!');
            //     setTimeout(function () {
            //         framework.unblockUI();
            //         self.do_notify('结果', '该功能还在开发中!');
            //     }, 5000);

            // }, function () {
            //     console.log('error!');
            //     FrameWork.unbolckUI();
            // });
        },

    });
    return CheckBalance;
});
// 快速选取期间
odoo.define("accountant.el_period", ['web.AbstractField', 'web.field_registry', 'web.time', 'accountant.period_tool'], function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    var ac_el_period = AbstractField.extend({
        supportedFieldTypes: ['date'],
        template: 'accountant.el_period',
        attributes: {
            style: "background-color:white;border: 1px solid grey;"
        },
    });
    var fieldRegistry = require('web.field_registry');
    fieldRegistry.add('ac_el_period', ac_el_period);
    return {
        ac_el_period: ac_el_period,
    };
});












odoo.define("accountant.fast_period", ['web.AbstractField', 'web.field_registry', 'web.time', 'accountant.period_tool'], function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    var time = require('web.time');
    var Perod_tool = require('accountant.period_tool');
    var ac_fast_period = AbstractField.extend({
        supportedFieldTypes: ['date'],
        template: 'accountant.fast_period',
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
    fieldRegistry.add('ac_fast_period', ac_fast_period);
    return {
        ac_fast_period: ac_fast_period,
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
            } else if (4 <= month && month < 6) {
                firstMonth = 4;
                endMonth = 6;
            } else if (7 <= month && month <= 9) {
                firstMonth = 7;
                endMonth = 9;
            };
            var days = this.getDaysOf(year, month)
            var firstDate = new Date(year, firstMonth - 1, 1);
            var endDate = new Date(year, endMonth - 1, days);
            return new PeriodScop(firstDate, endDate);

        },
        getPreSeason: function () {
            var month = this.month;
            var year = this.year;
            var firstMonth = 10;
            var endMonth = 12;
            if (1 <= month && month <= 3) {
                year = this.year - 1
            } else if (4 <= month && month < 6) {
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
    //连续的会计期间
    var Period = Class.extend({
        init: function (startDate, endDate) {
            this.startDate = startDate;
            this.endDate = endDate;
            this.startYear = startDate.getFullYear();
            this.startMonth = startDate.getMonth() + 1;
            this.endYear = endDate.getFullYear();
            this.endMonth = endDate.getMonth();

        },
        getPeriodList: function () {

        }

    });

    return {
        'VoucherPeriod': VoucherPeriod,
        'PeriodScop': PeriodScop,
        'Period': Period,
    };
});
// 自定义按钮
odoo.define('accountant.btn', ['web.AbstractField', 'web.field_registry'], function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    // 点击按钮触发后台@api.onchage('本字段')装饰的方法
    var opetions = {
        forceChange: true
    };
    var ac_btn_trigger_onchange = AbstractField.extend({
        events: _.extend({
            'click': '_btn_click',

        }, AbstractField.prototype.events, {}),
        supportedFieldTypes: ['char'],
        template: 'accountcor.ac_btn',
        start: function () {
            this.$el.find('span').text(this.string);
            this.$el.addClass(this.attrs.class);
            this._super.apply(this, arguments);
        },
        _btn_click: function () {

            // 确保每次点击值都改变以触发onchange
            // if(this.lastSetValue=='1'){
            //     this._setValue('0');
            //     return;
            // }
            this._setValue('1', opetions);
        },
    });
    var fieldRegistry = require('web.field_registry');
    fieldRegistry.add('ac_btn_trigger_onchange', ac_btn_trigger_onchange);
    return {
        ac_btn_trigger_onchange: ac_btn_trigger_onchange,
    };
});
// 报表设计器相关
odoo.define('accountant.myjexcel', ['web.AbstractField', 'web.field_registry', 'accountant.jexcel', 'accountant.jsuites', 'web.core', 'web.AbstractAction', 'web.session'], function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    var jexcel = require('accountant.jexcel');
    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');
    // var Session = require('web.session');
    // 公式类
    class ACFormula {
        constructor(cellstr) {
            if (!cellstr) {
                throw Error("公式错误,没有内容");
            }
            if (cellstr.charAt(0) != '=') {
                throw Error("公式错误，没有以=开头");
            }
            if (cellstr.slice(-2) != '")') {
                throw Error("公式错误，没有以\")结尾");
            }
            this.str = cellstr;
            this.index1 = this.str.indexOf('("');
            if (this.index1 == -1) {
                throw Error("公式错误，没有'(\"'");
            }
            this.index2 = this.str.lastIndexOf('")');
        }
        /**
         * 公式名称
         */
        name() {
            var name = this.str.slice(1, this.index1);
            if (name.length == 0) {
                throw Error("公式错误，在'=' 和'(\"='之间没有公式名称");
            }
            return name;
        }
        /**
         * 公式内容
         */
        value() {
            return this.str.slice(this.index1 + 2, -2);
        }
    }
    // 表格设计器表格的数据字段小部件
    var ac_jexcel = AbstractField.extend({
        events: _.extend({
            '.jexcel td click': '_do_check',

        }, AbstractField.prototype.events, {}),
        supportedFieldTypes: ['text'],
        template: 'ac_jexcel',
        // 选中的单元格
        selection_x1: 0,
        selection_y1: 0,
        selection_x2: 0,
        //右下角单元格
        selection_y2: 0,
        // 左上角单元格
        cellName_ul: "A1",
        cellName_lr: "A1",
        startDate: '',
        endDate: '',
        orgIds: '',
        _do_check: function () {
            alert('check');
            var cellName = jexcel.getColumnNameFromId([this.selection_x1, this.selection_y1]);
            alert(JSON.stringify(this.jexcel_obj.getMeta(cellName)));
            alert(JSON.stringify(this.jexcel_obj.getMeta(cellName, "ac")));
        },
        start: function () {
            core.bus.on('ac_jexcel_set_formula', this, this._onSet_formula);
            return this._super.apply(this, arguments);
        },
        /**
         * 获得供报表的公式计算的开始期间参数
         */
        _getStartDate: function () {
            var startDate = $("[name='startDate'] input").val()
            // 非编辑状态下取数
            if (!startDate) {
                startDate = $("[name='startDate']").text()
            }
            return this._changeDateStr(startDate);
        },
        /**
         * 获得供报表的公式计算的结束期间参数
         */
        _getEndDate: function () {
            var endDate = $("[name='endDate'] input").val()
            if (!endDate) {
                endDate = $("[name='endDate']").text()
            }
            return this._changeDateStr(endDate);
        },
        /**
         * 获得供报表公式计算的机构范围参数
         */
        _getOrgIds: function () {
            var ids = _.map($(".ac_choice_orgs").find('input:checked'), function (input) {
                return $(input).data("record-id");
            });
            return ids.join('/');
        },
        // 设置公式
        _onSet_formula: function (v) {
            var formula = "";
            if (v) {
                var formula = '=ac("' + v + '")';
            };
            var cellName = jexcel.getColumnNameFromId([this.selection_x1, this.selection_y1]);
            this.jexcel_obj.setMeta(cellName, 'ac', formula);
            this.jexcel_obj.setValueFromCoords(this.selection_x1, this.selection_y1, formula);
            this.jexcel_obj.updateSelectionFromCoords(this.selection_x1, this.selection_y1, this.selection_x1, this.selection_y1);
        },
        //判断是不是公式，"="开头
        _isACFormula: function (str) {
            if (!str) {
                return false;
            }
            if (str.slice(0, 3) == '=ac') {
                return true;
            }

        },
        // 触发更新表格单元格数据，样式和批注
        _changeStyleAndData: function (instance) {
            if (this.mode != 'edit') {
                return;
            }
            this._setValue(JSON.stringify(instance.jexcel.getData()));
            core.bus.trigger('ac_jexcel_style_change', instance.jexcel.getStyle());
            core.bus.trigger('ac_jexcel_merge_change', instance.jexcel.getMerge());
            core.bus.trigger('ac_jexcel_width_change', self._getWidths(instance));
            core.bus.trigger('ac_jexcel_height_change', self._getHeights(instance));
            core.bus.trigger('ac_jexcel_comments_change', this._getComments(instance));
            core.bus.trigger('ac_jexcel_meta_change', self._getMetas(instance));
        },
        // 获得表格批注信息
        _getComments: function (instance) {
            return self._getAllCellsInfo(instance.jexcel, 'getComments')
        },
        _getFomulas: function (jexcel) {

        },

        /**
         * @description 获得表格各列宽
         * @param  {} instance
         */
        _getWidths: function (instance) {
            var values = {};
            var je = instance.jexcel
            var length = je.colgroup.length;
            var widths = je["getWidth"]();
            for (var l = 0; l < length; l++) {
                values[l] = widths[l];
            };
            return values;
        },
        /**
         * @description 获得表格各行高
         * @param  {} instance
         */
        _getHeights: function (instance) {
            var values = {};
            var je = instance.jexcel
            var length = je.rows.length;
            var heights = je["getHeight"]();
            for (var l = 0; l < length; l++) {
                if (heights[l] > 0) {
                    values[l] = heights[l]
                } else {
                    values[l] = je.options.defaultRowsHeight;
                };
            };
            return values;
        },
        /**
         * @description 获得表格单元格的meta数据，公式等
         * @param  {} instance
         */
        _getMetas: function (instance) {
            var values = {};
            var je = instance.jexcel
            var rowsCount = je.rows.length;
            var colsCount = je.colgroup.length;
            var callName;
            for (var y = 0; y < rowsCount; y++) {
                for (var x = 0; x < colsCount; x++) {
                    callName = jexcel.getColumnNameFromId([x, y]);
                    if (je.getMeta(callName)) {
                        values[callName] = je.getMeta(callName);
                    }
                }
            };
            return values;
        },
        /**
         * @description 获得表格全部单元的指定信息，如批注，公式等
         * @param  {} jexcel
         * @param  {} fncName
         */
        _getAllCellsInfo: function (instance, fncName) {
            var values = {};
            var x = instance.rows.length;
            var y = instance.colgroup.length;
            var v;
            for (var j = 0; j < y; j++) {
                for (var i = 0; i < x; i++) {
                    v = instance[fncName]([j, i]);
                    if (v.length > 0) {
                        var cellName = jexcel.getColumnNameFromId([j, i]);
                        values[cellName] = v;
                    }
                };
            };
            return values;
        },
        /**
         * @description 更新选中单元格的字符串格式，如"A1"
         * @param  {} x1 左上角x坐标               
         * @param  {} y1 左上角y坐标
         * @param  {} x2 右下角x坐标
         * @param  {} y2 右下角y坐标
         */
        _setSelectionCells: function (x1, y1, x2, y2) {
            self.selection_x1 = x1;
            self.selection_y1 = y1;
            self.selection_x2 = x2;
            self.selection_y2 = y2;
            self.cellName_ul = jexcel.getColumnNameFromId([x1, y1]);
            self.cellName_lr = jexcel.getColumnNameFromId([x2, y2]);
        },
        _isAutoComputing: function () {
            return false;
        },
        _compute: function () {
            var x = self.jexcel_obj.rows.length;
            var y = self.jexcel_obj.colgroup.length;
            var v;
            for (var j = 0; j < y; j++) {
                for (var i = 0; i < x; i++) {
                    v = self.jexcel_obj.getValueFromCoords(j, i);
                    if (v && v.charAt(0) == '=') {
                        self.jexcel_obj.setValueFromCoords(j, i, v, false)
                    }
                }
            }
        },
        _changeDateStr: function (dateStr) {
            return dateStr.replace('年', '-').replace('月', '-').replace('日', '')

        },
        _renderEdit: function () {
            self = this;
            //避免重复加载
            if (this.ddom) {
                return;
            };
            this.ddom = document.createElement('div');
            this.$el.append(this.ddom);
            // var d = self.value;
            var options = {
                editable: (this.mode === 'edit'),
                fullscreen: false,
                defaultColWidth: 150,
                wordWrap: true,
                minDimensions: [4, 5],
                rowResize: true,
                columnResize: true,
                allowComments: (this.mode === 'edit'),
                columnDrag: (this.mode === 'edit'),
                allowInsertRow: (this.mode === 'edit'),
                allowManualInsertRow: (this.mode === 'edit'),
                allowInsertColumn: (this.mode === 'edit'),
                allowManualInsertColumn: (this.mode === 'edit'),
                selectionCopy: (this.mode === 'edit'),
                allowDeleteRow: (this.mode === 'edit'),
                allowDeleteColumn: (this.mode === 'edit'),
                // 不适用，有bug
                allowRenameColumn: false,
                // 排序和odoo可能有冲突，所以禁用
                columnSorting: false,
                data: $.parseJSON(self.value),
                mergeCells: $.parseJSON(self.record.data['merge_info']),
                // 自定义扩展option
                computing: this._isAutoComputing(),
                // 远程调用
                widget: this,
                // mergeCells:{},
                // 工具栏
                toolbar: [{
                        type: 'i',
                        content: 'undo',
                        onclick: function () {
                            self.jexcel_obj.undo();
                            if (self.mode != 'edit') {
                                return;
                            }

                        }
                    },
                    {
                        type: 'i',
                        content: 'redo',
                        onclick: function () {
                            self.jexcel_obj.redo();
                            if (self.mode != 'edit') {
                                return;
                            }

                        }
                    },
                    {
                        type: 'select',
                        k: 'font-family',
                        v: ['Arial', 'Verdana']
                    },
                    {
                        type: 'select',
                        k: 'font-size',
                        v: ['9px', '10px', '11px', '12px', '14px', '16px', '18px', '20px', '24px', '28px', '32px', '40px', '48px', '64px', '80px', ]
                    },
                    {
                        type: 'i',
                        content: 'format_align_left',
                        k: 'text-align',
                        v: 'left'
                    },
                    {
                        type: 'i',
                        content: 'format_align_center',
                        k: 'text-align',
                        v: 'center'
                    },
                    {
                        type: 'i',
                        content: 'format_align_right',
                        k: 'text-align',
                        v: 'right'
                    },
                    {
                        type: 'i',
                        content: 'format_bold',
                        k: 'font-weight',
                        v: 'bold'
                    },
                    {
                        type: 'color',
                        content: 'format_color_text',
                        k: 'color'
                    },
                    {
                        type: 'color',
                        content: 'format_color_fill',
                        k: 'background-color'
                    },
                    // 合并单元格
                    {
                        type: 'i',
                        content: 'view_stream',
                        onclick: function () {
                            if (self.mode != 'edit') {
                                return;
                            }
                            // var cell = jexcel.getColumnNameFromId([self.selection_x1, self.selection_y1])
                            var x = self.selection_x2 - self.selection_x1;
                            var y = self.selection_y2 - self.selection_y1;
                            self.jexcel_obj.setMerge("", x, y);

                        },
                    },
                    // 取消合并单元格
                    {
                        type: 'i',
                        content: 'view_module',
                        onclick: function () {
                            if (self.mode != 'edit') {
                                return;
                            }
                            var cell = jexcel.getColumnNameFromId([self.selection_x1, self.selection_y1]);
                            self.jexcel_obj.removeMerge(cell);

                        }
                    },
                    // 公式向导
                    {
                        type: 'i',
                        content: 'open_with',
                        onclick: function () {
                            if (self.mode != 'edit') {
                                return;
                            }
                            self._openAccountFormulaWizard();
                        }
                    },
                    // 下载表格为csv
                    {
                        type: 'i',
                        content: 'save_alt',
                        onclick: function () {
                            // self._do_check();
                            self.jexcel_obj.download();
                            // jexcel.current.options.computing=false;

                        }
                    },
                    // 计算
                    {
                        type: 'i',
                        content: 'exposure',
                        onclick: function () {
                            var startDate = self._getStartDate()
                            var endDate = self._getEndDate()
                            if (isNaN(startDate) && !isNaN(Date.parse(startDate)) &&
                                isNaN(endDate) && !isNaN(Date.parse(endDate))) {
                                    if(Date.parse(startDate)>Date.parse(endDate)){
                                        self.do_warn("开始日期不能晚于结束日期!")
                                        return
                                    }
                                jexcel.current.options.computing = !jexcel.current.options.computing;
                                self.startDate = startDate;
                                self.endDate = endDate;
                                self.orgIds = self._getOrgIds();
                                self._compute();
                            }else{
                                self.do_warn("期间不正确")
                            }
                        }
                    },
                ],
                // 
                text: {
                    noRecordsFound: '没有记录',
                    showingPage: '显示页',
                    show: '显示',
                    entries: '明细',
                    openAccountFormula: '设置科目取数公式',
                    insertANewColumnBefore: '在前面插入一列',
                    insertANewColumnAfter: '在后面插入一列',
                    deleteSelectedColumns: '删除选中列',
                    renameThisColumn: '重命名该列',
                    orderAscending: '按升序排列',
                    orderDescending: '按降序排列',
                    insertANewRowBefore: '在前面插入一行',
                    insertANewRowAfter: '在后面插入一行',
                    deleteSelectedRows: '删除选中行',
                    editComments: '编辑批批注',
                    addComments: '添加批注',
                    comments: '批注',
                    clearComments: '清除批注',
                    copy: '复制',
                    paste: '粘贴',
                    saveAs: '下载保存',
                    // about: ​ '关于', 修改后将无法使用
                    areYouSureToDeleteTheSelectedRows: '你确定要删除选中行?',
                    areYouSureToDeleteTheSelectedColumns: '你确定要删除选中列?',
                    thisActionWillDestroyAnyExistingMergedCellsAreYouSure: '你是否确定要取消合并单元格?',
                    thisActionWillClearYourSearchResultsAreYouSure: '该操作会清除你的搜索结果，你是否确定?',
                    thereIsAConflictWithAnotherMergedCell: '与另一个合并的单元格有冲突!',
                    invalidMergeProperties: '无效的合并',
                    cellAlreadyMerged: '单元格已经被合并,可以取消合并',
                    noCellsSelected: '没有选中任何单元格',

                },
                onload: function (instance) {
                    // 初始化表格单元格值
                    instance.jexcel.setStyle($.parseJSON(self.record.data['data_style']));
                    // 初始化表格行和列的高度和宽度
                    var width_info = $.parseJSON(self.record.data['width_info']);
                    var columns = Object.keys(width_info);
                    var height_info = $.parseJSON(self.record.data['height_info']);
                    var rows = Object.keys(height_info);
                    var column;
                    for (column in columns) {
                        instance.jexcel.setWidth(column, width_info[column])
                    };
                    var row;
                    for (row in rows) {
                        if (height_info[row]) {
                            instance.jexcel.setHeight(row, height_info[row])
                        } else {
                            // 默认行高
                            instance.jexcel.setHeight(row, instance.jexcel.opetions.defaultRowsHeight);
                        }
                    };
                    // 初始化表格表头名称
                    if (self.record.data['header_info']) {
                        var headers = (self.record.data['header_info']).split(',');
                        var i;
                        for (i = 0; i < headers.length; i++) {
                            instance.jexcel.setHeader(i, headers[i]);
                        };
                    };
                    // 初始化表格批次注
                    var comments = JSON.parse(self.record.data['comments_info']);
                    for (var cellName in comments) {
                        instance.jexcel.setComments(cellName, comments[cellName]);
                    };
                    // 初始化公式
                    var metas = JSON.parse(self.record.data['meta_info']);
                    for (var cellName in metas) {
                        for (var k in metas[cellName]) {
                            instance.jexcel.setMeta(cellName, k, metas[cellName][k]);
                        }
                    }
                    // instance.jexcel.setMeta(JSON.parse(self.record.data['meta_info']));
                    // 选中第一个单元格，以在点击保存时触发onblur事件
                    instance.jexcel.updateSelectionFromCoords(0, 0, 0, 0);
                },
                onchange: function (instance, cell, x, y, value) {
                    self._setValue(JSON.stringify(instance.jexcel.getData()));
                    var cellName = jexcel.getColumnNameFromId([x, y]);
                    var data = instance.jexcel.getData()[y][x];
                    if (self._isACFormula(data)) {
                        try {
                            var cellformula = new ACFormula(data);
                            instance.jexcel.setMeta(cellName, cellformula.name(), cellformula.value());
                        } catch (error) {
                            self.do_warn(error);
                        }
                    } else {
                        // var meta=instance.jexcel.getMeta(cellName);
                        // for(var k in meta){
                        //     instance.jexcel.setMeta(cellName,k,null);
                        // }
                        if (instance.jexcel.options.meta && instance.jexcel.options.meta[cellName]) {
                            delete instance.jexcel.options.meta[cellName];
                        }
                    }
                },
                oninsertrow: function (instance) {

                },
                ondeleterow: function (instance) {

                    self._changeStyleAndData(instance);
                },
                oninsertcolumn: function (instance) {

                },
                ondeletecolumn: function (instance) {

                    self._changeStyleAndData(instance);
                },
                onmoverow: function (instance) {

                },
                onmovecolumn: function (instance, from, to) {

                },
                onmerge: function (instance) {

                },
                onresizerow: function (instance) {

                },
                onresizecolumn: function (instance) {

                },
                onsort: function (instance, cellNum, order) {
                    if (self.mode != 'edit') {
                        return;
                    }


                },
                onresizerow: function (instance, cell, height) {
                    if (self.mode != 'edit') {
                        return;
                    }

                },
                onresizecolumn: function (instance, cell, width) {
                    if (self.mode != 'edit') {
                        return;
                    }

                },
                onchangeheader: function (instantce, column, old_name, new_name) {
                    if (this.mode != 'edit') {
                        return;
                    }
                },
                onmerge: function () {

                },

                onblur: function (instance) {
                    self._changeStyleAndData(instance);

                },
                onfocus() {

                },
                onselection: function (instance, x1, y1, x2, y2, origin) {
                    self._setSelectionCells(x1, y1, x2, y2);
                },
                updateTable: function (instance, cell, col, row, val, label, cellName) {

                },

            };
            self.jexcel_obj = jexcel(this.ddom, options);
            // 设置右键科目取数公式菜单在编辑状态下可见
            self.jexcel_obj.options.allowOpenAccountFormula = (this.mode === 'edit');
            // 设置默认行高             
            self.jexcel_obj.options.defaultRowsHeight = 25;
            // 注册打开设置公式向导方法                                                                     
            self.jexcel_obj.openAccountFormula = function () {
                self._openAccountFormulaWizard();
            };

        },
        _renderReadonly: function () {
            this._renderEdit(arguments);
        },
        // 打开报表公式设置向导窗体
        _openAccountFormulaWizard: function () {
            var formula = self.jexcel_obj.getValueFromCoords(self.selection_x1, self.selection_y1) || '';
            if (formula) {
                var pre = formula.slice(0, 5);
                var last = formula.slice(-2);
                if (pre == '=ac("' && last == '")') {
                    // if 单元格定义了ac公式
                    var context = {
                        ac: (formula.slice(0, -2)).slice(5)
                    }
                    this.do_action({
                        name: '报表科目取数公式设置向导',
                        type: 'ir.actions.act_window',
                        res_model: 'accountant.reportmodel_formula',
                        context: context,
                        views: [
                            [false, 'form']
                        ],
                        target: 'new'
                    });
                    return;
                }
            }
            this.do_action({
                name: '报表科目取数公式设置向导',
                type: 'ir.actions.act_window',
                res_model: 'accountant.reportmodel_formula',
                views: [
                    [false, 'form']
                ],
                target: 'new'
            });


        },
    });
    // 表格设计器表格的样式字段小部件
    var ac_jexcel_style = AbstractField.extend({
        events: _.extend({}, AbstractField.prototype.events, {}),
        supportedFieldTypes: ['text'],
        template: 'ac_jexcel',
        start: function () {
            this._super.apply(this, arguments);
            core.bus.on('ac_jexcel_style_change', this, this._onStyleChange);
        },
        _onStyleChange: function (style) {
            this._setValue(JSON.stringify(style));
        },
    });
    // 保存表格列宽度信息小部件
    var ac_jexcel_width_info = AbstractField.extend({
        events: _.extend({}, AbstractField.prototype.events, {}),
        supportedFieldTypes: ['text'],
        template: 'ac_jexcel',
        start: function () {
            this._super.apply(this, arguments);
            core.bus.on('ac_jexcel_width_change', this, this._onWidthChange);
        },
        _onWidthChange: function (value) {
            // this.info[value[0]] = value[1];
            this._setValue(JSON.stringify(value));
        },
    });
    // 保存表格行高度信息小部件
    var ac_jexcel_height_info = AbstractField.extend({
        events: _.extend({}, AbstractField.prototype.events, {}),
        supportedFieldTypes: ['text'],
        template: 'ac_jexcel',
        start: function () {
            this._super.apply(this, arguments);
            core.bus.on('ac_jexcel_height_change', this, this._onHeightChange);
        },
        _onHeightChange: function (value) {
            // this.info[value[0]] = value[1];
            this._setValue(JSON.stringify(value));
        },
    });
    // 保存表格头名称信息小部件
    var ac_jexcel_header_info = AbstractField.extend({
        events: _.extend({}, AbstractField.prototype.events, {}),
        supportedFieldTypes: ['text'],
        template: 'ac_jexcel',
        start: function () {
            this._super.apply(this, arguments);
            core.bus.on('ac_jexcel_header_change', this, this._onHeaderChange);
        },
        _onHeaderChange: function (value) {
            this._setValue(value);
        },
    });
    // 保存表格批注信息小部件
    var ac_jexcel_comments_info = AbstractField.extend({
        events: _.extend({}, AbstractField.prototype.events, {}),
        supportedFieldTypes: ['text'],
        template: 'ac_jexcel',
        start: function () {
            this._super.apply(this, arguments);
            core.bus.on('ac_jexcel_comments_change', this, this._onCommentsChange);
        },
        _onCommentsChange: function (value) {
            this._setValue(JSON.stringify(value));
        },
    });
    // 保存表格的合并单元格信息小部件
    var ac_jexcel_merge_info = AbstractField.extend({
        events: _.extend({}, AbstractField.prototype.events, {}),
        supportedFieldTypes: ['text'],
        template: 'ac_jexcel',
        start: function () {
            this._super.apply(this, arguments);
            core.bus.on('ac_jexcel_merge_change', this, this._onMergeChange);
        },
        _onMergeChange: function (value) {
            this._setValue(JSON.stringify(value));
        },
    });
    // 保存表格的公式信息小部件
    var ac_jexcel_meta_info = AbstractField.extend({
        events: _.extend({}, AbstractField.prototype.events, {}),
        supportedFieldTypes: ['text'],
        template: 'ac_jexcel',
        start: function () {
            this._super.apply(this, arguments);
            core.bus.on('ac_jexcel_meta_change', this, this._onMetaChange);
        },
        _onMetaChange: function (value) {
            this._setValue(JSON.stringify(value));
        },
    });
    // 客户端动作，从后台获得通过向导设置的公式
    var update_formula = AbstractAction.extend({
        context: {},
        init: function (classInfo, obj1, obj2) {
            this.context = obj1.context;
            this._super.apply(this, arguments);
        },
        start: function () {
            core.bus.trigger('ac_jexcel_set_formula', this.context.accountName);
        },
        on_attach_callback: function () {
            // 取消遮挡的小部件
            $('.modal-dialog button').trigger('click');
        },
    });
    core.action_registry.add('update_formula', update_formula);
    var fieldRegistry = require('web.field_registry');
    fieldRegistry.add('ac_jexcel', ac_jexcel);
    fieldRegistry.add('ac_jexcel_style', ac_jexcel_style);
    fieldRegistry.add('ac_jexcel_width_info', ac_jexcel_width_info);
    fieldRegistry.add('ac_jexcel_height_info', ac_jexcel_height_info);
    fieldRegistry.add('ac_jexcel_header_info', ac_jexcel_header_info);
    fieldRegistry.add('ac_jexcel_comments_info', ac_jexcel_comments_info);
    fieldRegistry.add('ac_jexcel_merge_info', ac_jexcel_merge_info);
    fieldRegistry.add('ac_jexcel_meta_info', ac_jexcel_meta_info);
    return {
        ac_jexcel: ac_jexcel,
        ac_jexcel_style: ac_jexcel_style,
        ac_jexcel_width_info: ac_jexcel_width_info,
        ac_jexcel_height_info: ac_jexcel_height_info,
        ac_jexcel_header_info: ac_jexcel_header_info,
        ac_jexcel_comments_info: ac_jexcel_comments_info,
        ac_jexcel_merge_info: ac_jexcel_merge_info,
        ac_jexcel_meta_info: ac_jexcel_meta_info,
    };
});