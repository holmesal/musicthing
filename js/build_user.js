updatetagshtml = function(){
	$('#html-tags').empty()
	
	$(tags).each(function(i,tag){
		elem = "<a class='tag btn btn-info'>"+tag.name+"</a>"
		console.log(elem)
		$("#html-tags").append(elem)
	})
	
	//re-register remove listener
	$(".tag").click(function(){
		$(this).remove()
	})
	
	//add to the hidden input field
	$("#tags").val(JSON.stringify(tags))
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
	
	/* tags = [] */
	
	$("#grabtags").click(function(){
		grabtags()
	})
	
	$("#signup").click(function(){
		postform(true)
	})
	
	$("#goplay").click(function(){
		postform(false)
	})

});