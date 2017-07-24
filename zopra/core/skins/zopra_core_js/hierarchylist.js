function hierarchylist_select_option(attr_name, table, elem)
{
    var parentid = $(elem).val();
    console.log("parent:"+parentid);
    $(elem).parent('div').nextAll().remove();
    if (parentid != 0) {
        $.ajax({
            type    : "GET",
            cache   : false,
            url     : "zopra_widget_hierarchylist_helper",
            data    : { table:     table,
                        parent:    parentid,
                        attr_name: attr_name, },
            success : function(html) {
                var jq_html = $(html);
                var selector = 'div.zopra-hierarchylist-addition';
                var new_list = jq_html.find(selector).add(jq_html.filter(selector));
                $("div#hierarchylist_"+attr_name+" div.container").append(new_list);
                // set the value of the hidden value store
                $("div#hierarchylist_"+attr_name+" input#"+attr_name).val(parentid);
                // not sure what this was supposed to mean?
                //elem.action="'hierarchylist_select_option("+parent+",'"+attr_name+"','"+table+"',this)'";
            }
        });
    }
}
