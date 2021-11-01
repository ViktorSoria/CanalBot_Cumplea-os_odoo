odoo.define('pos_pay_control.ReceiptLightScreen', function (require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const ReceiptLightScreen = (AbstractReceiptScreen) => {
        class ReceiptLightScreen extends AbstractReceiptScreen {
            constructor() {
                super(...arguments);
                console.log("--- LR 3 ----");
                console.log(this);
                let result = await this._printReceipt();
                console.log(result);
            }
        }
        ReceiptLightScreen.template = 'ReceiptLightScreen';
        return ReceiptLightScreen;
    }
    Registries.Component.addByExtending(ReceiptLightScreen, AbstractReceiptScreen);
    return ReceiptLightScreen;

});