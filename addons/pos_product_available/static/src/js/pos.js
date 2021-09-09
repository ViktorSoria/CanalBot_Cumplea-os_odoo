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

            async _clickProductAvailable(event) {
                console.log(this.props.product);
                var stock = await this.rpc({
                    model: 'product.product',
                    method: 'available_qty',
                    args: [this.props.product.id],
                });
                Gui.showPopup("StockProductPopup", {'stock': stock});
            }
        }
        const ProductScreen2 = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                // this.inicial();
            }
            inicial() {
                const self = this;
                async function loop(limit,offset) {
                    let newof = offset;
                    // if (self.env && self.env.pos && self.env.pos.session) {
                        let tam = self.env.pos.db.product_by_id.length;
                        let tiempo = 5000;
                        try {
                            await self.recompute_quantity(limit,offset);
                            newof += 5000;
                        } catch (error) {
                            console.log(error);
                            tiempo = 60000;
                        }
                    // }
                    if(newof>tam){newof=0;}
                    setTimeout(()=>{loop(5000,newof);}, limit !== 0 ? tiempo:60000);
                }
                loop(0,0);
            }
            async recompute_quantity(limit,offset){
                console.log("cargando cantidades");
                let location = this.env.pos.config.default_location_src_id[0];
                let products = await this.rpc({
                    model: 'product.product',
                    method: 'search_read',
                    fields: ["qty_available"],
                    context: {location:location},
                    limit: limit,
                    offset: offset,
                });
                let p;
                // console.log("llegaron cantidades");
                products.forEach(item => {
                    p = this.env.pos.db.product_by_id[item.id];
                    if(p){
                        p.qty_available = item.qty_available;
                    }
                });
                console.log("Termino de cargar");
            }

        }



    Registries.Component.extend(ProductItem, ProductItem2);
    Registries.Component.extend(ProductScreen, ProductScreen2);

    return ProductItem;
});
