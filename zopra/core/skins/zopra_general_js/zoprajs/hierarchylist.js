        function hierarchylist_remove_levels(elem)
		{
			elem = elem.parentNode.parentNode.nextSibling;
			while (elem!=null)
		    {
		    	rem_elem=elem
		        elem=elem.nextSibling;
		        rem_elem.remove();
		    }
		}
		
		function hierarchylist_select_option(parent,attr_name,table,elem)
		{
			//console.log("parent:"+parent);
			var xmlhttp;
			hierarchylist_remove_levels(elem);
			
			elem.action="";
			$('div#hierarchylist_'+attr_name+' div.loading')[0].style="visibility:visible;";
			
			if (window.XMLHttpRequest)
			{// code for IE7+, Firefox, Chrome, Opera, Safari
				xmlhttp=new XMLHttpRequest();
			}
			else
			{// code for IE6, IE5
				xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
			}
			xmlhttp.onreadystatechange=function()
			{
				if (xmlhttp.readyState==4 && xmlhttp.status==200)
			    {
			    	//console.log("response")
			    	node = document.createElement('div');
			    	node.innerHTML = xmlhttp.responseText;
			    	$("div#hierarchylist_"+attr_name+" div.container")[0].appendChild(node);
			    	document.getElementById(attr_name).value=parent;
			    	elem.action="'hierarchylist_select_option("+parent+",'"+attr_name+"','"+table+"',this)'";
			    	//console.log("action:"+elem.action)
			    	$('div#hierarchylist_'+attr_name+' div.loading')[0].style="visibility:collapse;";
			    }
			}
			xmlhttp.open("GET","zopra_widget_hierarchylist_helper?parent="+parent+"&attr_name="+attr_name+"&table="+table,true);
			xmlhttp.send();
		}