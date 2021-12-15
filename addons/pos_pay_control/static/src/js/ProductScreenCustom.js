odoo.define("pos_pay_control.ProductScreenCustom", function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    var exports = require("point_of_sale.models");

    exports.load_fields("product.pricelist", ["autorizacion"]);

    const ProductScreenCustom = (ProductScreen) =>
        class extends ProductScreen {
            /*
            Se realizan validaciones de que un producto no puede tener el precio en cero o
            cantiadad en cero, de ser así se mostrará una alerta y posiblemente
            no proceda a la pantalla de pago
            */
            _onClickPay() {
                var self = this;
                var show_payment_screen = true;
                this.currentOrder.orderlines.forEach(function(line){
                    if(line.quantity <= 0){
                        self.showPopup('ErrorPopup', {
                            title: "Error de cantidad",
                            body: "No puedes pagar cero productos.",
                        });
                        show_payment_screen = false;
                        return;
                    }
                    if(line.price <= 0.01){
                        self.showPopup('ErrorPopup', {
                            title: "Error de precio",
                            body: "No puedes pagar productos sin precio o con precio menor o igual a cero.",
                        });
                        show_payment_screen = false;
                        return;
                    }
                });
                if(show_payment_screen == true){
                    this.showScreen('PaymentScreen');
                }
            }
            /*
              Se asegura que tenga el cliente default al momento de vender.
            */
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
    Registries.Component.extend(ProductScreen, ProductScreenCustom);
});