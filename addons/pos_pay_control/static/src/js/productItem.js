odoo.define("pos_pay_control.productItem", function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const ProductItem = require("point_of_sale.ProductItem");

    const ProductItemCustom = (ProductItem) =>
        class extends ProductItem {
            constructor() {
                super(...arguments);
                console.log("4 OOOOOK !!! ");
                var dis_name = this.props.product.display_name;
                var short_name = (dis_name.split("]")[1]).substring(0,30);
                this['props']['product']['short_name'] = short_name;
            }
        }
    Registries.Component.extend(ProductItem, ProductItemCustom);
});
