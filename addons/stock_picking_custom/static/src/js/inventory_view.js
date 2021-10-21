odoo.define('stock.InventoryReportListViewFile', function (require) {
"use strict";

var ListView = require('web.ListView');
var InventoryReportListController = require('stock.InventoryReportListControllerFile');
var viewRegistry = require('web.view_registry');


var InventoryReportListViewFile = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: InventoryReportListController,
    }),
});

viewRegistry.add('inventory_report_list', InventoryReportListController);

return InventoryReportListViewFile;

});