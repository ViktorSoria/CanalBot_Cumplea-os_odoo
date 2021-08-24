odoo.define('pos_product_available.ShowStock', function (require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class StockProductPopup extends AbstractAwaitablePopup {}

    //Create products popup
    StockProductPopup.template = 'StockProductPopup';
    StockProductPopup.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: 'Inventario',
        body: '',
    };
    Registries.Component.add(StockProductPopup);
    return StockProductPopup;
});