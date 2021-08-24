odoo.define("pos_pay_control.ListPrice", function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const ActionpadWidget = require('point_of_sale.SetPricelistButton')
    var exports = require("point_of_sale.models");

    exports.load_fields("product.pricelist", ["autorizacion"]);

    const ActionpadWidget2 = (ActionpadWidget) =>
        class extends ActionpadWidget {
            async onClick() {
                return
            }
        }

    Registries.Component.extend(ActionpadWidget, ActionpadWidget2);
});
