odoo.define('pos_pay_control.PrintEnvScreen', function (require) {
    'use strict';

    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');
    const Registries = require('point_of_sale.Registries');

    const PrintEnvScreen = (AbstractReceiptScreen) => {
        class PrintEnvScreen extends AbstractReceiptScreen {
            mounted() {
                setTimeout(async () => await this._printReceipt(), 10);
            }
            async tryReprint(){
                await this._printReceipt();
            }
            confirm() {
                this.showScreen('ProductScreen');
            }
        }
        PrintEnvScreen.template = 'PrintEnvScreen';
        return PrintEnvScreen;
    };
    Registries.Component.addByExtending(PrintEnvScreen, AbstractReceiptScreen);

    return PrintEnvScreen;
});
