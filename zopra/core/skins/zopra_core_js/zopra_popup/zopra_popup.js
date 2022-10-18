$(document).ready(function () {
    //add popup param to links
    $('a[href*="?"]').each(function() { 
        this.href = this.href + '&zopra_popup=1';
     });
});
