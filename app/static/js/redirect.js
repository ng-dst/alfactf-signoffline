function verifyAndRedirect() {
    $.ajax({
                type: 'GET',
                url: '/api/jwt/verify',
                success: function(response, textStatus, jqXHR) {
                    if (jqXHR.status === 200) {
                        setTimeout(function(){ window.location.href = '/'; }, 400);
                    }
                },
                error: function(jqXHR) {
                    const message = jqXHR.responseJSON.message || 'Произошла ошибка. Попробуйте перелогиниться';
                    showPopup(message);
                }
            });
}