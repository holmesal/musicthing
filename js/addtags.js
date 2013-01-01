var removedupes = function(){
	var seen = {};
	$('#html-tags > .tag').each(function() {
	    var txt = $(this).text();
	    if (seen[txt]){
	        $(this).remove();
	        console.log("removed:" + this)
	    }else{
	        seen[txt] = true;
	    }
	});
}



var addtag = function(){
	
	tag = {
		"name"		:	$("#singletag").val(),
		"count"		:	high
	}
	
	tags.push(tag)
	
	tags = tags.sort(compare).reverse()
	
	
	updatetagshtml()
	
	$("#singletag").val("")
	
	
}

var postform = function(signup){
	
	to_post = {
		"tags"			:	tags,
		"serendipity"	:	$("#serendipity").val(),
		"email"			:	$("#email").val(),
		"pw"			:	$("#pw").val()
	}
	
	if (signup == true){
		to_post.signup = true
	} else{
		to_post.signup = false
	}
	
	console.log(to_post)

}


updatetagshtml = function(){
	$('#html-tags').empty()
	
	console.log(tags)
	
	$(tags).each(function(i,tag){
		size = Math.ceil((tag.count/high)*13 + 10)
/* 		console.log(size) */
		
		
		elem = "<a class='tag btn btn-info' style='font-size:"+size+"pt;line-height:100%;'>"+tag.name+"</a>"
/* 		console.log(tag.count/high) */
		$("#html-tags").append(elem)
	})
	
	//re-register remove listener
	$(".tag").click(function(){
		//remove the html
		$(this).remove()
		//log the name
		name = $(this).text()
		//remove the tag
		$(tags).each(function(i,tag){
			if (tag.name == name){
				tags.splice(i,1)
			}
		})
		//update the hidden input field
		$("#tags").val(JSON.stringify(tags))
	})
	
	//remove the html duplicates
	removedupes()
	
	//add to the hidden input field
	$("#tags").val(JSON.stringify(tags))
	
	//show the alert
	$("#html-tags").prepend('<p id="removealert">(click any tag to remove it)</p>')
	
	//enable the save button
	$("#saveTags").removeAttr("disabled");
	
	//re-disable the artist input
	$("#grabtags").attr("disabled", "disabled");
	
}

function compare(a,b) {
	return a.count - b.count
}

var grabtags = function(){

	var url = "http://ws.audioscrobbler.com/2.0/"
	
	var params = {
		"artist"		:	$('#artist').val(),
		"autocorrect"	:	1,
		"method"		:	"artist.gettoptags",
		"api_key"		:	"6b85f93a14d6029cba9d7750caf8ea47",
		"format"		:	"json"
	}
	
	console.log(params)
	
	$.get(url,params,function(data){
		
		try{
		
			var orig_tags = data.toptags.tag
	/* 		console.log(orig_tags) */
			//take the top 90% of tags
			high = orig_tags[0].count
			
			for (var i=0;i<orig_tags.length;i++){
				tag = orig_tags[i]
				if (tag.count/high > 0.05){
	/* 				console.log("adding: " + tag.name) */
					tags.push(tag)
				} else{
	/* 				console.log("not adding: " + tag.name) */
				}
				
			}
			
			//make uniques
	/*
			unique_tags = []
			$.each(tags,function(i,tag){
				if ($.inArray(tag))
			})
	*/
			
			tags = tags.sort(compare).reverse()
			console.log(tags)
			
			updatetagshtml()
			
			$('#artist').val("")
		
		} catch(err){
			console.log(err)
			alert("Could not find artist")
			$('#artist').val("")
		}
		
	});
	
}

$(document).ready(function(){
	
	//hide the alert
	$("#removealert").hide()
	
	$("#grabtags").click(function(){
		grabtags()
	})
	
	$("#addtag").click(function(){
		addtag()
	})
	
	$("#signup").click(function(){
		postform(true)
	})
	
	$("#goplay").click(function(){
		postform(false)
	})
	
	
    $("#artist,#singletag").bind("change keyup input",
		function () {      
			if ($(this).val() != ""){
				$(this).siblings(".btn").removeAttr("disabled");
			}else {
				$(this).siblings(".btn").attr("disabled", "disabled");
			}      
	});
	
	//prevent enter submitting
	$('.noEnterSubmit').keypress(function(e){
	    if ( e.which == 13 ) {
	    	return false;
	    }
/* 	    if ( e.which == 13 ) e.preventDefault(); */
	});
});