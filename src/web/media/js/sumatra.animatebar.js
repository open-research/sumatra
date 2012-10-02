$.fn.animateBar = function(option) {
  if (option === 'start'){
      $this = $(this);
      $this.css('display', 'block');
      $this.find('.bar').css('width', 0);
      var i = 0,
          interval;
      interval = setInterval(function() {
        w = i++;
        $this.find('.bar').css('width', w + '%');
        if ( w === 100 ) {
          clearInterval( interval );
        }
      }, 25);
  }else if (option === 'stop'){
      $(this).css('display', 'none');
  }
};