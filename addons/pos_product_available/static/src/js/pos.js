odoo.define("pos_product_available.PosModel", function (require) {
    "use strict";

    var exports = require("point_of_sale.models");
    const ProductItem = require("point_of_sale.ProductItem");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const { useListener } = require('web.custom_hooks');
    const {Gui} = require('point_of_sale.Gui');
    const Registries = require('point_of_sale.Registries');
    var field_utils = require("web.field_utils");

    exports.load_fields("product.product", ["qty_available", "type",'display_name']);
    var models = exports.PosModel.prototype.models;
    models.find(e=>e.model=="product.product").context = function(self){ return { display_default_code: true, location:self.config.default_location_src_id[0]}; };
    const ProductItem2 = (ProductItem) =>
        class extends ProductItem {
            format_float_value(val) {
                var value = parseFloat(val);
                value = field_utils.format.float(value, {digits: [69, 3]});
                return String(parseFloat(value));
            }

            get product_type() {
                return this.props.product.type;
            }

            get rounded_qty() {
                return this.format_float_value(this.props.product.qty_available);
            }

            async get_product_qty(product, location) {
                return await this.rpc({
                    model: 'product.product',
                    method: 'available_qty',
                    args: [product, location],
                });
            }

            get price() {
                const formattedUnitPrice = this.env.pos.format_currency(
                    this.props.product.get_price(this.pricelist, 1),
                    'Product Price'
                );
                return formattedUnitPrice;
            }
        }

    const ProductScreen2 = (ProductScreen)=>
        class extends ProductScreen{
            constructor() {
                super(...arguments);
                useListener('click-available', this._clickProductAvailable);
            }

            async _clickProductAvailable(event){
                console.log(this.props.product);
                var stock = await this.rpc({
                    model: 'product.product',
                    method: 'available_qty',
                    args: [this.props.product.id],
                });
                Gui.showPopup("StockProductPopup", {'stock':stock});
            }
        }



    Registries.Component.extend(ProductItem, ProductItem2);
    Registries.Component.extend(ProductItem, ProductScreen2);

    return ProductItem;
});
