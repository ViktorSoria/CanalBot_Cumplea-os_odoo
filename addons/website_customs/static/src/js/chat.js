odoo.define("website_customs.chat_web", function (require) {
    "use strict";
    var LivechatButton = require("im_livechat.legacy.im_livechat.im_livechat");
    var LivechatWindow = require("im_livechat.legacy.im_livechat.WebsiteLivechatWindow");
    var core = require('web.core');
    var ajax = require('web.ajax');
    var QWeb = core.qweb;
    var xml_load = ajax.loadXML(
        '/website_customs/static/src/xml/chat.xml',
        QWeb
    );

    LivechatButton.LivechatButton.include({
        start: function () {
            let res = this._super();
            this.$el.addClass("new_button");
            this.$el.css('background-color', '');
            this.$el.css('color', '');
            this.$el.html(QWeb.render(
                'website_customs.chat',
                {
                    'text': this.options.button_text,
                    'color': this.options.button_text_color,
                    'back_color': this.options.button_background_color,
                    'clase_text': '',
                }
            ));
            return res;
        },
    });

    LivechatWindow.include({
        // async start() {
        //     await this._super(...arguments);
        //     this.$el.addClass("new_chat");
        //     this.$('.o_thread_window_header').css('background-color', 'transparent');
        // },
        // renderHeader: function () {
        //     var options = this._getHeaderRenderingOptions();
        //     this.$header.html(
        //         QWeb.render('website_customs.livechat', options));
        // },
    });
});

