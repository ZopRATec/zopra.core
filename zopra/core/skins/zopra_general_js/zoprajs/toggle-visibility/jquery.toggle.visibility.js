/*!
 * toggle visibility
 *
 * This jquery plugin grants links the ability to toggle the visibility of a element given by its ID.
 *
 * e.g. <a href="the/link/for/non/js/users" rel="#target" class="toggleVisibility"> Show content of #target </a>
 *
 * <div id="target" class="hidden"> content </div>
 *
 * Copyright 2011, Paul Grunewald
 *
 * Datum: 16:44 Donnerstag, 14. Juli 2011
 * Zuletzt geändert: 19:03 Donnerstag, 14. Juli 2011
 */

(function( $ ){
    var methods = {
    init : function( paramOptions ) {
        var settings = { // default settings
            showText        : "einblenden",
            showTextClass   : "toggle-visibility-show-text",
            showTargetClass : "toggle-visibility-shown-target",
            showCallback    : function() {},
            hideText        : "ausblenden",
            hideTextClass   : "toggle-visibility-hide-text",
            hideTargetClass : "toggle-visibility-hidden-target",
            hideCallback    : function() {},
            target: null
        };
        if ( paramOptions )
            $.extend(settings, paramOptions);

        return this.each(function() {
            var link = $(this);
            var target = link.attr("rel");

            if (settings.target != null)
                target = settings.target;

            function update() { // update according to the target's visibility state
                if ($(target).is(":visible"))
                   link.html(settings.hideText).addClass(settings.hideTextClass).removeClass(settings.showTextClass);
                else
                   link.html(settings.showText).addClass(settings.showTextClass).removeClass(settings.hideTextClass);
            }


            update();

            link.bind("click",function(e) {
                if ($(target).is(":visible")) {
                    $(target).addClass(settings.hideTargetClass).removeClass(settings.showTargetClass);
                    settings.hideCallback(link);
               }
                else {
                    $(target).addClass(settings.showTargetClass).removeClass(settings.hideTargetClass);
                    settings.showCallback(link);
                }
                update();
                e.preventDefault();
                });
            });
        }
    };

  $.fn.toggleVisibility = function( method ) {

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
