odoo.define("back_moto.QtyAtDateWidget", function (require) {
    "use strict";

    var QtyAtDateWidget = require("sale_stock.QtyAtDateWidget");
    var utils = require('web.utils');

    QtyAtDateWidget.include({
        _updateData: function () {
            // add some data to simplify the template
            if (this.data.scheduled_date) {
                // The digit info need to get from free_qty_today in master (instead of virtual_available_at_date)
                var qty_considered = this.data.free_qty_today;
                this.data.will_be_fulfilled = utils.round_decimals(qty_considered, this.fields.virtual_available_at_date.digits[1]) >= utils.round_decimals(this.data.qty_to_deliver, this.fields.qty_to_deliver.digits[1]);
                this.data.will_be_late = this.data.forecast_expected_date && this.data.forecast_expected_date > this.data.scheduled_date;
                if (['draft', 'sent'].includes(this.data.state)) {
                    // Moves aren't created yet, then the forecasted is only based on virtual_available of quant
                    this.data.forecasted_issue = !this.data.will_be_fulfilled && !this.data.is_mto;
                } else {
                    // Moves are created, using the forecasted data of related moves
                    this.data.forecasted_issue = !this.data.will_be_fulfilled || this.data.will_be_late;
                }
            }
        },
    });
});
