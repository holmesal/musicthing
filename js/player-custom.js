function nextTrack(){
	idx = $('.sc-trackslist > .active').index()
	console.log(idx)
	next = $('.sc-trackslist > .active').eq(idx+1).index()
	console.log(next)
}

$(document).bind('onPlayerTrackSwitch.scPlayer', function(event, track){
/*   console.log(event.target, 'it jumped to this track:', track); */
/* 	elem = $('a[href*="'+track.permalink+'"]') */
	
	var newtrack = track
	
	
	setTimeout(function(event,track){
		idx = $('.sc-trackslist > .active').index()
		console.log(idx)
		
		if(idx > -1){
		
			margin = -400*idx-200
			console.log(margin)
			
			//slide
			$('.sc-controls').stop(true).animate({opacity:0},100)
			$('.sc-artwork-list,.sc-trackslist').stop(true).animate({'margin-left':margin},500,function(){
				$('.sc-controls').stop(true).animate({opacity:1},100)
			})
		
		}
		
/* 		console.log(newtrack) */
		//update the select link
		$('#btnSelect').attr('href','/artist/storetrack?track_url='+encodeURIComponent(newtrack.permalink_url)+'&track_id='+newtrack.id)
		
		//update the next/prev visibility
/* 		console.log($('.sc-trackslist > li').eq(idx)) */
		if (idx == 0){
			$('.sc-prev').hide()
			$('.sc-next').show()
		} else if (idx == $('.sc-trackslist > li').size()-1){
			$('.sc-prev').show()
			$('.sc-next').hide()
		} else{
			$('.sc-next').show()
			$('.sc-prev').show()
		}
		
		//update the next/prev listeners
		$('.sc-next').click(function(){
			$('.sc-trackslist > li').eq(idx+1).trigger("click")
		})
		
		$('.sc-prev').click(function(){
			$('.sc-trackslist > li').eq(idx-1).trigger("click")
		})
		
		
/* 		$('.sc-trackslist > li').eq(idx+1).trigger("click") */
		
	}, 10)
	
	
});

$('.sc-next').click(function(){
	alert('zomgz')
})