function nextTrack(){
	idx = $('.sc-trackslist > .active').index()
	console.log(idx)
	next = $('.sc-trackslist > .active').eq(idx+1).index()
	console.log(next)
}

$(document).bind('onPlayerTrackSwitch.scPlayer', function(event, track){
  console.log(event.target, 'it jumped to this track:', track);
/* 	elem = $('a[href*="'+track.permalink+'"]') */
	
	var newtrack = track
	
	
	setTimeout(function(event,track){
		idx = $('.sc-trackslist > .active').index()
		console.log(idx)
		
		if(idx > -1){
		
			margin = -400*idx-200
			console.log(margin)
			
			//slide
			$('.sc-controls').animate({opacity:0},100)
			$('.sc-artwork-list,.sc-trackslist').animate({'margin-left':margin},500,function(){
				$('.sc-controls').animate({opacity:1},100)
			})
		
		}
		
		console.log(newtrack)
		//update the select link
		$('#btnSelect').attr('href','/artist/storetrack?track_url='+encodeURIComponent(newtrack.permalink_url))
		
	}, 10)
	
	
});

$(document).bind('onPlayerPause.scPlayer', function(event){
	idx = $('.sc-trackslist > .active').index()
	if (idx == $('.sc-trackslist > li').size()-1){
		location.reload()
	}
  
});