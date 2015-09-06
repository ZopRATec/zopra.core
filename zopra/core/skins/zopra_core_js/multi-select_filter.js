$(document).ready(function() {
    //filter box for multi-selection
    $('select[multiple]').parents("table.multiselect").siblings("div.formHelp").after("Filter: <input type='text' />");
    $('.multiselect').siblings("input").keyup(function(){
        var valThis = $(this).val().toLowerCase();
        $(this).siblings("table").find("li").each(function(){
            var text = $(this).text().toLowerCase();
            (text.indexOf(valThis) > -1) ? $(this).removeClass("filtered") : $(this).addClass("filtered");
        });
    });
});