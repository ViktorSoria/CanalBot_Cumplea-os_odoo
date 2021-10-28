odoo.define("pos_pay_control.PaymentScreenCus", function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');

    const paymentScreenCustom = (PaymentScreen) =>
        class extends PaymentScreen{
            constructor() {
                super(...arguments);
                var order_id = this.currentOrder;
                var orderlines = order_id.orderlines;
                orderlines.forEach(function(line){
                    if(line.quantity <= 0){
                        line.order.remove_orderline(line);
                    }
                    console.log(line.quantity);
                });

            }
        }
    Registries.Component.extend(PaymentScreen, paymentScreenCustom);
});