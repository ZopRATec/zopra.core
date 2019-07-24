/** 
 *  this file is not used right now, because all new modules using
 *  plone / WebCMS javascripts do not need it.
 *  This is a place to collect all editing js needed for a standalone installation
 *  
 */ 
/**
 * Helper for styled file upload inputs (e.g. on zopra_table_import_form.cpt)
 * Mirrors the file name of a chosen file to the .filename-container
 */
(function ( $ ) {
    var regex = /[^\\]+$/;
    // ready handler
    $ (function () {
        $("input[type='file']").filter(function () {
            // only inputs that have a custom filename element as sibling
            return $(this).siblings(".filename").length > 0;
        })
        .on("change", function (event) {
            $(this).siblings(".filename").text( this.value.match(regex) );
        });
    );
})(jQuery);