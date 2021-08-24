odoo.define("pos_pay_control.PosButtonPay", function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const ActionpadWidget = require('point_of_sale.ActionpadWidget')
    var exports = require("point_of_sale.models");

    exports.load_fields("res.users", ["user_pay"]);

    const ActionpadWidget2 = (ActionpadWidget) =>
        class extends ActionpadWidget {
            get userpay() {
                return this.env.pos.user.user_pay;
            }
        }

    Registries.Component.extend(ActionpadWidget, ActionpadWidget2);
});
