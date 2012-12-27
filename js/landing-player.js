$(document).ready(function(){
	$("#expando").collapse({toggle:false})
	
	$("#genre,#radius").click(function(){
		$("#expando").collapse('toggle')
	})

});