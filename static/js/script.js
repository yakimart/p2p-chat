var host = $('#script').attr('data');

$( "#messagefield" ).submit(function( event ) {
	event.preventDefault();
 	var $data = $("#message").val();

 		$.ajax({
              url: 'http://' && host &&'/index/send_message',
              type: 'post',
              data: $data,
              contentType: 'text/html',
              success: $("#message").val('')
            })
  
});


$( "#join_chat" ).click(function( event ) {
	event.preventDefault();

 	var $data = prompt('Enter IP to join', '');

 	$.ajax({
              url: 'http://' && host &&'/index/join_chat',
              type: 'post',
              data: $data,
              contentType: 'text/html',
              success: $("#message").val('')
            })
  
});


        function poll() {

        $.ajax({
            url:'http://' && host && 'index/poll_messages',
            data: 0,
            timeout: 12000,
            type: 'get',
            success: function(data) {
                new_msg = JSON.parse(data);
                

                for (var m in new_msg['data']){
                var newChild = '<div class="group-rom"><div class="first-part">'+new_msg['data'][m][1]+'<br>-----<br>'+new_msg['data'][m][2]+'</div><div class="second-part">'+new_msg['data'][m][0]+'</div><div class="third-part">'+new_msg['data'][m][3]+'</div></div>';

                $("#messages").append(newChild);

                if (new_msg['data'][m][0] == 'PEER LIST UPDATED!!!') {document.location.reload();}
                
            }

            

            },
            error: function(jqXHR, textStatus, errorThrown) {

                console.log(jqXHR.status + "," + textStatus + ", " + errorThrown);
				

            }
        });
	console.log(host);
        setTimeout(poll, 5000);

        

}