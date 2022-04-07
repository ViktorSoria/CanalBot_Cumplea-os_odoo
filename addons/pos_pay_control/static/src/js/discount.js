odoo.define("pos_pay_control.Discount", function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen')
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    var exports = require("point_of_sale.models");

    exports.load_fields("product.pricelist", ["autorizacion"]);

    const ProductScreen2 = (ProductScreen) =>
        class extends ProductScreen {
            async _clickProduct(event) {
                if(event.detail.type === 'product' && event.detail.qty_available<=0){
                    this.playSound("error");
                    return;
                }
                super._clickProduct(...arguments);
                let product = event.detail.id;
                let pos = this.env.pos.config_id;
                let cliente = this.env.pos.get_client();
                if (cliente) {
                    cliente = cliente.id;
                }
                let dis = false;
                try{
                     dis = await this.rpc({
                        model: 'price.discount',
                        method: 'get_discount',
                        args: [null, product, cliente, pos],
                    });
                }catch (e) {
                    console.log(e);
                }
                let order = this.currentOrder;
                let line = order.get_selected_orderline();
                var to_merge_orderline;
                // valida
                order.get_orderlines().forEach(function (orderline) {
                    if (orderline.id !== line.id &&  orderline.get_product().id === line.get_product().id) {
                        to_merge_orderline = orderline;
                    }
                });
                if (to_merge_orderline) {
                    let cantidad = to_merge_orderline.get_quantity();
                    if(event.detail.type === 'product' && cantidad >= event.detail.qty_available){
                        line.set_quantity("remove");
                        this.playSound("error");
                    }else{
                        to_merge_orderline.merge(line);
                        line.set_quantity("remove");
                        order.select_orderline(to_merge_orderline);
                    }
                    return;
                }else{
                    if(event.detail.type === 'product' && line.get_quantity() > event.detail.qty_available){
                        line.set_quantity(event.detail.qty_available);
                        this.playSound("error");
                    }
                }
                // descuento
                if (dis.desc) {
                    let descuento = 0;
                    if (dis.desc === 'por') {
                        descuento = dis.value;
                    } else {
                        let total = line.get_price_with_tax();
                        descuento = dis.value * 100 / total;
                    }
                    line.set_discount(descuento);
                }
            }
            async _onClickCustomer() {
            // IMPROVEMENT: This code snippet is very similar to selectClient of PaymentScreen.
                const currentClient = this.currentOrder.get_client();
                const { confirmed, payload: newClient } = await this.showTempScreen(
                    'ClientListScreen',
                    { client: currentClient }
                );
                if (confirmed) {
                    this.currentOrder.set_client(newClient);
                    this.currentOrder.updatePricelist(newClient);
                    let cliente = newClient ? newClient.id: null;
                    await this.compute_discounts(cliente);
                }
            }
            async compute_discounts(cliente) {
                let order = this.currentOrder;
                let lines = order.get_orderlines();
                let pos = this.env.pos.config_id;
                let product;
                for (const line of lines) {
                    product = line.get_product().id;
                    let dis = await this.rpc({
                        model: 'price.discount',
                        method: 'get_discount',
                        args: [null, product, cliente, pos],
                    });
                    if (dis.desc) {
                        let descuento = 0;
                        if (dis.desc === 'por') {
                            descuento = dis.value;
                        } else {
                            let total = line.get_price_with_tax();
                            descuento = dis.value * 100 / total;
                        }
                        line.set_discount(descuento);
                    } else {
                        line.set_discount(0);
                    }
                }
            }
            _setValue(val) {
                if (this.currentOrder.get_selected_orderline()) {
                    let product = this.currentOrder.get_selected_orderline().get_product();
                    if(product.type==='product' && product.qty_available<val){
                        val = product.qty_available;
                        NumberBuffer.reset();
                    }
                }
                super._setValue(val);
            }
        }

    Registries.Component.extend(ProductScreen, ProductScreen2);
});
