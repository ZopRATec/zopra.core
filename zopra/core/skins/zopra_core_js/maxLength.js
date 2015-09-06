/*
 * maxLength Plugin
 *
 * Copyright 2011, Frank Kubis
 *
 * Datum: 13:37 Freitag, 01.09.2011
 * Zuletzt bearbeitet: 22:40 Freitag, 15. September 2011
 */

jQuery.fn.maxLength = function(max){
    this.each(function(){

        var type = this.tagName.toLowerCase();

        var inputType = this.type? this.type.toLowerCase() : null;

        if(type == "input" && (inputType == "text" || inputType == "password")){
            this.maxLength = max;
         // add meta-information
            if (!$(this).hasClass('maxLength')) {
                $(this).addClass("maxLength");
                $(this).attr("data-maxlength", max);
            } else
                return;
        }

        else if(type == "textarea"){

            // add meta-information
            if (!$(this).hasClass('maxLength')) {
                $(this).addClass("maxLength");
                $(this).attr("data-maxlength", max);
            } else
                return;
        }
        // add counter and functions to both input and textarea widgets
        if((type == "input" && (inputType == "text" || inputType == "password")) || type == "textarea"){
	        // add the counter
	        var counter = '<span id="countWords' + $(this).attr('id') + '">' + max + '</span>';
	        var cpos = $('<div>Verfügbare Zeichen: ' + counter + '</div>');
	        // inputs are directly inside the parent field div
	        if(type == "input" && (inputType == "text" || inputType == "password")){
	        	$(this).after(cpos);
	        }
	        // textareas are inside a fancybox-div, which is parent()
	        else if(type == "textarea"){
		        $(this).parent().after(cpos);
	        }

	        var changeLength = function(length, obj){
	            $('#countWords' + $(obj).attr('id')).html(length);
	        }
	
	        var init = function(obj){
	            changeLength(parseInt(max) - parseInt(obj.value.length), obj);
	        }
	
	        this.onkeypress = function(e){
	            //ie workaround, get event
	            var obj = e || event;
	            var keyCode = obj.keyCode;
	            var selected = document.selection? document.selection.createRange().text.length > 0 : this.selectionStart != this.selectionEnd;
	
	            return !(this.value.length >= max && !(keyCode == 0 || keyCode == 32 || keyCode == 13 || keyCode > 5) && !obj.ctrlKey && !obj.altKey && !selected);
	        };
	
	        //Add the key up event
	        this.onkeyup = function(){
	            var length = parseInt(this.value.length);
	            if(length > max)
	                this.value = this.value.substring(0,max);
	            else{
	                changeLength(parseInt(max) - length, this);
	            }
	        };
	
	        // onhit from fancybox
	        this.onfocus = function(){
	            var length = parseInt(this.value.length);
	            if(length > max)
	                this.value = this.value.substring(0,max);
	            else{
	                changeLength(parseInt(max) - length, this);
	            }
	        }
	
	        init(this);
        }
    });
};