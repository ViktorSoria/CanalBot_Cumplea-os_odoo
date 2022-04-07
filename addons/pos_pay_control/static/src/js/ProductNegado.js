odoo.define('pos_pay_control.ProductNegado', function (require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const ProductItem = require("point_of_sale.ProductItem");
    const { useListener } = require('web.custom_hooks');
    const {Gui} = require('point_of_sale.Gui');
    const { useState, useRef } = owl.hooks;

        const ProductItem2 = (ProductItem) =>
        class extends ProductItem {
            constructor() {
                super(...arguments);
                useListener('click-negado', this.negado);
            }
            async negado(event) {
                event.stopPropagation();
                event.cancelBubble = true;
                const { confirmed, payload } = await this.showPopup('NumberPopup',{
                    title: "Cantidad Negada",
                });
                if(confirmed){
                    let pos = this.env.pos.config.id;
                    await this.rpc({
                        model: 'product.product.negado',
                        method: 'create_line',
                        args: [this.props.product.id,payload,pos],
                    });
                }
            }

        }
    Registries.Component.extend(ProductItem, ProductItem2);
});