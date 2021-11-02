odoo.define("pos_pay_control.productItem", function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const ProductItem = require("point_of_sale.ProductItem");

    const ProductItemCustom = (ProductItem) =>
        class extends ProductItem {
            constructor() {
                super(...arguments);

            }
        }
    Registries.Component.extend(ProductItem, ProductItemCustom);
});
