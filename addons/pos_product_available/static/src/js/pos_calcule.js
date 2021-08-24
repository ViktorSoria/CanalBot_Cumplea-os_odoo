odoo.define("pos_product_available.Posquantity", function(require) {
    "use strict";

    var rpc = require("web.rpc");
    var exports = require("point_of_sale.models");
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require('point_of_sale.Registries');

    exports.load_fields("product.product", ["qty_available","type"]);
    exports.load_fields("pos.order", ["l10n_mx_edi_usage"]);

    const PaymentScreen2 = (PaymentScreen) =>
    class extends PaymentScreen{
        async validateOrder(isForceValidate) {
            if(this.env.pos.config.cash_rounding) {
                if(!this.env.pos.get_order().check_paymentlines_rounding()) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Rounding error in payment lines'),
                        body: this.env._t("The amount of your payment lines must be rounded to validate the transaction."),
                    });
                    return;
                }
            }
            if (await this._isOrderValid(isForceValidate)) {
                // remove pending payments before finalizing the validation
                for (let line of this.paymentLines) {
                    if (!line.is_done()) this.currentOrder.remove_paymentline(line);
                }
                await this._finalizeValidation();
                this.recompute_quantity()
            }
        }
        async recompute_quantity(){
            console.log("cargando cantidades");
            let productos = this.env.pos.db.product_by_id;
            let location = this.env.pos.config.default_location_src_id[0];
            let products = await rpc.query({
                model: 'product.product',
                method: 'search_read',
                fields: ["qty_available"],
                context: {location:location},
                domain: [["id",'in',Object.keys(productos).map(x=>+x)]],
            });
            let p,i;
            products.forEach(item => {
                i = item.id
                p = this.env.pos.db.product_by_id[i];
                p.qty_available = item.qty_available;
            });
        }
    }

    Registries.Component.extend(PaymentScreen,PaymentScreen2);

});
