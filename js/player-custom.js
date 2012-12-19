$(document).bind('onPlayerTrackSwitch.scPlayer', function(event, track){
  console.log(event.target, 'it jumped to this track:', track);
/* 	elem = $('a[href*="'+track.permalink+'"]') */

	setTimeout(function(event,track){
		idx = $('.sc-trackslist > .active').index()
		console.log(idx)
		
		if(idx > -1){
		
		margin = -400*idx-200
		console.log(margin)
		
		//slide
		$('.sc-artwork-list,.sc-trackslist').animate({'margin-left':margin},500)
		
		}
		
	}, 10)
	
	
});