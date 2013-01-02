$("#submitbtn").click(function(){
	
	data = {
		"body":$("#commenttext").val()
	}
	
	console.log(data)
	
	$.post('/feedback',{"body":data},function(){
		$('.feedback').animate({opacity:0})
	})
})