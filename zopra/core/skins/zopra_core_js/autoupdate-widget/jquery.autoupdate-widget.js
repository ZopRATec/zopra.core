/*!
 * autoupdate widget (for table_edit_form)
 *
 * This jquery plugin grants the ability to reload only certain parts (widgets) from the table_edit_form.
 *
 * When opening a link within the widget the new window will be tracked. After closing it, the designated widget will be reloaded.
 *
 * Example: $('div.autoupdate').autoupdateWidget();
 *
 * Copyright 2011, Paul Grunewald
 *
 * Datum: 12:57 Freitag, 4. November 2011
 */

(function( $ ) {
    var load_once = false;
    var methods = {
    init : function( paramOptions ) {
        var settings = { };
        if ( paramOptions ) {
            $.extend(settings, paramOptions);
        }
        var table = $("input[name='table']").val();
        var autoid = parseInt($("input[name='autoid']").val());

        if (load_once == false) { // register once
            $(this).on("click", "a.autoupdate_popup", function(e) {
                var link = $(this);
                var widget = $(this).parents('div.field');
                // the fieldset is not the direct parent in the rendered version, but a super-parent
                var form = widget.parents('form');
                var fieldset = widget.parents('fieldset');
                var macroname = fieldset.attr('id');
                var wnd = window.open("zopra_popup?url="+encodeURIComponent(link.attr('href')+'&zopra_popup=1'),"","width=910,height=1000");

                jQuery.fn.findAndSelf = function(selector) {
                    return this.find(selector).add(this.filter(selector));
                }

                var watchClose = setInterval(function() {
                    try {
                        if (wnd.closed) {

                            clearTimeout(watchClose);

                            // Check if this page has created a working copy. if yes, then update the autoid of the form
                            $.ajax({
                                type	: "GET",
                                cache	: false,
                                url		: "zopra_widget_ajax",
                                data	: { table: table,
                                            autoid: autoid,
                                            checkCopy: 1,
                                            form_id: form.attr('id')},
                                success	: function(output) {
                                    var new_autoid = parseInt(output);
                                    if (new_autoid != autoid) { // is now working copy? (e.g. due to dependent-entries)
                                        alert("Arbeitskopie wurde erzeugt und wird angezeigt. Sie können direkt weiterarbeiten. Alte ID: " + autoid + ", neue ID: " + new_autoid);
                                        // update form
                                        // .. ids
                                        $("input[name='autoid']").val(new_autoid);
                                        $("input[name='iscopyof']").val(autoid);
                                        // .. links in widgets
                                        $("a[href*='origid="+autoid+"']").each(function() {
                                            this.href = this.href.replace("origid="+autoid, "origid="+new_autoid);
                                        });
                                        // .. links from top and bottom
                                        // TODO: check if this is necessary (doesn't work right now, class is gone, tabs might need handling), but maybe we do not need to replace the id here anyway
                                        $(".zopra_special_links a[href*='"+autoid+"']").each(function() {
                                            this.href = this.href.replace(new RegExp(autoid, "g"), new_autoid);
                                        });

                                        autoid = new_autoid;

                                    }
                                    $.ajax({
                                        type	: "GET",
                                        cache	: false,
                                        url		: "zopra_widget_ajax",
                                        data	: { table:     table,
                                                    autoid:    autoid,
                                                    macroname: macroname,
                                                    form_id:      form.attr('id')},
                                        success	: function(html) {
                                            var labelOfWidget = widget.children("label").html();
                                             // since the macro returns potentially several widgets, we have to cut out the right one
                                            var reduced2WidgetChildren = $(html).findAndSelf('div.field').filter(function() { return $(this).children('label').html() == labelOfWidget; }).children();
                                            // replace old widget with new once
                                            widget.empty().append(reduced2WidgetChildren);
                                            // maybe we can just assume all links have been outfitted with autoupdate_popup and throw this away?
                                            widget.find("a").addClass('autoupdate_popup');
                                        }
                                    });
                                }
                            });
                        }
                    } catch (e) {}
                }, 200);
                e.preventDefault();
            });
            load_once = true;
        }

        return this.each(function() {
                $(this).find("a").addClass('autoupdate_popup');
            });

        }
    };

  $.fn.autoupdateWidget = function( method ) {

    // Method calling logic
    if ( methods[method] ) {
      return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
    } else if ( typeof method === 'object' || ! method ) {
      return methods.init.apply( this, arguments );
    } else {
      $.error( 'Method ' +  method + ' does not exist on this jQuery plugin' );
    }

  };

})( jQuery );
