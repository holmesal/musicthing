$("#submitbtn").click(function(){
	$.post('/feedback',{"body":$("commenttext").val()},function(){
		$('.feedback').animate({opacity:0})
	})
})