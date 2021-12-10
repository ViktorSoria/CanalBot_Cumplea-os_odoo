odoo.define("pos_pay_control.PaymentScreenCus", function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');

    const paymentScreenCustom = (PaymentScreen) =>
        class extends PaymentScreen{
            constructor() {
                super(...arguments);
                /* Cliente publico general */
                var client = this.currentOrder['attributes']['client'];
                if (client == null){
                    var default_client = this.env.pos.config.default_client;
                    if (default_client != null){
                        this.currentOrder.set_client(this.env.pos.db.get_partner_by_id(default_client[0]));
                    }

                }
            }
        }
    Registries.Component.extend(PaymentScreen, paymentScreenCustom);
});