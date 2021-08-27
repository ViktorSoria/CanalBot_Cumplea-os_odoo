odoo.define("pos_pay_control.Discount", function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen')
    var exports = require("point_of_sale.models");

    exports.load_fields("product.pricelist", ["autorizacion"]);

    const ProductScreen2 = (ProductScreen) =>
        class extends ProductScreen {
            async _clickProduct(event) {
                super._clickProduct(...arguments);
                let line = this.currentOrder.get_selected_orderline();
                let product = event.detail.id;
                let pos = this.env.pos.config_id;
                let cliente = this.env.pos.get_client();
                if(cliente){
                    cliente = cliente.id;
                }
                let dis = await this.rpc({
                            model: 'price.discount',
                            method: 'get_discount',
                            args: [null, product,cliente,pos],
                        });
                if(dis.desc){
                    let descuento = 0;
                    if(dis.desc==='por'){
                        descuento = dis.value;
                    }else{
                        let total = line.get_price_with_tax();
                        descuento = dis.value*100/total;
                    }
                    line.set_discount(descuento);
                }
            }
        }

    Registries.Component.extend(ProductScreen, ProductScreen2);
});
