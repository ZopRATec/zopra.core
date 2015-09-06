/*!
 * fancybox textarea-popup
 *
 * Copyright 2011, Paul Grunewald
 *
 * Datum: 15:15 Freitag, 24. Juni 2011
 * Zuletzt geändert: 23:07 Mittwoch, 29. Juni 2011
 */

(function( $ ){
    /* helper functions to save last fontsize ( see http://www.w3schools.com/js/js_cookies.asp ) */
    function setCookie(c_name,value,exdays) {
         var exdate=new Date();
         exdate.setDate(exdate.getDate() + exdays);
         var c_value=escape(value) + ((exdays==null) ? "" : "; expires="+exdate.toUTCString());
         document.cookie=c_name + "=" + c_value;
     }
    function getCookie(c_name) {
        var i,x,y,ARRcookies=document.cookie.split(";");
        for (i=0;i<ARRcookies.length;i++) {
            x=ARRcookies[i].substr(0,ARRcookies[i].indexOf("="));
            y=ARRcookies[i].substr(ARRcookies[i].indexOf("=")+1);
            x=x.replace(/^\s+|\s+$/g,"");
            if (x==c_name) {
                return unescape(y);
            }
        }
        return null;
    }

    var methods = {
    init : function( options ) {
        var settings = { // default settings
            fancybox:
                        {   "modal": false,
                            "title": "Zum Verlassen einfach <b>ESC</b> oder auf <img src='js/fancybox/fancy_close.png' class='fancybox-textarea-close'/> drücken. Schriftgr&ouml;&szlig;e &auml;ndern: <a href='#' class='fancybox-textarea-fontsize-increase' title='Schrift vergr&ouml;&szlig;ern'>+</a> / <a href='#' class='fancybox-textarea-fontsize-decrease' title='Schrift verkleinern'>-</a> / <a href='#' class='fancybox-textarea-fontsize-reset' title='Wiederherstellen der Schriftgr&ouml;&szlig;e'>r</a>",
                            "titlePosition": "inside",
                        },
            hoverMessage: "Diesen Text im großen Eingabefeld bearbeiten.",
            buttonText: "Text bearbeiten",
            percentageWindow: { width:0.8, height:0.8 },
            };
        if ( options )
            $.extend(settings, options);

        return this.each(function() {
            var textarea = $(this);
            textarea.wrap('<div class="fancybox-textarea"></div>')
		      .parent().append($('<div class="fancybox-textarea-button">'+settings.buttonText+'</div>').attr("title",settings.hoverMessage)).css("padding",textarea.css("padding"));
            var context = textarea.parent(),
                button = $(".fancybox-textarea-button", context);
            button.hide();

            button.bind("click",function() {

                var fontSize = getCookie("fancybox-textarea-font-size");
                if (fontSize != null)
                    fontSize = "font-size:"+fontSize;
                var absoluteWidth = Math.round($(window).width() * settings.percentageWindow.width),
                    absoluteHeight = Math.round($(window).height() * settings.percentageWindow.height);
                // need a special width for ERP Invoice Position Text (matching the invoice width), gets set in create/edit_additional macros
                if (typeof fancyBoxWidthOverwrite != 'undefined')
                	absoluteWidth = fancyBoxWidthOverwrite;

                $("body").append("<div class=\"fancybox-textarea-disposable\" id=\"fancybox-textarea-disposable\"><div><textarea style='width:"+(absoluteWidth)+"px;height:"+(absoluteHeight)+"px;"+fontSize+"'>"+ textarea.val() + "</textarea></div></div>");
                // check if the textarea has been decorated by other jquery-plugins and imitate that behaviour
                if (textarea.hasClass('maxLength')) { // maxLength-Plugin by Frank
                    var length = parseInt(textarea.attr("data-maxlength"));
                    $("#fancybox-textarea-disposable").find("textarea").maxLength(length);
                }
                var largeTextarea = $(".fancybox-textarea-disposable").find("textarea");


                $(largeTextarea).resizable({
                    handles: "se",
                    resize: function(event, ui) {
                    $("#fancy_outer").css({'width': largeTextarea.width()+'px', 'height': largeTextarea.height()+'px'});
                    $('#fancybox-content').width(largeTextarea.width()+10);
                    $('#fancybox-wrap').width(largeTextarea.width()+30);
                    $('#fancybox-title').width(largeTextarea.width()+10);
                    $.fancybox.center();
                    }
                });
                $('#fancybox-textarea-disposable').find(".ui-resizable-handle").attr("title","Hier Eingabefeld verschieben.");


                button.fadeOut();
                $.fancybox(
                    $.extend({
                        "href":"#fancybox-textarea-disposable",
                        "type":"inline",
                        "centerOnScroll": true,

                        "onComplete": function() {
                            $("textarea","#fancybox-textarea-disposable").focus();
                        },
                        "onClosed": function() {
                            textarea.val($("textarea","#fancybox-textarea-disposable").val());

                            $("#fancybox-textarea-disposable").remove();
                            textarea.focus();
                        }
                    }, settings.fancybox)
                );

                // set bindings for title content (close button, font resize links, etc.)
                $(".fancybox-textarea-close").click($.fancybox.close);
                $(".fancybox-textarea-fontsize-increase").click(function(e) {
                  	var currentFontSize = largeTextarea.css('font-size');
                    var currentFontSizeNum = parseFloat(currentFontSize, 10);
                    var newFontSize = currentFontSizeNum*1.2;
                    largeTextarea.css('font-size', newFontSize);
                    e.preventDefault();
                    largeTextarea.focus();
                    setCookie("fancybox-textarea-font-size",largeTextarea.css('font-size'),1);
                });
                $(".fancybox-textarea-fontsize-decrease").click(function(e) {
                  	var currentFontSize = largeTextarea.css('font-size');
                    var currentFontSizeNum = parseFloat(currentFontSize, 10);
                    var newFontSize = currentFontSizeNum*0.8;
                    largeTextarea.css('font-size', newFontSize);
                    e.preventDefault();
                    largeTextarea.focus();
                    setCookie("fancybox-textarea-font-size",largeTextarea.css('font-size'),1);
                });
                $(".fancybox-textarea-fontsize-reset").click(function(e) {
                    largeTextarea.css('font-size', '');
                    e.preventDefault();
                    largeTextarea.focus();
                    setCookie("fancybox-textarea-font-size",largeTextarea.css('font-size'),1);
                });



            });




            context.hover( function () {
                context.addClass("hovered");
                $(this).data('timeout', setTimeout( function () {
                    button.fadeIn(200);
                }, 200));
            }, function () {
                clearTimeout($(this).data('timeout'));
                $(this).data('timeout', setTimeout( function () {
                    context.removeClass("hovered");
                    if (!button.hasClass("hovered") && !context.hasClass("hovered"))
                        button.fadeOut(500);
                }, 200));

            });

            button.hover( function () {
                clearTimeout(context.data('timeout'));
                button.addClass("hovered").stop(true,true).show();
            }, function() {
                clearTimeout(context.data('timeout'));
                button.removeClass("hovered");
                if (!button.hasClass("hovered") && !context.hasClass("hovered"))
                    button.fadeOut(500);

            });


        });
    },
    hide : function( ) { }
    };



  $.fn.textareaPopup = function( method ) {

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
